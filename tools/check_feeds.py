#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_feeds.py — a fast pre-flight for the machine's senses.

Run it once before the trial (and any time a feed looks off). It calls each sense
against the LIVE endpoints and reports, for each: reachable? parsed? the value it
would hand the body. It writes nothing; it only reads.

    python tools/check_feeds.py

The sovereign voice (Infomaniak) is tested only if the environment carries the
secrets — otherwise it is skipped with a note:

    INFOMANIAK_TOKEN=... INFOMANIAK_PRODUCT_ID=... python tools/check_feeds.py

Exit code 0 if the eclipse-critical senses are sound (RTE by day + the computed
net), 1 otherwise. A WARN is tolerable: the body falls back to the computed net.
"""
from __future__ import annotations
import os
import sys
import time
import json
import datetime as dt
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import feeds, gift, conductor  # noqa: E402

OK, WARN, FAIL = "[ ok ]", "[warn]", "[FAIL]"


def _timed(fn, *a):
    t = time.time()
    try:
        return fn(*a), None, time.time() - t
    except Exception as e:                       # a sense must never crash the pre-flight
        return None, e, time.time() - t


def line(mark, name, detail):
    print("  %s  %-22s %s" % (mark, name, detail))


def main() -> int:
    conf = conductor.load_config()
    ok_critical = True
    print("\nFADETTE - pre-flight of the senses\n" + "-" * 56)

    # 1. cosmic texture - blind to the eclipse, but should still answer
    for name, fn in [("solar wind", feeds.solar_wind), ("Kp index", feeds.kp),
                     ("X-ray flux", feeds.xray)]:
        v, e, took = _timed(fn, conf)
        if e:
            line(WARN, name, "unreachable (%s)" % e)
        elif v is None:
            line(WARN, name, "no value (feed empty)")
        else:
            line(OK, name, "%s   (%.1fs)" % (v, took))

    # 2. RTE solar - the SOLAR eclipse's fingerprint (ECLIPSE-CRITICAL)
    v, e, took = _timed(feeds.grid_solar, conf)
    if e or not v or v.get("national_mw") is None:
        line(FAIL, "RTE solar (national)", "NO national_mw -- %s" % (e or v))
        ok_critical = False
    else:
        extra = (", Berry %s MW" % v["berry_mw"]) if v.get("berry_mw") is not None else ""
        line(OK, "RTE solar (national)", "%s MW%s   (%.1fs)" % (v["national_mw"], extra, took))

    # 3. TESS night brightness - the LUNAR eclipse's fingerprint (not blocking)
    v, e, took = _timed(feeds.sky_brightness, conf)
    if v and v.get("_fallback"):
        line(WARN, "TESS night brightness", "station not set (STARS_TO_SET) -- the gift covers the lunar")
    elif e or not v or v.get("mag_arcsec2") is None:
        line(WARN, "TESS night brightness", "no msas -- %s" % (e or v))
    else:
        line(OK, "TESS night brightness",
             "%s mag/arcsec2, cloud %s%%   (%.1fs)" % (v["mag_arcsec2"], v.get("clouds_pct"), took))

    # 4. METAR - the Berry's local sky (the chain LFLD -> LFOA -> LFLX)
    v, e, took = _timed(feeds.metar, conf)
    if e or not v:
        line(WARN, "METAR (the Berry)", "no reading -- %s" % (e or "chain silent"))
    else:
        line(OK, "METAR (the Berry)", "%s: %s   (%.1fs)" % (v["station"], v["metar"][:48], took))

    # 5. the computed net (offline, must ALWAYS work) - proof on the real eclipse max
    when = dt.datetime(2026, 8, 12, 18, 15, tzinfo=dt.timezone.utc)
    v, e, took = _timed(gift.want_of_light, conf["place"]["latitude"], conf["place"]["longitude"], when)
    w = (v or {}).get("want_of_light", 0)
    if e or w < 0.5:
        line(FAIL, "computed net (gift)", "want=%s at the eclipse max -- expected high %s" % (w, e or ""))
        ok_critical = False
    else:
        line(OK, "computed net (gift)", "want=%s at 12 Aug 18:15 UTC (the eclipse is caught)" % round(w, 3))

    # 6. Infomaniak - the sovereign voice (only if the secrets are present)
    if not (os.environ.get("INFOMANIAK_TOKEN") and os.environ.get("INFOMANIAK_PRODUCT_ID")):
        line(WARN, "Infomaniak", "set INFOMANIAK_TOKEN and INFOMANIAK_PRODUCT_ID to test the voice")
    else:
        url = "%s/%s/openai/v1/models" % (conf["infomaniak"]["base_url"], os.environ["INFOMANIAK_PRODUCT_ID"])
        try:
            req = urllib.request.Request(url, headers={"Authorization": "Bearer %s" % os.environ["INFOMANIAK_TOKEN"]})
            with urllib.request.urlopen(req, timeout=30) as r:
                ids = [m.get("id") for m in json.loads(r.read().decode("utf-8")).get("data", [])]
            wt, wf = conf["infomaniak"]["text_model"], conf["finale"]["model"]
            line(OK if wt in ids else WARN, "Infomaniak models",
                 "%d models; text '%s' %s, finale '%s' %s"
                 % (len(ids), wt, "present" if wt in ids else "MISSING",
                    wf, "present" if wf in ids else "MISSING"))
        except Exception as e:
            line(FAIL, "Infomaniak models", "%s" % e)
        try:
            from src import infomaniak
            t0 = time.time()
            txt = infomaniak.text(conf, "Reponds en un seul mot.", "Dis le mot: pret.",
                                  temperature=0.0, max_tokens=5)
            line(OK, "Infomaniak generate", "replied %r   (%.1fs)" % (txt[:30], time.time() - t0))
        except Exception as e:
            line(FAIL, "Infomaniak generate", "%s" % e)

    print("-" * 56)
    print("GO -- the eclipse-critical senses are sound." if ok_critical
          else "NO-GO -- an eclipse-critical sense failed (see [FAIL] above).")
    print("(A [warn] is tolerable: the body falls back to the computed net.)\n")
    return 0 if ok_critical else 1


if __name__ == "__main__":
    sys.exit(main())

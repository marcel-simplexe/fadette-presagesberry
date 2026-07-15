# -*- coding: utf-8 -*-
"""
sky.py — "what the sky is doing", at an instant, seen from the Berry.

We gather the cosmic texture, the daylight (RTE), the nightlight (TESS), the
Berry's sky (METAR), and the computed context (ephemeris: phase, altitudes). Then
we decide on an OBSERVED "want of light": by day from the RTE solar collapse, by
night from the TESS brightness drop.

The gift (calculation) only steps in as a FALLBACK: if the observation is mute or
ambiguous (a missing feed, clouds, a low moon), we take the computed value so the
eclipse is not missed. The provenance is traced ("observed" / "fallback-gift") in
the archive — but the lens itself receives only a state, never a date.
"""
from __future__ import annotations
import datetime as dt
from . import feeds, ephemeris, gift


def _safe(fn, *a):
    """A sense that fails returns nothing, never an exception that kills the breath."""
    try:
        return fn(*a)
    except Exception:
        return None


def _peak_gift(conf: dict, lat: float, lon: float, when_utc: dt.datetime) -> dict:
    """The greatest want of light over the stretch of time THIS BREATH ANSWERS FOR.

    A breath is not a photograph, it is a WATCH: it is responsible for the hours since
    the last one. Sampling a single instant every two hours cannot see an event that
    lasts less than two hours -- and the failing of light this machine was built for
    lasts a hundred minutes. Worse, a scheduled run is not punctual: it drifts, and it
    is sometimes dropped. A machine whose one great answer depends on a clock it does
    not own has no answer at all.

    So the breath looks BACK, minute by minute, over the stretch it owns, and keeps the
    sky's deepest want. It misses nothing, however late it wakes.

    This is not aiming the machine at a date: every breath of every day looks back the
    same way. The eye still receives only a state. The body still knows no eclipse.
    """
    span = int((conf.get("gift") or {}).get("look_back_min", 0) or 0)
    step = int((conf.get("gift") or {}).get("look_back_step_min", 5) or 5)
    best, at = gift.want_of_light(lat, lon, when_utc), when_utc
    if span <= 0:
        return best, at
    for m in range(step, span + 1, step):
        t = when_utc - dt.timedelta(minutes=m)
        c = _safe(gift.want_of_light, lat, lon, t)
        if c and c.get("want_of_light", 0.0) > best.get("want_of_light", 0.0):
            best, at = c, t
    return best, at


def state(conf: dict, when_utc: dt.datetime | None = None) -> dict:
    when_utc = when_utc or dt.datetime.now(dt.timezone.utc)
    lat, lon = conf["place"]["latitude"], conf["place"]["longitude"]

    eph = ephemeris.read(lat, lon, when_utc)
    cosmic = {"solar_wind": _safe(feeds.solar_wind, conf), "kp": _safe(feeds.kp, conf), "xray": _safe(feeds.xray, conf)}
    day_light = _safe(feeds.grid_solar, conf)
    night_light = _safe(feeds.sky_brightness, conf)
    berry = _safe(feeds.metar, conf)

    want_obs, source = _observed_want(eph, day_light, night_light, berry)

    computed, watched = ({}, when_utc)
    if conf["gift"]["active"]:
        computed, watched = _peak_gift(conf, lat, lon, when_utc)
        # THE WATCH REPORTS THE MOMENT IT KEPT. If the light failed at some point of the
        # stretch this breath answers for, it is THAT sky the scribe must be given -- the
        # sun's height, the moon's, and the failing, all of the same instant. Otherwise the
        # eye would be handed a want of light out of a past hour together with the sky of
        # now, and would sing a darkness at a sunny breakfast. On an ordinary breath the
        # deepest want IS now, and nothing moves.
        if watched != when_utc:
            eph = ephemeris.read(lat, lon, watched)
    want, prov = want_obs, source
    if conf["gift"]["active"]:
        trig = conf["gift"].get("trigger", 0.15)
        if want_obs is None or (computed.get("want_of_light", 0) - (want_obs or 0)) > trig:
            want = computed.get("want_of_light", want_obs)
            prov = "fallback-gift"

    return {
        "instant_utc": when_utc.isoformat(timespec="minutes"),
        "watched_utc": watched.isoformat(timespec="minutes"),   # traced; never handed to the eye
        "ephemeris": eph,
        "cosmic": cosmic,
        "day_light": day_light,
        "night_light": night_light,
        "berry": berry,
        "want_of_light": round(want, 3) if want is not None else None,
        "want_source": prov,                 # observed | fallback-gift | undetermined
        "_computed_fallback": computed,       # traced, never handed to the lens
    }


def _observed_want(eph: dict, day_light, night_light, berry=None):
    """Deduce the want of light from MEASURED feeds only, with the ephemeris for
    context (where the light ought to be).

    THE TRAP, found on the first cloudy trial day: a covered sky drops solar
    production exactly as an eclipse does. Read naively, an ordinary grey morning
    reads as a failing sun. So the observed path only speaks when the weather says
    the sky is CLEAR: under cloud, low production is expected, not an omen, and we
    hand back to the computed net (gift), which is blind to weather. An eclipse on a
    clear day still triggers; a storm no longer counterfeits one."""
    covered = _is_covered(berry)
    if (eph["day"] and eph["sun_alt_deg"] > 8 and not covered
            and day_light and day_light.get("national_mw") is not None):
        expected = max(1.0, eph["sun_alt_deg"] * 700.0)   # MW, order of magnitude
        miss = 1.0 - min(1.0, day_light["national_mw"] / expected)
        # a clear sky that still loses most of its light is the only observed eclipse
        if miss >= 0.5:
            return max(0.0, round(miss, 3)), "observed"
        return 0.0, "observed"
    if (eph["night"] and eph["moon_illum"] > 0.8 and not covered
            and night_light and night_light.get("mag_arcsec2") is not None):
        msas = night_light["mag_arcsec2"]                 # ~19 full-moon-clear ; ~22 dark
        miss = min(1.0, max(0.0, (msas - 19.0) / 3.0))
        return round(miss, 3), "observed"
    return None, "undetermined"


def _is_covered(berry) -> bool:
    """Is the Berry sky overcast? Read from the METAR the machine already holds.
    Cloud cover BKN (broken) or OVC (overcast), or any present weather of rain/storm,
    means low solar production is the weather's doing, not the moon's. Unknown ->
    treated as covered, so a missing METAR never manufactures an eclipse."""
    if not berry:
        return True
    raw = (berry.get("metar") or berry.get("raw") or "")
    if not isinstance(raw, str) or not raw:
        return True
    r = raw.upper()
    if " OVC" in r or " BKN" in r:
        return True
    for w in (" RA", " SHRA", " TSRA", " TS", " DZ", " +RA", "-RA", " GR", " FG", " BR"):
        if w in r:
            return True
    return False

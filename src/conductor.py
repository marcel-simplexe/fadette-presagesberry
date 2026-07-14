# -*- coding: utf-8 -*-
"""
conductor.py — the body of the machine, its entry point.

The BODY knows the calendar: the birth (1 August), the death (31 August). The EYE
(the lens) never does. That boundary is the whole doctrine.

At each beat (the heartbeat), in the window of life only:
  - the body weighs the sky's agitation and utters that many omens - none when the
    sky is still, several in a storm, a flood when the light fails - each omen a
    cycle sky -> presage (text) -> air (a score, engraved to .mid) -> augury ;
  - at the refine hour: the lens drifts one notch ;
  - on the day of death, at the last breath: the closing nouvelle (about twenty pages).
"""
from __future__ import annotations
import os
import sys
import datetime as dt
import yaml

from . import sky as sky_mod
from . import memory, lens, midi, augury, drift, finale, tempo

ROOT = memory.ROOT


def load_config() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def in_window(conf: dict, day: dt.date) -> bool:
    b = dt.date.fromisoformat(conf["window"]["birth"])
    d = dt.date.fromisoformat(conf["window"]["death"])
    return b <= day <= d


def _emit(conf: dict, sky: dict, prompts: dict, now: dt.datetime, k: int, n: int) -> dict:
    """Utter ONE omen for this breath. In a flood (n>1) the later cries get a small
    nudge to see what the others did not, so the flood does not repeat itself."""
    eph = sky["ephemeris"]
    breath = {
        "time": now.strftime("%H:%M"),
        "night": eph["night"],
        "phase": eph["phase_bucket"],
        "dark": (sky.get("want_of_light") or 0.0) > 0.25,
        "notch": prompts.get("notch", 0),
        "want_source": sky.get("want_source"),
    }
    if n > 1:
        breath["nth"], breath["of"] = k + 1, n
    extra = ""
    if k > 0:
        extra = (
            "\n\n(This is one cry among several uttered in the same hour; let it see "
            "what the others did not - another of the night's people, or another face "
            "of the same dread, never the same vision twice.)")
    try:
        fragment = lens.sky_to_text(conf, sky, prompts, extra=extra)
        breath["presage"] = fragment
    except Exception as e:
        breath["presage_error"] = str(e)
        fragment = None
    if fragment:
        try:
            breath["presage_en"] = lens.to_english(conf, fragment)
        except Exception as e:
            breath["presage_en_error"] = str(e)
        try:
            score = lens.text_to_score(conf, fragment, prompts)
            breath["score"] = score
            name = f"midi-{now.strftime('%Y-%m-%dT%H%MZ')}-{k + 1}.mid"
            midi.engrave(score, memory.work_path(name))
            breath["midi"] = f"work/{name}"
        except Exception as e:
            breath["score_error"] = str(e)
    breath["augury"] = augury.read(sky)
    memory.add_breath(breath)
    return breath


def breathe(conf: dict) -> int:
    """One beat of the heartbeat. The body weighs the sky and utters that many omens:
    none when the sky is still, several in a storm, a flood when the light fails. The
    flood on the day the light fails is the machine's answer to the sky, not to a date."""
    now = dt.datetime.now(dt.timezone.utc)
    prompts = memory.read_lens()
    sky = sky_mod.state(conf, now)
    vh = conf.get("tempo", {}).get("vespers_hour_utc", 20)
    vespers = vh <= now.hour < vh + 2
    n = tempo.how_many(sky, conf, is_vespers=vespers)
    if n <= 0:
        print("The sky is still; the scribe keeps silence this breath ({}).".format(sky.get("want_source")))
        return 0
    print("One breath: the sky moves the scribe to {} omen{}.".format(n, "s" if n != 1 else ""))
    for k in range(n):
        _emit(conf, sky, prompts, now, k, n)
    return n



def main() -> int:
    conf = load_config()

    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()

    if not in_window(conf, today):
        print(f"Outside the window of life ({today}). The machine is silent.")
        return 0

    death = dt.date.fromisoformat(conf["window"]["death"])
    refine = now.hour >= 23   # the day's last act

    if refine:
        if conf.get("lens", {}).get("drift", True):
            print("Refining the lens (one notch).")
            drift.one_notch(conf)
        else:
            print("Lens drift disabled; the prompt stays as written.")
        if today == death:
            print("The last breath. The nouvelle.")
            try:
                finale.write_novella(conf)
            except Exception as e:
                print(f"  novella: failed {e}")
            print("The machine has given its last breath.")
    else:
        breathe(conf)

    return 0


if __name__ == "__main__":
    sys.exit(main())

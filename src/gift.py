# -*- coding: utf-8 -*-
"""
gift.py — "the gift": the machine's second sight.

In Berry witchcraft the sorcerer, the meneu, has *the gift*. Marcel Simplexe grafts
a FACULTY onto the machine — not a sense. It is a CALCULATION, declared as such,
never disguised as observation.

Role: FALLBACK. Observation leads (RTE by day, TESS by night). The gift only
recovers the eclipse when the natural reading is mute or doubtful (a clouded night
of the 28th, a low dawn moon). We stay honest: this number exists because we
computed the geometry.

Output: a continuous scalar, the "want of celestial light", in [0, 1].
0 = the sky gives all its light. 1 = the light is as wanting as it can be.
The lens receives only a NUMBER — never a date, never the word "eclipse".
"""
from __future__ import annotations
import math
import datetime as dt
import ephem

_R_SUN = 0.265
_R_MOON = 0.272
_R_EARTH_SHADOW = 0.70   # angular radius of Earth's umbra at the moon's distance


def want_of_light(lat: float, lon: float, when_utc: dt.datetime) -> dict:
    """Compute the want of celestial light (the fallback net). APPROXIMATE."""
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = ephem.Date(when_utc)
    obs.pressure = 0
    sun = ephem.Sun(obs)
    moon = ephem.Moon(obs)

    # solar want: the moon passes in front of the sun (by day)
    want_sun = 0.0
    if float(sun.alt) > math.radians(-2):
        sep = math.degrees(float(ephem.separation(sun, moon)))
        want_sun = _overlap(sep, _R_SUN, _R_MOON)

    # lunar want: the moon dips into Earth's shadow (by night, near full)
    want_moon = 0.0
    if float(moon.alt) > math.radians(-2) and float(moon.phase) > 80:
        sep_antisolar = 180.0 - math.degrees(float(ephem.separation(sun, moon)))
        shadow = _overlap(sep_antisolar, _R_EARTH_SHADOW, _R_MOON)
        want_moon = shadow * (float(moon.phase) / 100.0)

    want = max(want_sun, want_moon)
    return {
        "want_of_light": round(want, 3),
        "_want_solar": round(want_sun, 3),
        "_want_lunar": round(want_moon, 3),
        "_note": "calculation (the gift) — a fallback net, never named to the lens",
    }


def _overlap(sep_deg: float, r1: float, r2: float) -> float:
    if sep_deg >= (r1 + r2):
        return 0.0
    if sep_deg <= abs(r1 - r2):
        return 1.0
    return (r1 + r2 - sep_deg) / (r1 + r2 - abs(r1 - r2))


def want_over_day(lat: float, lon: float, date_iso: str, step_min: int = 10) -> dict:
    """Scan a whole (simulated) day and return the DEEPEST want of light and the
    moment it occurs. Used by the POC to catch an eclipse that falls between the
    nominal breaths — the same idea the real machine should later apply to the
    recent feed trace. date_iso is 'YYYY-MM-DD' (UTC)."""
    y, m, d = (int(x) for x in date_iso.split("-"))
    best, best_t, kind = 0.0, None, "none"
    t = dt.datetime(y, m, d, 0, 0, tzinfo=dt.timezone.utc)
    end = t + dt.timedelta(days=1)
    while t < end:
        w = want_of_light(lat, lon, t)
        if w["want_of_light"] > best:
            best = w["want_of_light"]
            best_t = t
            kind = "solar" if w["_want_solar"] >= w["_want_lunar"] else "lunar"
        t += dt.timedelta(minutes=step_min)
    return {"want": round(best, 3),
            "at_utc": best_t.isoformat(timespec="minutes") if best_t else None,
            "kind": kind}

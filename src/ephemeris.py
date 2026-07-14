# -*- coding: utf-8 -*-
"""
ephemeris.py — the GPS as CONTEXT, not as prediction.

From the coordinate of the Berry we compute, locally, what is deterministic: the
altitude of the sun and the moon, the phase, the age, the distance, day or night.

BLINDNESS RULE: we hand over ONLY the phase and the altitudes. NEVER the sun-moon
elongation nor the ecliptic latitude — those would betray an eclipse in advance
(an eclipse falls when the new/full moon lands on a node). The machine must not
*know* the eclipse is coming; it must *observe* that the light is leaving, through
the ground feeds (RTE by day, TESS by night). Eclipse geometry, if ever allowed,
lives in gift.py — not here.
"""
from __future__ import annotations
import math
import datetime as dt
import ephem


def read(lat: float, lon: float, when_utc: dt.datetime | None = None) -> dict:
    """The deterministic celestial state at the place and instant. Phase only."""
    when_utc = when_utc or dt.datetime.now(dt.timezone.utc)
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = ephem.Date(when_utc)
    obs.pressure = 0          # no refraction: we want the bare geometry

    sun = ephem.Sun(obs)
    moon = ephem.Moon(obs)

    sun_alt = math.degrees(float(sun.alt))
    moon_alt = math.degrees(float(moon.alt))
    illum = float(moon.phase) / 100.0                  # 0 = new, 1 = full ; this is PHASE

    last_new = ephem.previous_new_moon(obs.date)
    age = float(obs.date) - float(last_new)

    next_full = ephem.next_full_moon(obs.date)
    last_full = ephem.previous_full_moon(obs.date)
    waxing = (float(next_full) - float(obs.date)) < (float(obs.date) - float(last_full))

    distance_km = float(moon.earth_distance) * 149597870.7
    night = sun_alt < -6.0
    day = sun_alt > 0.0

    return {
        "instant_utc": when_utc.isoformat(timespec="minutes"),
        "sun_alt_deg": round(sun_alt, 2),
        "moon_alt_deg": round(moon_alt, 2),
        "moon_illum": round(illum, 3),
        "moon_age_days": round(age, 2),
        "moon_waxing": bool(waxing),
        "moon_distance_km": int(distance_km),
        "day": bool(day),
        "night": bool(night),
        "phase_bucket": _bucket(illum, waxing),     # waxing | waning | full | dark
        "phase_word": _phase_word(illum, waxing),   # a word for the lens, never an eclipse
    }


def _bucket(illum: float, waxing: bool) -> str:
    if illum < 0.04:
        return "dark"
    if illum > 0.96:
        return "full"
    return "waxing" if waxing else "waning"


def _phase_word(illum: float, waxing: bool) -> str:
    if illum < 0.04:
        return "dark moon"
    if illum > 0.96:
        return "full moon"
    if illum < 0.45:
        return "waxing crescent" if waxing else "waning crescent"
    if illum < 0.55:
        return "first quarter" if waxing else "last quarter"
    return "waxing gibbous" if waxing else "waning gibbous"

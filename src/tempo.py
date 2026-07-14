# -*- coding: utf-8 -*-
"""
tempo.py - the tempo of the machine is the tempo of the sky.

The scribe speaks when the sky moves him. Each breath (the cron heartbeat) the BODY
weighs how far the sky departs from calm - the troubled north (Kp), a solar flare, a
hurrying wind, and ABOVE ALL a failing of light - and that decides how many omens the
breath utters: one or none when the sky is still, several in a storm, a flood when the
light fails. The machine never knows it is an eclipse: the flood is only its answer to
the want of light, the same answer it would give to a freak aurora.

Like everything in the body, this reads numbers; the EYE never does. No date, no
learned name, never the word "eclipse" enters here either.
"""
from __future__ import annotations
import math as _math
import re as _re


def _flare_num(xray) -> float:
    """Turn a solar X-ray reading into 0 (quiet) / 1 (M) / 2 (X), defensively."""
    if not xray:
        return 0.0
    cls = None
    if isinstance(xray, dict):
        cls = xray.get("class") or xray.get("flare_class") or xray.get("level")
        if cls is None:
            flux = xray.get("flux_w_m2") or xray.get("flux")
            try:
                f = float(flux)
                if f >= 1e-4:
                    return 2.0
                if f >= 1e-5:
                    return 1.0
            except (TypeError, ValueError):
                return 0.0
            return 0.0
    elif isinstance(xray, str):
        cls = xray
    if isinstance(cls, str) and cls[:1].upper() in ("M", "X"):
        return 2.0 if cls[:1].upper() == "X" else 1.0
    return 0.0


def _of_the_day(sky: dict, c: dict) -> float:
    """The texture of the DAY ITSELF, in omens. Without this the machine hears only the
    cosmos -- and a calm summer sky is cosmically silent, so it spoke once a day, always
    at the same evening beat, and the whole day (the dawn, the noon heat, the storm over
    the wood) passed unsaid. The terms are small BY DESIGN: an ordinary day must draw
    one or two omens, never anything near the flood a failing light draws."""
    n = float(c.get("base", 0.10))                       # the bare fact of being awake

    eph = sky.get("ephemeris") or {}

    # THE LIGHT CHANGING HANDS. Not a switch -- a BELL on the horizon, fading away from
    # it. A switch on a band six degrees wide is a lottery: the sun crosses that band in
    # an hour and the machine breathes every two, so it steps clean over the dawn on most
    # days of the month and the whole texture of the day is lost. A bell is felt by
    # WHICHEVER breath falls nearest the crossing, and never missed.
    alt = eph.get("sun_alt_deg")
    if alt is not None:
        deg = float(c.get("liminal_deg", 11.0)) or 11.0
        n += float(c.get("per_liminal", 0.9)) * _math.exp(-(float(alt) / deg) ** 2)

    # THE MOON, only when she is actually THERE. The phase bucket lasts four days; hanging
    # an omen on the bucket makes the machine cry at all forty-eight breaths of those four
    # days -- a second flood, and not the one the work is for. What the lore watches is a
    # moon RIDING THE SKY and lighting the field: her height, and her brightness. She
    # rises fifty minutes later each night, so the hour she moves the scribe walks
    # through the month, and no two days are struck the same.
    m_alt, illum = eph.get("moon_alt_deg"), eph.get("moon_illum")
    if m_alt is not None and illum is not None:
        per_moon = float(c.get("per_moon", 0.7))
        if float(m_alt) > 0.0:                           # she is up: her light on the fields
            n += per_moon * float(illum) * _math.sin(_math.radians(float(m_alt)))
        elif eph.get("night"):                           # she is gone: the black night
            n += per_moon * (1.0 - float(illum)) * float(c.get("per_black_moon", 0.5))

    raw = ((sky.get("berry") or {}).get("metar") or "").upper()
    if raw:
        if "TS" in raw:
            n += float(c.get("per_storm", 2.0))
        elif "RA" in raw or "SH" in raw or "DZ" in raw:
            n += float(c.get("per_rain", 0.8))
        if " FG" in raw or " BR" in raw:
            n += float(c.get("per_mist", 0.6))
        if "OVC" in raw or "BKN" in raw:
            n += float(c.get("per_overcast", 0.4))
        t = _re.search(r"\b(M?\d{2})/(M?\d{2})\b", raw)
        if t:
            g = t.group(1)
            try:
                deg = -int(g[1:]) if g.startswith("M") else int(g)
                if deg >= int(c.get("hot_deg", 30)):
                    n += float(c.get("per_heat", 0.8))
            except ValueError:
                pass
    return n


def agitation(sky: dict, conf: dict) -> float:
    """How far the sky departs from calm, measured in omens. 0 = perfectly still."""
    c = conf.get("tempo", {})
    cosmic = sky.get("cosmic") or {}
    kp = cosmic.get("kp") or 0.0
    wind = ((cosmic.get("solar_wind") or {}).get("speed_km_s")) or 0.0
    flare = _flare_num(cosmic.get("xray"))
    want = sky.get("want_of_light") or 0.0
    return (c.get("per_kp", 0.5) * max(0.0, float(kp) - c.get("calm_kp", 2))
            + c.get("per_wind", 1.0) * max(0.0, (float(wind) - c.get("calm_wind", 450)) / c.get("wind_span", 130))
            + c.get("per_flare", 1.5) * flare
            + _of_the_day(sky, c)
            + c.get("want_surge", 11.0) * (float(want) ** c.get("want_power", 2)))


def how_many(sky: dict, conf: dict, is_vespers: bool = False) -> int:
    """How many omens this breath should utter, given the sky's agitation."""
    c = conf.get("tempo", {})
    floor = c.get("vespers_floor", 1) if is_vespers else 0
    n = round(floor + agitation(sky, conf))
    return max(0, min(int(n), int(c.get("cap", 12))))

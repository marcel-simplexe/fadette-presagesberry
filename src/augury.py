# -*- coding: utf-8 -*-
"""
augury.py — the augury: the third voice, after the presage and the air.

This is NOT a model. It is a fixed table of signs that turns each captured FIGURE,
and the direction in which it moves, into an omen — a stable cipher laid over the
numbers. Like everything the lens touches, it is blind: it reads the figures,
never the calendar. The same table is used everywhere, so the reading is
reproducible.

read(sky) -> a list of [figure, reading, sign] rows, ready for the page.
"""
from __future__ import annotations


def figures(sky: dict) -> dict:
    """Pull the bare figures the augury reads out of the sky-state."""
    eph = sky.get("ephemeris", {})
    cosmic = sky.get("cosmic", {})
    wind = (cosmic.get("solar_wind") or {}).get("speed_km_s")
    kp = cosmic.get("kp")
    xray = cosmic.get("xray")
    want = sky.get("want_of_light")
    light = None if want is None else max(0.0, min(1.0, 1.0 - want))   # light present
    return {
        "wind": wind,
        "kp": kp,
        "fire": ("flare" if (xray is not None and xray >= 1e-5) else ("quiet" if xray is not None else None)),
        "light": light,
        "phase": eph.get("phase_bucket"),       # waxing | waning | full | dark
        "night": bool(eph.get("night")),
    }


def read(sky: dict) -> list:
    """The augury rows. Figures from down feeds are skipped if absent; the light
    and the moon, which come from the ephemeris and the gift, are always present."""
    f = figures(sky)
    rows = []

    if f["wind"] is not None:
        w = f["wind"]
        rows.append(["solar wind", f"{int(round(w))} km/s",
                     "the dead sleep; nothing rides" if w < 400 else
                     ("the Wild Hunt rides hard" if w >= 550 else "the air above holds its breath")])

    if f["kp"] is not None:
        k = f["kp"]
        rows.append(["the north", f"Kp {k:g}",
                     "the north keeps its peace" if k <= 3 else
                     ("the north has a fever \u2014 discord comes" if k >= 5 else "the north stirs in its sleep")])

    if f["fire"] is not None:
        rows.append(["the sun's fire", f["fire"],
                     "a spark flies from the anvil" if f["fire"] == "flare" else "the great forge lies cold"])

    if f["light"] is not None:
        L = f["light"]
        lamp = "the moon's lamp" if f["night"] else "the lamp"
        rows.append(["light", f"{int(round(L * 100))}%",
                     f"{lamp} is whole" if L > 0.9 else
                     (f"a hand passes over {lamp}" if L < 0.5 else f"{lamp} gutters")])

    if f["phase"] is not None:
        p = f["phase"]
        sign = ("a night of power" if p == "full" else
                "swear nothing, sow nothing" if p == "dark" else
                "the time to bind and to build" if p == "waxing" else
                "the time to undo what was bound")
        rows.append(["the moon", p, sign])

    return rows

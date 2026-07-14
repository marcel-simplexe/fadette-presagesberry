# -*- coding: utf-8 -*-
"""
feeds.py — the machine's senses. No model here: we read, we do not think.

Four families:
  1. cosmic texture  — NOAA SWPC (solar wind, Bz, Kp, X-ray). BLIND to the eclipse.
  2. daylight        — RTE eCO2mix (solar power). Catches the SOLAR eclipse.
  3. nightlight      — TESS / STARS4ALL (sky brightness). Catches the LUNAR eclipse.
  4. the Berry's sky — METAR chain (the Berry -> Avord -> Chateauroux).

Every function is fault-tolerant: a feed that does not answer returns None, never
an exception that would kill the breath.
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error

_UA = {"User-Agent": "fadette/1.0 (Marcel Simplexe; watching the sky over the Berry)"}
_TIMEOUT = 20


def _get_json(url: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _get_text(url: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=_TIMEOUT) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


# ---------------------------------------------------------------- 1. cosmic
def solar_wind(conf: dict) -> dict | None:
    plasma = _get_json(conf["feeds"]["solar_wind_plasma"])
    mag = _get_json(conf["feeds"]["solar_wind_mag"])
    out = {}
    if plasma and len(plasma) > 1:
        cols, *rows = plasma
        d = dict(zip(cols, rows[-1]))
        out["speed_km_s"] = _f(d.get("speed"))
        out["density"] = _f(d.get("density"))
    if mag and len(mag) > 1:
        cols, *rows = mag
        d = dict(zip(cols, rows[-1]))
        out["bz_nT"] = _f(d.get("bz_gsm"))
    return out or None


def kp(conf: dict):
    """Le Kp planetaire n'a jamais eu la meme forme que plasma/mag : c'est une liste
    de DICTS (`[{"time_tag":..., "Kp":..., ...}, ...]`), pas une liste de listes avec
    en-tete. Prouve en direct le 14 juillet 2026 : HTTP 200, JSON frais (donnees du
    jour meme), et pourtant `data[-1][1]` levait KeyError — indexer un dict par un
    entier. Ce n'etait pas le reseau qui echouait, c'etait cette ligne."""
    data = _get_json(conf["feeds"]["planetary_kp"])
    if data and len(data) > 1:
        last = data[-1]
        if isinstance(last, dict):
            return _f(last.get("Kp"))
        return _f(last[1])          # au cas ou NOAA reviendrait un jour a l'ancienne forme
    return None


def xray(conf: dict):
    data = _get_json(conf["feeds"]["xray_goes"])
    if isinstance(data, list) and data:
        return _f(data[-1].get("flux"))
    return None


# ------------------------------------------------------- 2. daylight (the sun)
def grid_solar(conf: dict) -> dict | None:
    """Solar power on the French grid (RTE eCO2mix), in MW. On 12 August at dusk
    this collapses toward zero before the ordinary nightfall: the measured
    fingerprint of the solar eclipse."""
    out = {}
    nat = _get_json(conf["feeds"]["rte_national"])
    if nat and nat.get("results"):
        for rec in nat["results"]:
            if rec.get("solaire") is not None:
                out["national_mw"] = _f(rec["solaire"])
                out["instant"] = rec.get("date_heure")
                break
    reg = _get_json(conf["feeds"]["rte_region"])
    if reg and reg.get("results"):
        for rec in reg["results"]:
            if rec.get("solaire") is not None:
                out["berry_mw"] = _f(rec["solaire"])
                break
    return out or None


# ------------------------------------------------------- 3. nightlight (the moon)
def _first(d: dict, keys):
    """First present, numeric-parseable value among several possible field names."""
    for k in keys:
        if k in d and d[k] is not None:
            v = _f(d[k])
            if v is not None:
                return v
    return None


def sky_brightness(conf: dict) -> dict | None:
    """Night-sky brightness (mag/arcsec2) of a SPANISH dark-site TESS-W station of
    the STARS4ALL network, with a cloud estimate. On the night of 28 August, over
    the full moon, this brightness drops: the (partial, from Europe) fingerprint of
    the lunar eclipse.

    The STARS4ALL live readings are served through Grafana/IDA; the one stable REST
    route is {tess_base}{tess_readings_path} (default /photometers/{station}), which
    carries the photometer document. We read it defensively and accept several field
    spellings. The exact dark-site station name is read once from
    tess.dashboards.stars4all.eu and set in config.yaml; until it is set, and on any
    failure, we return None and the gift carries the want-of-light instead."""
    f = conf["feeds"]
    base, station = f.get("tess_base", ""), f.get("tess_station", "")
    if not station or station == "STARS_TO_SET":
        return {"_fallback": "TESS station not set — read it from tess.dashboards.stars4all.eu"}
    tmpl = f.get("tess_readings_path", "/photometers/{station}")
    data = _get_json(base.rstrip("/") + tmpl.format(station=station))
    rec = data[0] if isinstance(data, list) and data else data
    if not isinstance(rec, dict):
        return None
    mag = _first(rec, ("mag_arcsec2", "magnitude", "mag", "msas", "sky_brightness", "value"))
    if mag is None:
        return None
    return {"mag_arcsec2": mag,
            "clouds_pct": _first(rec, ("clouds_pct", "cloud", "clouds", "cover", "ir_cloud"))}


# ------------------------------------------------------- 4. the Berry's sky
def metar(conf: dict) -> dict | None:
    """The first station in the chain that answers with a fresh reading.
    the Berry (LFLD) -> Avord (LFOA) -> Chateauroux (LFLX). All in the Berry."""
    base = conf["feeds"]["metar_base"]
    for icao in conf["feeds"]["metar_chain"]:
        txt = _get_text(f"{base}?ids={icao}&format=raw&hours=2")
        if txt and txt.strip() and icao in txt:
            return {"station": icao, "metar": txt.strip().splitlines()[0]}
    return None


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

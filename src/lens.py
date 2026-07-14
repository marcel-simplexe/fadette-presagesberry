# -*- coding: utf-8 -*-
"""
lens.py — the lens. It turns the sky into text, then the text into a score,
through Berry witchcraft read in George Sand.

ALL prompts now live in config.yaml under `prompts:` — edit them there, not here.
This module only reads them (with a safe default if a key is missing) and applies
the absolute blindness rule by construction: it gives the model only a state of the
sky turned to sensations, never a date nor the word "eclipse".
"""
from __future__ import annotations
import json
import re
from . import infomaniak, entropy

# Safe fallbacks, used only if a prompt is missing from config.yaml.
_DEFAULT_SYSTEM = (
    "Tu es un scribe du Berry qui lit le ciel pour son sens caché, dans la voix "
    "rustique de George Sand. Ne nomme jamais la science, la mesure ni la cause. Quand "
    "la clarté manque sans raison, prends-la pour un signe."
)
_DEFAULT_PRESAGE = (
    "À partir de l'état du ciel ci-dessous, écris UN court présage du Berry (3 phrases au "
    "plus) dans la voix de George Sand. Pas de titre, pas de date. Finis sur une image."
)
_DEFAULT_AIR = (
    "À partir du fragment ci-dessous, rends UNIQUEMENT une liste JSON d'événements de note "
    '[{"note":62,"start":0.0,"duration":0.5,"force":70}, ...], 16 à 40 notes, un air de '
    "veillée grave et tournant ; là où la clarté manque, qu'il défaille et se vide."
)
_DEFAULT_TRANSLATE = (
    "Translate the following Berry omen from French into English, keeping George Sand's "
    "plain rustic register and the same images; add nothing, explain nothing, no title "
    "or quotation marks. Return only the English."
)


def system(conf: dict) -> str:
    return _p(conf).get("system", _DEFAULT_SYSTEM)


def seed_presage(conf: dict) -> str:
    return _p(conf).get("presage", _DEFAULT_PRESAGE)


def seed_air(conf: dict) -> str:
    return _p(conf).get("air", _DEFAULT_AIR)


def seed_translate(conf: dict) -> str:
    return _p(conf).get("translate", _DEFAULT_TRANSLATE)


def to_english(conf: dict, french: str, max_tokens: int = 600) -> str:
    """Translate a French fragment into English (FR -> EN), to serve the English page.
    French is the source; this never runs the other way. Faithful, low temperature."""
    if not (french or "").strip():
        return ""
    task = seed_translate(conf) + "\n\n--- le texte source (francais) ---\n" + french
    return infomaniak.text(conf, system(conf), task, temperature=0.3, max_tokens=max_tokens)


def sky_to_text(conf: dict, sky: dict, prompts: dict, extra: str = "") -> str:
    """Transcribe the state of the sky into a fragment (the lens, in its text sense).
    `extra` carries a small per-omen nudge during a flood, so it does not repeat."""
    task = (prompts.get("text", seed_presage(conf)) + "\n\n--- the state of the sky ---\n"
            + say_the_sky(sky) + entropy.nudge_text() + (extra or ""))
    raw = infomaniak.text(conf, system(conf), task, temperature=0.95, max_tokens=520)
    return _clean_presage(raw)


def text_to_score(conf: dict, fragment: str, prompts: dict) -> list:
    """Turn the fragment into a symbolic score (note events). The deterministic
    engraving to .mid is done afterwards by src/midi.py."""
    task = (prompts.get("score", seed_air(conf)) + entropy.nudge_air()
            + "\n\n--- the fragment ---\n" + fragment)
    raw = infomaniak.text(conf, system(conf), task, temperature=0.8, max_tokens=1500)
    return _extract_notes(raw)


_ORD = ["", "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
        "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth",
        "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth",
        "twenty-first", "twenty-second", "twenty-third", "twenty-fourth", "twenty-fifth",
        "twenty-sixth", "twenty-seventh", "twenty-eighth", "twenty-ninth", "thirtieth"]


def say_the_sky(sky: dict) -> str:
    """Tourne l'etat MESURE en pures SENSATIONS francaises pour l'oeil -- jamais de science.

    Pas de date, pas de nom savant, jamais le mot << eclipse >> n'entre ici. Seulement
    des qualites : la phase de la lune, la nuit ou le jour, et le manque de clarte quand
    il vient. La variete ne vient plus des nombres captes mais du tirage (entropy.py).
    """
    eph = sky.get("ephemeris", {})
    lines = []
    age = eph.get("moon_age_days")
    if age is not None:
        a = float(age) % 29.53
        if a < 1.85 or a > 27.68:
            ph = "noire"
        elif a < 5.54:
            ph = "en croissant, et croît"
        elif a < 9.23:
            ph = "à son premier quartier"
        elif a < 12.92:
            ph = "gibbeuse, et croît"
        elif a < 16.61:
            ph = "pleine"
        elif a < 20.30:
            ph = "gibbeuse, et décroît"
        elif a < 23.99:
            ph = "à son dernier quartier"
        else:
            ph = "en vieux croissant, et décroît"
        lines.append("La lune est %s." % ph)
        n = int(round(age)); n = 1 if n < 1 else (30 if n > 30 else n)
        lines.append("La lune en est à sa %se nuit." % n)
    else:
        lines.append("La lune est voilée.")
    # L'HEURE, dite comme une qualite de lumiere -- jamais une horloge, jamais une date.
    lines.append(_the_hour(eph, sky))

    # LE TEMPS QU'IL FAIT, dit comme une sensation -- jamais un instrument, jamais un
    # nom savant. C'est par la que la journee entre : midi ne se lit plus comme l'aube,
    # ni l'orage comme le ciel pur.
    lines.extend(_the_weather(sky))

    # LE COMPTE. La graine ordonne : << lis les nombres que la nuit te donne -- l'age de
    # la lune en nuits, et le compte de ce qui remue au ciel >>. Ce compte ne lui etait
    # jamais donne : l'oeil ecrivait donc SUR des chiffres absents. On le lui rend, nu.
    lines.append("Le compte de ce qui remue au ciel est de %d." % _stir_count(sky))

    want = sky.get("want_of_light")
    if want is not None and want > 0.25:
        if eph.get("day"):
            lines.append("Et voici l'étrange : la clarté se retire, comme si le soir tombait avant son heure.")
        else:
            lines.append("Et voici l'étrange : la lune perd sa lumière, et le pays retourne au noir.")
    return "\n".join(lines)


def _p(conf: dict) -> dict:
    return conf.get("prompts", {}) or {}


_K_NOTE = ("note", "pitch", "midi", "n")
_K_START = ("start", "begin", "onset", "t", "s")
_K_DUR = ("duration", "dur", "length", "len", "d")
_K_FORCE = ("force", "velocity", "vel", "v", "f")


def _pick(d: dict, keys, default=None):
    low = {str(k).lower(): v for k, v in d.items()}
    for k in keys:
        if k in low:
            return low[k]
    return default


def _extract_notes(raw: str) -> list:
    """Pull note events from the model's reply. TOLERANT BY DESIGN: an empty list here
    means a silent air and a dead .mid on the page, so we try hard. The reply may be
    prose-wrapped, fenced, truncated before the closing bracket, keyed otherwise
    (pitch/dur/velocity), or given as bare arrays [note, start, duration, force]."""
    out = []
    txt = re.sub(r"```[a-zA-Z]*", " ", raw or "").replace("```", " ")

    # 1) flat {...} objects, each parsed alone (an incomplete last one is dropped)
    for m in re.finditer(r"\{[^{}]*\}", txt):
        try:
            d = json.loads(m.group(0))
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        p = _pick(d, _K_NOTE)
        if p is None:
            continue
        out.append({"note": p,
                    "start": _pick(d, _K_START, 0.0),
                    "duration": _pick(d, _K_DUR, 0.5),
                    "force": _pick(d, _K_FORCE, 70)})
    if out:
        return out

    # 2) bare arrays: [62, 0.0, 0.5, 70]
    for m in re.finditer(r"\[\s*(\d{1,3})\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*(\d{1,3})\s*)?\]", txt):
        out.append({"note": int(m.group(1)), "start": float(m.group(2)),
                    "duration": float(m.group(3)),
                    "force": int(m.group(4)) if m.group(4) else 70})
    return out


# --------------------------------------------------------------------------
# The day, given to the eye as SENSATION -- never an instrument, never a date.
# --------------------------------------------------------------------------

_META = ("cette version", "voici la", "voici une", "note :", "explication",
         "j'ai resserr", "resserre et aiguise", "cette invite", "cette consigne")

_CLOUD = (("OVC", "Le ciel est bouché."),
          ("BKN", "Le ciel se couvre."),
          ("SCT", "Des nuées passent."),
          ("FEW", "Le ciel est presque pur."))


def _clean_presage(raw: str) -> str:
    """The model chatters: it returns a separator, a meta-comment, or breaks off in the
    middle of a word when the tokens run out. Keep the omen alone -- three sentences at
    most, all of them closed."""
    t = re.sub(r"```[a-zA-Z]*", " ", raw or "").replace("```", " ").strip()
    kept = []
    for ln in t.splitlines():
        s = ln.strip()
        if not s or not s.strip("-—_= "):          # a bare separator line
            continue
        if s.lower().startswith(_META):            # the model's own commentary
            continue
        kept.append(s)
    t = " ".join(kept).strip().strip('"«»').strip()
    parts = re.findall(r"[^.!?…]+[.!?…]+", t)      # only CLOSED sentences survive
    if parts:
        t = "".join(parts[:3]).strip()
    return t


def _rising(sky: dict) -> bool:
    """Before the Berry's solar noon or after it -- so the eye can tell a morning from
    an evening. It is given the QUALITY, never the hour itself."""
    t = sky.get("instant_utc") or ""
    try:
        h = int(t[11:13]) + int(t[14:16]) / 60.0
    except (ValueError, IndexError):
        return True
    return h < 11.85


def _the_hour(eph: dict, sky: dict) -> str:
    alt = eph.get("sun_alt_deg")
    if alt is None:
        return "L'heure est indécise."
    up = _rising(sky)
    if alt > 50:
        return "Le soleil est au plus haut, et la terre n'a plus d'ombre où se mettre."
    if alt > 25:
        return "Le jour est plein." if up else "Le jour penche déjà."
    if alt > 6:
        return ("Le soleil monte, jaune et bas sur les blés." if up
                else "Le soleil descend, et les ombres s'allongent.")
    if alt > -0.5:
        return ("C'est le point du jour ; la clarté vient sans qu'on sache d'où." if up
                else "Le soleil touche la terre, et tout le pays devient rouge.")
    if alt > -6:
        return "C'est l'heure entre chien et loup."
    if (eph.get("moon_alt_deg") or -90) > 5 and (eph.get("moon_illum") or 0) > 0.5:
        return "Il fait nuit, et la lune tient la campagne."
    return "Il fait nuit noire."


def _weather_tokens(raw: str) -> str:
    toks = raw.split()[1:]                          # drop the station
    keep = [tk for tk in toks
            if re.fullmatch(r"[+-]?[A-Z]{2,6}", tk)
            and tk not in ("AUTO", "COR", "NOSIG", "RMK", "CAVOK", "NSC", "SKC", "CLR")]
    return " ".join(keep)


def _the_weather(sky: dict) -> list:
    raw = ((sky.get("berry") or {}).get("metar") or "").upper()
    if not raw:
        return []
    out = []
    m = re.search(r"\b(?:\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT\b", raw)
    if m:
        kt = int(m.group(1))
        if kt <= 3:
            out.append("L'air ne bouge pas.")
        elif kt <= 10:
            out.append("Un souffle passe sur les blés.")
        elif kt <= 20:
            out.append("Le vent se lève.")
        elif kt <= 33:
            out.append("Le vent souffle dur.")
        else:
            out.append("La bourrasque couche les herbes.")
        if m.group(2):
            out.append("Il donne par rafales.")

    wx = _weather_tokens(raw)
    if "TS" in wx:
        out.append("L'orage gronde du côté du bois.")
    elif "RA" in wx or "SH" in wx:
        out.append("Il pleut sur le pays.")
    elif "DZ" in wx:
        out.append("Il bruine.")
    if "GR" in wx or "GS" in wx:
        out.append("La grêle bat les toits.")
    if "FG" in wx:
        out.append("Le brouillard noie le pays.")
    elif "BR" in wx or "HZ" in wx:
        out.append("Une brume traîne sur les prés.")

    if "CAVOK" in raw or " SKC" in raw or " NSC" in raw or " CLR" in raw:
        out.append("Le ciel est pur d'un bout à l'autre.")
    else:
        for tag, said in _CLOUD:
            if tag in raw:
                out.append(said)
                break

    t = re.search(r"\b(M?\d{2})/(M?\d{2})\b", raw)
    if t:
        c = t.group(1)
        try:
            val = -int(c[1:]) if c.startswith("M") else int(c)
        except ValueError:
            return out
        if val >= 30:
            out.append("La chaleur pèse, et le pays a soif.")
        elif val >= 25:
            out.append("Il fait lourd.")
        elif val <= 12:
            out.append("L'air est froid pour la saison.")
    return out


def _stir_count(sky: dict) -> int:
    """<< Le compte de ce qui remue au ciel >> -- the diviner's number. Not a measure:
    a bare figure, drawn from what truly stirs up there, so no two hours read alike."""
    c = sky.get("cosmic") or {}
    n = 0.0
    # A PRESENCE, not an excess. The tempo asks "how far from calm?" and rightly answers
    # zero on a still night. The diviner asks something else: "how many things stir up
    # there?" -- and the answer is never nothing. A count that flatlined at zero would
    # hand the eye the same figure every calm night, and the seed promises the contrary:
    # << nulle nuit pareille a l'autre >>.
    kp = c.get("kp")
    if kp is not None:
        try:
            n += max(0.0, float(kp))
        except (TypeError, ValueError):
            pass
    w = (c.get("solar_wind") or {}).get("speed_km_s")
    if w is not None:
        try:
            n += max(0.0, (float(w) - 300.0) / 100.0)
        except (TypeError, ValueError):
            pass
    x = c.get("xray")
    if x is not None:
        try:
            xf = float(x)
            n += 2.0 if xf >= 1e-4 else (1.0 if xf >= 1e-5 else 0.0)
        except (TypeError, ValueError):
            s = str(x).upper()
            n += 2.0 if s.startswith("X") else (1.0 if s.startswith("M") else 0.0)
    if (sky.get("ephemeris") or {}).get("phase_bucket") in ("full", "dark"):
        n += 1.0
    if "TS" in _weather_tokens(((sky.get("berry") or {}).get("metar") or "").upper()):
        n += 2.0
    try:
        n += 3.0 * float(sky.get("want_of_light") or 0.0)
    except (TypeError, ValueError):
        pass
    return max(0, min(12, int(round(n))))

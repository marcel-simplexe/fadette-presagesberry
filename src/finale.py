# -*- coding: utf-8 -*-
"""
finale.py — the last breath. On 31 August the machine gathers everything it
wrote across the month and composes a single dense nouvelle of about twenty
pages: a legend of the Berry in George Sand's voice, written by Apertus — the
Swiss sovereign model, on the same host as the daily breaths. Then it falls
silent. There are no plates; the bare page is how the work salutes Bascoulard — his
spirit, not his work.

GROUNDED in the real capture: before writing, the machine reads its own archive
and draws a true LEDGER — which of the Berry's night-people actually returned in
the omens, and how often, and how many nights the light failed for no reason it
could name. The nouvelle is built from THAT material, not from generic folklore.

BLINDNESS to the end: the writer is never given a date or the word "eclipse". The
nights of failed light enter only as the archive's own `dark` mark — an anomaly —
and the nouvelle canonises them into legend. The event becomes folklore.

Twenty pages do not come from one call. The nouvelle is built in a chain: distil
the matter from the ledger and the omens, lay a frame of movements that form one
arc, write each movement upon the last, stitch. The finale's voice is one
Infomaniak model (Apertus by default; swap to another in config.yaml).
"""
from __future__ import annotations
import os
from . import memory, infomaniak, lens

# The country's night-people, and the words by which they show in the omens.
_BEINGS = [
    ("les laveuses de nuit au gué", ["laveuse", "lavandière", "battoir", "au gué", "battent", "linge"]),
    ("le meneu' de loups et sa meute", ["meneu", "meneur de loups", "loup", "la meute", "loups"]),
    ("la Grand'Bête", ["grand'bête", "grande bête", "grand-bête", "la bête"]),
    ("les feux errants", ["flambette", "feu follet", "feu errant", "feux errants", "flamme", "feu qui marche", "lumière qui marche"]),
    ("les morts qui reviennent", ["les morts", "revenant", "le noyé", "noyés", "enterré", "défunt", "trépassé"]),
    ("les fades", ["fade", "fée", "petit peuple"]),
    ("le lupeux des roseaux", ["lupeux", "roseaux"]),
    ("le moine et la cloche", ["moine", "cloche", "glas"]),
]


def _ledger(presages: list, dark_breaths: int, dark_nights: int) -> str:
    """A true tally of the month, to anchor the legend in what was written."""
    low = [p.lower() for p in presages]
    counted = []
    for name, keys in _BEINGS:
        c = sum(1 for p in low if any(k in p for k in keys))   # in how many omens it appears
        if c:
            counted.append((c, name))
    counted.sort(reverse=True)
    head = ("Voici le REGISTRE VÉRIDIQUE de ce mois, tiré des présages tels qu'ils "
            "furent réellement écrits, nuit après nuit. Bâtis la légende de CETTE matière "
            "et d'aucune autre — les êtres qui sont vraiment revenus, le plus vu d'abord :\n")
    body = ("\n".join("  - %s (nommé dans %d présage%s)" % (n, c, "" if c == 1 else "s") for c, n in counted)
            if counted else "  (aucun être ne s'est imposé plus qu'un autre)")
    tail = ("\n\nEt les nuits où la clarté a manqué sans raison que le veilleur pût nommer : "
            "%d présage%s de clarté manquée, sur %d nuit%s pareille%s. Ces nuits sont le "
            "cœur de la légende ; qu'elles pèsent dans le conte exactement autant qu'elles "
            "ont pesé dans le registre, ni plus." % (dark_breaths, "" if dark_breaths == 1 else "s",
                                                      dark_nights, "" if dark_nights == 1 else "s",
                                                      "" if dark_nights == 1 else "s"))
    return head + body + tail


def write_novella(conf: dict) -> str:
    presages, dark_breaths, dark_nights = [], 0, set()
    for day in memory.all_days():                       # chronological, first day to last
        for b in day.get("breaths", []):
            p = b.get("presage")
            if p:
                presages.append(p)
            if b.get("dark"):
                dark_breaths += 1
                dark_nights.add(b.get("night"))
    corpus = "\n\n".join(presages) if presages else "(the months left nothing)"
    ledger = _ledger(presages, dark_breaths, len(dark_nights))

    sys = lens.system(conf)
    fp = (conf.get("prompts", {}) or {}).get("finale", {}) or {}
    fin = conf.get("finale", {}) or {}
    n_mv = int(fin.get("movements", 9))
    mv_tokens = int(fin.get("movement_max_tokens", 2800))

    matter = _voice(conf, sys,
        fp.get("matter", "From the ledger and the omens that follow, draw the matter of a "
        "Berry legend; stay faithful to what is there.") + "\n\n" + ledger +
        "\n\n--- the omens themselves, night after night ---\n\n" + corpus,
        max_tokens=1100, temperature=0.6)

    frame = _voice(conf, sys,
        fp.get("frame", "From this matter, lay the frame of a Berry nouvelle in George "
        "Sand's manner, in {movements} titled movements that form one arc.").format(movements=n_mv)
        + "\n\n" + matter,
        max_tokens=1400, temperature=0.7)

    tmpl = fp.get("movement", "Write MOVEMENT {n} of {total} of this nouvelle, in full, "
        "finished prose, never a summary, in George Sand's voice. --- frame --- {frame} "
        "--- written so far --- {written}")
    movements = []
    for i in range(1, n_mv + 1):
        written = "\n\n".join(movements) if movements else "(the beginning)"
        sec = _voice(conf, sys,
            tmpl.format(n=i, total=n_mv, frame=frame, written=written),
            max_tokens=mv_tokens, temperature=0.9)
        movements.append(sec.strip())

    novella = "\n\n".join(movements)
    title = _title(conf, sys, fp, matter)
    _save_text("novella.txt", novella)
    _save_text("novella-title.txt", title)
    _save_text("novella-matter.txt", ledger + "\n\n---\n\n" + matter + "\n\n---\n\n" + frame)
    # La page anglaise est servie en traduisant le francais (la source), mouvement par mouvement.
    try:
        en = "\n\n".join(x for x in (lens.to_english(conf, m, max_tokens=3200) for m in movements) if x)
        _save_text("novella-en.txt", en)
        if title:
            _save_text("novella-title-en.txt", lens.to_english(conf, title, max_tokens=60))
    except Exception as e:
        _save_text("novella-en-error.txt", str(e))
    return novella


def _voice(conf: dict, system: str, task: str, max_tokens: int, temperature: float) -> str:
    """The finale's voice: one Infomaniak model, set by finale.model (Apertus by default)."""
    model = (conf.get("finale", {}) or {}).get("model")
    return infomaniak.text(conf, system, task, temperature=temperature,
                           max_tokens=max_tokens, model=model)


def _title(conf: dict, sys: str, fp: dict, matter: str) -> str:
    """One short call for the nouvelle's title. Failure is harmless (no title)."""
    try:
        p = fp.get("title", "Give a short title for this Berry legend, in George Sand's "
            "manner — a few words, no quotation marks, no explanation.")
        t = _voice(conf, sys, p + "\n\n" + matter, max_tokens=40, temperature=0.7)
        return t.strip().strip('"').splitlines()[0][:120] if t else ""
    except Exception:
        return ""


def _save_text(name: str, text: str) -> None:
    path = os.path.join(memory.HISTORY, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text or "")

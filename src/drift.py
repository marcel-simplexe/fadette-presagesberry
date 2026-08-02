# -*- coding: utf-8 -*-
"""
drift.py — the lens drifts, one notch a day. This is the only re-prompting in the
machine: a single daily call rewrites the lens's own task prompt by one notch, on
that day's own fragments. The fragments themselves are never re-prompted — Fadette
keeps what the scribe says. Every state of the lens is historised.

Blind: the refiner is given neither date nor "eclipse".

THE GUARD (the heart of this module). A refiner asked to "improve a prompt" will,
sooner or later, answer with an improved *text* instead of an improved *instruction*
— and once that happens the lens is no longer a lens: it is a finished presage that
the machine paraphrases for ever after. It happened, on the live machine. So the
drift no longer trusts what comes back: a candidate must PROVE it is still an
instruction (`_is_instruction`) and, for the air, that it still carries the JSON
contract (`_is_air_contract`). A candidate that fails is DROPPED and the lens keeps
its state — a missed notch is no harm; a rotted lens is the end of the work.
"""
from __future__ import annotations
import datetime as dt
import re
from . import memory, infomaniak
from . import lens

_DEFAULT_REFINER = (
    "Voici la CONSIGNE que suit un scribe, puis les visions qu'il a ecrites aujourd'hui. "
    "Reecris LA CONSIGNE ELLE-MEME, d'un cran plus juste. N'ecris AUCUN presage, AUCUN "
    "exemple, AUCUN commentaire : rien qu'une consigne, a l'imperatif, qui garde toutes "
    "ses contraintes. Rends seulement la nouvelle consigne."
)

# What an instruction must still say, whatever the refiner does to it. This is the
# work's contract, not its style: lose it and the machine stops being Fadette.
_MUST_KEEP_TEXT = ("sand",)                       # the voice
_MARKS_TEXT = ("trois phrases", "3 phrases", "pas de titre", "pas de date",
               "ne decris pas", "ne décris pas", "au plus", "finis", "dis ", "lis ", "vois")
_MARKS_AIR = ("json", "note", "start", "duration", "force")

# The ENGLISH lens has its own tongue; it is judged in it. These marks are what any
# faithful translation of the seed instructions carries, and what a rotted candidate
# (an omen, a bare score) does not.
_MARKS_TEXT_EN = ("sentence", "vision", "omen", "never", "read", "say", "short", "sand")
_MARKS_AIR_EN = ("json", "note")


def _is_instruction_en(cand: str, seed: str) -> bool:
    """True if the English candidate still reads like an ORDER, not a finished omen."""
    c = _norm(cand)
    if len(c) < 80:
        return False
    if c.startswith("---") or "```" in c:
        return False
    if len(cand) > 1.8 * max(1, len(seed)):
        return False
    if sum(1 for m in _MARKS_TEXT_EN if m in c) < 2:
        return False
    return True


def _is_air_contract_en(cand: str, seed: str) -> bool:
    """True if the English candidate still DEMANDS a JSON score rather than being one."""
    c = _norm(cand)
    if len(c) < 80:
        return False
    if c.startswith("---") or "```" in c:
        return False
    if len(cand) > 1.8 * max(1, len(seed)):
        return False
    if not all(m in c for m in _MARKS_AIR_EN):
        return False
    if len(re.findall(r'"note"', c)) > 2:               # it became a melody, not a form
        return False
    return True


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _is_instruction(cand: str, seed: str) -> bool:
    """True if the candidate still reads like an ORDER, not a finished presage."""
    c = _norm(cand)
    if len(c) < 120:
        return False
    if c.startswith("---") or "```" in c:                # a text, or a fenced example
        return False
    if len(cand) > 1.8 * max(1, len(seed)):             # the creeping bloat
        return False
    if not all(k in c for k in _MUST_KEEP_TEXT):        # the voice was dropped
        return False
    if sum(1 for m in _MARKS_TEXT if m in c) < 2:       # no imperative left: it is prose
        return False
    return True


def _is_air_contract(cand: str, seed: str) -> bool:
    """True if the candidate still DEMANDS a JSON score. The air prompt is a technical
    contract before it is literature; a refiner that 'improves' it into prose silently
    kills every melody in the work."""
    c = _norm(cand)
    if len(c) < 120:
        return False
    if c.startswith("---") or "```" in c:
        return False
    if len(cand) > 1.8 * max(1, len(seed)):
        return False
    if not all(m in c for m in _MARKS_AIR):             # the contract was lost
        return False
    if len(re.findall(r'"note"', c)) > 2:               # it became a melody, not a form
        return False
    return True


def one_notch(conf: dict, date: str | None = None) -> dict:
    cur = memory.read_lens()
    day = memory.read_day(date or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    fragments = [b.get("presage", "") for b in day.get("breaths", []) if b.get("presage")]
    matter = "\n---\n".join(fragments) if fragments else "(aucune vision aujourd'hui)"

    refiner = (conf.get("prompts", {}) or {}).get("refiner", _DEFAULT_REFINER)
    sys = lens.system(conf)
    seed_text, seed_air = lens.seed_presage(conf), lens.seed_air(conf)
    p = conf.get("prompts", {}) or {}

    new = dict(cur)
    moved = False

    # The gaze. A candidate is accepted only if it is still an instruction.
    try:
        task = (refiner + "\n\n--- la consigne actuelle ---\n" + cur.get("text", seed_text)
                + "\n\n--- les visions d'aujourd'hui ---\n" + matter)
        cand = infomaniak.text(conf, sys, task, temperature=0.5, max_tokens=500)
        if _is_instruction(cand, seed_text):
            new["text"] = cand.strip()
            moved = True
        else:
            print("drift: the gaze's candidate was not an instruction — notch skipped.")
    except Exception as e:
        print("drift: the gaze could not be refined (%s) — the lens keeps its state." % e)

    # The air. Same, plus it must still demand a JSON score.
    try:
        task = (refiner + "\n\n--- la consigne actuelle (l'air) ---\n" + cur.get("score", seed_air)
                + "\n\n--- les visions d'aujourd'hui ---\n" + matter)
        cand = infomaniak.text(conf, sys, task, temperature=0.4, max_tokens=500)
        if _is_air_contract(cand, seed_air):
            new["score"] = cand.strip()
            moved = True
        else:
            print("drift: the air's candidate lost the JSON contract — notch skipped.")
    except Exception as e:
        print("drift: the air could not be refined (%s) — the lens keeps its state." % e)

    # A lens that has ALREADY rotted (a state from before this guard) is brought back to
    # its seed rather than drifted further: the work must never paraphrase itself.
    if not _is_instruction(new.get("text", ""), seed_text):
        print("drift: the gaze had rotted — restored to its seed.")
        new["text"] = seed_text
        new["text_en"] = p.get("presage_en", new.get("text_en", ""))
        moved = True
    if not _is_air_contract(new.get("score", ""), seed_air):
        print("drift: the air had rotted — restored to its seed.")
        new["score"] = seed_air
        new["score_en"] = p.get("air_en", new.get("score_en", ""))
        moved = True

    if not moved:
        # A REFUSED NOTCH MUST STILL LEAVE A MARK. Until now a refusal wrote nothing at
        # all, and the trial paid for it: seventeen days lived, one drift file, and no
        # way afterwards to tell a guarded refusal from a workflow that never ran. The
        # dated snapshot is written; the LIVING lens (history/lens.json) is not touched.
        print("drift: the lens did not move today.")
        _note_refusal(cur, date)
        return cur

    new["notch"] = cur.get("notch", 0) + 1

    # Translate the drifted optic for the Original/Translation display; never blocking.
    try:
        new["text_en"] = lens.to_english(conf, new["text"])
    except Exception:
        pass
    try:
        new["score_en"] = lens.to_english(conf, new["score"])
    except Exception:
        pass

    # THE ENGLISH SIDE IS A LENS TOO, AND IT IS SHOWN. The trial ended with an English
    # gaze that had become an omen and an English air that had become a bare JSON score,
    # fences and all -- displayed, both of them, on the eye's page. The guard that keeps
    # the French from rotting is owed to the English -- but in ENGLISH: the French
    # markers ("trois phrases", "pas de date") never survive translation, and judging a
    # translation by them would freeze the English side at its seed forever. A
    # translation that has stopped being an instruction is not shown; it is returned to
    # its seed. When no English seed exists, nothing is judged and nothing is touched.
    if p.get("presage_en") and not _is_instruction_en(new.get("text_en", ""), p["presage_en"]):
        print("drift: the English gaze was no longer an instruction — restored to its seed.")
        new["text_en"] = p["presage_en"]
    if p.get("air_en") and not _is_air_contract_en(new.get("score_en", ""), p["air_en"]):
        print("drift: the English air lost the JSON contract — restored to its seed.")
        new["score_en"] = p["air_en"]

    memory.write_lens(new, date)
    return new


def _note_refusal(cur: dict, date: str | None) -> None:
    """Write a dated note for a day on which no notch was taken. It is a .txt, NOT a
    .json: the eye's page lists every history/drift/*.json as a notch of the lens, and
    a refusal is not a notch -- thirty identical pseudo-notches would bury the real
    ones. The note keeps the archive honest without touching the display, and the
    living lens is left exactly as it stands."""
    import json, os
    note = dict(cur)
    note["moved"] = False
    note["noted_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    try:
        os.makedirs(memory.DRIFT, exist_ok=True)
        path = os.path.join(memory.DRIFT, "%s-refus.txt" % (date or memory.today()))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(note, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("  drift: the refusal could not be noted (%s)." % e)

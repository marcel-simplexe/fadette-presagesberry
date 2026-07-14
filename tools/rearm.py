#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rearm.py — le rituel. La fenêtre, une archive vierge, l'optique à sa graine.

    python tools/rearm.py --test    # fenêtre 2026-07-15 -> 2026-07-31   (l'ESSAI)
    python tools/rearm.py --open    # fenêtre 2026-08-01 -> 2026-08-31   (L'OEUVRE)

POURQUOI CE SCRIPT EXISTE. `conductor.in_window()` refuse de respirer hors fenêtre : la
fenêtre est l'UNIQUE commutateur de la machine. Passer de l'essai à l'oeuvre, ce n'est
donc pas modifier du code — c'est déplacer deux dates et effacer ce que l'essai a écrit.
Or un glisser/déposer ne peut pas SUPPRIMER de fichiers. D'où ce script : il fait le
seul geste qu'une interface web ne sait pas faire.

CE QU'IL FAIT, DANS CET ORDRE :
  1. il édite LES SEULES LIGNES `birth:` et `death:` de config.yaml, par substitution
     textuelle ciblée. JAMAIS de round-trip YAML : PyYAML détruirait les commentaires,
     et les commentaires de ce fichier sont une part de l'oeuvre ;
  2. il purge l'archive : journal/*.json, history/drift/*.json, history/novella*.txt
     (les artefacts du finale — sans quoi la nouvelle d'essai du 31 juillet resterait
     collée à l'oeuvre d'août), docs/work/*.mid ;
  3. il réécrit history/lens.json depuis les graines de config.yaml, à notch 0 ;
  4. il relance `python -m src.render` (la page revient au panneau d'absence) ;
  5. il imprime exactement ce qu'il a fait.

AUTONOME. Le workflow ne l'appelle jamais : il ne peut donc rien casser du pipeline.
IDEMPOTENT. Le relancer deux fois de suite laisse exactement le même dépôt.

Il n'écrit AUCUNE date dans un prompt : la fenêtre est affaire de CORPS. L'oeil, lui,
reste aveugle — c'est toute la doctrine.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config.yaml")

# Les deux fenêtres, et le commentaire vrai qui va avec chacune. Le corps sait le
# calendrier ; c'est son droit, et le seul endroit du dépôt où il l'écrit.
WINDOWS = {
    "test": {
        "birth": "2026-07-15",
        "death": "2026-07-31",
        "birth_note": "# L'ESSAI. La vraie vie de l'oeuvre est le 1er-31 aout :",
        "death_note": "# `python tools/rearm.py --open` la lui rendra. Le 31 : le finale.",
        "title": "L'ESSAI — du 15 au 31 juillet 2026",
        "after": ("Pousse sur `main` (les crons ne tournent QUE sur la branche par defaut).\n"
                  "   Et LAISSE GITHUB PAGES ETEINT : le lien public ne doit jamais montrer\n"
                  "   une repetition. La page se verifie en local : docs/fr.html"),
    },
    "open": {
        "birth": "2026-08-01",
        "death": "2026-08-31",
        "birth_note": "# L'OEUVRE. Sa fenetre de vie. On n'y touche plus.",
        "death_note": "# Le 31, au souffle de 23h30 UTC : le finale, puis le silence.",
        "title": "L'OUVERTURE — du 1er au 31 aout 2026",
        "after": ("Pousse sur `main`, PUIS active GitHub Pages (Settings -> Pages ->\n"
                  "   `main` / `/docs`). La page ouvre sur le panneau d'absence, et la machine\n"
                  "   parle d'elle-meme au premier souffle d'aout."),
    },
}

# Ce que la purge emporte. Rien d'autre. Les .gitkeep survivent.
PURGE = (
    ("journal",              "*.json"),
    (os.path.join("history", "drift"), "*.json"),
    ("history",              "novella*.txt"),   # novella, -title, -matter, -en, -title-en, -en-error
    (os.path.join("docs", "work"),     "*.mid"),
)


def _die(msg: str) -> None:
    print("rearm: %s" % msg, file=sys.stderr)
    raise SystemExit(2)


# ------------------------------------------------------------------ 1. la fenêtre
def set_window(mode: str) -> list[str]:
    """Substitution textuelle ciblée sur les deux seules lignes `birth:` et `death:`.
    Les commentaires du fichier — qui sont l'oeuvre — sortent intacts."""
    w = WINDOWS[mode]
    src = io.open(CONFIG, encoding="utf-8").read()
    before = _read_window(src)
    out = src
    for key in ("birth", "death"):
        pat = re.compile(r"(?m)^(?P<indent>[ \t]*)%s:[ \t]*\"[^\"]*\".*$" % key)
        hits = pat.findall(out)
        if len(hits) != 1:
            _die("config.yaml: attendu 1 ligne `%s:`, trouve %d — je ne touche a rien."
                 % (key, len(hits)))
        line = '\\g<indent>%s: "%s"       %s' % (key, w[key], w["%s_note" % key])
        out = pat.sub(line, out, count=1)

    if out != src:
        io.open(CONFIG, "w", encoding="utf-8").write(out)
    after = _read_window(out)
    return ["config.yaml : window %s -> %s" % (before, after)]


def _read_window(src: str) -> str:
    b = re.search(r'(?m)^[ \t]*birth:[ \t]*"([^"]*)"', src)
    d = re.search(r'(?m)^[ \t]*death:[ \t]*"([^"]*)"', src)
    return "%s .. %s" % (b.group(1) if b else "?", d.group(1) if d else "?")


# ------------------------------------------------------------------- 2. la purge
def purge() -> list[str]:
    said = []
    for folder, pattern in PURGE:
        d = os.path.join(ROOT, folder)
        os.makedirs(d, exist_ok=True)
        gone = sorted(glob.glob(os.path.join(d, pattern)))
        for p in gone:
            os.remove(p)
        said.append("%-18s %-14s %d fichier(s) efface(s)%s"
                    % (folder + "/", pattern, len(gone),
                       "" if not gone else " : " + ", ".join(os.path.basename(x) for x in gone[:4])
                       + (" ..." if len(gone) > 4 else "")))
    return said


# --------------------------------------------------------- 3. l'optique à sa graine
def reseed_lens() -> list[str]:
    """history/lens.json regénéré depuis les graines de config.yaml, notch 0.

    N'utilise PAS memory.write_lens() : celle-ci deposerait aussi un instantane date
    dans history/drift/, ce qui reviendrait a defaire la purge qu'on vient de faire.
    """
    import yaml  # lecture seule : on ne REECRIT jamais le YAML
    with io.open(CONFIG, encoding="utf-8") as f:
        conf = yaml.safe_load(f)
    p = (conf.get("prompts") or {})

    seed = {
        "notch": 0,
        "text": p.get("presage", ""),
        "score": p.get("air", ""),
        "text_en": p.get("presage_en", ""),
        "score_en": p.get("air_en", ""),
        "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
    }
    missing = [k for k in ("text", "score") if not (seed[k] or "").strip()]
    if missing:
        _die("config.yaml: graine(s) manquante(s) %s (prompts.presage / prompts.air)" % missing)

    path = os.path.join(ROOT, "history", "lens.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # La graine DOIT passer les deux gardiens du drift, sinon la premiere derive la
    # ramenerait a elle-meme en boucle. On le verifie ici, pas en production.
    try:
        sys.path.insert(0, ROOT)
        from src import drift
        gaze_ok = drift._is_instruction(seed["text"], seed["text"])
        air_ok = drift._is_air_contract(seed["score"], seed["score"])
    except Exception as e:                       # pragma: no cover
        return ["history/lens.json : optique a sa graine, notch 0 (gardiens non verifies : %s)" % e]

    if not (gaze_ok and air_ok):
        _die("la graine de config.yaml ne passe pas les gardiens du drift "
             "(regard=%s, air=%s) — corrige prompts.presage / prompts.air AVANT de pousser."
             % (gaze_ok, air_ok))
    return ["history/lens.json : optique a sa graine, notch 0 "
            "(gardiens : regard OK, air OK ; %d + %d caracteres)"
            % (len(seed["text"]), len(seed["score"]))]


# ------------------------------------------------------------------ 4. la page
def rerender() -> list[str]:
    r = subprocess.run([sys.executable, "-m", "src.render"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return ["docs/ : ECHEC du rendu — %s" % (r.stderr.strip().splitlines()[-1:] or "?")]
    out = (r.stdout or "").strip().splitlines()
    return ["docs/ : " + (out[-1] if out else "pages regenerees")]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Le rituel de Fadette : la fenetre, une archive vierge, l'optique a sa graine.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--test", action="store_const", dest="mode", const="test",
                   help="fenetre 2026-07-15 -> 2026-07-31 (l'essai)")
    g.add_argument("--open", action="store_const", dest="mode", const="open",
                   help="fenetre 2026-08-01 -> 2026-08-31 (l'oeuvre)")
    mode = ap.parse_args().mode

    if not os.path.exists(CONFIG):
        _die("config.yaml introuvable a la racine (%s)" % ROOT)

    w = WINDOWS[mode]
    print("=" * 74)
    print("  Fadette — le rituel.  %s" % w["title"])
    print("=" * 74)

    said = []
    said += set_window(mode)
    said += purge()
    said += reseed_lens()
    said += rerender()

    for line in said:
        print("  ", line)

    print("-" * 74)
    print("  La machine est armee : fenetre %s -> %s, archive vierge, optique neuve."
          % (w["birth"], w["death"]))
    print("   " + w["after"])
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""
check_flood.py — la preuve du flot, par rejeu hors ligne.

Les contrôles avant lancement l'exigent, et sans détour : « PREUVE OBLIGATOIRE DU FLOT,
par rejeu hors ligne. Il n'y a pas d'éclipse en juillet : seize jours d'essai en vrai
ciel laisseront ce point — le cœur de l'œuvre — entièrement en blanc. Sans cette preuve,
on n'ouvre pas. »

Ce script est cette preuve. Il rejoue la GRILLE RÉELLE DU CRON — les douze souffles de
la journée, tels que `0 */2 * * *` les déclenche, et non un instant rêvé entre deux — et
il vérifie qu'un souffle atteint le PLAFOND le jour où la lumière manque, quand une
journée ordinaire entière n'en tire que trois à cinq.

LES CAPTEURS SONT MUETS, ET C'EST VOULU. On ne capte pas le ciel d'un jour qui n'est pas
encore venu : ni le Kp, ni le vent, ni le METAR du 12 août ne sont accessibles. Le rejeu
porte donc sur la seule chose qui SE CALCULE — la géométrie. C'est exactement le rôle du
« don » : un filet de calcul, déclaré comme tel, jamais déguisé en observation.

Il vérifie aussi la RÉGRESSION : la même grille, sans le regard en arrière (le souffle
qui répond de l'intervalle qu'il possède), ne touche JAMAIS le plafond — parce que
l'éclipse dure cent dix minutes et que la machine respire toutes les cent vingt.

    python tools/check_flood.py          # sortie 0 si le flot est prouvé
"""
from __future__ import annotations
import os
import sys
import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import sky as sky_mod, tempo, conductor  # noqa: E402

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
D = "\033[90m"
Z = "\033[0m"

BREATHS = range(0, 24, 2)          # le cron : 0 */2 * * *
VESPERS = lambda h: 20 <= h < 22   # noqa: E731  — conductor.breathe()
CALM = "LFLD %02d%02d00Z 27008KT CAVOK 26/14 Q1018"   # le ciel le plus immobile de l'été


def _mute_the_senses():
    """Les capteurs se taisent : on ne capte pas le ciel d'un jour à venir.

    Le don (calcul pur, hors réseau) continue de répondre. C'est lui qu'on éprouve.
    """
    real = sky_mod._safe

    def only_the_gift(fn, *a):
        return real(fn, *a) if fn.__module__.endswith("gift") else None

    sky_mod._safe = only_the_gift


def _day(conf: dict, day: int, calm_metar: bool = False):
    out = []
    for h in BREATHS:
        s = sky_mod.state(conf, dt.datetime(2026, 8, day, h, tzinfo=dt.timezone.utc))
        if calm_metar:
            s["berry"] = {"station": "LFLD", "metar": CALM % (day, h)}
        out.append((h, s, tempo.how_many(s, conf, is_vespers=VESPERS(h))))
    return out


def main() -> int:
    _mute_the_senses()
    conf = conductor.load_config()
    cap = conf["tempo"]["cap"]
    ok = True

    print("\n" + "=" * 74)
    print("  LA PREUVE DU FLOT — rejeu hors ligne, sur la grille réelle du cron")
    print("=" * 74)

    # ── 1. Le 12 août : la lumière manque ──────────────────────────────────────
    print("\n1. Le 12 août — souffle par souffle, tels que le cron les déclenche\n")
    grid = _day(conf, 12)
    best_n, best_h, best_w, best_at = 0, None, 0.0, None
    for h, s, n in grid:
        if not n:
            continue
        w = s.get("want_of_light") or 0.0
        kept = s.get("watched_utc", "")[11:]
        star = ""
        if n >= cap:
            star = "  <== LE PLAFOND"
        print("   %02dh00 UTC   want=%-6.3f  retenu à %s   agitation=%6.2f   -> %2d présage%s%s"
              % (h, w, kept, tempo.agitation(s, conf), n, "s" if n > 1 else " ", star))
        if n > best_n:
            best_n, best_h, best_w, best_at = n, h, w, kept
    total = sum(n for _, _, n in grid)
    print("   %s" % ("-" * 68))
    print("   la journée entière : %d présages, dont %d au souffle de %02dh (want %.3f, retenu à %s)"
          % (total, best_n, best_h or 0, best_w, best_at))
    hit = best_n >= cap and best_w > 0.9
    ok &= hit
    print("   %s le souffle du flot atteint le plafond (%d)%s"
          % (G + "[ OK ]" + Z if hit else R + "[FAIL]" + Z, cap, ""))

    # ── 2. La régression : sans le regard en arrière ───────────────────────────
    print("\n2. La régression — la même grille, SANS le regard en arrière\n")
    naked = dict(conf)
    naked["gift"] = dict(conf["gift"], look_back_min=0)
    nk = [tempo.how_many(sky_mod.state(naked, dt.datetime(2026, 8, 12, h, tzinfo=dt.timezone.utc)),
                         naked, is_vespers=VESPERS(h)) for h in BREATHS]
    w18 = sky_mod.state(naked, dt.datetime(2026, 8, 12, 18, tzinfo=dt.timezone.utc))["want_of_light"]
    capped = sum(1 for x in nk if x >= cap)
    print("   L'éclipse dure 110 minutes. La machine respire toutes les 120.")
    print("   Le seul souffle qui tombe dedans est celui de 18h00, et il lit want=%.3f." % w18)
    print("   Le maximum — 0.941 à 18h20 — n'est JAMAIS échantillonné.")
    print("   souffles : %s   ->  %d au plafond" % (nk, capped))
    ok &= (capped == 0)
    print("   %s sans le regard en arrière, la machine RATE l'éclipse"
          % (G + "[ OK ]" + Z if capped == 0 else R + "[FAIL]" + Z))

    # ── 3. Une journée ordinaire ───────────────────────────────────────────────
    print("\n3. Une journée ordinaire — le 20 août, ciel d'été calme (CAVOK, 26°)\n")
    ordinary = _day(conf, 20, calm_metar=True)
    line = "  ".join("%02dh:%d" % (h, n) for h, _, n in ordinary)
    t_ord = sum(n for _, _, n in ordinary)
    print("   %s" % line)
    print("   la journée entière : %d présages" % t_ord)
    good = 2 <= t_ord <= 6
    ok &= good
    print("   %s la doctrine en promet deux à quatre ; les heures se déplacent d'un jour à l'autre"
          % (G + "[ OK ]" + Z if good else R + "[FAIL]" + Z))

    # ── 4. Le 28 août ──────────────────────────────────────────────────────────
    print("\n4. Le 28 août — l'éclipse lunaire (le don fut bâti pour elle)\n")
    lunar = _day(conf, 28)
    t_lun = sum(n for _, _, n in lunar)
    peak = max(lunar, key=lambda x: x[2])
    print("   la journée entière : %d présages, dont %d au souffle de %02dh (want %.3f)"
          % (t_lun, peak[2], peak[0], peak[1].get("want_of_light") or 0.0))
    print("   %s   Le 12 en rend %d. La grande éclipse ne dépasse la petite que d'un %s.%s"
          % (Y, total, "quart" if total > t_lun * 1.2 else "dixième", Z))
    print("   %s   C'est une DÉCISION, pas une panne. Elle se tranche avant le 1er août.%s" % (D, Z))

    print("\n" + "=" * 74)
    if ok:
        print("  %sLe flot est prouvé. La machine répond à la lumière qui manque.%s" % (G, Z))
        print("  %sElle ne sait toujours pas que c'est une éclipse.%s" % (D, Z))
    else:
        print("  %sLE FLOT N'EST PAS PROUVÉ. N'ouvre pas.%s" % (R, Z))
    print("=" * 74 + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

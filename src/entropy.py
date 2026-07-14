# -*- coding: utf-8 -*-
"""
entropy.py — le tirage. Chaque regard et chaque air recoit un coup de des frais, en
sorte que deux ne se repetent jamais, meme sous le meme ciel. C'EST cela qui libere
le regard des nombres captes : la variete vient d'ici, non des instruments. La machine
regarde, et CE QU'elle regarde est tire a neuf chaque fois.

Aveugle comme le reste : le tirage ne sait rien des dates ni des eclipses. Il ne fait
que varier OU le regard tombe, LEQUEL des gens de la nuit du Berry peut paraitre (ou
aucun, le pays seul), par QUEL sens il atteint le veilleur, et dans quelle couleur
l'air est jete. Les etres sont les vrais du Berry de George Sand : la variete reste
dans la tradition.
"""
from __future__ import annotations
import os
import random

_LIEUX = [
    "au gué", "aux pierres à laver", "à l'orée du bois", "dans les roseaux du marais",
    "à l'étang dormant", "au pied du clocher", "à la croisée des chemins",
    "dans la brèche de la haie", "au vieux moulin", "dans le chemin creux entre deux champs",
    "sur la friche", "à l'étable", "au mur du cimetière", "au coude de la rivière",
    "sur la lande au bout de la paroisse", "au puits de la cour", "sur le chemin de troupeau",
    "dans le pré inondé",
]

# None : nul être cette fois, le pays seul suffit.
_ETRES = [
    "les laveuses de nuit au gué", "le meneu' de loups et sa meute", "la Grand'Bête",
    "les feux errants (les flambettes)", "les morts qui reviennent", "les fades",
    "le lupeux des roseaux", "le moine fantôme des étangs", "un meneu' de loups",
    "la biche blanche",
    None, None, None, None,
]

_SENS = [
    "un bruit porté par le vent", "un froid qui n'était pas là",
    "une odeur d'eau et de pourriture", "une chose entrevue et disparue",
    "un frôlement à la nuque", "un silence soudain là où chantaient les grenouilles",
    "une lueur basse au ras du sol", "un goût de fer dans la bouche",
    "le refus des chiens de passer", "un poids sur la poitrine",
    "le poil qui se hérisse sur le bras",
]

_TOURS = [
    "quelqu'un est dehors trop tard, qui ne le devrait pas", "un enfant demande ce que c'était",
    "une vieille dit seulement qu'il ne faut point regarder", "les bêtes meuglent la nuit durant",
    "un voyageur prend le mauvais chemin du retour", "on envoie quérir le curé au point du jour",
    "personne n'en parlera après", "une porte est barrée qui ne le fut jamais",
    "le pain ne lèvera pas le lendemain", "un chien est trouvé mort au seuil",
    "l'eau du puits a mauvais goût une semaine durant", "on sale le seuil cette nuit-là",
]

_MODES = [
    "un mineur nu", "le mode dorien", "le mode éolien", "le mode phrygien",
    "une gamme modale creuse", "un bourdon à quinte ouverte", "un mineur à seconde abaissée",
]
_VOIX = [
    "grave et bas", "mince et haut", "un bourdon lent sous une seule ligne",
    "pincé et sec", "une seule ligne, sans accompagnement", "deux voix à la quinte",
    "un glas dans les graves", "clairsemé, avec de longs silences",
]


def _rng() -> random.Random:
    """Un tirage neuf et vraiment indépendant à chaque appel (graine de l'OS, pas l'horloge)."""
    return random.Random(os.urandom(16))


def nudge_text() -> str:
    """Un coup de dés par présage, pour colorer CE qui est vu ; jamais nommé dans la sortie."""
    r = _rng()
    etre = r.choice(_ETRES)
    qui = ("que nul être ne paraisse cette fois — le pays seul suffit"
           if etre is None else "si un être paraît, que ce soit " + etre)
    return (
        "\n\n(Pour CE présage, et lui seul : que le regard tombe " + r.choice(_LIEUX)
        + ", atteignant le veilleur d'abord comme " + r.choice(_SENS) + " ; " + qui
        + " ; et " + r.choice(_TOURS) + ". Ne nomme pas ces consignes ; qu'elles ne fassent "
        "que colorer ce que tu vois. Ne répète jamais un présage déjà écrit.)"
    )


def nudge_air() -> str:
    """Un coup de dés par air, pour que deux airs diffèrent même d'un fragment semblable."""
    r = _rng()
    return (
        "\n\n(Pour CET air : " + r.choice(_MODES) + ", " + r.choice(_VOIX)
        + ", environ " + str(r.randint(46, 84)) + " temps à la minute. Là où la clarté "
        "manque, que l'air défaille et se vide.)"
    )

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_identity.py — proves, mechanically, that this repository bears no trace of its
author's civil identity. Run it BEFORE the first push, and before every push after.

    python tools/check_identity.py
    python tools/check_identity.py "Prenom Nom" "ton-adresse-civile"

WHY IT NAMES NO NAME. A checklist that writes the secret down in order to certify the
secret is absent is not a check: it IS the leak. That is exactly how it happened here —
the one file asserting "this name appears nowhere" was the one file that carried it, in
a public repository, in the git history, for weeks.

So this script works by ALLOWLIST. It asserts that every identity it finds — in the
files, in the git config, in every commit of the history — is one of the few the work is
allowed to bear. Anything else is a finding. Extra forbidden strings may be passed on the
command line: they are typed at run time and never committed.

Exit code 0 = clean. Non-zero = a leak, or something to look at.
"""
from __future__ import annotations
import os
import re
import subprocess
import sys

# The identities the work IS allowed to bear. All public, all pseudonymous.
ALLOWED_NAME = "Marcel Simplexe"
ALLOWED_EMAILS = {
    "marcel.simplexe@proton.me",          # the page's footer
    "marcel.simplexe@fadette.invalid",    # the machine's own committer
    "noreply@github.com",                 # le cachet de GitHub — voir WEB_FLOW plus bas.
                                          # Générique, publique, ne dit rien de personne.
                                          # Elle figure dans CE fichier : il faut donc que
                                          # le scan des fichiers l'accepte. L'AUTEUR, lui,
                                          # exige en plus le nom « Marcel Simplexe ».
}
# GitHub's privacy address for the pseudonymous account: <id>+<user>@users.noreply.github.com
ALLOWED_EMAIL_RE = re.compile(r"^[\w.+-]*\+?marcel-?simplexe@users\.noreply\.github\.com$", re.I)

# LE CACHET DE LA POSTE, PAS UN AUTEUR.
# GitHub signe TOUT commit fait au navigateur — éditeur crayon, « Create new file »,
# « Upload files », github.dev — avec sa propre clé GPG « web flow », et se met alors
# lui-même en COMMITTEUR. C'est ainsi qu'il peut les afficher « Verified ». Aucun
# réglage n'évite ça : un déploiement sans terminal ne peut STRUCTURELLEMENT pas
# produire autre chose.
#
# Git a deux champs distincts : l'AUTEUR (qui a écrit) et le COMMITTEUR (qui a déposé).
# La doctrine exige « Marcel Simplexe est l'auteur ici, et le seul » — et elle porte sur
# l'AUTEUR. GitHub n'est l'auteur de rien ; il est le tampon de l'enveloppe.
#
# L'auteur reste donc verrouillé, sans la moindre indulgence. Seul le committeur admet
# cette identité-là, et elle seule — un nom civil en committeur resterait une fuite.
WEB_FLOW = ("GitHub", "noreply@github.com")

EMAIL_RE = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}

RED, GREEN, YELLOW, OFF = "\033[91m", "\033[92m", "\033[93m", "\033[0m"
findings: list[str] = []
warnings: list[str] = []


def ok(msg: str) -> None:
    print(f"  {GREEN}[ ok ]{OFF} {msg}")


def bad(msg: str) -> None:
    findings.append(msg)
    print(f"  {RED}[LEAK]{OFF} {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"  {YELLOW}[ ?? ]{OFF} {msg}")


def email_allowed(addr: str) -> bool:
    return addr.lower() in ALLOWED_EMAILS or bool(ALLOWED_EMAIL_RE.match(addr))


def git(*args: str) -> str | None:
    try:
        r = subprocess.run(("git",) + args, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


# ---------------------------------------------------------------- 1. the working tree
def check_tree(forbidden: list[bytes]) -> None:
    print("\n1. Les fichiers du dépôt")
    seen_emails: dict[str, str] = {}
    hits = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            p = os.path.join(root, f)
            try:
                with open(p, "rb") as fh:
                    blob = fh.read()
            except OSError:
                continue
            low = blob.lower()
            for needle in forbidden:
                if needle in low:
                    bad(f"{p} contient une chaîne interdite")
                    hits += 1
            for m in EMAIL_RE.findall(blob):
                seen_emails.setdefault(m.decode("utf-8", "replace"), p)

    for addr, where in sorted(seen_emails.items()):
        if email_allowed(addr):
            ok(f"adresse trouvée, autorisée : {addr}")
        else:
            bad(f"adresse NON autorisée : {addr}  (dans {where})")
    if not hits and forbidden:
        ok("aucune des chaînes interdites fournies n'apparaît dans un fichier")
    if not seen_emails:
        ok("aucune adresse e-mail dans le dépôt")


# ------------------------------------------------------------------ 2. the git config
def check_config() -> None:
    print("\n2. La configuration git (celle qui SIGNERA tes commits)")
    if not os.path.isdir(".git"):
        warn("pas de dépôt git ici — relance ce script depuis le dépôt, avant le premier commit")
        return

    local_name = git("config", "--local", "user.name")
    local_mail = git("config", "--local", "user.email")
    glob_name = git("config", "--global", "user.name")
    glob_mail = git("config", "--global", "user.email")

    if not local_name or not local_mail:
        bad("AUCUNE identité git LOCALE n'est fixée pour ce dépôt — "
            "tes commits porteront la configuration GLOBALE de ta machine")
        if glob_name or glob_mail:
            warn(f"or la configuration globale est : name={glob_name!r} email={glob_mail!r} "
                 "— c'est CELA qui sera écrit dans chaque commit")
        print("\n     Corrige AVANT le premier commit :")
        print("       git config user.name  \"Marcel Simplexe\"")
        print("       git config user.email \"<id>+marcel-simplexe@users.noreply.github.com\"")
        print("     (l'adresse « noreply » de GitHub, pour que le commit ne soit rattaché")
        print("      à AUCUN autre compte : Paramètres GitHub → Emails → keep my email private)")
    else:
        if local_name == ALLOWED_NAME:
            ok(f"user.name (local) = {local_name!r}")
        else:
            bad(f"user.name (local) = {local_name!r} — attendu {ALLOWED_NAME!r}")
        if email_allowed(local_mail):
            ok(f"user.email (local) = {local_mail!r}")
        else:
            bad(f"user.email (local) = {local_mail!r} — adresse non autorisée")

    if (git("config", "--local", "commit.gpgsign") or
            git("config", "--global", "commit.gpgsign")) == "true":
        warn("commit.gpgsign = true — la SIGNATURE porte l'identité de ta clé. "
             "Désactive-la ici (git config commit.gpgsign false) ou signe avec une clé au pseudonyme")


# ----------------------------------------------------------------- 3. the git history
def check_history(forbidden: list[bytes]) -> None:
    print("\n3. L'historique — chaque commit, jusqu'au premier")
    if not os.path.isdir(".git"):
        return
    log = git("log", "--all", "--format=%H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%s")
    if log is None:
        ok("aucun commit encore — c'est le meilleur moment pour tout verrouiller")
        return
    lines = [l for l in log.splitlines() if l.strip()]
    if not lines:
        ok("aucun commit encore")
        return

    authors: set[tuple[str, str]] = set()
    committers: set[tuple[str, str]] = set()
    for line in lines:
        parts = line.split("\x1f")
        if len(parts) < 6:
            continue
        h, an, ae, cn, ce, subj = parts[:6]
        authors.add((an, ae))
        committers.add((cn, ce))
        low = subj.lower().encode()
        for needle in forbidden:
            if needle in low:
                bad(f"le message du commit {h[:8]} contient une chaîne interdite")

    # L'AUTEUR — verrouillé. C'est lui que la doctrine nomme, et lui seul.
    for name, mail in sorted(authors):
        if name == ALLOWED_NAME and email_allowed(mail):
            ok(f"auteur : {name} <{mail}>")
        else:
            bad(f"auteur NON autorisé dans l'historique : {name} <{mail}> "
                "— un commit ne se corrige pas, il se réécrit")

    # LE COMMITTEUR — le cachet de la poste. GitHub y est inévitable au navigateur.
    for name, mail in sorted(committers):
        if name == ALLOWED_NAME and email_allowed(mail):
            ok(f"committeur : {name} <{mail}>")
        elif (name, mail) == WEB_FLOW:
            ok(f"committeur : {name} <{mail}> — le cachet de GitHub sur tout commit "
               "fait au navigateur. L'auteur, lui, reste Marcel Simplexe.")
        else:
            bad(f"committeur NON autorisé dans l'historique : {name} <{mail}> "
                "— un commit ne se corrige pas, il se réécrit")
    print(f"       ({len(lines)} commit(s) inspecté(s))")


def main() -> int:
    forbidden = [a.lower().encode() for a in sys.argv[1:] if a.strip()]
    print("=" * 74)
    print("  Fadette — contrôle d'identité. Ce script ne nomme personne.")
    if forbidden:
        print(f"  ({len(forbidden)} chaîne(s) interdite(s) reçue(s) en argument, jamais écrite(s) sur disque)")
    else:
        print("  Astuce : passe ton nom civil en argument pour le chercher aussi.")
        print("           python tools/check_identity.py \"Prenom Nom\" \"ton-adresse-civile\"")
    print("=" * 74)

    check_tree(forbidden)
    check_config()
    check_history(forbidden)

    print("\n" + "=" * 74)
    if findings:
        print(f"{RED}  {len(findings)} FUITE(S). Ne pousse pas.{OFF}")
        for f in findings:
            print(f"   - {f}")
        return 1
    if warnings:
        print(f"{YELLOW}  Aucune fuite, mais {len(warnings)} point(s) à regarder.{OFF}")
        for w in warnings:
            print(f"   - {w}")
        return 0
    print(f"{GREEN}  Propre. Le dépôt ne porte que Marcel Simplexe.{OFF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

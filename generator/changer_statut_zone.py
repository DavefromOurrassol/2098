#!/usr/bin/env python3
"""
changer_statut_zone.py — Ourrassol 2098 (S27, 13 octobre 2026)
==============================================================

Change le `statut` d'UNE zone dans geographie/<scénario>.md, sans toucher
au reste du fichier (modification de la seule ligne `statut` du bloc de la
zone, pas de réécriture YAML). Refuse si le bloc est introuvable ou double,
ou si le statut actuel n'est pas celui annoncé par --avant.

USAGE
    python3 generator/changer_statut_zone.py --scenario breakdown --zone geneve_bunker_institutions --avant fragmenté --apres en_declin           # aperçu
    python3 generator/changer_statut_zone.py --scenario breakdown --zone geneve_bunker_institutions --avant fragmenté --apres en_declin --apply   # écrit (.bak_statut)

Ensuite, pour le texte du corps : python3 generator/regenerer_corps_geographie.py --scenario <scénario> --execute
"""

import argparse
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
STATUTS = ["dominant", "stable", "fragmenté", "en_declin", "disparu", "emergent"]


def plie(s):
    s = unicodedata.normalize("NFKD", str(s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def main():
    ap = argparse.ArgumentParser(description="Change le statut d'une zone (aperçu par défaut).")
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--zone", required=True, help="slug de la zone")
    ap.add_argument("--avant", required=True, help="statut actuel attendu (contrôle)")
    ap.add_argument("--apres", required=True, help=" | ".join(STATUTS))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    apres = {plie(s): s for s in STATUTS}.get(plie(a.apres))
    if not apres:
        sys.exit(f"✗ statut {a.apres!r} invalide ({' | '.join(STATUTS)})")
    p = VAULT / "geographie" / f"{a.scenario}.md"
    if not p.exists():
        sys.exit(f"✗ {p.relative_to(VAULT)} introuvable")
    texte = p.read_text(encoding="utf-8")
    L = texte.split("\n")

    debut = re.compile(r"^(\s*)-\s+slug:\s*['\"]?" + re.escape(a.zone) + r"['\"]?\s*$")
    blocs = [i for i, l in enumerate(L) if debut.match(l)]
    if len(blocs) != 1:
        sys.exit(f"✗ bloc de la zone {a.zone!r} introuvable ou en double (lignes {[i + 1 for i in blocs]})")
    i = blocs[0]
    ind = len(L[i]) - len(L[i].lstrip())
    fin = next((k for k in range(i + 1, len(L))
                if L[k].strip() and (len(L[k]) - len(L[k].lstrip()) <= ind or L[k].startswith("---"))), len(L))
    # Clés directes du bloc : même retrait que la première clé après « - ».
    retrait_cle = ind + (len(L[i].lstrip()) - len(L[i].lstrip()[1:].lstrip()))
    lignes_statut = [k for k in range(i + 1, fin) if re.match(r"^ {" + str(retrait_cle) + r"}statut:", L[k])]
    if len(lignes_statut) != 1:
        sys.exit(f"✗ {len(lignes_statut)} ligne(s) `statut` dans le bloc (lignes {i + 1}-{fin}) : attendu 1")
    k = lignes_statut[0]
    actuel = re.sub(r"^\s+statut:\s*", "", L[k]).strip().strip("'\"")
    if plie(actuel) != plie(a.avant):
        sys.exit(f"✗ statut actuel {actuel!r}, pas {a.avant!r} : rien écrit")
    nouvelle = re.sub(r"(statut:\s*).*", lambda m: m.group(1) + apres, L[k])
    L[k] = nouvelle
    nouveau = "\n".join(L)

    m = re.match(r"^---\s*\n(.*?)\n---", nouveau, re.S)
    try:
        fm = yaml.safe_load(m.group(1)) if m else None
    except yaml.YAMLError as e:
        sys.exit(f"✗ frontmatter illisible après modification : {e}")
    relu = [z.get("statut") for z in (fm or {}).get("zones") or [] if isinstance(z, dict) and z.get("slug") == a.zone]
    if relu != [apres]:
        sys.exit(f"✗ relecture inattendue : {relu}")

    print(f"{'ÉCRITURE' if a.apply else 'APERÇU (rien écrit)'} — {p.relative_to(VAULT)}, ligne {k + 1}")
    print(f"  {a.zone} : {actuel} → {apres}")
    if not a.apply:
        print("Relancer avec --apply pour écrire (sauvegarde .bak_statut).")
        return
    bak = p.with_name(p.name + ".bak_statut")
    if not bak.exists():
        shutil.copy2(p, bak)
    p.write_text(nouveau, encoding="utf-8")
    print(f"✓ écrit. Texte du corps : python3 generator/regenerer_corps_geographie.py --scenario {a.scenario} --execute")


if __name__ == "__main__":
    main()

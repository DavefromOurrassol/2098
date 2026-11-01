#!/usr/bin/env python3
"""patch_s30_mots_generiques.py — Ourrassol 2098, 1er novembre 2026

Défaut relevé au test réel de S30 (chute_holdfast_2072) : la rubrique « Fiches
à relire » de la liste d'application cherchait « Réseau » (mot à majuscule de
« Réseau des Citadelles du Sud-Pacifique ») : 12 zones sans rapport listées
(Réseau Terrafond, Réseau Väinälä, réseau de capteurs…).

_termes_hypothese() (simuler_et_si.py) écarte déjà les mots de MOTS_GENERIQUES,
mais la liste ne contient que des mots d'événement (Invasion, Chute…) et
quelques mots d'État. Correctif : ajouter les mots génériques d'organisation et
d'événement qui ouvrent les noms du vault (Réseau, Conseil, Consortium, Pacte,
Arc, Bloc…). Les noms propres qui les suivent (Holdfast, Tabriz, Citadelles)
restent cherchés. La liste sert aussi aux noms courts de sous-zones (V8.14) :
même effet souhaité.

Usage (depuis la racine du vault) :
    python3 generator/patch_s30_mots_generiques.py
Idempotent (marqueur PATCH_S30_MOTS_GENERIQUES) ; sauvegarde
simuler_et_si.py.bak_s30generiques ; contrôle de compilation, restauration si échec.
"""
import py_compile
import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
CIBLE = GEN / "simuler_et_si.py"
MARQUEUR = "PATCH_S30_MOTS_GENERIQUES"

AVANT = '"États", "Etats", "État", "Etat", "Nations", "République", "Royaume"}'
APRES = ('"États", "Etats", "État", "Etat", "Nations", "République", "Royaume",\n'
         '                   # PATCH_S30_MOTS_GENERIQUES (1er nov 2026) : mots qui ouvrent les noms\n'
         '                   # d\'organisations et d\'événements du vault (« Réseau des Citadelles… »).\n'
         '                   "Réseau", "Reseau", "Conseil", "Consortium", "Consortiums", "Fédération",\n'
         '                   "Confédération", "Ligue", "Alliance", "Union", "Agence", "Autorité",\n'
         '                   "Assemblée", "Commission", "Comité", "Bureau", "Office", "Institut",\n'
         '                   "Fonds", "Banque", "Pacte", "Accord", "Accords", "Traité", "Coalition",\n'
         '                   "Collectif", "Collectifs", "Mouvement", "Front", "Communauté", "Organisation",\n'
         '                   "Système", "Plateforme", "Plateformes", "Bloc", "Zone", "Zones", "Arc",\n'
         '                   "Ceinture", "Corridor", "Bassin", "Territoire", "Territoires",\n'
         '                   "Destruction", "Explosion", "Occupation", "Réintégration", "Vague",\n'
         '                   "Disparition", "Fin", "Naissance", "Création", "Dissolution"}')


def main():
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable — lancer depuis la racine du vault. Rien fait.")
    src = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in src:
        print("· déjà appliqué — rien fait.")
        return
    n = src.count(AVANT)
    if n != 1:
        sys.exit(f"✗ fin de MOTS_GENERIQUES trouvée {n} fois (attendu 1) — rien fait.")
    bak = CIBLE.with_name(CIBLE.name + ".bak_s30generiques")
    shutil.copy2(CIBLE, bak)
    CIBLE.write_text(src.replace(AVANT, APRES, 1), encoding="utf-8")
    try:
        py_compile.compile(str(CIBLE), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, CIBLE)
        sys.exit(f"✗ compilation échouée, fichier restauré : {e}")
    print(f"✓ {CIBLE.name} patché (sauvegarde {bak.name})")


if __name__ == "__main__":
    main()

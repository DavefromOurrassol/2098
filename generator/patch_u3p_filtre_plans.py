#!/usr/bin/env python3
"""
patch_u3p_filtre_plans.py — Ourrassol 2098 (U3p, 11 novembre 2026)
==================================================================
Extracteur d'événements : filtre mécanique qui écarte les plans, projets et débats
(futur, « en préparation », « devrait »…) que l'IA liste encore malgré la consigne.

Modifie generator/extraire_evenements_article.py :
  - ajoute motif_non_evenement(description, citation, annee_article) ;
  - l'appelle dans extraire() avant le contrôle de citation ; un candidat écarté
    produit un avertissement « écarté (plan / projet / débat) : <motif> » ;
  - le résultat JSON gagne la clé "ecartes" (description + motif), sans effet sur la GUI.

Trois motifs :
  1. année postérieure à l'article écrite dans la description (ex. « 2099-2120 ») ;
  2. marqueur de projet / futur dans la description ou la citation (forts) ;
  3. description qui s'ouvre sur un plan / programme / projet / débat sans verbe
     d'accomplissement (adopté, lancé, voté, signé, entré en vigueur…).

USAGE (depuis la racine du vault)
  python3 generator/patch_u3p_filtre_plans.py            # dry-run
  python3 generator/patch_u3p_filtre_plans.py --apply    # applique (sauvegarde .bak_u3p)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "extraire_evenements_article.py"
TAG = "u3p"

# ---- 1. fonction ajoutée avant extraire() -------------------------------------------
ANCRE_FONCTION = "def extraire(fichier, scenario, annee, mois, racine=RACINE_DEFAUT, _llm=appeler_llm):\n"

FONCTION = '''# U3p : marqueurs d'un plan / projet / débat (texte normalisé : minuscules, sans accents)
_MARQUEURS_PROJET = (
    " en preparation ", " se prepare ", " se preparent ", " est en projet ", " en projet ",
    " projet de ", " en discussion ", " en debat ", " fait debat ", " font debat ",
    " devrait ", " devraient ", " pourrait ", " pourraient ", " envisage ", " envisagent ",
    " envisagee ", " prevu pour ", " prevue pour ", " prevus pour ", " prevues pour ",
    " d ici 20", " a l horizon ", " sera lance ", " sera lancee ", " seront lances ",
    " sera mis en place ", " sera adopte ", " sera adoptee ", " vise a ",
)
_DEBUT_PLAN = (" plan ", " programme ", " projet ", " strategie ", " feuille de route ",
               " debat ", " reforme ", " proposition ", " initiative ")
_ACCOMPLI = (" adopte", " lance ", " lancee ", " vote", " signe", " entre en vigueur",
             " entree en vigueur", " promulgue", " ratifie", " inaugure", " active ",
             " activee ", " annonce ", " annoncee ", " adoptee ")


def motif_non_evenement(description, citation, annee_article):
    """Retourne le motif d'écart (str) si le candidat ressemble à un plan, un projet ou un
    débat, sinon None."""
    import re as _re
    desc_n = _norm(description)
    cit_n = _norm(citation)
    # 1. année postérieure à l'article écrite dans la description
    for a in _re.findall(r"\\b(2[01]\\d\\d)\\b", str(description or "")):
        if int(a) > int(annee_article):
            return f"mentionne l'année {a}, postérieure à l'article"
    # 2. marqueur de projet / futur
    for m in _MARQUEURS_PROJET:
        if m in desc_n or m in cit_n:
            return f"marqueur de projet « {m.strip()} »"
    # 3. description qui s'ouvre sur un plan / programme / débat, sans verbe d'accomplissement
    debut = " " + " ".join(desc_n.split()[:4]) + " "
    for d in _DEBUT_PLAN:
        if d in debut:
            if not any(v in desc_n for v in _ACCOMPLI):
                return f"s'ouvre sur « {d.strip()} » sans fait accompli"
            break
    return None


'''

# ---- 2. appel dans extraire() ----------------------------------------------------------
ANCRE_APPEL = '        cit = " ".join(str(ev.get("citation") or "").split())\n        cit_ok = bool(cit)'
APPEL = '''        motif = motif_non_evenement(ev.get("description"), ev.get("citation"), annee)
        if motif:
            av.append(f"« {str(ev['description'])[:60]}… » écarté (plan / projet / débat) : {motif}")
            ecartes.append({"description": " ".join(str(ev["description"]).split()), "motif": motif})
            continue
'''

# ---- 3. liste ecartes + clé de sortie --------------------------------------------------
ANCRE_INIT = "    sortie, av = [], []\n"
INIT = "    sortie, av, ecartes = [], [], []\n"
ANCRE_RET = '            "evenements": sortie, "avertissements": av}'
RET = '            "evenements": sortie, "avertissements": av, "ecartes": ecartes}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")
    if "motif_non_evenement" in src:
        print("= déjà appliqué, rien à faire")
        return
    for nom, ancre in (("fonction", ANCRE_FONCTION), ("appel", ANCRE_APPEL),
                       ("init", ANCRE_INIT), ("retour", ANCRE_RET)):
        n = src.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (attendu 1) : fichier modifié depuis U3f ?")
    nouveau = src.replace(ANCRE_FONCTION, FONCTION + ANCRE_FONCTION)
    nouveau = nouveau.replace(ANCRE_APPEL, APPEL + ANCRE_APPEL)
    nouveau = nouveau.replace(ANCRE_INIT, INIT)
    nouveau = nouveau.replace(ANCRE_RET, RET)
    print(f"{CIBLE.name} : 4 modifications prévues (+{len(nouveau.splitlines()) - len(src.splitlines())} lignes)")
    if not args.apply:
        print("dry-run : rien écrit. Relancer avec --apply.")
        return
    bak = CIBLE.with_name(CIBLE.name + f".bak_{TAG}")
    shutil.copy2(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"✓ appliqué ; sauvegarde {bak.name} ; py_compile OK")


if __name__ == "__main__":
    main()

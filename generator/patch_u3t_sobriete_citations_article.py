#!/usr/bin/env python3
"""
patch_u3t_sobriete_citations_article.py — Ourrassol 2098 (U3t, 11 novembre 2026)
================================================================================
Suite de U3s. Test réel du 11 nov (ouverture du dispensaire des Grottes, 2042) : le passage de
l'article était bien transmis, mais l'IA a quand même romancé (scène du 12 octobre, citation
prêtée à un personnage de l'article, chiffre différent). Cause : le schéma demande une
description « de 3-4 lignes vivantes ».

Quand un passage d'article est fourni (U3s), ce patch :
  1. remplace « 3-4 lignes vivantes » par « 3-4 lignes sobres, tirées du passage : ni scène,
     ni dialogue, ni détail absent du passage » ;
  2. ajoute au bloc de contexte : paroles de personnage seulement si elles sont dans le
     passage, pas de citation entre guillemets nouvelle, pas de date plus précise ni de
     chiffre absent du passage ;
  3. contrôle MÉCANIQUE (sans IA) après la génération : toute citation « … » d'au moins 4 mots
     dans la réalisation, la description ou les conséquences qui ne figure nulle part dans
     l'article produit un avertissement « ⚠ [scénario] citation absente de l'article : … »
     (non bloquant ; il apparaît dans les « Alertes de l'injection »).
Sans passage d'article, rien ne change.

Modifie generator/inject_custom_events.py (6 modifications). Exige U3s appliqué. Sauvegarde .bak_u3t.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3t_sobriete_citations_article.py            # dry-run
  python3 generator/patch_u3t_sobriete_citations_article.py --apply    # applique
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "inject_custom_events.py"
TAG = "u3t"

# 1. cache de l'article + fonction de contrôle
A1 = "# U3s (11 novembre 2026) -- contexte de l'article d'origine pour l'étape 2\n"
N1 = A1 + '''_DERNIER_ARTICLE_U3S = {}   # U3t : scénario -> texte de l'article trouvé (pour le contrôle des citations)


def _citations_absentes_u3t(instance_data, scenario):
    """U3t : citations « … » (4 mots au moins) du récit absentes de l'article d'origine."""
    article = _DERNIER_ARTICLE_U3S.get(scenario)
    if not article:
        return []
    base = _norm_ctx_u3s(article)
    out = []
    for k in ("realisation", "description_complete", "consequences"):
        for m in re.finditer(r"«\\s*([^»]{15,}?)\\s*»", str(instance_data.get(k) or "")):
            q = _norm_ctx_u3s(m.group(1))
            if len(q.split()) >= 4 and q not in base:
                out.append(" ".join(m.group(1).split())[:140])
    return out


'''

# 2. remise à zéro du cache au début de la recherche de contexte
A2 = '    try:\n        cands = [f["fait"] for f in _faits_du_scenario(idea, scenario)\n'
N2 = "    _DERNIER_ARTICLE_U3S.pop(scenario, None)   # U3t\n" + A2

# 3. mémorisation de l'article trouvé
A3 = '            print(f"  [contexte article] {f.name} (paragraphe {i + 1}/{len(paras)})")\n'
N3 = '            _DERNIER_ARTICLE_U3S[scenario] = " ".join(paras)   # U3t\n' + A3

# 4. consigne de sobriété dans le prompt
A4 = "    contexte_txt = _texte_contexte_article(idea, scenario)  # U3s\n"
N4 = A4 + '''    if contexte_txt:   # U3t : sobriété quand un passage d'article est fourni
        contexte_txt += ("Ne prête à un personnage de l'article que des paroles qui figurent dans ce passage ; "
                         "n'ajoute aucune citation entre guillemets, aucune date plus précise (jour, mois, saison) "
                         "que celle du passage, aucun chiffre, lieu ni détail de scène qui n'y figure pas.\\n")
        desc_consigne_txt = ("description journalistique de l'événement — 3-4 lignes sobres, tirées du passage "
                             "de l'article : ni scène, ni dialogue, ni détail absent du passage")
    else:
        desc_consigne_txt = "description journalistique de l'événement — 3-4 lignes vivantes"
'''
A4b = '  "description_complete": "description journalistique de l\'événement — 3-4 lignes vivantes",\n'
N4b = '  "description_complete": "{desc_consigne_txt}",\n'

# 5. avertissement après la génération
A5 = '            for v in etat_contraintes or []:   # PATCH_S30_CONTRAINTES\n                print(f"  ⚠ [{scenario}] fait imposé non respecté : {v}")\n'
N5 = A5 + '''            for q in _citations_absentes_u3t(instance_data, scenario):   # U3t
                print(f"  ⚠ [{scenario}] citation absente de l'article : « {q} »")
'''

REMPLACEMENTS = [("cache + contrôle", A1, N1), ("reset", A2, N2), ("mémorisation", A3, N3),
                 ("consigne", A4, N4), ("schéma description", A4b, N4b), ("avertissement", A5, N5)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")
    if "_citations_absentes_u3t" in src:
        print("= déjà appliqué, rien à faire")
        return
    if "_texte_contexte_article" not in src:
        sys.exit("✗ U3s n'est pas appliqué")
    for nom, ancre, _ in REMPLACEMENTS:
        n = src.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (attendu 1) : fichier modifié ?")
    nouveau = src
    for _, ancre, rempl in REMPLACEMENTS:
        nouveau = nouveau.replace(ancre, rempl)
    print(f"{CIBLE.name} : {len(REMPLACEMENTS)} modifications prévues "
          f"(+{len(nouveau.splitlines()) - len(src.splitlines())} lignes)")
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

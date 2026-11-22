#!/usr/bin/env python3
"""
patch_u4m_extracteur_incises_anachronismes.py — Ourrassol 2098 (22 novembre 2026)
================================================================================

B9 « source mince → invention, suite », volets a) et b), traités À LA SOURCE :
l'extracteur d'événements d'un article (extraire_evenements_article.py). Depuis
U3aa, la description extraite devient le texte de la fiche injectée : un défaut
ici se retrouve tel quel dans le vault.

b) Incises : un événement seulement nommé en passant (« depuis la crise de 2044 »)
   donnait une hypothèse sans matière, donc une fiche inventée.
   - consigne : champ "mention" = "detaille" | "incise" ;
   - mécanique : un événement « incise » est écarté (liste « écartés », motif dit).
a) Anachronisme sans année : un article de 2098 raconte un événement de 2039 avec
   la situation de 2098 (« aujourd'hui », « désormais »…) ; U3y ne voyait que les années.
   - consigne : la description raconte l'événement À SA DATE ;
   - mécanique, pour un événement d'une année antérieure à l'article : marqueurs du
     présent de l'article (aujourd'hui, actuellement, désormais, de nos jours, à présent,
     à ce jour, depuis lors) ou année postérieure à l'événement dans la description
     -> ⚠ et champ "anachronismes" (l'événement est gardé : corriger sa description
     avant ✨ Proposer).

Cible : generator/extraire_evenements_article.py (sauvegarde .bak_u4m).

Usage (depuis la racine du vault) :
    python3 generator/patch_u4m_extracteur_incises_anachronismes.py           # dry-run
    python3 generator/patch_u4m_extracteur_incises_anachronismes.py --apply   # écrit
"""

import argparse
import shutil
import sys
from pathlib import Path

CIBLE = Path("generator/extraire_evenements_article.py")
TAG = "u4m"

REMPLACEMENTS = [
    ("prompt : règles mention et description à sa date",
     '- "deja_connu" : le slug EXACT de la liste ci-dessous si c\'est le même événement, sinon null.\n',
     '- "deja_connu" : le slug EXACT de la liste ci-dessous si c\'est le même événement, sinon null.\n'
     '- "mention" : "detaille" si l\'article dit ce qui s\'est passé (au moins qui et quoi) ; "incise" si\n'
     '  l\'événement est seulement nommé au détour d\'une phrase (« depuis la crise de 2044 », « après les\n'
     '  accords de Lagos »), sans être raconté.\n'
     '- "description" raconte l\'événement À SA DATE : jamais « aujourd\'hui », « actuellement »,\n'
     '  « désormais », ni l\'état du monde au moment de l\'article, ni ce qui s\'est passé ensuite.\n'),
    ("prompt : exemple JSON",
     '  "date_explicite": true, "nature": "passe", "deja_connu": null}}]}}"""',
     '  "date_explicite": true, "nature": "passe", "mention": "detaille", "deja_connu": null}}]}}"""'),
    ("mécanique : incise écartée",
     '        motif = motif_non_evenement(ev.get("description"), ev.get("citation"), annee)\n',
     '        if str(ev.get("mention") or "").strip().lower() == "incise":   # U4m\n'
     '            motif_i = "simple mention en incise : l\'article ne raconte pas l\'événement"\n'
     '            av.append(f"« {str(ev[\'description\'])[:60]}… » écarté : {motif_i}")\n'
     '            ecartes.append({"description": " ".join(str(ev["description"]).split()), "motif": motif_i})\n'
     '            continue\n'
     '        motif = motif_non_evenement(ev.get("description"), ev.get("citation"), annee)\n'),
    ("mécanique : anachronismes",
     '        nature = "propre" if str(ev.get("nature")).strip().lower() == "propre" else "passe"\n',
     '        nature = "propre" if str(ev.get("nature")).strip().lower() == "propre" else "passe"\n'
     '        anach = anachronismes_u4m(ev.get("description"), an, annee)   # U4m\n'
     '        if anach:\n'
     '            av.append(f"« {str(ev[\'description\'])[:60]}… » : anachronisme ({\'; \'.join(anach)}) : "\n'
     '                      f"corriger la description avant ✨ Proposer (elle devient le texte de la fiche)")\n'),
    ("sortie : champ anachronismes",
     '            "deja_connu_nom": slugs_connus[dk][1] if dk else None,\n',
     '            "deja_connu_nom": slugs_connus[dk][1] if dk else None,\n'
     '            "anachronismes": anach,   # U4m\n'),
    ("fonction anachronismes_u4m()",
     "def _nettoyer_citation(s):\n",
     '''# U4m (22 nov 2026) : présent de l'article glissé dans un événement plus ancien
_PRESENT_ARTICLE_U4M = ((" aujourd hui ", "aujourd'hui"), (" actuellement ", "actuellement"),
                        (" desormais ", "désormais"), (" de nos jours ", "de nos jours"),
                        (" a present ", "à présent"), (" a ce jour ", "à ce jour"),
                        (" depuis lors ", "depuis lors"))


def anachronismes_u4m(description, annee_evenement, annee_article):
    """Marqueurs du présent de l'article, ou années postérieures à l'événement, dans la
    description d'un événement d'une année antérieure à l'article. Liste (vide sinon)."""
    try:
        an, an_art = int(annee_evenement), int(annee_article)
    except (TypeError, ValueError):
        return []
    if an >= an_art:
        return []
    d = _norm(description)
    out = [f"« {lib} »" for m, lib in _PRESENT_ARTICLE_U4M if m in d]
    apres = sorted({int(a) for a in re.findall(r"(?<!\\d)(20\\d\\d)(?!\\d)", str(description or ""))
                    if an < int(a) <= an_art})
    if apres:
        out.append("année(s) postérieure(s) à l'événement : " + ", ".join(str(a) for a in apres))
    return out


def _nettoyer_citation(s):
'''),
]


def main():
    ap = argparse.ArgumentParser(description="Patch U4m : extracteur, incises et anachronismes.")
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon dry-run)")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ {CIBLE} introuvable : lancer depuis la racine du vault.")
    texte = CIBLE.read_text(encoding="utf-8")
    if "anachronismes_u4m" in texte:
        sys.exit("✗ U4m déjà appliqué : rien à faire.")
    nouveau, ok = texte, True
    for nom, ancien, neuf in REMPLACEMENTS:
        n = nouveau.count(ancien)
        if n != 1:
            print(f"✗ {nom} : ancre trouvée {n} fois (attendu 1)")
            ok = False
            continue
        nouveau = nouveau.replace(ancien, neuf)
        print(f"✓ {nom}")
    if not ok:
        sys.exit("✗ Patch non appliqué (fichier différent de celui attendu).")
    try:
        compile(nouveau, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas : {e}")
    print("✓ Le fichier patché compile.")
    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    shutil.copy(CIBLE, CIBLE.with_name(CIBLE.name + f".bak_{TAG}"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"\n→ {CIBLE} patché (sauvegarde {CIBLE.name}.bak_{TAG}).")


if __name__ == "__main__":
    main()

"""Corrige la fiche piratage_ecrans_greffes_hepatiques_2098 d'après l'article source.
Sauvegarde .bak_u3h puis réécrit. À lancer depuis la racine du vault."""
import re, shutil
from pathlib import Path

F = Path("event_instances/piratage_ecrans_greffes_hepatiques_2098_new_sustainability.md")
D = "Le 8 mars 2098, les écrans du Centre Régénératif du Léman, à Genève, affichent les noms de 1 247 personnes en attente d'une greffe hépatique dans le canton. Le collectif Santé pour Tous revendique l'action et dénonce une médecine de tri algorithmique : la grille de priorité d'ARIA, l'IA qui alloue les ressources médicales, désavantagerait les travailleurs précaires. Selon le collectif, 89 % des personnes listées travaillent dans les serres verticales du Delta du Rhône ou les entrepôts de la Ceinture Boréale, et l'algorithme les juge « remplaçables »."
C = "L'action place la grille de priorité d'ARIA au centre du débat sur l'accès aux soins régénératifs à Genève : publication des algorithmes, nationalisation des cliniques et passeport sanitaire universel figurent parmi les pistes discutées. La tension monte sur *sante_biotechnologies*, *gouvernance_institutions* et *technologie_information*, tandis que *valeurs_culture_tempo_sociale* recule."
R = "Dans new_sustainability, le collectif Santé pour Tous prend le contrôle des écrans du Centre Régénératif du Léman pour y afficher la liste des 1 247 personnes en attente d'une greffe hépatique dans le canton. L'action vise ARIA, dont la grille de priorité est jugée défavorable aux travailleurs précaires des secteurs agricole et logistique."
N = "Événement tiré de l'article du 24 mars 2098 (Sofia Waeber) : grille ARIA, inégalités d'accès aux soins régénératifs, résistance algorithmique. Il s'inscrit dans la trajectoire de new_sustainability : gouvernance technocratique stable mais contestée."
A = [
    "collectifs_de_desobeissance_algorithmique_new_sustainability",
    "reseau_global_de_cliniques_regeneratives_new_sustainability",
    "grille_aria_new_sustainability",
]

t = F.read_text(encoding="utf-8")
if "grille_aria_new_sustainability" in t:
    raise SystemExit("déjà appliqué")
shutil.copy2(F, str(F) + ".bak_u3h")


def sub(t, k, nxt, v):
    return re.sub(rf"^{k}:.*?^(?={nxt}:)", lambda m: v, t, count=1, flags=re.M | re.S)


t = sub(t, "description", "consequences", f"description: >\n  {D}\n")
t = sub(t, "consequences", "realisation", f"consequences: >\n  {C}\n")
t = sub(t, "realisation", "impact_sur_variables", f"realisation: >\n  {R}\n")
t = sub(t, "acteurs_impliques", "note_coherence", "acteurs_impliques:\n" + "".join(f"    - {a}\n" for a in A))
t = sub(t, "note_coherence", "custom_source", f"note_coherence: >\n  {N}\n")

fm, corps = t.split("\n# ", 1)
titre = corps.split("\n")[0]
impact = re.search(r"## Impact sur les variables\n.*?(?=\n## Acteurs impliqués)", corps, re.S).group(0)
F.write_text(
    fm + f"\n# {titre}\n\n## Réalisation dans [[new_sustainability]]\n{R}\n\n"
    f"## Description journalistique\n{D}\n\n## Conséquences\n{C}\n\n{impact}\n\n## Acteurs impliqués\n"
    + "".join(f"- [[{a}]]\n" for a in A)
    + f"\n## Note de cohérence\n{N}\n",
    encoding="utf-8",
)
print("ok")

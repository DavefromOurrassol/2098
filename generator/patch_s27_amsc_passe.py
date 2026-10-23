#!/usr/bin/env python3
"""
patch_s27_amsc_passe.py — 23 octobre 2026 (S27.2, restes de Genève).

Fiche instances/agence_stabilisation_climatique_breakdown.md (BCUC, disparu en
2076 avec Genève) : rôle, responsabilités, description journalistique, signes
distinctifs et tensions narratives réécrits au passé (le Directeur Général
« nommé en 2089 » devient « nommé en 2072 ») ; corps « ## Relations » aligné
sur le frontmatter (vidé le 13 oct).

Chaque texte est remplacé là où il figure (frontmatter et corps) ; le nombre
d'occurrences est vérifié avant toute écriture, puis le frontmatter est relu.
Sauvegarde .bak_s27_amsc. Refuse un second passage.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_amsc_passe.py            # aperçu, rien n'est écrit
    python3 generator/patch_s27_amsc_passe.py --apply
"""

import re
import shutil
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
CIBLE = VAULT / "instances" / "agence_stabilisation_climatique_breakdown.md"

# (champ, ancien, nouveau, occurrences attendues : frontmatter + corps)
TEXTES = [
    ("role_dans_scenario",
     "Vestige dysfonctionnel de l'Agence Mondiale pour la Stabilisation Climatique, le BCUC survit comme une "
     "coquille administrative sans autorité réelle. Jadis mandaté pour orchestrer les grandes interventions "
     "géo-ingénieristes, il n'existe plus que comme structure fantôme, réclamant une légitimité que personne ne "
     "lui reconnaît. Dans un monde fragmenté, les blocs régionaux ont cessé de financer et d'obéir à ses "
     "directives dès 2071, mais l'agence refuse de se dissoudre, continuant d'émettre des protocoles que personne "
     "n'applique. Elle représente la mémoire institutionnelle d'un ordre mondial révolu, à la fois inutile et "
     "dangereusement nostalgique.",
     "Vestige dysfonctionnel de l'Agence Mondiale pour la Stabilisation Climatique, le BCUC a survécu jusqu'en "
     "2076 comme une coquille administrative sans autorité réelle. Jadis mandaté pour orchestrer les grandes "
     "interventions géo-ingénieristes, il n'était plus qu'une structure fantôme, réclamant une légitimité que "
     "personne ne lui reconnaissait. Les blocs régionaux avaient cessé de financer et d'obéir à ses directives "
     "dès 2071, mais l'agence a refusé de se dissoudre et a continué d'émettre des protocoles que personne "
     "n'appliquait, jusqu'à la destruction de Genève en 2076, qui l'a emportée. Elle reste le symbole d'un ordre "
     "mondial révolu, à la fois inutile et dangereusement nostalgique.",
     2),
    ("responsabilites",
     "Émet des 'directives d'urgence climatique' ignorées par la majorité des entités régionales souveraines. "
     "Gère un réseau résiduel de stations de monitoring atmosphérique — le seul actif tangible encore "
     "opérationnel — et tente de négocier des accords de réponse aux catastrophes avec des blocs régionaux de "
     "plus en plus hostiles. Sert occasionnellement de canal diplomatique de dernier recours entre factions qui "
     "refusent tout contact direct.",
     "Émettait des « directives d'urgence climatique » ignorées par la majorité des entités régionales "
     "souveraines. Gérait un réseau résiduel de stations de monitoring atmosphérique — son seul actif tangible "
     "encore opérationnel — et tentait de négocier des accords de réponse aux catastrophes avec des blocs "
     "régionaux de plus en plus hostiles. Servait occasionnellement de canal diplomatique de dernier recours "
     "entre factions qui refusaient tout contact direct.",
     2),
    ("description_journalistique",
     "Au 47e étage d'une tour de Genève à moitié abandonnée, une centaine de fonctionnaires continuent "
     "d'imprimer des rapports que personne ne lit. Le Bureau de Coordination d'Urgence Climatique — dernier "
     "souffle de l'ancienne AMSC — émet chaque semaine des 'alertes planétaires' en trois langues mortes de la "
     "diplomatie internationale. Ses serveurs contiennent l'historique complet de cinquante ans d'interventions "
     "géo-ingénieristes, une archive inestimable que les blocs régionaux s'arrachent par espionnage plutôt que "
     "par coopération. Son Directeur Général, nommé en 2089 par un vote de neuf États sur cent quarante, signe "
     "des décrets avec l'aplomb d'un homme qui gouvernerait encore le monde.",
     "Jusqu'en 2076, au 47e étage d'une tour de Genève à moitié abandonnée, une centaine de fonctionnaires "
     "imprimaient des rapports que personne ne lisait. Le Bureau de Coordination d'Urgence Climatique — dernier "
     "souffle de l'ancienne AMSC — émettait chaque semaine des « alertes planétaires » en trois langues mortes de "
     "la diplomatie internationale. Ses serveurs contenaient l'historique de cinquante ans d'interventions "
     "géo-ingénieristes, une archive que les blocs régionaux s'arrachaient par espionnage plutôt que par "
     "coopération. Son dernier Directeur Général, nommé en 2072 par un vote de neuf États sur cent quarante, "
     "signait des décrets avec l'aplomb d'un homme qui gouvernerait encore le monde, jusqu'à la destruction de "
     "Genève.",
     2),
    ("signes_distinctifs",
     "Logo original de l'AMSC — le globe terrestre cerclé de vecteurs de stabilisation bleus — désormais tagué "
     "de croix rouges et de graffitis dans la plupart des capitales régionales. Les agents du BCUC portent encore "
     "l'uniforme gris-acier réglementaire, reconnaissable et souvent perçu comme une provocation dans les zones "
     "de tension. Leurs véhicules arborent des plaques d'immunité diplomatique que la moitié des checkpoints "
     "régionaux refusent désormais d'honorer.",
     "Le logo de l'AMSC — le globe terrestre cerclé de vecteurs de stabilisation bleus — était, dans ses "
     "dernières années, tagué de croix rouges et de graffitis dans la plupart des capitales régionales. Les "
     "agents du BCUC portaient encore l'uniforme gris-acier réglementaire, souvent perçu comme une provocation "
     "dans les zones de tension. Leurs véhicules arboraient des plaques d'immunité diplomatique que la moitié des "
     "checkpoints régionaux refusaient d'honorer.",
     1),
    ("tensions_narratives",
     "La question centrale : qui possède légitimement les archives et les données de monitoring climatique "
     "accumulées depuis soixante-dix ans ? Des blocs régionaux tentent de s'en emparer par la force ou la "
     "corruption, tandis que le BCUC les utilise comme ultime monnaie d'échange pour rester en vie. Une faction "
     "interne milite pour dissoudre l'agence et redistribuer les données en open source — ce qui pourrait "
     "déclencher une guerre de l'information climatique. Enfin, un groupe de directeurs régionaux tente "
     "secrètement de ressusciter l'AMSC sous une forme autoritaire, invoquant l'état d'urgence permanent pour "
     "justifier un pouvoir sans mandat démocratique.",
     "La question centrale : à qui revient ce qu'il reste des archives et des données de monitoring climatique "
     "accumulées par l'agence ? Avant 2076, des blocs régionaux tentaient de s'en emparer par la force ou la "
     "corruption, tandis que le BCUC s'en servait comme ultime monnaie d'échange pour survivre. Une faction "
     "interne militait pour dissoudre l'agence et redistribuer les données en open source ; un groupe de "
     "directeurs régionaux rêvait au contraire de ressusciter l'AMSC sous une forme autoritaire, au nom de "
     "l'état d'urgence permanent. Depuis 2076, l'AMSC n'est plus qu'une référence : nostalgique pour les uns, "
     "repoussoir pour les autres.",
     2),
]

RELATIONS_AVANT = re.compile(r"^\*\*Alliés\*\* : .*\n\*\*Opposants\*\* : .*$", re.MULTILINE)
RELATIONS_APRES = "**Alliés** : aucun\n**Opposants** : aucun"


def motif(texte):
    """Retrouve le texte quels que soient les retours à la ligne et l'indentation
    (blocs YAML `|`)."""
    return re.compile(r"\s+".join(re.escape(m) for m in texte.split()))


def main() -> int:
    apply = "--apply" in sys.argv
    if not CIBLE.exists():
        print(f"✗ Fiche introuvable : {CIBLE}")
        return 1
    texte = CIBLE.read_text(encoding="utf-8")
    if "nommé en 2072" in texte:
        print("✗ Patch déjà appliqué (« nommé en 2072 » présent) — rien fait.")
        return 1

    for champ, ancien, nouveau, attendu in TEXTES:
        m = motif(ancien)
        n = len(m.findall(texte))
        if n != attendu:
            print(f"✗ {champ} : {n} occurrence(s) au lieu de {attendu} — rien écrit.")
            return 1
        texte = m.sub(lambda _m: nouveau, texte)
        print(f"  {champ} : {n} occurrence(s) remplacée(s)")

    n = len(RELATIONS_AVANT.findall(texte))
    if n != 1:
        print(f"✗ Relations du corps : {n} bloc(s) au lieu d'un — rien écrit.")
        return 1
    texte = RELATIONS_AVANT.sub(RELATIONS_APRES, texte)
    print("  corps « ## Relations » : aligné sur le frontmatter (aucun)")

    fm = re.match(r"^---\s*\n(.*?)\n---", texte, re.DOTALL)
    try:
        data = yaml.safe_load(fm.group(1)) if fm else None
    except yaml.YAMLError as e:
        print(f"✗ Le frontmatter ne se lirait plus ({e}) — rien écrit.")
        return 1
    if not isinstance(data, dict) or "2072" not in str(data.get("description_journalistique")):
        print("✗ Frontmatter inattendu après correction — rien écrit.")
        return 1

    if not apply:
        print("\nAperçu seulement — relancer avec --apply pour écrire.")
        return 0
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s27_amsc"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"\n✓ {CIBLE.name} corrigé ; sauvegarde .bak_s27_amsc")
    return 0


if __name__ == "__main__":
    sys.exit(main())

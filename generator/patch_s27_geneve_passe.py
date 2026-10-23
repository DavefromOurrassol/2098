#!/usr/bin/env python3
"""
patch_s27_geneve_passe.py — 23 octobre 2026 (S27.2, restes de Genève).

Deux fiches disparues avec Genève en 2076 (destruction_geneve_2076) étaient
encore écrites au présent : la Tour BCUC (Comptoir des Ruines) et le Résidu de
Genève (Palais des Fantômes). Même principe que patch_s27_amsc_passe.py : rôle,
responsabilités, description journalistique, signes distinctifs et tensions
narratives réécrits au passé, sans nouveau fait sauf la fin en 2076.

L'ancien texte de chaque champ est lu dans le frontmatter de la fiche, puis
remplacé partout où il figure (frontmatter et corps) ; le nombre d'occurrences
est vérifié avant toute écriture, puis le frontmatter est relu.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_geneve_passe.py            # aperçu + avant/après dans
                                                           # documentation/need_action/geneve_fiches_au_passe.md
    python3 generator/patch_s27_geneve_passe.py --apply    # sauvegardes .bak_s27_geneve
"""

import re
import shutil
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
RAPPORT = VAULT / "documentation" / "need_action" / "geneve_fiches_au_passe.md"

# champ -> occurrences attendues (frontmatter + corps ; les signes distinctifs n'ont pas de section)
ATTENDU = {"role_dans_scenario": 2, "responsabilites": 2, "description_journalistique": 2,
           "signes_distinctifs": 1, "tensions_narratives": 2}

FICHES = {
    "tour_bcuc_geneve_breakdown": {
        "role_dans_scenario":
            "Vestige d'une ancienne institution financière internationale basée à Genève, la Tour Bcuc a "
            "fonctionné jusqu'en 2076 comme une structure hybride semi-autonome après l'effondrement des organes "
            "de régulation globaux. Elle tentait de maintenir une forme de coordination économique locale entre "
            "les fragments d'États européens en survie, avec une légitimité contestée et des ressources en déclin. "
            "Ni banque centrale ni tribunal arbitral reconnu, elle occupait un espace interstitiel : celui d'un "
            "intermédiaire dont personne ne voulait pleinement mais que personne n'osait formellement liquider, "
            "car ses archives contractuelles et ses protocoles hérités restaient les seuls référentiels communs "
            "encore partiellement acceptés dans les négociations entre fragments souverains. La destruction de "
            "Genève, en 2076, l'a emportée.",
        "responsabilites":
            "La Tour Bcuc émettait des certificats de reconnaissance de dette inter-fragments, tenait un registre "
            "des accords économiques passés entre anciennes entités étatiques européennes, et proposait une "
            "chambre d'arbitrage informelle pour les litiges commerciaux et énergétiques régionaux. Elle "
            "entretenait également un service de mémoire réglementaire — conservant les textes des traités, normes "
            "et conventions financières pré-effondrement — utilisé comme base de référence par les acteurs qui ne "
            "disposaient plus de leur propre appareil juridique.",
        "description_journalistique":
            "Jusqu'en 2076, au 34e étage de la tour de verre grise qui dominait la rade de Genève, une vingtaine de "
            "techniciens en costume élimé continuaient de saisir des données dans des terminaux dont la moitié "
            "fonctionnaient sur générateurs de secours. Le Comptoir des Ruines — surnom que lui avaient collé les "
            "diplomates de la Ligue Méditerranéenne — émettait ses fameux « certificats Bcuc », ces documents en "
            "papier pelure sécurisé que les fragments d'États acceptaient comme base de négociation faute de "
            "mieux. Mais l'autorité de la Tour était celle d'un arbitre dont tout le monde connaissait les "
            "limites : ses décisions n'étaient appliquées que si les deux parties y avaient intérêt, et ses "
            "archives, bien que précieuses, étaient convoitées par des acteurs qui préféraient les posséder plutôt "
            "que de les voir neutraliser. Entre deux délestages électriques, ses agents parcouraient les couloirs "
            "en tenant à bout de bras la mémoire contractuelle d'un monde qui n'existait plus — jusqu'à ce que la "
            "destruction de Genève emporte la tour.",
        "signes_distinctifs":
            "La tour avait conservé son logo d'origine — un double cercle entrelacé en bleu acier — peint à la "
            "main, dans ses dernières années, sur les documents officiels faute d'encre d'imprimante "
            "standardisée. Les agents portaient un brassard blanc frappé du sigle « BCUC/GE » en lettres noires, "
            "signe de neutralité revendiquée que certaines milices respectaient encore par réflexe institutionnel. "
            "Les couloirs dégageaient une odeur caractéristique d'archives papier humides et de diesel froid.",
        "tensions_narratives":
            "La Tour reposait sur un paradoxe existentiel : plus elle mobilisait ses archives pour arbitrer des "
            "conflits, plus elle révélait l'étendue de ses anciennes compromissions avec des entités disparues ou "
            "ennemies, sapant la neutralité qu'elle revendiquait. Certains fragments d'États membres la "
            "soupçonnaient de favoriser secrètement les grandes enclaves corporatives qui la finançaient "
            "discrètement, ce qui alimentait les fronts populistes réclamant sa dissolution. En parallèle, des "
            "réseaux comme les Archives Neutres de Genève ou Mnemos Pannonie cherchaient à absorber ses fonds "
            "documentaires, rendant sa survie conditionnelle à sa capacité à rester irremplaçable — un pari "
            "auquel la destruction de Genève, en 2076, a mis fin.",
    },
    "geneve_bunker_institutions_breakdown": {
        "role_dans_scenario":
            "Vestige institutionnel de l'ancien système onusien et diplomatique genevois, le Résidu de Genève a "
            "survécu jusqu'en 2076 dans un état fragmenté après l'effondrement des structures internationales. "
            "Réduit à gérer la survie locale et la coordination minimale entre communautés isolées, il tentait de "
            "préserver une légitimité symbolique sans véritable pouvoir coercitif. Ses représentants négociaient "
            "au cas par cas avec les entités locales dominantes — milices, corporations, seigneuries logistiques — "
            "pour maintenir une forme d'ordre résiduel. Il n'était plus le gardien d'un droit international mais "
            "un intermédiaire de dernière instance, reconnu moins pour son autorité que pour sa neutralité "
            "relative et sa mémoire des procédures, jusqu'à la destruction de Genève en 2076.",
        "responsabilites":
            "Coordonnait a minima les flux humanitaires entre communautés isolées de l'arc lémanique et alpin. "
            "Négociait des trêves et des accords de passage ponctuels entre entités locales armées. Gérait les "
            "archives diplomatiques résiduelles et maintenait un espace de médiation symbolique dans l'enceinte "
            "du Palais des Nations partiellement occupé, jusqu'en 2076.",
        "description_journalistique":
            "Jusqu'en 2076, dans l'aile est du Palais des Nations, là où des délégations de cent "
            "quatre-vingt-dix-trois États venaient autrefois siéger sous les fresques allégoriques, une "
            "cinquantaine de fonctionnaires rescapés géraient des stocks de rations médicales et des carnets "
            "d'adresses de chefs de milice. Le drapeau à l'olivier tenait encore sur sa hampe rouillée. On le "
            "laissait là — non par respect, mais parce que personne ne voulait prendre la responsabilité de "
            "l'abaisser. Les négociateurs du Résidu de Genève se déplaçaient à pied ou en véhicule à traction "
            "animale entre les enclaves du bassin lémanique, porteurs non de mandats mais de mémoires : ils "
            "savaient qui avait signé quoi, qui devait quoi à qui, quelle procédure avait jadis fonctionné. "
            "C'est cette mémoire procédurale — pas le droit international — qui leur valait encore une chaise à "
            "la table, jusqu'à la destruction de Genève.",
        "signes_distinctifs":
            "Badges onusiens décolorés portés sur des vestes civiles rapiécées. Documents tamponnés d'un sceau "
            "bleu dont l'encre s'effaçait — les interlocuteurs les acceptaient par habitude autant que par "
            "conviction. Locaux marqués d'une ligne bleue peinte à même le sol, délimitant une zone de neutralité "
            "tacite reconnue par la plupart des factions armées locales.",
        "tensions_narratives":
            "Le Résidu de Genève oscillait en permanence entre deux abîmes : se soumettre davantage aux logiques "
            "locales pour rester utile, au risque de ne plus être distinguable d'un simple intermédiaire "
            "mercenaire ; ou s'accrocher à une posture symbolique qui l'isolait et le rendait inopérant. Certains "
            "de ses fonctionnaires militaient pour une alliance formelle avec les Archives Neutres afin de créer "
            "un pôle de mémoire institutionnelle à valeur contraignante ; d'autres craignaient que cette fusion ne "
            "les dévoie définitivement vers l'archivage plutôt que vers l'action. La destruction de Genève, en "
            "2076, a laissé sans réponse la question qu'il posait : qui, dans ce monde fracturé, a encore besoin "
            "d'une légitimité qui ne s'appuie sur aucune force ?",
    },
}


def motif(texte):
    return re.compile(r"\s+".join(re.escape(m) for m in str(texte).split()))


def frontmatter(texte):
    m = re.match(r"^---\s*\n(.*?)\n---", texte, re.DOTALL)
    return yaml.safe_load(m.group(1)) if m else None


def preparer(slug, nouveaux):
    path = VAULT / "instances" / f"{slug}.md"
    if not path.exists():
        raise SystemExit(f"✗ Fiche introuvable : {path}")
    texte = path.read_text(encoding="utf-8")
    fm = frontmatter(texte) or {}
    if " ".join(str(fm.get("description_journalistique") or "").split()).startswith("Jusqu'en 2076"):
        raise SystemExit(f"✗ {slug} : déjà au passé (patch appliqué ?) — rien fait.")
    avant_apres = []
    for champ, nouveau in nouveaux.items():
        ancien = " ".join(str(fm.get(champ) or "").split())
        if not ancien:
            raise SystemExit(f"✗ {slug} : champ {champ} vide — rien écrit.")
        m = motif(ancien)
        n = len(m.findall(texte))
        if n != ATTENDU[champ]:
            raise SystemExit(f"✗ {slug} : {champ}, {n} occurrence(s) au lieu de {ATTENDU[champ]} — rien écrit.")
        texte = m.sub(lambda _m: nouveau, texte)
        avant_apres.append((champ, ancien, nouveau, n))
    try:
        apres = frontmatter(texte)
    except yaml.YAMLError as e:
        raise SystemExit(f"✗ {slug} : le frontmatter ne se lirait plus ({e}) — rien écrit.")
    if not isinstance(apres, dict) or not str(apres.get("description_journalistique")).startswith("Jusqu'en 2076"):
        raise SystemExit(f"✗ {slug} : frontmatter inattendu après correction — rien écrit.")
    return path, texte, fm.get("name") or slug, avant_apres


def main() -> int:
    apply = "--apply" in sys.argv
    prets = [preparer(slug, nouveaux) for slug, nouveaux in FICHES.items()]
    lignes = ["# Fiches de Genève au passé — avant / après (patch_s27_geneve_passe.py)", ""]
    for path, _, nom, avant_apres in prets:
        print(f"{path.name} ({nom})")
        lignes += [f"## {nom}", ""]
        for champ, ancien, nouveau, n in avant_apres:
            print(f"  {champ} : {n} occurrence(s)")
            lignes += [f"### {champ}", "", f"**Avant** : {ancien}", "", f"**Après** : {nouveau}", ""]
    if not apply:
        RAPPORT.parent.mkdir(parents=True, exist_ok=True)
        RAPPORT.write_text("\n".join(lignes), encoding="utf-8")
        print(f"\nAperçu : rien écrit dans les fiches. Avant / après : {RAPPORT.relative_to(VAULT)}")
        print("Relancer avec --apply pour écrire.")
        return 0
    for path, texte, _, _ in prets:
        shutil.copy2(path, path.with_name(path.name + ".bak_s27_geneve"))
        path.write_text(texte, encoding="utf-8")
    print(f"\n✓ {len(prets)} fiches corrigées ; sauvegardes .bak_s27_geneve")
    return 0


if __name__ == "__main__":
    sys.exit(main())

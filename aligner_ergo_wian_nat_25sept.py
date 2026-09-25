#!/usr/bin/env python3
"""
Script ponctuel S15.1 (25 sept 2026) — aligner Ergo-Wian et la NAT
(fortress_world) sur le lore Hyphan : Ergo-Wian gouverne Euro-Nord
(Espace Nordique et Arctique), la NAT est sa filiale armée — fait connu
de tous en 2098.

Retouche CIBLÉE (pas de régénération) de 2 instances :
  - instances/ergo_wian_sovereign_holdings_fortress_world.md
      localisation -> espace_nordique_arctique ; rôle, responsabilités,
      description journalistique (BlackRock -> "ancien gérant de fonds du
      XXIe siècle") ; alliés + NAT + Contrats de service
  - instances/armada_logistique_nordique_fortress_world.md
      rôle, responsabilités, description journalistique, tensions ;
      alliés + Ergo-Wian + Contrats de service

Chaque texte est remplacé à l'identique dans le frontmatter ET dans le corps
markdown. Tout remplacement doit trouver exactement le nombre d'occurrences
attendu, sinon rien n'est écrit. Frontmatter relu par yaml.safe_load après
modification, avant écriture. .bak de chaque fichier.

Usage (depuis la racine du vault) :
  python3 aligner_ergo_wian_nat_25sept.py            # aperçu
  python3 aligner_ergo_wian_nat_25sept.py --execute  # écriture
"""
import re
import shutil
import sys
from pathlib import Path

import yaml

EW = "instances/ergo_wian_sovereign_holdings_fortress_world.md"
NAT = "instances/armada_logistique_nordique_fortress_world.md"

# ─────────────────────────── Ergo-Wian ───────────────────────────────────
EW_ROLE_OLD = (
    "Ergo-Wian Sovereign Dominion incarne l'aboutissement extrême de la fusion entre "
    "souveraineté territoriale et logique corporative dans le scénario *fortress_world*. "
    "Opérant comme un conglomérat militaro-industriel et gouvernemental, l'EWSD gère des "
    "zones entières sous un régime d'apartheid corporate, où les populations sont classées "
    "en catégories de productivité et soumises à des migrations forcées vers des zones de "
    "labeur optimisées. Son modèle repose sur une gouvernance algorithmique qui élimine toute "
    "distinction entre État et marché, transformant les territoires en actifs financiers et "
    "les citoyens en contractants sous surveillance permanente."
)
EW_ROLE_NEW = (
    "Gouvernement-entreprise d'Euro-Nord — l'Espace Nordique et Arctique —, l'Ergo-Wian "
    "Sovereign Dominion y détient les pleins pouvoirs : aucune élection, un conseil des "
    "actionnaires en guise de parlement, et une filiale armée, la Nordisk Arktisk "
    "Transitkontroll (NAT), qui tient les frontières et les corridors arctiques. Opérant comme "
    "un conglomérat militaro-industriel et gouvernemental, l'EWSD administre son territoire "
    "sous un régime d'apartheid corporate, où les populations sont classées en catégories de "
    "productivité et soumises à des migrations forcées vers des zones de labeur optimisées. "
    "Pour compenser le déclin démographique d'Euro-Nord, il importe une main-d'œuvre captive "
    "depuis le Hors par ses contrats de service. Son modèle repose sur une gouvernance "
    "algorithmique qui élimine toute distinction entre État et marché, transformant les "
    "territoires en actifs financiers et les citoyens en contractants sous surveillance "
    "permanente."
)

EW_RESP_OLD = (
    "L'EWSD contrôle des corridors logistiques stratégiques, des zones minières militarisées "
    "et des infrastructures critiques (énergie, eau, données) au sein des blocs forteresses."
)
EW_RESP_NEW = (
    "Depuis Euro-Nord, l'EWSD contrôle les corridors arctiques par sa filiale armée, la NAT, "
    "ainsi que des zones minières militarisées et des infrastructures critiques (énergie, eau, "
    "données), chez lui comme dans d'autres blocs forteresses où il opère par contrats de "
    "gérance."
)

EW_JOUR_OLD_1 = "Dans les zones contrôlées par l'Ergo-Wian Sovereign Dominion, les villes"
EW_JOUR_NEW_1 = ("À Euro-Nord comme dans les zones que l'Ergo-Wian Sovereign Dominion gère "
                 "par contrat, les villes")
EW_JOUR_OLD_2 = "son PDG, un ancien cadre de BlackRock reconverti en seigneur territorial"
EW_JOUR_NEW_2 = ("son souverain-gérant, un ancien gérant de fonds du XXIe siècle reconverti "
                 "en seigneur territorial")

EW_LOC_OLD = """localisation:
  zone: null
  lieu: null
  type_lieu: null
  note: transnationale_sans_ancrage
"""
EW_LOC_NEW = """localisation:
  zone: espace_nordique_arctique
  lieu: Euro-Nord (Espace Nordique et Arctique)
  type_lieu: site_strategique
"""

EW_ALLI_OLD = "    - commandement_strategique_des_matieres_critiques_atlantique_fortress_world\n"
EW_ALLI_NEW = (EW_ALLI_OLD
               + "    - armada_logistique_nordique_fortress_world\n"
               + "    - contrats_de_service_d_ergo_wian_fortress_world\n")
EW_BODY_ALLI_OLD = "[[commandement_strategique_des_matieres_critiques_atlantique_fortress_world]]\n"
EW_BODY_ALLI_NEW = ("[[commandement_strategique_des_matieres_critiques_atlantique_fortress_world]], "
                    "[[armada_logistique_nordique_fortress_world]], "
                    "[[contrats_de_service_d_ergo_wian_fortress_world]]\n")

# ─────────────────────────── NAT ─────────────────────────────────────────
NAT_ROLE_OLD = (
    "Dans un monde Fortress World fracturé, la NAT est devenue l'une des rares entités à "
    "opérer légitimement aux frontières entre blocs hermétiques, en contrôlant les corridors "
    "arctiques déglaciés comme autant de détroits stratégiques. Elle n'est plus seulement une "
    "entreprise logistique : c'est une puissance de transit armée, mi-État mi-cartel, dont la "
    "neutralité affichée masque une capacité réelle à asphyxier ou ravitailler un bloc entier. "
    "Son pouvoir repose sur l'irremplaçabilité — dans un monde où les routes maritimes "
    "méridionales sont militarisées ou sabotées, les voies arctiques qu'elle opère sont "
    "devenues des artères vitales. Elle impose sa propre loi sur les eaux, les plateformes "
    "flottantes et les nœuds terrestres du Grand Nord."
)
NAT_ROLE_NEW = (
    "Filiale armée d'Ergo-Wian Sovereign Dominion, le gouvernement-entreprise qui règne sur "
    "Euro-Nord (Espace Nordique et Arctique), la NAT en est le bras opérationnel : elle tient "
    "les frontières du territoire et contrôle les corridors arctiques déglaciés comme autant "
    "de détroits stratégiques. Nul n'ignore en 2098 qui la possède, et c'est précisément ce "
    "qui fait sa force : chaque licence de transit, chaque convoi de brise-glaces sert d'abord "
    "les intérêts d'Ergo-Wian, qui peut asphyxier ou ravitailler un bloc entier d'une décision "
    "de son conseil des actionnaires. Son pouvoir repose sur l'irremplaçabilité — dans un monde "
    "où les routes maritimes méridionales sont militarisées ou sabotées, les voies arctiques "
    "qu'elle opère sont devenues des artères vitales. Sur les eaux, les plateformes flottantes "
    "et les nœuds terrestres du Grand Nord, la loi de la NAT est celle d'Ergo-Wian."
)

NAT_RESP_OLD = ("Elle négocie directement avec les autorités des blocs-forteresses, contournant "
                "toute gouvernance internationale résiduelle.")
NAT_RESP_NEW = ("Elle négocie directement avec les autorités des blocs-forteresses au nom "
                "d'Ergo-Wian, contournant toute gouvernance internationale résiduelle, et "
                "assure la sécurité armée d'Euro-Nord (frontières, côtes, installations "
                "critiques).")

NAT_JOUR_OLD = ("Les journalistes qui ont tenté d'enquêter sur ses marges tarifaires ou ses "
                "accords secrets avec tel ou tel bloc sont revenus avec peu de réponses.")
NAT_JOUR_NEW = ("Filiale armée d'Ergo-Wian, elle ne s'en cache pas : ses tarifs se décident à "
                "Euro-Nord, en conseil des actionnaires. Les journalistes qui ont tenté "
                "d'enquêter sur ses marges ou ses accords avec tel ou tel bloc sont revenus "
                "avec peu de réponses.")

NAT_TENS_OLD = (
    "La NAT se dit neutre, mais plusieurs blocs l'accusent de favoriser ses alliés "
    "scandinaves dans les priorités de transit, précipitant des crises d'approvisionnement en "
    "chaîne. En interne, une faction technocratique pousse à automatiser intégralement les "
    "négociations via IA, ce qui déposséderait les diplomates humains de leur rôle — et "
    "mettrait fin à la corruption qui fait vivre nombre de fonctionnaires nordiques. La "
    "question qui hante les chancelleries : si la NAT coupe les corridors arctiques à un bloc "
    "en crise, est-ce un acte commercial ou un acte de guerre ?"
)
NAT_TENS_NEW = (
    "Les blocs dépendent d'une route commerciale possédée par un gouvernement-entreprise qui "
    "ne rend de comptes à personne : chaque priorité de transit ou hausse tarifaire décidée "
    "par Ergo-Wian peut précipiter des crises d'approvisionnement en chaîne. En interne, une "
    "faction technocratique pousse à automatiser intégralement les négociations via IA, ce qui "
    "déposséderait les diplomates humains de leur rôle — et mettrait fin à la corruption qui "
    "fait vivre nombre d'agents de liaison nordiques. La question qui hante les chancelleries : "
    "si Ergo-Wian fait couper les corridors arctiques à un bloc en crise, est-ce un acte "
    "commercial ou un acte de guerre ?"
)

NAT_ALLI_OLD = "- kalaallit_nunaat_sovereign_fund_fortress_world\noppositions:\n"
NAT_ALLI_NEW = ("- kalaallit_nunaat_sovereign_fund_fortress_world\n"
                "- ergo_wian_sovereign_holdings_fortress_world\n"
                "- contrats_de_service_d_ergo_wian_fortress_world\n"
                "oppositions:\n")
NAT_BODY_ALLI_OLD = "- [[kalaallit_nunaat_sovereign_fund_fortress_world]]\n**Opposants :**"
NAT_BODY_ALLI_NEW = ("- [[kalaallit_nunaat_sovereign_fund_fortress_world]]\n"
                     "- [[ergo_wian_sovereign_holdings_fortress_world]]\n"
                     "- [[contrats_de_service_d_ergo_wian_fortress_world]]\n"
                     "**Opposants :**")

# (libellé, ancien, nouveau, occurrences attendues : 2 = frontmatter + corps)
PLAN = {
    EW: [
        ("localisation", EW_LOC_OLD, EW_LOC_NEW, 1),
        ("rôle", EW_ROLE_OLD, EW_ROLE_NEW, 2),
        ("responsabilités", EW_RESP_OLD, EW_RESP_NEW, 2),
        ("description (ouverture)", EW_JOUR_OLD_1, EW_JOUR_NEW_1, 2),
        ("description (BlackRock)", EW_JOUR_OLD_2, EW_JOUR_NEW_2, 2),
        ("alliés (frontmatter)", EW_ALLI_OLD, EW_ALLI_NEW, 1),
        ("alliés (corps)", EW_BODY_ALLI_OLD, EW_BODY_ALLI_NEW, 1),
    ],
    NAT: [
        ("rôle", NAT_ROLE_OLD, NAT_ROLE_NEW, 2),
        ("responsabilités", NAT_RESP_OLD, NAT_RESP_NEW, 2),
        ("description journalistique", NAT_JOUR_OLD, NAT_JOUR_NEW, 2),
        ("tensions narratives", NAT_TENS_OLD, NAT_TENS_NEW, 2),
        ("alliés (frontmatter)", NAT_ALLI_OLD, NAT_ALLI_NEW, 1),
        ("alliés (corps)", NAT_BODY_ALLI_OLD, NAT_BODY_ALLI_NEW, 1),
    ],
}

CONTROLES = {
    EW: lambda fm: (fm["localisation"]["zone"] == "espace_nordique_arctique"
                    and "note" not in fm["localisation"]
                    and "armada_logistique_nordique_fortress_world" in fm["alliances"]
                    and "BlackRock" not in fm["description_journalistique"]
                    and "Euro-Nord" in fm["role_dans_scenario"]),
    NAT: lambda fm: ("ergo_wian_sovereign_holdings_fortress_world" in fm["alliances"]
                     and "Ergo-Wian" in fm["role_dans_scenario"]
                     and "Ergo-Wian" in fm["tensions_narratives"]),
}


def frontmatter(texte):
    m = re.match(r"^---\n(.*?)\n---", texte, re.S)
    if not m:
        raise ValueError("frontmatter introuvable")
    return yaml.safe_load(m.group(1))


def main():
    execute = "--execute" in sys.argv
    print(f"Mode : {'ÉCRITURE' if execute else 'APERÇU (rien écrit)'}\n")
    nouveaux, erreurs = {}, 0
    for chemin, etapes in PLAN.items():
        p = Path(chemin)
        print(f"== {chemin}")
        if not p.exists():
            print("  ✗ fichier introuvable (lance depuis la racine du vault)")
            erreurs += 1
            continue
        src = p.read_text(encoding="utf-8")
        txt = src
        for label, old, new, attendu in etapes:
            if new in txt:
                print(f"  · {label} : déjà appliqué")
                continue
            n = txt.count(old)
            if n != attendu:
                print(f"  ✗ {label} : {n} occurrence(s), attendu {attendu}")
                erreurs += 1
                continue
            txt = txt.replace(old, new)
            print(f"  ✓ {label} ({n}×)")
        try:
            fm = frontmatter(txt)
            ok = CONTROLES[chemin](fm)
            print(f"  {'✓' if ok else '✗'} frontmatter YAML valide, contrôles de contenu "
                  f"{'OK' if ok else 'KO'}")
            erreurs += 0 if ok else 1
        except Exception as e:
            print(f"  ✗ frontmatter invalide après modification : {e}")
            erreurs += 1
        if txt != src:
            nouveaux[p] = txt
    if erreurs:
        print(f"\n{erreurs} anomalie(s) — rien écrit. Envoie cette sortie à Claude.")
        sys.exit(1)
    if not nouveaux:
        print("\nRien à faire : déjà aligné.")
        return
    if not execute:
        print(f"\n{len(nouveaux)} fichier(s) prêts. Relance avec --execute pour écrire.")
        return
    for p, txt in nouveaux.items():
        shutil.copy2(p, p.with_suffix(p.suffix + ".bak"))
        p.write_text(txt, encoding="utf-8")
        print(f"  écrit : {p} (+ .bak)")


if __name__ == "__main__":
    main()

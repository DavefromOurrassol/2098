#!/usr/bin/env python3
"""
patch_s27_murmansk_passe.py — 24 octobre 2026 (S27, point 6).

Murmansk Transit Arctique (reference) a disparu en 2081 avec l'explosion du
Polaris-7 (explosion_brise_glace_murmansk_2081, appliquée par la phase 4 le
17 oct), mais sa fiche était encore écrite au présent : la phase 4 change la
trajectoire, pas le texte. Même traitement que patch_s27_geneve_passe.py : rôle,
responsabilités, description journalistique, signes distinctifs et tensions
narratives au passé ; seuls faits ajoutés, ceux de l'hypothèse (fin en 2081,
Mourmansk survit déclinante, trafic repris par l'Armada de Tromsø).

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_murmansk_passe.py            # aperçu + avant/après dans
                                                             # documentation/need_action/murmansk_fiche_au_passe.md
    python3 generator/patch_s27_murmansk_passe.py --apply    # sauvegarde .bak_s27_murmansk
"""

import re
import shutil
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent
RAPPORT = VAULT / "documentation" / "need_action" / "murmansk_fiche_au_passe.md"

# champ -> occurrences attendues (frontmatter + corps ; les signes distinctifs n'ont pas de section)
ATTENDU = {"role_dans_scenario": 2, "responsabilites": 2, "description_journalistique": 2,
           "signes_distinctifs": 1, "tensions_narratives": 2}

FICHES = {
    "murmansk_transit_arctique_reference": {
        "role_dans_scenario":
            "Plaque tournante stratégique du trafic maritime et énergétique arctique, Murmansk Transit Arctique "
            "s'était imposée comme nœud incontournable des nouvelles routes commerciales ouvertes par la fonte "
            "accélérée des glaces polaires depuis les années 2040. Le territoire était administré par un "
            "consortium russo-scandinave fragile — le Pacte de Kola — soumis aux pressions concurrentes des "
            "puissances cherchant à contrôler le passage du Nord-Est. Sa position géopolitique unique en faisait "
            "un terrain de négociations permanentes et de tensions sourdes entre acteurs étatiques et corporatifs, "
            "rendant toute gouvernance stable structurellement impossible : sa valeur même le condamnait à "
            "l'instabilité chronique. L'explosion du brise-glace Polaris-7, en décembre 2081, a mis fin à son "
            "existence ; la ville de Mourmansk lui a survécu, déclinante et en partie évacuée.",
        "responsabilites":
            "Jusqu'en 2081 : coordination et taxation du transit maritime sur la route du Nord-Est, gestion des "
            "infrastructures portuaires et énergétiques de Mourmansk, arbitrage quotidien des droits de passage "
            "entre opérateurs concurrents, et maintien d'un équilibre minimal entre les souverainetés "
            "russo-scandinave, les intérêts corporatifs et les revendications autochtones.",
        "description_journalistique":
            "Jusqu'en 2081, à Mourmansk, les grues ne s'arrêtaient jamais. Chaque semaine, des centaines de "
            "convois maritimes transitaient par ce port reconfiguré à la hâte en capitale logistique de l'Arctique "
            "dégelé. Dans les salles de réunion du Pacte de Kola, diplomates scandinaves et représentants de la "
            "Fédération Russe du Nord négociaient au centimètre les droits de passage pendant que des lobbyistes "
            "corporatifs faisaient la queue dans les couloirs. La ville elle-même était devenue un microcosme de "
            "la multipolarité mondiale : enseignes en douze langues, milices privées postées aux quais, et une "
            "classe administrative locale qui apprenait chaque matin si l'accord de la veille tenait encore — "
            "jusqu'à l'explosion du Polaris-7, après laquelle l'essentiel du trafic arctique est passé à "
            "l'Armada Logistique Nordique de Tromsø.",
        "signes_distinctifs":
            "Le logo officiel du consortium représentait une boussole dont l'aiguille pointait vers le "
            "nord-ouest — compromis symbolique entre Moscou et Oslo jamais vraiment assumé. Les infrastructures "
            "portuaires arboraient simultanément les couleurs des États membres et les identités visuelles des "
            "grands opérateurs logistiques privés. La langue de travail officielle était un créole administratif "
            "russo-norvégien surnommé localement « le kola ».",
        "tensions_narratives":
            "La montée en puissance du Consortium Logistique Asiatique de Contournement ALN, qui finançait "
            "activement des routes alternatives via le détroit de Béring, fragilisait la rente de position de "
            "Mourmansk et accentuait les divisions internes du Pacte de Kola. Parallèlement, les collectifs Inuit "
            "et Sami intensifiaient leurs revendications sur les zones côtières transformées en zones "
            "industrielles sans consultation. La question que posait le consortium — jusqu'à quand tenir face à "
            "une puissance asiatique qui préférait payer pour contourner plutôt que pour traverser ? — a été "
            "tranchée autrement, par l'explosion du Polaris-7 en 2081.",
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
    if " ".join(str(fm.get("description_journalistique") or "").split()).startswith("Jusqu'en 2081"):
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
    if not isinstance(apres, dict) or not str(apres.get("description_journalistique")).startswith("Jusqu'en 2081"):
        raise SystemExit(f"✗ {slug} : frontmatter inattendu après correction — rien écrit.")
    return path, texte, fm.get("name") or slug, avant_apres


def main() -> int:
    apply = "--apply" in sys.argv
    prets = [preparer(slug, nouveaux) for slug, nouveaux in FICHES.items()]
    lignes = ["# Fiche de Mourmansk au passé — avant / après (patch_s27_murmansk_passe.py)", ""]
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
        shutil.copy2(path, path.with_name(path.name + ".bak_s27_murmansk"))
        path.write_text(texte, encoding="utf-8")
    print(f"\n✓ {len(prets)} fiche(s) corrigée(s) ; sauvegardes .bak_s27_murmansk")
    return 0


if __name__ == "__main__":
    sys.exit(main())

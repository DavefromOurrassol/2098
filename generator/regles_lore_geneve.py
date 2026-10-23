#!/usr/bin/env python3
"""
regles_lore_geneve.py — 23 octobre 2026 (S27.2, restes de Genève).

Ajoute à documentation/lore_regles.yaml, section breakdown, une règle par
fiche disparue avec Genève en 2076 (destruction_geneve_2076, appliquée à la
main le 13 octobre, donc sans étape ⑤). Même contrôle et même insertion que
l'étape ⑤ (et_si_main.verifier_regles / inserer_regles) : les commentaires du
fichier sont gardés, les autres sections relues à l'identique.

Usage (depuis la racine du vault) :
    python3 generator/regles_lore_geneve.py            # aperçu, rien n'est écrit
    python3 generator/regles_lore_geneve.py --apply    # sauvegarde lore_regles.yaml.bak_geneve
"""

import shutil
import sys
from pathlib import Path

import yaml

GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
import et_si_main as m  # noqa: E402

SC = "breakdown"
MESSAGE = ("{nom} disparaît en 2076 avec la destruction de Genève (destruction_geneve_2076) : "
           "toute mention au présent après 2076 est fausse.")
REGLES = [
    {"id": "agence_stabilisation_climatique_disparu_2076", "gravite": "a_relire",
     "termes": ["Résidu AMSC", "Bureau de Coordination d'Urgence Climatique"],
     "message": MESSAGE.format(nom="Le Bureau de Coordination d'Urgence Climatique (Résidu AMSC)")},
    {"id": "geneve_bunker_institutions_disparu_2076", "gravite": "a_relire",
     "termes": ["Palais des Fantômes"],
     "message": MESSAGE.format(nom="Le Résidu de Genève — Le Palais des Fantômes")},
    {"id": "tour_bcuc_geneve_disparu_2076", "gravite": "a_relire",
     "termes": ["Tour BCUC", "Tour Bcuc", "Comptoir des Ruines"],
     "message": MESSAGE.format(nom="La Tour BCUC — Le Comptoir des Ruines")},
]


def main() -> int:
    apply = "--apply" in sys.argv
    lore = m.LORE
    if not lore.exists():
        print(f"✗ {lore} introuvable")
        return 1
    contenu = lore.read_text(encoding="utf-8")
    avant = yaml.safe_load(contenu) or {}
    texte = yaml.safe_dump(REGLES, allow_unicode=True, sort_keys=False, width=1000)
    regles, err = m.verifier_regles(texte, set(m.ids_existants(contenu)))
    print(("ÉCRITURE" if apply else "APERÇU (rien écrit)") + f" — règles de lore, section {SC}\n")
    if err:
        print("✗ Refusé :\n" + "\n".join(f"  - {e}" for e in err))
        return 1
    nouveau = m.inserer_regles(contenu, SC, regles)
    try:
        apres = yaml.safe_load(nouveau) or {}
    except yaml.YAMLError as e:
        print(f"✗ le fichier ne serait plus lisible ({e}) : rien écrit.")
        return 1
    ids_sc = [str(r.get("id")) for r in ((apres.get(SC) or {}).get("regles") or [])]
    autres_ok = all(apres.get(k) == v for k, v in avant.items() if k != SC)
    if not all(r["id"] in ids_sc for r in regles) or not autres_ok:
        print("✗ contrôle après insertion en échec : rien écrit.")
        return 1
    for r in regles:
        print(f"  + {r['id']} : {r['termes']}")
    if not apply:
        print("\nRelancer avec --apply pour écrire.")
        return 0
    shutil.copy2(lore, lore.with_name("lore_regles.yaml.bak_geneve"))
    lore.write_text(nouveau, encoding="utf-8")
    print(f"\n✓ {len(regles)} règles ajoutées (sauvegarde lore_regles.yaml.bak_geneve).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

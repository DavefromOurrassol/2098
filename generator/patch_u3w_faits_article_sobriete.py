#!/usr/bin/env python3
"""
patch_u3w_faits_article_sobriete.py — Ourrassol 2098 (U3w, 11 novembre 2026)
============================================================================
Suite de U3s / U3t. Test réel des arrestations des Grottes : la fiche omettait la libération
(pétition de 120 000 Genevois) pourtant dans la phrase de l'article imposée comme fait, parlait de
« débat » (inventé) et nommait le scénario dans la description.

Modifie generator/inject_custom_events.py (5 modifications). Exige U3s et U3t appliqués.
  1. CONTRÔLE DES FAITS : un fait imposé qui est une phrase de l'article d'origine (trouvée par
     U3s) est marqué [ARTICLE] dans la liste soumise à l'IA de contrôle, avec la règle : le récit
     doit en reprendre les éléments essentiels (qui, quoi, quand, issue) ; une omission ou un
     changement de sens = NON respecté (donc une réécriture, comme pour les autres faits). Même
     appel IA qu'avant, aucun coût en plus.
  2. CONSIGNE (quand un passage d'article est fourni) : ne jamais écrire le nom d'un scénario dans
     la description ni les conséquences ; conséquences limitées à des tensions ou tendances que le
     passage permet de déduire (aucun débat, aucune réaction d'autorité ou de médias, aucun
     chiffre absent du passage).
  3. AVERTISSEMENT mécanique : « ⚠ [scénario] le nom du scénario « … » apparaît dans … » si un nom
     de scénario figure dans la description ou les conséquences (la réalisation est exclue : elle
     s'ouvre légitimement par « Dans <scénario>, »).
Sans passage d'article, rien ne change.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3w_faits_article_sobriete.py            # dry-run
  python3 generator/patch_u3w_faits_article_sobriete.py --apply    # applique (.bak_u3w)
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "inject_custom_events.py"
TAG = "u3w"

# H1 : fonctions d'aide
H1_A = "def _citations_absentes_u3t(instance_data, scenario):\n"
H1_N = '''def _fait_de_article_u3w(fait, scenario):
    """U3w : le fait imposé est-il une phrase (8 mots au moins) de l'article d'origine ?"""
    article = _DERNIER_ARTICLE_U3S.get(scenario)
    if not article:
        return False
    n = _norm_ctx_u3s(fait)
    return len(n.split()) >= 8 and n in _norm_ctx_u3s(article)


def _noms_scenario_u3w(instance_data):
    """U3w : [(champ, scénario)] pour chaque nom de scénario écrit dans la description ou les
    conséquences (la réalisation est exclue)."""
    out = []
    for k in ("description_complete", "consequences"):
        t = str(instance_data.get(k) or "")
        for s in SCENARIOS:
            if re.search(r"(?<![a-z_])" + re.escape(s) + r"(?![a-z_])", t):
                out.append((k, s))
    return out


''' + H1_A

# H2 : règle dans le prompt de contrôle
H2_A = ("- Respecté : le récit le confirme, ou n'en parle pas — sauf si le fait est le sujet même de\n"
        "  l'événement : il doit alors y figurer.\n")
H2_N = H2_A + ("- Un fait marqué [ARTICLE] vient de l'article d'origine : le récit doit en reprendre les éléments\n"
               "  essentiels (qui, quoi, quand, issue : libération, démenti, bilan…) ; l'omission d'un de ces\n"
               "  éléments, ou une version qui en change le sens, = NON respecté.\n")

# H3 : marquage des faits de l'article dans la liste
H3_A = "    liste = \"\\n\".join(f\"{i}. {f['fait']}\" for i, f in enumerate(faits, 1))\n"
H3_N = ("    liste = \"\\n\".join(f\"{i}. \" + (\"[ARTICLE] \" if _fait_de_article_u3w(f['fait'], scenario) else \"\")\n"
        "                      + f['fait'] for i, f in enumerate(faits, 1))   # U3w\n")

# H4 : consigne de génération
H4_A = ("    else:\n"
        "        desc_consigne_txt = \"description journalistique de l'événement — 3-4 lignes vivantes\"\n")
H4_N = ('''        contexte_txt += ("N'écris jamais le nom d'un scénario (ex. « new_sustainability ») dans la description "
                         "ni dans les conséquences. Les conséquences se limitent à des tensions ou des tendances que "
                         "le passage permet de déduire : aucun débat, aucune réaction d'autorité ou de médias, aucun "
                         "chiffre qui n'est pas dans le passage.\\n")   # U3w
''' + H4_A)

# H5 : avertissement mécanique
H5_A = ("            for q in _citations_absentes_u3t(instance_data, scenario):   # U3t\n"
        "                print(f\"  ⚠ [{scenario}] citation absente de l'article : « {q} »\")\n")
H5_N = H5_A + ('''            for champ, nom_sc in _noms_scenario_u3w(instance_data):   # U3w
                print(f"  ⚠ [{scenario}] le nom du scénario « {nom_sc} » apparaît dans {champ} : à retoucher")
''')

REMPLACEMENTS = [("aide", H1_A, H1_N), ("règle de contrôle", H2_A, H2_N), ("liste des faits", H3_A, H3_N),
                 ("consigne", H4_A, H4_N), ("avertissement", H5_A, H5_N)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")
    if "_fait_de_article_u3w" in src:
        print("= déjà appliqué, rien à faire")
        return
    if "_citations_absentes_u3t" not in src:
        sys.exit("✗ U3s / U3t ne sont pas appliqués")
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

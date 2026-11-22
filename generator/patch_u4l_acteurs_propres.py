#!/usr/bin/env python3
"""
patch_u4l_acteurs_propres.py — Ourrassol 2098 (22 novembre 2026)
================================================================

B9 wild cards, reste b) : une idée valable pour plusieurs scénarios ne doit
nommer aucun acteur propre à l'un d'eux (le lore diffère d'un monde à l'autre).

1. generator/hypothese_depuis_texte.py
   - controle_acteurs_propres(h) : relève, dans le nom, la description et les
     contraintes, les noms d'instances du vault (6 caractères au moins, mot
     entier, sans accents ni casse) qui n'existent pas dans TOUS les scénarios
     de l'hypothèse (y compris un acteur d'un autre monde). Une ligne par nom.
   - Pour une WILD CARD : erreur à ✨ Proposer et à Vérifier / Ajouter.
   - Consigne ajoutée au prompt wild card de ✨ Proposer.
2. generator/suggerer_lacunes.py (bouton ⚡) : même consigne dans le prompt ;
   le même contrôle devient un ⚠ sur l'idée proposée.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4l_acteurs_propres.py           # dry-run
    python3 generator/patch_u4l_acteurs_propres.py --apply   # écrit (.bak_u4l)
"""

import argparse
import shutil
import sys
from pathlib import Path

TAG = "u4l"

FONCTION = '''

# ---------------------------------------------------------------------------
# U4l (22 nov 2026) : acteur propre à un monde dans une idée à plusieurs scénarios
# ---------------------------------------------------------------------------

_NOMS_INSTANCES_U4L = None


def _plie_u4l(texte):
    t = unicodedata.normalize("NFKD", str(texte or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _noms_par_scenario_u4l():
    """{nom plié: (nom affiché, {scénarios où une instance porte ce nom})}, en cache."""
    global _NOMS_INSTANCES_U4L
    if _NOMS_INSTANCES_U4L is None:
        from loader import load_instances_for_scenario
        noms = {}
        for sc in se.SCENARIOS:
            for i in load_instances_for_scenario(sc) or []:
                nom = " ".join(str((i or {}).get("name") or "").split())
                cle = _plie_u4l(nom)
                if len(cle) >= 6:
                    noms.setdefault(cle, (nom, set()))[1].add(sc)
        _NOMS_INSTANCES_U4L = noms
    return _NOMS_INSTANCES_U4L


def controle_acteurs_propres(h, _noms=None):
    """U4l : messages pour chaque nom d'instance cité par l'hypothèse qui n'existe pas
    dans tous ses scénarios. Liste vide si rien à signaler."""
    scen = (h or {}).get("scenarios") or "tous"
    if isinstance(scen, str):
        couverts = set(se.SCENARIOS) if scen.strip() in ("tous", "all") else {scen.strip()}
    else:
        couverts = {s for s in scen if s in se.SCENARIOS}
    if not couverts:
        return []
    contraintes = (h or {}).get("contraintes") or []
    if isinstance(contraintes, str):
        contraintes = [contraintes]
    texte = _plie_u4l(" ".join([str(h.get("nom") or ""), str(h.get("description") or "")]
                               + [str(c) for c in contraintes]))
    noms = _noms_par_scenario_u4l() if _noms is None else _noms
    msgs = []
    for cle, (nom, ou) in sorted(noms.items(), key=lambda x: -len(x[0])):
        if ou >= couverts:
            continue
        if not re.search(r"(?<![a-z0-9])" + re.escape(cle) + r"(?![a-z0-9])", texte):
            continue
        presents = [s for s in se.SCENARIOS if s in ou]
        msgs.append(f"acteur propre à un monde : « {nom} » n'existe que dans {', '.join(presents)} "
                    f"(hypothèse : {', '.join(s for s in se.SCENARIOS if s in couverts)}) -- le désigner par "
                    f"sa fonction, ou limiter les scénarios à ceux où il existe")
    return msgs
'''

REMPLACEMENTS = {
    Path("generator/hypothese_depuis_texte.py"): [
        ("prompt wild card : consigne",
         'f"{se.WILD_CARD_FORCE_MIN_SC} au moins dans les autres.\\n\\n")   # U4d3 / U4f\n',
         'f"{se.WILD_CARD_FORCE_MIN_SC} au moins dans les autres. Si l\'élément vaut pour plusieurs "\n'
         '                       "scénarios, ne nomme aucun acteur, lieu ou institution propre à l\'un d\'eux (le lore "\n'
         '                       "diffère d\'un monde à l\'autre) : désigne-les par leur fonction.\\n\\n")   # U4d3 / U4f / U4l\n'),
        ("fonction controle_acteurs_propres()",
         "\n\ndef proposer(texte, _llm=appeler_llm, type_force=None, imposes=None):\n",
         FONCTION + "\n\ndef proposer(texte, _llm=appeler_llm, type_force=None, imposes=None):\n"),
        ("✨ Proposer : erreur pour une wild card",
         "    erreurs = list(erreurs) + se.controle_wild_cards(h)   # U4a\n",
         "    erreurs = list(erreurs) + se.controle_wild_cards(h)   # U4a\n"
         "    if wild:   # U4l\n"
         "        erreurs += controle_acteurs_propres(h)\n"),
        ("Vérifier / Ajouter : erreur pour une wild card",
         "    err2 = list(err2) + se.controle_wild_cards(h)   # U4a : quota et espacement\n",
         "    err2 = list(err2) + se.controle_wild_cards(h)   # U4a : quota et espacement\n"
         "    if se.est_wild_card(h):   # U4l\n"
         "        err2 += controle_acteurs_propres(h)\n"),
    ],
    Path("generator/suggerer_lacunes.py"): [
        ("prompt ⚡ : consigne",
         "- Varie les domaines d'une idée à l'autre ; aucune ne doit reprendre une wild card déjà prévue.\n",
         "- Varie les domaines d'une idée à l'autre ; aucune ne doit reprendre une wild card déjà prévue.\n"
         "- Acteurs (U4l) : une idée valable pour plusieurs scénarios ne nomme AUCUN acteur, lieu ou institution\n"
         "  propre à l'un d'eux (le lore diffère d'un monde à l'autre) : désigne-les par leur fonction\n"
         "  (« les grandes agences spatiales », « un consortium minier »).\n"),
        ("⚡ : contrôle en avertissement",
         '                                             "scenarios": scen}, hyps)\n',
         '                                             "scenarios": scen}, hyps)\n'
         '        try:   # U4l : acteur propre à un monde\n'
         '            import hypothese_depuis_texte as _hdt\n'
         '            avert += _hdt.controle_acteurs_propres({"nom": i.get("titre"), "description": desc,\n'
         '                                                    "scenarios": scen})\n'
         '        except Exception as e:  # noqa: BLE001 -- le contrôle ne doit jamais bloquer les idées\n'
         '            avert.append(f"contrôle des acteurs propres impossible ({type(e).__name__})")\n'),
    ],
}


def main():
    ap = argparse.ArgumentParser(description="Patch U4l : acteurs propres à un monde dans les wild cards.")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon dry-run)")
    args = ap.parse_args()

    manquants = [str(f) for f in REMPLACEMENTS if not f.is_file()]
    if manquants:
        sys.exit("✗ introuvable(s) : " + ", ".join(manquants) + " (lancer depuis la racine du vault)")
    if "controle_acteurs_propres" in Path("generator/hypothese_depuis_texte.py").read_text(encoding="utf-8"):
        sys.exit("✗ U4l déjà appliqué : rien à faire.")

    a_ecrire, ok = {}, True
    for chemin, rempl in REMPLACEMENTS.items():
        texte = chemin.read_text(encoding="utf-8")
        for nom, ancien, neuf in rempl:
            n = texte.count(ancien)
            if n != 1:
                print(f"✗ {chemin} : {nom} — ancre trouvée {n} fois (attendu 1)")
                ok = False
                continue
            texte = texte.replace(ancien, neuf)
            print(f"✓ {chemin} : {nom}")
        try:
            compile(texte, str(chemin), "exec")
        except SyntaxError as e:
            print(f"✗ {chemin} ne compile plus : {e}")
            ok = False
        a_ecrire[chemin] = texte
    if not ok:
        sys.exit("✗ Patch non appliqué : aucun fichier n'a été modifié.")
    print("✓ Toutes les ancres trouvées ; les fichiers patchés compilent.")

    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    for chemin, texte in a_ecrire.items():
        shutil.copy(chemin, chemin.with_name(chemin.name + f".bak_{TAG}"))
        chemin.write_text(texte, encoding="utf-8")
        print(f"→ {chemin} écrit (sauvegarde {chemin.name}.bak_{TAG})")


if __name__ == "__main__":
    main()

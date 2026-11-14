#!/usr/bin/env python3
"""
patch_u3aw_annee_entite.py — Ourrassol 2098 (14 novembre 2026)

Une entité garde la date d'origine voulue par l'auteur. Constat (injection en
aperçu de « Cité-Relais Radiologique d'Haïfa », « créée en 2082 ») : la date n'était
transmise à aucune étape, l'IA a daté les instances 2026-2028.

Nouveau champ OPTIONNEL `annee_debut` (2026-2098) dans une hypothèse de type entité :
l'année où l'entité naît dans son scénario de référence.
  simuler_et_si.py          : contrôle du champ (erreur si hors 2026-2098 ou non entier) ;
  hypothese_depuis_texte.py : ✨ Proposer le remplit seulement si l'idée donne l'année
                              de naissance (« créée en 2082 »), sinon null ;
  et_si_dossiers.py         : la décision « adopter » transmet annee_debut ;
  create_entities_and_instances.py : l'archétype reçoit la consigne ; la fiche entité
                              mémorise `annee_ref` (une régénération la retrouve) ;
  instance_generation_common.py : scénario de référence = contrainte DURE (annee_debut
                              doit valoir exactement l'année, vérifié) ; autres scénarios =
                              consigne de cohérence (même ordre de grandeur, sauf raison
                              narrative). Sans annee_debut : comportement inchangé.

Prérequis : U3aj, U3al, U3am. Après application : redémarrer Flask.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3aw_annee_entite.py            # aperçu
    python3 generator/patch_u3aw_annee_entite.py --apply
Sauvegardes .bak_u3aw ; refuse un second passage ; py_compile avec restauration.
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

MARQUEUR = "U3aw"
GEN = Path("generator")

# (fichier, prérequis, [(libellé, ancre, remplacement)])
PLAN = [
    ("simuler_et_si.py", "U3aj", [
        ("contrôle annee_debut",
         '    norm = {\n        "type": "entite", "id": hid, "nom": nom or hid,\n',
         '''    annee_ok = None   # U3aw : année d'origine (optionnelle) dans le scénario de référence
    if h.get("annee_debut") not in (None, ""):
        try:
            annee_ok = int(h.get("annee_debut"))
            if not 2026 <= annee_ok <= 2098:
                erreurs.append(f"annee_debut {annee_ok} hors de la période 2026-2098")
                annee_ok = None
        except (TypeError, ValueError):
            erreurs.append("annee_debut : une année entière (ex. 2082), année où l'entité naît "
                           "dans le scénario de référence")
    norm = {
        "type": "entite", "id": hid, "nom": nom or hid,
'''),
        ("annee dans la fiche normalisée",
         '        "scenarios": scen,\n    }\n    return norm, erreurs, avert\n',
         '        "scenarios": scen,\n    }\n    if annee_ok:\n        norm["annee_debut"] = annee_ok\n    return norm, erreurs, avert\n'),
    ]),
    ("hypothese_depuis_texte.py", "U3aj", [
        ("règle du prompt",
         '- "scenarios" : "tous", sauf si l\'idée limite explicitement l\'entité à certains scénarios\n  (liste de slugs).\n',
         '- "scenarios" : "tous", sauf si l\'idée limite explicitement l\'entité à certains scénarios\n  (liste de slugs).\n'
         '- "annee_debut" : l\'année (entre 2026 et 2098) où l\'entité NAÎT dans le scénario de\n'
         '  référence, SEULEMENT si l\'idée la donne (« créée en 2082 », « née en 2061 »…) ; sinon\n'
         '  null. Ne la déduis pas d\'une autre date de l\'idée (gouvernance, événement, déclin).\n'),
        ("exemple JSON du prompt",
         '  "scenario_ref": "reference", "role": null, "etat": null, "scenarios": "tous",\n',
         '  "scenario_ref": "reference", "role": null, "etat": null, "annee_debut": null, "scenarios": "tous",\n'),
        ("normalisation",
         '            h[cle] = v\n    scen = brut.get("scenarios") or "tous"\n    if isinstance(scen, list):\n        valides',
         '''            h[cle] = v
    annee = str(brut.get("annee_debut") or "").strip()   # U3aw
    if annee and annee.lower() not in ("null", "none"):
        try:
            a_ = int(float(annee))
            if 2026 <= a_ <= 2098:
                h["annee_debut"] = a_
            else:
                av.append(f"annee_debut {a_} hors de la période 2026-2098 : retirée")
        except ValueError:
            av.append(f"annee_debut {annee!r} illisible : retirée")
            h[cle] = v
    scen = brut.get("scenarios") or "tous"
    if isinstance(scen, list):
        valides'''),
    ]),
    ("et_si_dossiers.py", "U3al", [
        ("annee_debut dans l'entrée d'adoption",
         '    scen = brut.get("scenarios")\n    if isinstance(scen, list) and scen:\n        idee["scenario_hint"]',
         '''    a_ = str(brut.get("annee_debut") or "").strip()   # U3aw
    if a_.isdigit():
        idee["annee_debut"] = int(a_)
    scen = brut.get("scenarios")
    if isinstance(scen, list) and scen:
        idee["scenario_hint"]'''),
    ]),
    ("create_entities_and_instances.py", "U3al", [
        ("consigne dans l'archétype",
         '                 f"{idea[\'description\']}" if idea.get("description") else "")   # U3al\n',
         '''                 f"{idea['description']}" if idea.get("description") else "")   # U3al
    if str(idea.get("annee_debut") or "").strip():   # U3aw
        desc_u3al += (f"\\n- Année d'origine de l'entité (imposée par l'auteur, scénario de référence) : "
                      f"{idea['annee_debut']} — la description et le rôle doivent s'y accorder")
'''),
        ("write_entity_file : paramètre",
         "                       est_clandestin_ref=None, consignes_scenarios=None):\n",
         "                       est_clandestin_ref=None, consignes_scenarios=None, annee_ref=None):\n"),
        ("write_entity_file : front-matter",
         "    # consignes_scenarios (24 septembre 2026) : persistées dans la fiche",
         '    if annee_ref:   # U3aw : année d\'origine voulue par l\'auteur\n'
         '        extra_fm += f"annee_ref: {int(annee_ref)}\\n"\n'
         "    # consignes_scenarios (24 septembre 2026) : persistées dans la fiche"),
        ("entity_fm",
         '        "est_clandestin_ref": est_clandestin_ref,\n        "zone_hint": zone_hint,\n',
         '        "est_clandestin_ref": est_clandestin_ref,\n'
         '        "annee_ref": (int(idea["annee_debut"]) if str(idea.get("annee_debut") or "").strip().isdigit() else None),   # U3aw\n'
         '        "zone_hint": zone_hint,\n'),
        ("appel write_entity_file",
         "            est_clandestin_ref=est_clandestin_ref,\n            consignes_scenarios=consignes_scenarios,\n        )\n",
         "            est_clandestin_ref=est_clandestin_ref,\n            consignes_scenarios=consignes_scenarios,\n"
         '            annee_ref=(int(idea["annee_debut"]) if str(idea.get("annee_debut") or "").strip().isdigit() else None),   # U3aw\n'
         "        )\n"),
    ]),
    ("instance_generation_common.py", "U3am", [
        ("ligne contrainte année",
         "        _l_etat = (f\"- État temporel dans ce scénario : {hard_constraint['etat']}\\n\"\n"
         "                   if hard_constraint.get(\"etat\") else \"\")\n",
         "        _l_etat = (f\"- État temporel dans ce scénario : {hard_constraint['etat']}\\n\"\n"
         "                   if hard_constraint.get(\"etat\") else \"\")\n"
         "        _l_annee = (f\"- Année d'origine (annee_debut) : {hard_constraint['annee_debut']}\\n\"\n"
         "                    if hard_constraint.get(\"annee_debut\") else \"\")   # U3aw\n"),
        ("bloc contraintes",
         "{_l_role}{_l_etat}\n",
         "{_l_role}{_l_etat}{_l_annee}\n"),
        ("instruction JSON",
         "        _txt_instr_u3am = (",
         '''        if hard_constraint.get("annee_debut"):   # U3aw
            _instr_u3am.append(
                f"\\"annee_debut\\" devant valoir exactement {hard_constraint['annee_debut']} "
                f"(année d'origine fixée par l'auteur : elle prime sur la CONSIGNE CHRONOLOGIE "
                f"et sur les jalons de la chronologie du scénario)")
        _txt_instr_u3am = ('''),
        ("origine hors scénario de référence",
         '    injection_block = ""\n    injection_schema = ""\n',
         '''    try:   # U3aw : année d'origine voulue par l'auteur, pour les scénarios autres que la référence
        _annee_ref_u3aw = int(entity_fm.get("annee_ref") or 0) or None
    except (TypeError, ValueError):
        _annee_ref_u3aw = None
    if _annee_ref_u3aw and not (hard_constraint and hard_constraint.get("annee_debut")):
        constraint_block += f"""
## ORIGINE DE L'ENTITÉ (fixée par l'auteur)
Dans son scénario de référence, cette entité naît vers {_annee_ref_u3aw}. Dans ce scénario,
annee_debut doit rester cohérent avec cette origine : même ordre de grandeur (quelques
années d'écart au plus), sauf raison narrative forte propre à ce scénario. Ne la ramène
pas à 2026 ou au présent par défaut : cette consigne prime sur la CONSIGNE CHRONOLOGIE.
"""
    injection_block = ""
    injection_schema = ""
'''),
        ("contrôle de l'année",
         "        # est_clandestin optionnel dans hard_constraint (None = pas de\n",
         '''        if hard_constraint.get("annee_debut"):   # U3aw
            try:
                _a_u3aw = int(data.get("annee_debut"))
            except (TypeError, ValueError):
                _a_u3aw = None
            if _a_u3aw != int(hard_constraint["annee_debut"]):
                issues.append(
                    f"annee_debut ({data.get('annee_debut')!r}) ne respecte pas "
                    f"la contrainte dure ({hard_constraint['annee_debut']!r})"
                )
        # est_clandestin optionnel dans hard_constraint (None = pas de
'''),
        ("lecture de annee_ref",
         '    _etat_u3am = _val_fixee_u3am(entity_fm.get("etat_ref"))\n',
         '''    _etat_u3am = _val_fixee_u3am(entity_fm.get("etat_ref"))
    try:   # U3aw
        _annee_u3aw = int(entity_fm.get("annee_ref") or 0) or None
    except (TypeError, ValueError):
        _annee_u3aw = None
'''),
        ("contrainte dure : condition",
         '            _role_u3am or _etat_u3am or entity_fm.get("est_clandestin_ref") is not None):\n',
         '            _role_u3am or _etat_u3am or _annee_u3aw or entity_fm.get("est_clandestin_ref") is not None):\n'),
        ("contrainte dure : valeur",
         '            "etat": _etat_u3am,\n',
         '            "etat": _etat_u3am,\n            "annee_debut": _annee_u3aw,   # U3aw\n'),
    ]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dir", default=str(GEN))
    a = ap.parse_args()
    base = Path(a.dir)
    prepares = []
    for nom, prerequis, remp in PLAN:
        chemin = base / nom
        if not chemin.exists():
            print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
            return 2
        texte = chemin.read_text(encoding="utf-8")
        if prerequis not in texte:
            print(f"✗ Prérequis {prerequis} absent de {nom} : appliquer d'abord le patch correspondant.")
            return 1
        if MARQUEUR in texte:
            print(f"✗ {MARQUEUR} déjà appliqué dans {nom} — refus d'un second passage.")
            return 1
        nouveau = texte
        for libelle, ancre, rempl in remp:
            n = nouveau.count(ancre)
            if n != 1:
                print(f"✗ {nom} : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
                return 1
            nouveau = nouveau.replace(ancre, rempl, 1)
            print(f"  ✓ {nom} : {libelle}")
        prepares.append((chemin, texte, nouveau))
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3aw")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")
    try:
        for chemin, _ in baks:
            py_compile.compile(str(chemin), doraise=True)
    except py_compile.PyCompileError as e:
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)
        print(f"✗ py_compile a échoué, fichiers restaurés : {e}")
        return 1
    for chemin, bak in baks:
        print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    print("\nÀ faire : redémarrer Flask.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

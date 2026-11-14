#!/usr/bin/env python3
"""
patch_u3am_contrainte_dure_vide.py — Ourrassol 2098 (14 novembre 2026)

Correction d'un défaut ANCIEN révélé par le premier test d'entité « Et si ? »
(archives_de_la_maree, --dry-run : 5 instances créées, 1 erreur).

Cause : quand une idée d'entité a un scenario_ref mais pas d'état (`etat`),
write_entity_file() écrit « etat_ref: None » dans la fiche ; l'instance du
scénario de référence reçoit alors une « contrainte dure » : trajectoire
devant valoir exactement « None », ce qu'aucune réponse ne peut satisfaire.
L'instance du scénario de référence échoue donc toujours (le mécanisme n'avait
« jamais été exercé » sans état, d'après son propre commentaire).

Correction (aucune contrainte ne change quand rôle et état SONT donnés) :
  instance_generation_common.py
    1. « None » / « null » / vide = pas de valeur (fiches déjà écrites comprises) ;
       la contrainte dure n'existe que si un rôle, un état ou est_clandestin est fixé ;
    2. le prompt ne cite que les éléments fixés ;
    3. validate_instance ne contrôle la trajectoire que si un état est fixé.
  create_entities_and_instances.py
    4. write_entity_file n'écrit plus « etat_ref: None » ni un role_ref vide.
  et_si_injecter.py
    5. une instance en erreur est signalée en clair (« ⚠ entité injectée
       partiellement ») au lieu d'un « injectée » sans réserve.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3am_contrainte_dure_vide.py            # aperçu
    python3 generator/patch_u3am_contrainte_dure_vide.py --apply    # écrit

Sauvegarde .bak_u3am ; refuse un second passage ; py_compile de tous
(restauration automatique de TOUS en cas d'échec).
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

MARQUEUR = "U3am"
G = Path("generator")

# ---------------------------------------------------------------- instance_generation_common.py
IGC_ANCRE_HC = '''    hard_constraint = None
    if entity_fm.get("scenario_ref") == scenario:
        hard_constraint = {
            "role": entity_fm.get("role_ref", ""),
            "etat": entity_fm.get("etat_ref", ""),
'''
IGC_NOUV_HC = '''    hard_constraint = None
    # U3am : "None" / "null" / vide = valeur non fixée (une fiche écrite sans état
    # portait « etat_ref: None » : trajectoire exigée = "None", donc échec assuré)
    def _val_fixee_u3am(v):
        v = " ".join(str(v if v is not None else "").split())
        return "" if v.lower() in ("none", "null") else v
    _role_u3am = _val_fixee_u3am(entity_fm.get("role_ref"))
    _etat_u3am = _val_fixee_u3am(entity_fm.get("etat_ref"))
    if entity_fm.get("scenario_ref") == scenario and (
            _role_u3am or _etat_u3am or entity_fm.get("est_clandestin_ref") is not None):
        hard_constraint = {
            "role": _role_u3am,
            "etat": _etat_u3am,
'''

IGC_ANCRE_PROMPT = '''        constraint_block = f"""
## CONTRAINTES DURES POUR CE SCÉNARIO (ne pas reformuler, ne pas contredire)
- Rôle dans ce scénario : {hard_constraint['role']}
- État temporel dans ce scénario : {hard_constraint['etat']}

Ces deux éléments sont déjà fixés par l'utilisateur. Construis le reste
'''
IGC_NOUV_PROMPT = '''        _l_role = (f"- Rôle dans ce scénario : {hard_constraint['role']}\\n"
                   if hard_constraint.get("role") else "")   # U3am
        _l_etat = (f"- État temporel dans ce scénario : {hard_constraint['etat']}\\n"
                   if hard_constraint.get("etat") else "")
        constraint_block = f"""
## CONTRAINTES DURES POUR CE SCÉNARIO (ne pas reformuler, ne pas contredire)
{_l_role}{_l_etat}
Ces éléments sont déjà fixés par l'utilisateur. Construis le reste
'''

IGC_ANCRE_INSTR = '''        role_etat_instruction = f"""
Réponds en JSON, avec "role_dans_scenario" reprenant le rôle ci-dessus
(tu peux le développer en 3-5 lignes mais sans en changer le sens) et
"trajectoire" devant valoir exactement "{hard_constraint['etat']}".
'''
IGC_NOUV_INSTR = '''        _instr_u3am = []
        if hard_constraint.get("role"):
            _instr_u3am.append('"role_dans_scenario" reprenant le rôle ci-dessus '
                               '(tu peux le développer en 3-5 lignes mais sans en changer le sens)')
        if hard_constraint.get("etat"):
            _instr_u3am.append(f'"trajectoire" devant valoir exactement "{hard_constraint["etat"]}"')
        _txt_instr_u3am = ("Réponds en JSON, avec " + " et ".join(_instr_u3am) + ".") if _instr_u3am else ""
        role_etat_instruction = f"""
{_txt_instr_u3am}
'''

IGC_ANCRE_VAL = '        if data.get("trajectoire") != hard_constraint["etat"]:\n'
IGC_NOUV_VAL = '        if hard_constraint.get("etat") and data.get("trajectoire") != hard_constraint["etat"]:   # U3am\n'

IGC_REMPL = [
    ("contrainte dure seulement si fixée", IGC_ANCRE_HC, IGC_NOUV_HC),
    ("prompt : éléments fixés seulement", IGC_ANCRE_PROMPT, IGC_NOUV_PROMPT),
    ("prompt : consigne de réponse", IGC_ANCRE_INSTR, IGC_NOUV_INSTR),
    ("validation de la trajectoire", IGC_ANCRE_VAL, IGC_NOUV_VAL),
]

# ---------------------------------------------------------------- create_entities_and_instances.py
CRE_ANCRE = '''        extra_fm += f"role_ref: >\\n  {role_ref_clean}\\n"
        extra_fm += f"etat_ref: {etat_ref}\\n"
'''
CRE_NOUV = '''        if role_ref_clean:   # U3am : pas de role_ref vide ni d'« etat_ref: None »
            extra_fm += f"role_ref: >\\n  {role_ref_clean}\\n"
        if etat_ref:
            extra_fm += f"etat_ref: {etat_ref}\\n"
'''
CRE_REMPL = [("role_ref / etat_ref seulement si fixés", CRE_ANCRE, CRE_NOUV)]

# ---------------------------------------------------------------- et_si_injecter.py
INJ_ANCRE = '''    st_i = res.get("instance_stats") or {}
    print(f"\\n✓ entité {res.get('slug')} injectée — instances : {st_i or 'voir ci-dessus'}")
'''
INJ_NOUV = '''    st_i = res.get("instance_stats") or {}
    if st_i.get("errors"):   # U3am : instance(s) en erreur = injection partielle
        print(f"\\n⚠ entité {res.get('slug')} injectée PARTIELLEMENT — instances : {st_i} : "
              f"relancer « generate_instances.py » pour les scénarios manquants (ou voir ci-dessus).")
    else:
        print(f"\\n✓ entité {res.get('slug')} injectée — instances : {st_i or 'voir ci-dessus'}")
'''
INJ_REMPL = [("instance en erreur signalée", INJ_ANCRE, INJ_NOUV)]

CIBLES = [
    ("instance_generation_common.py", None, IGC_REMPL),
    ("create_entities_and_instances.py", None, CRE_REMPL),
    ("et_si_injecter.py", "U3al", INJ_REMPL),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="écrit (sinon aperçu)")
    ap.add_argument("--dossier", default=str(G))
    a = ap.parse_args()
    base = Path(a.dossier)
    prepares = []
    for nom, prereq, remp in CIBLES:
        chemin = base / nom
        if not chemin.exists():
            print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
            return 2
        texte = chemin.read_text(encoding="utf-8")
        if prereq and prereq not in texte:
            print(f"✗ {nom} : prérequis {prereq} absent.")
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
        for chemin, avant, apres in prepares:
            print(f"  {chemin.name} : {len(avant.splitlines())} -> {len(apres.splitlines())} lignes")
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3am")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")
    try:
        for chemin, _ in baks:
            py_compile.compile(str(chemin), doraise=True)
    except py_compile.PyCompileError as e:
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)
        print(f"✗ py_compile a échoué, tous les fichiers restaurés : {e}")
        return 1
    for chemin, bak in baks:
        print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

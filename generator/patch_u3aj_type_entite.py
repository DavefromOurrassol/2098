#!/usr/bin/env python3
"""
patch_u3aj_type_entite.py — Ourrassol 2098 (14 novembre 2026)

Patch 1/4 du type « entité » dans « Et si ? » (option A : pas de simulation
chiffrée). Deux fichiers de generator/ :

  simuler_et_si.py (U3aj)
    1. verifier_hypothese() accepte `type: entite` : contrôle propre (nom,
       categorie, scenario_ref, scenarios ; role et etat facultatifs), sans
       date ni impact. Les champs d'événement (date, impacts, geographie,
       carte, mode...) sont signalés « ignorés », jamais refusés.
    2. --id <entité> : refus net de simuler (« une entité ne se simule pas »),
       au lieu d'une erreur obscure sur la date.

  hypothese_depuis_texte.py (U3aj)
    3. --proposer --type entite : un appel IA transforme une idée en bloc
       d'entité (id, nom, description, categorie, scenario_ref, role, etat,
       scenarios), contrôlé par le même verifier_hypothese(). N'écrit rien.
       --verifier et --ajouter acceptent déjà le bloc (même contrôle).
       Sans --type, l'IA ne propose jamais « entite » : le choix est celui de
       l'auteur.

Bloc d'une entité dans et_si/hypotheses.yaml :
    - id: archives_de_la_marée_2050
      nom: Archives de la Marée
      type: entite
      description: ...
      categorie: institution        # IA|organisation|entreprise|institution|...
      scenario_ref: reference       # scénario où rôle/état s'imposent
      role: ...                     # facultatif
      etat: ...                     # facultatif
      scenarios: tous               # ou liste ; sert de scenario_hint

Usage (depuis la racine du vault) :
    python3 generator/patch_u3aj_type_entite.py            # aperçu
    python3 generator/patch_u3aj_type_entite.py --apply    # écrit

Sauvegarde .bak_u3aj ; refuse un second passage ; py_compile après écriture
(restauration automatique des deux fichiers en cas d'échec).
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

MARQUEUR = "U3aj"
SIM = Path("generator/simuler_et_si.py")
HYP = Path("generator/hypothese_depuis_texte.py")

# --------------------------------------------------------------------------
# simuler_et_si.py
# --------------------------------------------------------------------------

SIM_HELPER = '''# U3aj (14 nov 2026) : catégories d'une entité -- MÊME liste que VALID_CATEGORIES
# dans create_entities_and_instances.py (à garder alignées).
CATEGORIES_ENTITE = [
    "IA", "organisation", "entreprise", "institution", "infrastructure",
    "réseau", "humain", "système", "hybride", "autre", "média", "territoire",
]
CHAMPS_EVENEMENT_IGNORES = ("date", "impacts", "geographie", "carte", "mode", "persistance",
                            "contraintes", "lieu", "via_matrice")


def _verifier_entite(h):
    """U3aj : contrôle d'une hypothèse `type: entite` (pas de simulation chiffrée).
    Retourne (hypothèse normalisée, erreurs, avertissements)."""
    erreurs, avert = [], []
    hid = h.get("id") or "?"
    nom = " ".join(str(h.get("nom") or "").split())
    if not nom:
        erreurs.append("`nom` requis (le nom de l'entité, tel qu'il apparaîtra dans le monde)")
    cat = str(h.get("categorie") or "").strip()
    if cat not in CATEGORIES_ENTITE:
        erreurs.append(f"categorie {h.get('categorie')!r} invalide ({' | '.join(CATEGORIES_ENTITE)})")
    ref = str(h.get("scenario_ref") or "").strip()
    if ref not in SCENARIOS:
        erreurs.append(f"scenario_ref {h.get('scenario_ref')!r} invalide ({' | '.join(SCENARIOS)})")
    scen = h.get("scenarios") or "tous"
    if isinstance(scen, str):
        scen = list(SCENARIOS) if scen.strip() in ("tous", "all") else [scen.strip()]
    if not isinstance(scen, list):
        erreurs.append("`scenarios` : « tous » ou une liste de scénarios")
        scen = list(SCENARIOS)
    inconnus = [s for s in scen if s not in SCENARIOS]
    if inconnus:
        erreurs.append(f"scénarios inconnus : {inconnus}")
    scen = [s for s in scen if s in SCENARIOS]
    if ref in SCENARIOS and scen and ref not in scen:
        avert.append(f"scenario_ref {ref!r} absent de `scenarios` : il sera ajouté à l'injection")
    ignores = [c for c in CHAMPS_EVENEMENT_IGNORES if h.get(c) not in (None, "", [], {})]
    if ignores:
        avert.append("ignorés pour une entité : " + ", ".join(ignores)
                     + " (une entité n'a ni date, ni impact chiffré, ni carte)")
    norm = {
        "type": "entite", "id": hid, "nom": nom or hid,
        "description": str(h.get("description") or "").strip(),
        "categorie": cat, "scenario_ref": ref,
        "role": " ".join(str(h.get("role") or "").split()) or None,
        "etat": " ".join(str(h.get("etat") or "").split()) or None,
        "scenarios": scen,
    }
    return norm, erreurs, avert


'''

SIM_ANCRE_DEF = ('def verifier_hypothese(h, valid_vars, dyn):\n'
                 '    """Retourne (hypothèse normalisée, erreurs, avertissements)."""\n'
                 '    erreurs, avert = [], []\n')
SIM_DEF_NOUV = ('def verifier_hypothese(h, valid_vars, dyn):\n'
                '    """Retourne (hypothèse normalisée, erreurs, avertissements)."""\n'
                '    if str(h.get("type") or "").strip().lower() == "entite":   # U3aj\n'
                '        return _verifier_entite(h)\n'
                '    erreurs, avert = [], []\n')

SIM_ANCRE_SCEN = ('    if args.scenario and args.scenario not in hyp["scenarios"]:\n'
                  '        sys.exit(f"✗ Scénario {args.scenario!r} non couvert par l\'hypothèse')
SIM_REFUS = ('    if hyp.get("type") == "entite":   # U3aj : pas de simulation chiffrée pour une entité\n'
             '        sys.exit(f"✗ {args.id!r} est une entité : une entité ne se simule pas. "\n'
             '                 "Parcours : vérifier, décider, injecter (« Simuler l\'injection » pour tester).")\n')

SIM_REMPL = [
    ("verifier_hypothese : type entite", SIM_ANCRE_DEF, SIM_HELPER + SIM_DEF_NOUV),
    ("refus de simuler une entité", SIM_ANCRE_SCEN, SIM_REFUS + SIM_ANCRE_SCEN),
]

# --------------------------------------------------------------------------
# hypothese_depuis_texte.py
# --------------------------------------------------------------------------

HYP_FONCTIONS = '''# ---------------------------------------------------------------------------
# U3aj : proposition d'une ENTITÉ (pas de date, pas d'impact, pas de simulation)
# ---------------------------------------------------------------------------

def construire_prompt_entite(texte):
    return f"""TYPE IMPOSÉ PAR L'AUTEUR : entite (ne le change pas).

Tu aides l'auteur du monde fictif Ourrassol 2098 (6 scénarios d'avenir) à transformer une IDÉE en
fiche de départ d'une ENTITÉ du monde (une organisation, une IA, une institution, un lieu,
une personne...). L'entité sera créée puis déclinée dans les scénarios ; ici tu ne fais que
cadrer l'idée.

IDÉE DE L'UTILISATEUR :
<<<
{texte.strip()}
>>>

LES 6 SCÉNARIOS :
{resume_scenarios()}

RÈGLES :
- "nom" : le nom de l'entité tel qu'écrit dans l'idée (sinon un nom court et sobre). "id" :
  snake_case sans accents, 2 à 4 mots.
- "description" : 1 à 4 phrases qui reprennent UNIQUEMENT ce que dit l'idée, avec ses mots.
  N'ajoute AUCUN fait, date, lieu, chiffre ou acteur absent de l'idée : une idée courte donne
  une description courte.
- "categorie" : une valeur parmi {" | ".join(CATEGORIES_ENTITE)}.
- "scenario_ref" : le scénario où l'idée se situe SI elle en nomme un ; sinon "reference".
- "role" et "etat" : seulement si l'idée les dit (rôle de l'entité dans ce scénario, son état
  actuel) ; sinon null. Ne les invente pas.
- "scenarios" : "tous", sauf si l'idée limite explicitement l'entité à certains scénarios
  (liste de slugs).
- "justification" : 2 phrases au plus (choix de la catégorie et du scénario de référence).

Réponds UNIQUEMENT en JSON valide, sans texte autour :
{{"id": "...", "nom": "...", "description": "...", "categorie": "institution",
  "scenario_ref": "reference", "role": null, "etat": null, "scenarios": "tous",
  "justification": "..."}}"""


def normaliser_entite(brut, ids_pris):
    """Réponse de l'IA -> bloc d'entité. Chaque correction est signalée."""
    av = []
    nom = " ".join(str(brut.get("nom") or "").split())
    id_ = slugifier(brut.get("id")) or slugifier(nom) or "entite"
    base, n = id_, 2
    while id_ in ids_pris:
        id_ = f"{base}_{n}"
        n += 1
    if id_ != base:
        av.append(f"id {base!r} déjà pris -> {id_!r}")
    h = {"id": id_, "nom": nom or id_, "type": "entite"}
    description = " ".join(str(brut.get("description") or "").split())
    if description:
        h["description"] = description
    cat = str(brut.get("categorie") or "").strip()
    if cat not in CATEGORIES_ENTITE:
        av.append(f"categorie {cat!r} inconnue -- à choisir ({' | '.join(CATEGORIES_ENTITE)})")
    h["categorie"] = cat
    ref = str(brut.get("scenario_ref") or "").strip()
    if ref not in se.SCENARIOS:
        if ref:
            av.append(f"scenario_ref {ref!r} inconnu -> reference")
        ref = "reference"
    h["scenario_ref"] = ref
    for cle in ("role", "etat"):
        v = " ".join(str(brut.get(cle) or "").split())
        if v and v.lower() not in ("null", "none"):
            h[cle] = v
    scen = brut.get("scenarios") or "tous"
    if isinstance(scen, list):
        valides = [s for s in scen if s in se.SCENARIOS]
        if len(valides) != len(scen):
            av.append(f"scénario(s) inconnu(s) retiré(s) : {[s for s in scen if s not in se.SCENARIOS]}")
        scen = valides if valides and len(valides) < len(se.SCENARIOS) else "tous"
    elif str(scen).strip() not in se.SCENARIOS:
        scen = "tous"
    h["scenarios"] = scen
    return h, av


def proposer_entite(texte, _llm=appeler_llm):
    brut = _llm(construire_prompt_entite(texte))
    if not isinstance(brut, dict):
        raise ValueError("réponse de l'IA inexploitable")
    h, av = normaliser_entite(brut, ids_existants())
    _, erreurs, av2 = se.verifier_hypothese(dict(h), valid_vars(), dyn)
    return {"ok": True, "bloc": bloc_yaml(h), "id": h["id"],
            "justification": str(brut.get("justification") or "").strip(),
            "avertissements": av + av2, "erreurs": erreurs}


'''

HYP_ANCRE_CONST = 'MAX_IMPACTS = 8\n'
HYP_CONST_NOUV = ('MAX_IMPACTS = 8\n'
                  'CATEGORIES_ENTITE = se.CATEGORIES_ENTITE   # U3aj\n')

HYP_ANCRE_PROPOSER = 'def proposer(texte, _llm=appeler_llm, type_force=None, imposes=None):\n'

HYP_ANCRE_VAR = ('    variables = valid_vars()\n'
                 '    brut = _llm(construire_prompt(texte, variables, type_force, imposes))\n')
HYP_VAR_NOUV = ('    if type_force == "entite":   # U3aj : parcours propre, sans date ni impact\n'
                '        return proposer_entite(texte, _llm)\n') + HYP_ANCRE_VAR

HYP_ANCRE_ARG = 'ap.add_argument("--type", choices=("evenement", "signal"), default=None,'
HYP_ARG_NOUV = 'ap.add_argument("--type", choices=("evenement", "signal", "entite"), default=None,'

HYP_REMPL = [
    ("constante des catégories", HYP_ANCRE_CONST, HYP_CONST_NOUV),
    ("fonctions de l'entité", HYP_ANCRE_PROPOSER, HYP_FONCTIONS + HYP_ANCRE_PROPOSER),
    ("aiguillage dans proposer()", HYP_ANCRE_VAR, HYP_VAR_NOUV),
    ("--type entite", HYP_ANCRE_ARG, HYP_ARG_NOUV),
]


def preparer(chemin, remplacements):
    texte = chemin.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print(f"✗ {MARQUEUR} déjà appliqué dans {chemin} — refus d'un second passage.")
        return None, None
    nouveau = texte
    for nom, ancre, rempl in remplacements:
        n = nouveau.count(ancre)
        if n != 1:
            print(f"✗ {chemin.name} : ancre « {nom} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
            return None, None
        nouveau = nouveau.replace(ancre, rempl, 1)
        print(f"  ✓ {chemin.name} : {nom}")
    return texte, nouveau


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="écrit (sinon aperçu)")
    ap.add_argument("--sim", default=str(SIM))
    ap.add_argument("--hyp", default=str(HYP))
    args = ap.parse_args()
    cibles = []
    for chemin, remp in ((Path(args.sim), SIM_REMPL), (Path(args.hyp), HYP_REMPL)):
        if not chemin.exists():
            print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
            return 2
        avant, apres = preparer(chemin, remp)
        if apres is None:
            return 1
        cibles.append((chemin, avant, apres))
    if not args.apply:
        for chemin, avant, apres in cibles:
            print(f"  {chemin.name} : {len(avant.splitlines())} -> {len(apres.splitlines())} lignes")
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, avant, apres in cibles:
        bak = chemin.with_name(chemin.name + ".bak_u3aj")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
patch_s27_injection_imposee.py — Ourrassol 2098 (S27, refonte de l'injection, 11 octobre 2026)

Ajoute à generator/inject_custom_events.py la possibilité d'IMPOSER les forces,
la date et la propagation d'un événement (valeurs issues du simulateur « et si ? »),
au lieu de les laisser recalculer par l'IA.

Nouveaux champs optionnels d'une idée (queue.yaml ou --idea) :
  impacts_imposes:      {scénario: [{variable, delta_level, duree, polarite}]}
  date_imposee:         2029        (année 2025-2098)
  via_matrice_impose:   true|false

Sans ces champs : comportement strictement inchangé.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_injection_imposee.py            # aperçu, n'écrit rien
    python3 generator/patch_s27_injection_imposee.py --apply    # écrit (.bak_imposee)

Refuse un second passage (marqueur PATCH_S27_INJECTION_IMPOSEE).
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "inject_custom_events.py"
MARQUEUR = "PATCH_S27_INJECTION_IMPOSEE"

# ---------------------------------------------------------------------------
# 1. Fonctions ajoutées, juste avant process_idea()
# ---------------------------------------------------------------------------
ANCRE_FONCTIONS = "def process_idea(client, idea, dry_run=False):\n"
FONCTIONS = '''# PATCH_S27_INJECTION_IMPOSEE (11 octobre 2026) -- forces, date et propagation
# imposées par le simulateur « et si ? ». Sans ces champs dans l'idée, rien ne change.

def lire_impositions(idea):
    """Lit et contrôle impacts_imposes / date_imposee / via_matrice_impose.
    Retourne (impositions ou None, erreurs). Les valeurs ne sont jamais
    corrigées en silence : une valeur invalide est une erreur."""
    brut = idea.get("impacts_imposes")
    date = idea.get("date_imposee")
    via = idea.get("via_matrice_impose")
    if brut is None and date is None and via is None:
        return None, []
    erreurs, impacts = [], {}
    if brut is not None:
        if not isinstance(brut, dict) or not brut:
            erreurs.append("impacts_imposes doit être un dictionnaire {scénario: [impacts]}")
            brut = {}
        for sc, liste in brut.items():
            if sc not in SCENARIOS:
                erreurs.append(f"impacts_imposes : scénario inconnu {sc!r}")
                continue
            if not isinstance(liste, list) or not liste:
                erreurs.append(f"impacts_imposes[{sc}] doit être une liste non vide")
                continue
            propres = []
            for n, imp in enumerate(liste, 1):
                ou = f"impacts_imposes[{sc}] n°{n}"
                if not isinstance(imp, dict):
                    erreurs.append(f"{ou} mal formé")
                    continue
                var = str(imp.get("variable") or "").strip()
                if var not in VALID_VARS:
                    erreurs.append(f"{ou} : variable inconnue {var!r}")
                    continue
                try:
                    force = abs(float(imp.get("delta_level")))
                except (TypeError, ValueError):
                    erreurs.append(f"{ou} : delta_level absent ou non numérique")
                    continue
                if not 1 <= force <= MAX_DELTA_LEVEL:
                    erreurs.append(f"{ou} : delta_level {force:g} hors de 1-{MAX_DELTA_LEVEL}")
                    continue
                try:
                    pol = int(imp.get("polarite"))
                except (TypeError, ValueError):
                    pol = None
                if pol not in (1, -1):
                    erreurs.append(f"{ou} : polarite doit valoir 1 ou -1")
                    continue
                try:
                    duree = float(imp.get("duree") or 10)
                except (TypeError, ValueError):
                    erreurs.append(f"{ou} : duree non numérique")
                    continue
                if duree <= 0:
                    erreurs.append(f"{ou} : duree doit être positive")
                    continue
                propres.append({"variable": var,
                                "delta_level": int(force) if force == int(force) else force,
                                "duree": int(duree) if duree == int(duree) else duree,
                                "polarite": pol})
            if propres:
                impacts[sc] = propres
        jeux = {tuple(sorted(i["variable"] for i in v)) for v in impacts.values()}
        if len(jeux) > 1:
            erreurs.append("impacts_imposes : les scénarios doivent porter les mêmes variables")
    if date is not None:
        try:
            date = float(date)
        except (TypeError, ValueError):
            erreurs.append("date_imposee non numérique")
            date = None
        if date is not None and not 2025 <= date <= 2098:
            erreurs.append(f"date_imposee {date:g} hors de 2025-2098")
    if via is not None and not isinstance(via, bool):
        erreurs.append("via_matrice_impose doit valoir true ou false")
    if erreurs:
        return None, erreurs
    return {"impacts": impacts, "date": date, "via_matrice": via}, []


def appliquer_impositions(instance_data, idea, scenario):
    """Remplace dans la réponse de l'IA ce que l'idée impose (appelé après chaque
    réponse, essai initial et relances, AVANT la validation)."""
    imp, _ = lire_impositions(idea)
    if not imp:
        return
    if scenario in imp["impacts"]:
        instance_data["impact_sur_variables"] = [dict(i) for i in imp["impacts"][scenario]]
    if imp["date"] is not None:
        annee = int(imp["date"])
        instance_data["date"] = int(imp["date"]) if imp["date"] == annee else imp["date"]
        label = str(instance_data.get("date_label") or "")
        ancienne = re.search(r"\\b(20\\d\\d)\\b", label)
        if ancienne and ancienne.group(1) != str(annee):
            label = label.replace(ancienne.group(1), str(annee))
        elif not ancienne:
            label = str(annee)
        instance_data["date_label"] = label
    if imp["via_matrice"] is not None:
        instance_data["propagation_via_matrice"] = imp["via_matrice"]
    if instance_data.get("impossible_dans_scenario"):
        print(f"  ⚠ [{scenario}] l'IA juge l'événement impossible dans ce scénario, "
              f"mais les impacts sont imposés : relire la fiche.")


def _texte_impositions(idea, scenario):
    """Bloc du prompt de l'étape 2 : ce qui est fixé, pour que le texte raconte ce choc-là."""
    imp, _ = lire_impositions(idea)
    if not imp:
        return ""
    lignes = ["", "## VALEURS IMPOSÉES (issues d'une simulation, NE PAS LES MODIFIER)"]
    for i in imp["impacts"].get(scenario, []):
        sens = "aggrave" if i["polarite"] > 0 else "apaise"
        lignes.append(f"- {i['variable']} : force {i['delta_level']}, {sens}, montée sur {i['duree']} ans")
    if imp["date"] is not None:
        lignes.append(f"- Date de l'événement : {int(imp['date'])}")
    if imp["via_matrice"] is not None:
        lignes.append(f"- Propagation via la matrice : {'oui' if imp['via_matrice'] else 'non'}")
    lignes.append("Écris la réalisation, la description et les conséquences pour qu'elles "
                  "correspondent à ces valeurs (ampleur, sens et date).")
    return "\\n".join(lignes) + "\\n"


'''

# ---------------------------------------------------------------------------
# 2. Prompt de l'étape 2 : date fixée et bloc des valeurs imposées
# ---------------------------------------------------------------------------
ANCRE_PROMPT_AVANT = '    actors_list_txt = "\\n".join(\n'
AJOUT_PROMPT = '''    # PATCH_S27_INJECTION_IMPOSEE : date fixée et valeurs imposées
    impositions_txt = _texte_impositions(idea, scenario)
    if idea.get("date_imposee") is not None and impositions_txt:
        date_rule_txt = (f"- La date est FIXÉE à {int(float(idea['date_imposee']))} "
                         f"(issue d'une simulation) : n'en propose pas d'autre")

'''
ANCRE_PROMPT_BLOC = "{actors_hint_txt}{zone_hint_txt}\n"
NOUVEAU_PROMPT_BLOC = "{actors_hint_txt}{zone_hint_txt}{impositions_txt}\n"

# ---------------------------------------------------------------------------
# 3. process_idea : contrôle avant tout appel IA, variables imposées
# ---------------------------------------------------------------------------
ANCRE_SCENARIOS = "    scenarios = [s for s in scenarios if s in SCENARIOS]\n"
AJOUT_SCENARIOS = '''
    # PATCH_S27_INJECTION_IMPOSEE : contrôle des valeurs imposées AVANT tout appel IA.
    impositions, err_imp = lire_impositions(idea)
    if err_imp:
        return {"status": "needs_review", "idea": idea,
                "reason": "valeurs imposées invalides : " + " ; ".join(err_imp)}
    if impositions and impositions["impacts"]:
        if not idea.get("scenarios"):
            scenarios = [s for s in SCENARIOS if s in impositions["impacts"]]
        manquants = [s for s in scenarios if s not in impositions["impacts"]]
        if manquants:
            return {"status": "needs_review", "idea": idea,
                    "reason": f"impacts_imposes absent pour : {', '.join(manquants)}"}
        vars_imposees = list(dict.fromkeys(
            i["variable"] for v in impositions["impacts"].values() for i in v))
        variables_hint = vars_imposees
        variables_hint_count = len(vars_imposees)
        print(f"  [imposé] impacts de la simulation pour {', '.join(scenarios)}"
              + (f", date {impositions['date']:g}" if impositions["date"] is not None else ""))
'''

ANCRE_TYPE = '    type_evenement = selection.get("type_evenement", "systemic")\n'
AJOUT_TYPE = '''    # PATCH_S27_INJECTION_IMPOSEE : les variables sont celles des impacts imposés.
    if impositions and impositions["impacts"]:
        variables = list(variables_hint)
'''

ANCRE_EDITION = '            if idea.get("edition_active"):\n'
NOUVEAU_EDITION = '''            if idea.get("edition_active") and idea.get("date_imposee") is not None:
                print("  ⚠ edition_active ignoré : la date est imposée par la simulation.")
            elif idea.get("edition_active"):
'''

# ---------------------------------------------------------------------------
# 4. Documentation de la queue
# ---------------------------------------------------------------------------
ANCRE_TEMPLATE = "#\n# EXEMPLE :\n#   - id: guerre_israelo_iranienne\n"
AJOUT_TEMPLATE = '''#   impacts_imposes        : optionnel (simulateur « et si ? »). Forces IMPOSÉES
#                            par scénario, l'IA ne les recalcule pas :
#                              fortress_world:
#                                - {variable: geopolitique_conflits,
#                                   delta_level: 20, duree: 5, polarite: 1}
#                            Mêmes variables dans chaque scénario ; scenarios
#                            null = les scénarios listés ici.
#   date_imposee           : optionnel, année 2025-2098 imposée (prime sur
#                            edition_active).
#   via_matrice_impose     : optionnel, true/false imposé.
'''


def remplacer_une_fois(texte, ancre, nouveau, nom):
    n = texte.count(ancre)
    if n != 1:
        sys.exit(f"✗ Ancre « {nom} » trouvée {n} fois (attendu 1) : rien n'est écrit.")
    return texte.replace(ancre, nouveau)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="écrit le fichier (sinon aperçu)")
    args = ap.parse_args()

    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable.")
    texte = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit("✗ Patch déjà appliqué (marqueur présent) : rien n'est fait.")

    t = texte
    t = remplacer_une_fois(t, ANCRE_FONCTIONS, FONCTIONS + ANCRE_FONCTIONS, "def process_idea")
    t = remplacer_une_fois(t, ANCRE_PROMPT_AVANT, AJOUT_PROMPT + ANCRE_PROMPT_AVANT, "actors_list_txt")
    t = remplacer_une_fois(t, ANCRE_PROMPT_BLOC, NOUVEAU_PROMPT_BLOC, "bloc du prompt")
    t = remplacer_une_fois(t, ANCRE_SCENARIOS, ANCRE_SCENARIOS + AJOUT_SCENARIOS, "liste des scénarios")
    t = remplacer_une_fois(t, ANCRE_TYPE, AJOUT_TYPE + ANCRE_TYPE, "type_evenement")
    t = remplacer_une_fois(t, ANCRE_EDITION, NOUVEAU_EDITION, "edition_active")
    t = remplacer_une_fois(t, ANCRE_TEMPLATE, "#\n" + AJOUT_TEMPLATE + ANCRE_TEMPLATE[2:], "modèle de queue")

    # Après chaque truncate_actors() de process_idea (essai initial et relances).
    motif = re.compile(r"^( +)truncate_actors\(instance_data, actors_hint, actors_hint_count, available_actors\)\n",
                       re.M)
    appels = motif.findall(t)
    if len(appels) != 2:
        sys.exit(f"✗ {len(appels)} appel(s) à truncate_actors() trouvés (attendu 2) : rien n'est écrit.")
    t = motif.sub(lambda m: m.group(0) + f"{m.group(1)}appliquer_impositions(instance_data, idea, scenario)\n", t)

    try:
        compile(t, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier modifié ne compilerait pas ({e}) : rien n'est écrit.")

    print(f"Modifications prêtes : 7 remplacements + 2 appels appliquer_impositions() "
          f"({len(texte.splitlines())} → {len(t.splitlines())} lignes).")
    if not args.apply:
        print("Aperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_imposee"))
    CIBLE.write_text(t, encoding="utf-8")
    print(f"✓ {CIBLE.name} modifié (sauvegarde : {CIBLE.name}.bak_imposee).")


if __name__ == "__main__":
    main()

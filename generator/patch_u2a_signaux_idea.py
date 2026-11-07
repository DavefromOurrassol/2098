#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unification « et si ? » — étape 2a : inject_custom_signals.py accepte
  --idea '<json>' [--json]   (une idée unique, hors queue.yaml)
et des VALEURS IMPOSÉES (même principe que inject_custom_events.py) :
  impacts_imposes {scénario: [{variable, delta_level 1-10, polarite ±1, duree}]}
  date_imposee    (année de début de fenêtre, la même pour les 6 scénarios)
  via_matrice_impose (true|false)
Sans ces champs, rien ne change (queue.yaml et GUI actuels intacts).

    python3 generator/patch_u2a_signaux_idea.py            # dry-run
    python3 generator/patch_u2a_signaux_idea.py --apply    # applique (.bak_u2a)
"""
import py_compile
import shutil
import sys
from pathlib import Path

F = Path("generator/inject_custom_signals.py")

NOUVEAU_BLOC = r'''# ---------------------------------------------------------------------------
# U2a (unification « et si ? ») -- valeurs imposées par le simulateur
# ---------------------------------------------------------------------------
# Champs d'idée : impacts_imposes, date_imposee, via_matrice_impose (+ mode_impose
# "choc" toléré). Jamais corrigés en silence : une valeur invalide est une erreur.

def lire_impositions_signal(idea):
    """Retourne (impositions ou None, erreurs).
    impositions = {"par_var": {variable: {"delta": n, "scen": {sc: {"polarite": ±1,
    "duree": n}}}}, "date": int ou None, "via_matrice": bool ou None}."""
    brut = idea.get("impacts_imposes")
    date_i = idea.get("date_imposee")
    via = idea.get("via_matrice_impose")
    mode = idea.get("mode_impose")
    if brut is None and date_i is None and via is None and mode is None:
        return None, []
    erreurs = []
    if brut is None:
        erreurs.append("impacts_imposes obligatoire dès qu'une valeur est imposée "
                       "(forces et sens par scénario)")
    par_var = {}
    if brut is not None:
        if not isinstance(brut, dict) or not brut:
            erreurs.append("impacts_imposes doit être un dictionnaire {scénario: [impacts]}")
            brut = {}
        for sc in brut:
            if sc not in SCENARIOS:
                erreurs.append("impacts_imposes : scénario inconnu {!r}".format(sc))
        if brut and not erreurs:
            manquants = [s for s in SCENARIOS if s not in brut]
            if manquants:
                erreurs.append("impacts_imposes : un signal couvre toujours les 6 scénarios, "
                               "manquants : {}".format(manquants))
        for sc in SCENARIOS:
            liste = brut.get(sc)
            if liste is None:
                continue
            if not isinstance(liste, list) or not liste:
                erreurs.append("impacts_imposes[{}] doit être une liste non vide".format(sc))
                continue
            for n, imp in enumerate(liste, 1):
                ou = "impacts_imposes[{}] n°{}".format(sc, n)
                if not isinstance(imp, dict):
                    erreurs.append("{} mal formé".format(ou))
                    continue
                var = str(imp.get("variable") or "").strip()
                if var not in VALID_VARS:
                    erreurs.append("{} : variable inconnue {!r}".format(ou, var))
                    continue
                try:
                    force = abs(float(imp.get("delta_level")))
                except (TypeError, ValueError):
                    erreurs.append("{} : delta_level absent ou non numérique".format(ou))
                    continue
                if not 1 <= force <= MAX_DELTA_SIGNAL:
                    erreurs.append("{} : delta_level {:g} hors de 1-{} (plafond d'un signal)"
                                   .format(ou, force, MAX_DELTA_SIGNAL))
                    continue
                try:
                    pol = int(imp.get("polarite"))
                except (TypeError, ValueError):
                    pol = None
                if pol not in (1, -1):
                    erreurs.append("{} : polarite doit valoir 1 ou -1".format(ou))
                    continue
                try:
                    duree = float(imp.get("duree") or 10)
                except (TypeError, ValueError):
                    erreurs.append("{} : duree non numérique".format(ou))
                    continue
                if duree < 1 or duree != int(duree):
                    erreurs.append("{} : duree doit être un nombre entier d'années >= 1".format(ou))
                    continue
                force = int(force) if force == int(force) else force
                v = par_var.setdefault(var, {"delta": force, "scen": {}})
                if v["delta"] != force:
                    erreurs.append("{} : delta_level {:g} différent de {:g} dans un autre scénario "
                                   "(un signal a UNE force par variable)".format(ou, force, v["delta"]))
                    continue
                if sc in v["scen"]:
                    erreurs.append("{} : variable {} présente deux fois dans {}".format(ou, var, sc))
                    continue
                v["scen"][sc] = {"polarite": pol, "duree": int(duree)}
        if par_var and not erreurs:
            for var, v in par_var.items():
                absents = [s for s in SCENARIOS if s not in v["scen"]]
                if absents:
                    erreurs.append("impacts_imposes : la variable {} doit figurer dans les 6 "
                                   "scénarios (manque : {})".format(var, absents))
    date_ok = None
    if date_i is not None:
        try:
            d = float(date_i)
            if d != int(d):
                raise ValueError
            date_ok = int(d)
        except (TypeError, ValueError):
            erreurs.append("date_imposee doit être une année entière")
        if date_ok is not None:
            try:
                ap = int(idea.get("annee_apparition"))
            except (TypeError, ValueError):
                ap = None
            plancher = annee_plancher_bascule(ap)
            if not plancher <= date_ok <= ANNEE_APPARITION_MAX:
                erreurs.append("date_imposee {} hors de {}-{} (plancher de bascule d'un signal)"
                               .format(date_ok, plancher, ANNEE_APPARITION_MAX))
    if via is not None and not isinstance(via, bool):
        erreurs.append("via_matrice_impose doit valoir true ou false")
    if mode is not None and str(mode).strip().lower() != "choc":
        erreurs.append("mode_impose {!r} non pris en charge pour un signal (pas de rupture)".format(mode))
    if erreurs:
        return None, erreurs
    return {"par_var": par_var, "date": date_ok, "via_matrice": via}, []


def _fenetre_imposee(imp, variable_slug, scen):
    """'AAAA-BBBB' pour ce scénario, ou None si la date n'est pas imposée."""
    v = (imp or {}).get("par_var", {}).get(variable_slug)
    if not v or imp.get("date") is None:
        return None
    debut = imp["date"]
    fin = min(debut + v["scen"][scen]["duree"], 2098)
    return "{}-{}".format(debut, fin)


def texte_impositions_signal(imp, variable_slug):
    """Bloc de prompt : ce qui est fixé, pour que le texte raconte ce signal-là."""
    v = (imp or {}).get("par_var", {}).get(variable_slug)
    if not v:
        return ""
    lignes = ["\n⚠️ VALEURS IMPOSÉES (simulateur « et si ? ») -- elles ne se discutent pas, "
              "elles seront rétablies telles quelles après ta réponse :",
              "- delta_level = {} (force, identique dans les 6 scénarios)".format(v["delta"])]
    for sc in SCENARIOS:
        pol = v["scen"][sc]["polarite"]
        sens = "aggrave la crise de {} (niveau qui monte)".format(variable_slug) if pol > 0 \
            else "apaise la crise de {} (niveau qui baisse)".format(variable_slug)
        fen = _fenetre_imposee(imp, variable_slug, sc)
        lignes.append("- [{}] polarite {:+d} : le signal {}{}".format(
            sc, pol, sens, " ; date_bascule = {}".format(fen) if fen else ""))
    lignes.append("Rédige `evolution` et `evenement_cle` de chaque scénario pour qu'ils RACONTENT ce "
                  "sens-là" + (", et place dans chaque `evenement_cle` une année comprise dans la "
                              "fenêtre `date_bascule` de CE scénario." if imp.get("date") is not None
                              else "."))
    if imp.get("date") is not None:
        lignes.append("Les 6 scénarios ont la même fenêtre de départ : c'est voulu, ne la décale pas.")
    return "\n".join(lignes) + "\n"


def appliquer_impositions_signal(develop, imp, variable_slug):
    """Rétablit dans la réponse de l'IA les valeurs imposées (appelé après chaque
    réponse, essai initial et relances, AVANT la validation)."""
    v = (imp or {}).get("par_var", {}).get(variable_slug)
    if not v:
        return
    develop["delta_level"] = v["delta"]
    develop["polarite"] = {sc: v["scen"][sc]["polarite"] for sc in SCENARIOS}
    develop["propagation_via_matrice"] = True if imp.get("via_matrice") is None else imp["via_matrice"]
    if imp.get("date") is None:
        return
    courant = None
    sortie = []
    for ligne in str(develop.get("signal_to_state_yaml") or "").split("\n"):
        m = re.match(r"^\s*(" + "|".join(SCENARIOS) + r"):\s*$", ligne)
        if m:
            courant = m.group(1)
        elif courant and re.match(r"^\s*date_bascule:", ligne):
            indent = ligne[: len(ligne) - len(ligne.lstrip())]
            ligne = "{}date_bascule: {}".format(indent, _fenetre_imposee(imp, variable_slug, courant))
        sortie.append(ligne)
    develop["signal_to_state_yaml"] = "\n".join(sortie)


'''

# (ancre, remplacement) -- chaque ancre doit exister exactement une fois
EDITS = [
    # 1. fonctions neuves, avant step2_develop
    ("def step2_develop(client, idea_text, source, variable_slug, signal_slug, categorie,\n",
     NOUVEAU_BLOC + "def step2_develop(client, idea_text, source, variable_slug, signal_slug, categorie,\n"),
    # 2. signature step2_develop
    ("                   zone_hint=None, annee_apparition=None, interdits=None):\n",
     "                   zone_hint=None, annee_apparition=None, interdits=None,\n"
     "                   impositions_txt=\"\"):\n"),
    # 3. prompt
    ("{zone_hint_txt}{apparition_txt}\n{FORMAT_RULES}",
     "{zone_hint_txt}{apparition_txt}{impositions_txt}\n{FORMAT_RULES}"),
    # 4. validate : signature + contrôle des fenêtres dupliquées
    ("                           annee_apparition=None):\n    \"\"\"Retourne une liste de problèmes",
     "                           annee_apparition=None, fenetres_imposees=False):\n    \"\"\"Retourne une liste de problèmes"),
    ("    for window, scens in new_windows_by_scen.items():\n        if len(scens) > 1:\n",
     "    for window, scens in new_windows_by_scen.items():\n"
     "        # U2a : fenêtre imposée = la même pour les 6 scénarios, voulu\n"
     "        if len(scens) > 1 and not fenetres_imposees:\n"),
    # 5. process_idea : lecture des impositions avant tout appel IA
    ('    print(f"\\n=== {idea_id} ===  (persistance : {persistance}"',
     '    # U2a : valeurs imposées, contrôlées AVANT tout appel IA\n'
     '    imp, erreurs_imp = lire_impositions_signal(idea)\n'
     '    if erreurs_imp:\n'
     '        return {"status": "needs_review", "idea": idea,\n'
     '                "reason": "valeurs imposées invalides : " + " ; ".join(erreurs_imp)}\n'
     '    if imp and not idea.get("reprise"):\n'
     '        variable_hint = list(imp["par_var"])\n'
     '        variable_hint_count = len(variable_hint)\n'
     '\n'
     '    print(f"\\n=== {idea_id} ===  (persistance : {persistance}"'),
    # 6. variables imposées = variables de l'idée
    ('        variables = [v for v in selection["variables"] if v in VALID_VARS]\n',
     '        variables = [v for v in selection["variables"] if v in VALID_VARS]\n'
     '        if imp:  # U2a : les variables sont celles des impacts imposés\n'
     '            variables = list(imp["par_var"])\n'),
    # 7. premier appel step2
    ("                registre_text, sibling_events=sibling_events, zone_hint=zone_hint,\n"
     "                annee_apparition=annee_apparition,\n"
     "            )\n",
     "                registre_text, sibling_events=sibling_events, zone_hint=zone_hint,\n"
     "                annee_apparition=annee_apparition,\n"
     "                impositions_txt=texte_impositions_signal(imp, variable_slug),\n"
     "            )\n"
     "            appliquer_impositions_signal(develop, imp, variable_slug)\n"),
    # 8. validation
    ("                    polarite=develop.get(\"polarite\"),\n"
     "                    annee_apparition=annee_apparition,\n"
     "                )\n",
     "                    polarite=develop.get(\"polarite\"),\n"
     "                    annee_apparition=annee_apparition,\n"
     "                    fenetres_imposees=bool(imp and imp.get(\"date\") is not None),\n"
     "                )\n"),
    # 9. relance step2
    ("                        annee_apparition=annee_apparition, interdits=interdits,\n"
     "                    )\n",
     "                        annee_apparition=annee_apparition, interdits=interdits,\n"
     "                        impositions_txt=texte_impositions_signal(imp, variable_slug),\n"
     "                    )\n"
     "                    appliquer_impositions_signal(develop, imp, variable_slug)\n"),
    # 10. doc du gabarit de queue
    ("#   reprise             : NE PAS REMPLIR À LA MAIN.",
     "#   impacts_imposes     : NE PAS REMPLIR À LA MAIN (posé par « et si ? »). Forces et sens\n"
     "#                         imposés : {scénario: [{variable, delta_level 1-10, polarite 1|-1,\n"
     "#                         duree}]}, les 6 scénarios, mêmes variables, une force par variable.\n"
     "#   date_imposee        : idem. Année de début de la fenêtre, la même dans les 6 scénarios\n"
     "#                         (fin = début + duree). via_matrice_impose : true|false.\n"
     "#   reprise             : NE PAS REMPLIR À LA MAIN."),
    # 11. main : mode --idea
    ("def main():\n    parser = argparse.ArgumentParser()\n"
     "    parser.add_argument(\"--dry-run\", action=\"store_true\",\n"
     "                         help=\"Appelle le LLM et valide, mais n'écrit rien sur disque.\")\n"
     "    args = parser.parse_args()\n",
     "def run_single_idea_mode(client, idea, dry_run, json_output):\n"
     "    \"\"\"U2a : une idée fournie en JSON, hors queue.yaml (même convention que\n"
     "    inject_custom_events.py --idea --json). Trace dans processed/needs_review.\"\"\"\n"
     "    manquants = [f for f in (\"id\", \"description\") if not idea.get(f)]\n"
     "    if manquants:\n"
     "        msg = \"Champs requis manquants : {}\".format(\", \".join(manquants))\n"
     "        print(json.dumps({\"ok\": False, \"error\": msg}, ensure_ascii=False) if json_output\n"
     "              else \"[erreur] \" + msg)\n"
     "        raise SystemExit(1)\n"
     "    try:\n"
     "        outcome = process_idea(client, idea, dry_run=dry_run)\n"
     "    except Exception as e:\n"
     "        outcome = {\"status\": \"needs_review\", \"idea\": idea, \"error\": str(e)}\n"
     "    if dry_run:\n"
     "        if json_output:\n"
     "            print(json.dumps({\"ok\": True, \"dry_run\": True, \"outcome\": outcome},\n"
     "                              ensure_ascii=False, default=str))\n"
     "        else:\n"
     "            print(json.dumps(outcome, ensure_ascii=False, indent=2, default=str))\n"
     "        return\n"
     "    if outcome[\"status\"] == \"injected\":\n"
     "        append_yaml_list(PROCESSED_PATH, outcome, key=\"processed\")\n"
     "    else:\n"
     "        append_yaml_list(NEEDS_REVIEW_PATH, outcome, key=\"needs_review\")\n"
     "    res = outcome.get(\"results\") or []\n"
     "    injectees = [r[\"variable\"] for r in res if r.get(\"status\") == \"injected\"]\n"
     "    echouees = [r[\"variable\"] for r in res if r.get(\"status\") == \"needs_review\"]\n"
     "    if json_output:\n"
     "        print(json.dumps({\n"
     "            \"ok\": True,\n"
     "            \"status\": outcome.get(\"status\"),\n"
     "            \"signal_slug\": (outcome.get(\"selection\") or {}).get(\"signal_slug\"),\n"
     "            \"injected_variables\": injectees,\n"
     "            \"failed_variables\": echouees,\n"
     "            \"reason\": outcome.get(\"reason\") or outcome.get(\"error\"),\n"
     "        }, ensure_ascii=False))\n"
     "    else:\n"
     "        print(\"\\nTerminé : {} variable(s) injectée(s), {} en échec. Voir {} et {}.\".format(\n"
     "            len(injectees), len(echouees), PROCESSED_PATH, NEEDS_REVIEW_PATH))\n"
     "\n\n"
     "def main():\n    parser = argparse.ArgumentParser()\n"
     "    parser.add_argument(\"--dry-run\", action=\"store_true\",\n"
     "                         help=\"Appelle le LLM et valide, mais n'écrit rien sur disque.\")\n"
     "    parser.add_argument(\"--idea\", default=None,\n"
     "                         help=\"Idée unique en JSON (mêmes champs qu'une entrée de queue.yaml, \"\n"
     "                              \"+ impacts_imposes/date_imposee/via_matrice_impose), injectée \"\n"
     "                              \"directement sans passer par la queue.\")\n"
     "    parser.add_argument(\"--json\", action=\"store_true\",\n"
     "                         help=\"Avec --idea : dernière ligne = résultat JSON.\")\n"
     "    args = parser.parse_args()\n"
     "\n"
     "    if args.idea is not None:\n"
     "        try:\n"
     "            idea = json.loads(args.idea)\n"
     "        except json.JSONDecodeError as e:\n"
     "            msg = \"--idea n'est pas un JSON valide : {}\".format(e)\n"
     "            print(json.dumps({\"ok\": False, \"error\": msg}, ensure_ascii=False) if args.json\n"
     "                  else \"[erreur] \" + msg)\n"
     "            sys.exit(1)\n"
     "        if not isinstance(idea, dict):\n"
     "            msg = \"--idea doit être un objet JSON\"\n"
     "            print(json.dumps({\"ok\": False, \"error\": msg}, ensure_ascii=False) if args.json\n"
     "                  else \"[erreur] \" + msg)\n"
     "            sys.exit(1)\n"
     "        client = get_client()\n"
     "        _sigterm_comme_ctrl_c()\n"
     "        run_single_idea_mode(client, idea, dry_run=args.dry_run, json_output=args.json)\n"
     "        return\n"),
]


def main():
    if not F.is_file():
        print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(F))
        return 1
    src = F.read_text(encoding="utf-8")
    if "def lire_impositions_signal" in src:
        print("Déjà appliqué : rien à faire.")
        return 0
    for i, (ancre, _) in enumerate(EDITS, 1):
        n = src.count(ancre)
        if n != 1:
            print("ERREUR : ancre n°{} trouvée {} fois (attendu : 1). Rien modifié.".format(i, n))
            return 1
    print("{} modifications prévues dans {}.".format(len(EDITS), F))
    if "--apply" not in sys.argv:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0
    new = src
    for ancre, rempl in EDITS:
        new = new.replace(ancre, rempl)
    shutil.copy2(F, str(F) + ".bak_u2a")
    F.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(F), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(str(F) + ".bak_u2a", F)
        print("ERREUR de syntaxe, fichier restauré :\n{}".format(e))
        return 1
    print("Appliqué (sauvegarde .bak_u2a). Syntaxe vérifiée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

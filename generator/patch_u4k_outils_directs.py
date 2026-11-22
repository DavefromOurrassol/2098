#!/usr/bin/env python3
"""
patch_u4k_outils_directs.py — Ourrassol 2098 (22 novembre 2026)
===============================================================

B9 « Outils directs » : décision du 22 nov (David). Les deux injecteurs directs
contournaient la porte unique « et si ? » : ils traitaient TOUTE la file, y
compris les entrées adoptées par « et si ? » (probable origine du signal
« adopté, absent de la queue »). La file des entités reste nécessaire aux flux
de maintenance (extract_phantom_slugs.py, enrich_minimal.py, requeue_needs_review.py).

1. gui/scripts_config.json
   - entrées `inject_events` et `inject_signals` retirées (scripts conservés,
     toujours lancés par « et si ? » via et_si_injecter.py) ;
   - `create_entities` devient un outil d'entretien : « Traiter la file des
     entités (fantômes) », mode custom fixe (`--mode custom`), sans formulaire de
     saisie ni modes auto / auto-suggest (qui créaient des entités hors « et si ? ») ;
     la file reste visible en lecture seule.
2. gui/static/app.js : groupe « Outils directs » supprimé du menu ;
   « Traiter la file des entités » rangé dans « Entretien », après
   « Repérer les alliances fantômes ».
3. generator/simuler_et_si.py et generator/appliquer_et_si.py : les nouvelles
   entités de la lecture IA ne renvoient plus vers entites_custom/queue.yaml
   (texte périmé depuis U3be) mais vers l'étape ⑤ (hypothèses d'entité).

Non touché : gui/app.py (routes /api/yaml/append et /api/idees/proposer laissées
en place, sans appelant ; pas de relance de Flask nécessaire).

Tout ou rien : toutes les ancres sont vérifiées avant toute écriture.
Après --apply : Cmd-Maj-R dans le navigateur (app.js) ; scripts_config.json est
relu à chaque requête.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4k_outils_directs.py           # dry-run
    python3 generator/patch_u4k_outils_directs.py --apply   # écrit (.bak_u4k)
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

TAG = "u4k"
CONFIG = Path("gui/scripts_config.json")

TEXTE = {
    Path("gui/static/app.js"): [
        ("menu : groupe des outils directs vidé",
         "const NAV_DIRECTS_U3AP = ['create_entities', 'inject_events', 'inject_signals'];\n",
         "const NAV_DIRECTS_U3AP = [];   // U4k (22 nov 2026) : outils directs retirés ; create_entities -> Entretien\n"),
        ("menu : create_entities rangé dans Entretien",
         "'extract_phantom_slugs', 'requeue_needs_review',",
         "'extract_phantom_slugs', 'create_entities', 'requeue_needs_review',"),
        ("menu : en-tête « Outils directs » retiré",
         "    _navGroupeReplieU3ap(nav, 'directs', 'Outils directs (ancien, avancé)', _navScriptsU3ap(NAV_DIRECTS_U3AP), false);\n",
         "    // U4k : groupe « Outils directs (ancien, avancé) » retiré (porte unique « et si ? »)\n"),
    ],
    Path("generator/simuler_et_si.py"): [
        ("liste d'application : nouvelles entités",
         '''        _etape(E, "Nouvelles entités", f"{len(cons['nouvelles_entites'])} entrée(s) prête(s) (bloc YAML ci-dessous) "
               "pour entites_custom/queue.yaml"
               + (f" — catégorie à choisir pour {sans_cat}" if sans_cat else " — catégorie proposée, à relire"),
               "étape ⑤ du panneau (« Ajouter à la file »), puis python3 generator/create_entities_and_instances.py --mode custom",
               "scenario_hint limite à ce scénario")
''',
         '''        _etape(E, "Nouvelles entités", f"{len(cons['nouvelles_entites'])} entité(s) proposée(s) (bloc ci-dessous)"
               + (f" — catégorie à choisir pour {sans_cat}" if sans_cat else " — catégorie proposée, à relire"),
               "étape ⑤ du panneau (« Lecture IA » : cocher, puis ajouter comme hypothèses d'entité)",
               "chaque entité suit ensuite le parcours « et si ? » : vérifier, adopter, injecter")   # U4k
'''),
        ("rapport : titre du bloc des entités",
         'L += ["Entrées pour `entites_custom/queue.yaml` :", "", "```yaml", _yaml_bloc(entrees), "```", ""]',
         'L += ["Entités proposées (pour mémoire : l\'ajout se fait à l\'étape ⑤, « Lecture IA ») :", "",   # U4k\n'
         '              "```yaml", _yaml_bloc(entrees), "```", ""]'),
    ],
    Path("generator/appliquer_et_si.py"): [
        ("check-list : nouvelles entités",
         '''            case(f"{len(nouv)} entité(s) : choisir `category`, garder ou retirer chaque entrée, coller dans "
                 "`entites_custom/queue.yaml`, puis `python3 generator/create_entities_and_instances.py --mode custom`.")
''',
         '''            case(f"{len(nouv)} entité(s) : les ajouter comme hypothèses d'entité à l'étape ⑤ du panneau "
                 "(« Lecture IA »), puis vérifier, adopter, injecter.")   # U4k
'''),
    ],
}


def nouvelle_config(data):
    """Retourne (data modifiée, messages) ou lève ValueError."""
    ids = [s.get("id") for s in data]
    for attendu in ("create_entities", "inject_events", "inject_signals"):
        if ids.count(attendu) != 1:
            raise ValueError(f"entrée {attendu!r} trouvée {ids.count(attendu)} fois (attendu 1)")
    msgs = []
    data = [s for s in data if s.get("id") not in ("inject_events", "inject_signals")]
    msgs.append("entrées inject_events et inject_signals retirées")
    ce = next(s for s in data if s.get("id") == "create_entities")
    ce["label"] = "Traiter la file des entités (fantômes)"
    ce["icon"] = "👥"
    ce["description"] = (
        "Entretien. Crée les entités en attente dans entites_custom/queue.yaml (alliances fantômes repérées "
        "par « Repérer les alliances fantômes », entités relancées par « Relancer les entités en échec ») "
        "avec leurs instances. Pour ajouter une entité nouvelle au monde, passer par « et si ? » "
        "(Nouvelle hypothèse, type entité) : ce bouton ne sert qu'à vider la file de maintenance.")
    ce.pop("mode_select", None)
    ce["fixed_args"] = ["--mode", "custom"]
    gardees = []
    for o in ce.get("options") or []:
        if o.get("flag") in ("--ancrage-temporel", "--dry-run"):
            o = dict(o)
            o.pop("mode_only", None)
            if o.get("flag") == "--ancrage-temporel":
                o["description"] = str(o.get("description") or "").replace(
                    " Sans effet en mode auto-suggest (ne crée pas d'instances).", "")
            gardees.append(o)
    ce["options"] = gardees
    for cle in ("config_file", "config_fields", "config_fields_mode"):
        ce.pop(cle, None)
    ce["yaml_files"] = [{"path": "entites_custom/queue.yaml",
                         "label": "entites_custom/queue.yaml — file de maintenance (lecture seule)",
                         "readonly": True}]
    msgs.append("create_entities -> « Traiter la file des entités (fantômes) » : --mode custom fixe, "
                "sans formulaire ni modes auto / auto-suggest, file en lecture seule")
    return data, msgs


def main():
    ap = argparse.ArgumentParser(description="Patch U4k : retrait des outils directs.")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon dry-run)")
    args = ap.parse_args()

    fichiers = [CONFIG] + list(TEXTE)
    manquants = [str(f) for f in fichiers if not f.is_file()]
    if manquants:
        sys.exit("✗ introuvable(s) : " + ", ".join(manquants) + " (lancer depuis la racine du vault)")

    a_ecrire, ok = {}, True

    brut = CONFIG.read_text(encoding="utf-8")
    try:
        data = json.loads(brut)
        if not any(s.get("id") == "inject_events" for s in data) and \
                any(s.get("label") == "Traiter la file des entités (fantômes)" for s in data):
            sys.exit("✗ U4k déjà appliqué : rien à faire.")
        data2, msgs = nouvelle_config(data)
        a_ecrire[CONFIG] = json.dumps(data2, indent=2, ensure_ascii=False)
        for m in msgs:
            print(f"✓ {CONFIG} : {m}")
    except ValueError as e:
        print(f"✗ {CONFIG} : {e}")
        ok = False

    for chemin, rempl in TEXTE.items():
        texte = chemin.read_text(encoding="utf-8")
        for nom, ancien, neuf in rempl:
            n = texte.count(ancien)
            if n != 1:
                print(f"✗ {chemin} : {nom} — ancre trouvée {n} fois (attendu 1)")
                ok = False
                continue
            texte = texte.replace(ancien, neuf)
            print(f"✓ {chemin} : {nom}")
        if chemin.suffix == ".py":
            try:
                compile(texte, str(chemin), "exec")
            except SyntaxError as e:
                print(f"✗ {chemin} ne compile plus : {e}")
                ok = False
        a_ecrire[chemin] = texte

    if not ok:
        sys.exit("✗ Patch non appliqué : aucun fichier n'a été modifié.")
    print("✓ Toutes les ancres trouvées ; les fichiers Python patchés compilent.")

    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    for chemin, texte in a_ecrire.items():
        shutil.copy(chemin, chemin.with_name(chemin.name + f".bak_{TAG}"))
        chemin.write_text(texte, encoding="utf-8")
        print(f"→ {chemin} écrit (sauvegarde {chemin.name}.bak_{TAG})")
    print("\nSuite : Cmd-Maj-R dans le navigateur (app.js). Pas de relance de Flask.")


if __name__ == "__main__":
    main()

"""
patch_s26_liste_zones_journal.py — S26 (6 octobre 2026), liste déroulante
------------------------------------------------------------------------
Remplace le champ texte « Journal d'une autre zone » (generate.py, mode
Forcer) par une liste déroulante.

gui/app.py
  - /api/slugs : nouveau type « zones_journal_forcer ». Paramètres : slug et
    element_type (l'élément forcé), ligne (ligne éditoriale). Liste les zones
    ayant une rédaction pour cette ligne, dans les scénarios où l'élément
    existe. Libellé : « Nom de la zone — Nom du journal (scénario) ».

gui/scripts_config.json
  - --forcer-zone-journal : type slug_select, rechargé quand l'élément, son
    type ou la ligne éditoriale changent.

Usage (depuis la racine du vault) :
    python3 generator/patch_s26_liste_zones_journal.py          # aperçu
    python3 generator/patch_s26_liste_zones_journal.py --apply  # écrit (.bak_s26_liste)
Refuse un second passage.
"""

import json
import os
import shutil
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(RACINE, "gui", "app.py")
CFG = os.path.join(RACINE, "gui", "scripts_config.json")
MARQUEUR = "zones_journal_forcer"

ANCRE = '        elif slug_type == "zones_candidates_oral":\n'
NOUVEAU = (
    '        elif slug_type == "zones_journal_forcer":\n'
    '            # S26 (6 octobre 2026) : liste du champ « Journal d\'une autre\n'
    '            # zone » (generate.py --forcer-zone-journal, mode Forcer). Zones\n'
    '            # ayant une rédaction pour la ligne choisie, dans les scénarios\n'
    '            # où l\'élément forcé existe. Valeur = slug de zone ; vide (option\n'
    '            # par défaut du menu) = journal de la zone de l\'élément.\n'
    '            forcer_type = (request.args.get("element_type") or request.args.get("forcer_type") or "")\n'
    '            slug_element = request.args.get("slug", "")\n'
    '            ligne_j = request.args.get("ligne") or "pro_pouvoir"\n'
    '            if ligne_j not in ("pro_pouvoir", "opposition"):\n'
    '                ligne_j = "pro_pouvoir"\n'
    '            if not forcer_type or not slug_element:\n'
    '                return jsonify({"slugs": [], "labels": {}})\n'
    '            code = (\n'
    '                "import sys, json; sys.path.insert(0, \'.\'); import loader; "\n'
    '                "print(json.dumps(loader.scenarios_disponibles_pour_element({!r}, {!r})))"\n'
    '            ).format(forcer_type, slug_element)\n'
    '            resultat = subprocess.run(\n'
    '                [sys.executable, "-c", code], cwd=pipeline_dir,\n'
    '                capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL,\n'
    '            )\n'
    '            if resultat.returncode != 0:\n'
    '                return jsonify({"slugs": [], "error": resultat.stderr.strip()[-500:]})\n'
    '            try:\n'
    '                dispo = json.loads(resultat.stdout.strip())\n'
    '            except json.JSONDecodeError:\n'
    '                dispo = []\n'
    '            import yaml as _yaml\n'
    '            try:\n'
    '                jx = _yaml.safe_load((pipeline_dir / "journaux.yaml").read_text(encoding="utf-8")) or {}\n'
    '            except Exception:\n'
    '                jx = {}\n'
    '            vus = {}\n'
    '            for sc in dispo:\n'
    '                zones_j = (((jx.get(sc) or {}).get(ligne_j) or {}).get("zones") or {})\n'
    '                noms = {z["slug"]: z["nom"] for z in _scan_zone_slugs_hier(vault_root, sc)}\n'
    '                for zs in zones_j:\n'
    '                    if zs in vus:\n'
    '                        vus[zs]["scenarios"].append(sc)\n'
    '                        continue\n'
    '                    vus[zs] = {"nom": noms.get(zs, zs.replace("_", " ")),\n'
    '                               "journal": ((zones_j.get(zs) or {}).get("nom") or ""),\n'
    '                               "scenarios": [sc]}\n'
    '            ordre = sorted(vus, key=lambda s: (vus[s]["scenarios"][0], vus[s]["nom"].lower()))\n'
    '            labels = {\n'
    '                s: "{} — {} ({})".format(vus[s]["nom"], vus[s]["journal"], ", ".join(vus[s]["scenarios"]))\n'
    '                if vus[s]["journal"] else "{} ({})".format(vus[s]["nom"], ", ".join(vus[s]["scenarios"]))\n'
    '                for s in ordre\n'
    '            }\n'
    '            return jsonify({"slugs": ordre, "labels": labels})\n'
) + ANCRE


def main():
    apply = "--apply" in sys.argv
    ok = True

    texte = open(APP, encoding="utf-8").read()
    if MARQUEUR in texte:
        print("✗ gui/app.py : déjà patché (« {} » présent).".format(MARQUEUR))
        ok = False
    elif texte.count(ANCRE) != 1:
        print("✗ gui/app.py : ancre trouvée {} fois (attendu 1).".format(texte.count(ANCRE)))
        ok = False
    else:
        texte = texte.replace(ANCRE, NOUVEAU)
        try:
            compile(texte, "app.py", "exec")
        except SyntaxError as e:
            print("✗ gui/app.py : erreur de syntaxe après patch ({}).".format(e))
            ok = False
        else:
            print("✓ gui/app.py : branche zones_journal_forcer")

    cfg = json.load(open(CFG, encoding="utf-8"))
    gen = next((s for s in cfg if s.get("id") == "generate"), None)
    opt = next((o for o in (gen or {}).get("options", []) if o.get("flag") == "--forcer-zone-journal"), None)
    if opt is None:
        print("✗ scripts_config.json : option --forcer-zone-journal introuvable.")
        ok = False
    elif opt.get("type") == "slug_select":
        print("✗ scripts_config.json : déjà en liste déroulante.")
        ok = False
    else:
        opt["type"] = "slug_select"
        opt["slug_type"] = "zones_journal_forcer"
        opt["slug_extra_params"] = {
            "slug": "--forcer-slug",
            "element_type": "--forcer-type",
            "ligne": "--ligne-editoriale",
        }
        opt.pop("placeholder", None)
        opt["description"] = (
            "Vide = le journal de la zone de l'élément écrit (comportement habituel). "
            "Sinon, choisis le journal qui couvre l'élément comme un fait étranger, vu "
            "depuis sa zone (regard local, sources à distance). La liste montre les zones "
            "qui ont une rédaction pour la ligne éditoriale choisie, dans les scénarios où "
            "l'élément existe ; elle se recharge quand l'élément ou la ligne change. Seuls "
            "les scénarios où cette zone a une rédaction sont traités, et l'article est "
            "rangé sous la zone du journal sur le site."
        )
        print("✓ scripts_config.json : --forcer-zone-journal en liste déroulante")

    if not ok:
        print("\nRien écrit.")
        sys.exit(1)
    if not apply:
        print("\nAperçu seulement — relancer avec --apply pour écrire.")
        return

    shutil.copy2(APP, APP + ".bak_s26_liste")
    open(APP, "w", encoding="utf-8").write(texte)
    shutil.copy2(CFG, CFG + ".bak_s26_liste")
    json.dump(cfg, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("✓ écrit (sauvegardes .bak_s26_liste) — redémarre Flask.")


if __name__ == "__main__":
    main()

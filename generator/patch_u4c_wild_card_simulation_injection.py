#!/usr/bin/env python3
"""
patch_u4c_wild_card_simulation_injection.py — Ourrassol 2098 (U4c, 15 novembre 2026)
====================================================================================

Wild cards, deuxième morceau (après U4a ; U4b abandonné) : étape ① et injection.

  1. Simulation (simuler_et_si.py) : pour une wild card, la lecture IA et la Passe
     exhaustive sont FORCÉES (cochées ou non dans le panneau).
  2. Règles de lore (simuler_et_si.py) : avant la simulation, un appel IA par scénario
     (en cache) vérifie que la wild card ne contredit AUCUNE règle de
     documentation/lore_regles.yaml (section du scénario + _tous, zones en
     quarantaine comprises). Une règle contredite = erreur bloquante, rien n'est simulé.
  3. Fiches et tendances : la lecture IA et la Passe exhaustive sont prévenues qu'une
     wild card a le droit de les contredire ; ce qu'elle rend faux devient une
     correction (obligatoire) au lieu d'être atténué.
  4. Adoption (et_si_dossiers.py) : refusée si la dernière simulation d'une wild card
     n'a pas eu de Passe exhaustive.
  5. Injection (simuler_et_si.py, inject_custom_events.py) : l'entrée porte
     `wild_card_impose: true` ; forces acceptées jusqu'à 35 ; la fiche d'événement
     reçoit `wild_card: true` ; le récit est prévenu que l'événement se produit.

USAGE (depuis la racine du vault)
    python3 generator/patch_u4c_wild_card_simulation_injection.py            # dry-run
    python3 generator/patch_u4c_wild_card_simulation_injection.py --apply
Sauvegardes : <fichier>.bak_u4c ; syntaxe vérifiée sur copie avant écriture, retour
arrière automatique en cas d'échec. Exige U4a.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

VAULT = Path.cwd()
GEN = VAULT / "generator"
TAG = "U4c"

# ---------------------------------------------------------------------------
# simuler_et_si.py
# ---------------------------------------------------------------------------

SE = [
    ("lecture IA : consigne wild card",
     '''    if hyp.get("mode") == "rupture":
        nature = "MODE RUPTURE (déplacement permanent de l'équilibre du scénario)"
''',
     '''    if hyp.get("wild_card"):   # U4c
        bloc_contraintes += ("WILD CARD : rupture improbable voulue par l'auteur. Elle a le droit d'aller contre "
                             "la logique et les tendances du scénario : ne l'atténue pas pour la rendre "
                             "vraisemblable, décris le bouleversement qu'elle provoque.\\n")
    if hyp.get("mode") == "rupture":
        nature = "MODE RUPTURE (déplacement permanent de l'équilibre du scénario)"
'''),
    ("contrôle des règles de lore",
     '''def _decider(args, hyps):
''',
     '''# U4c (15 nov 2026) : une wild card ne contredit jamais une règle de lore.
LORE_REGLES_PATH = VAULT_ROOT / "documentation" / "lore_regles.yaml"
CACHE_LORE_U4C = SCRIPT_DIR / "state" / "et_si_regles_lore.json"
VERSION_LORE_U4C = "1"


def regles_lore_scenario(sc):
    """U4c : [(id, message)] des règles de lore valables pour `sc` (section `_tous` + section
    du scénario, zones en quarantaine comprises). None si le fichier est illisible."""
    try:
        data = yaml.safe_load(LORE_REGLES_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    out = []
    for cle in ("_tous", sc):
        sec = data.get(cle) if isinstance(data, dict) else None
        if not isinstance(sec, dict):
            continue
        for r in sec.get("regles") or []:
            if isinstance(r, dict) and str(r.get("message") or "").strip():
                out.append((str(r.get("id") or "?"), " ".join(str(r["message"]).split())))
        for z in sec.get("zones_quarantaine") or []:
            if isinstance(z, dict) and str(z.get("message") or "").strip():
                out.append((f"quarantaine_{z.get('zone')}", " ".join(str(z["message"]).split())))
    return out


def controle_regles_lore(hyp, scenarios, refaire=False):
    """U4c : un appel IA par scénario qui a des règles (en cache). Retourne (erreurs, infos).
    Un appel en échec est une erreur : la wild card n'est simulée qu'une fois contrôlée."""
    import hashlib
    import re as _re
    from llm_client import call_llm
    erreurs, infos = [], []
    try:
        cache = json.loads(CACHE_LORE_U4C.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    elem = (f"{hyp['nom']} — {_date_lisible_u3ad(hyp['date'])}.\\n{hyp.get('description') or ''}"
            + "".join(f"\\n- fait imposé : {c}" for c in hyp.get("contraintes") or []))
    for sc in scenarios:
        regles = regles_lore_scenario(sc)
        if regles is None:
            erreurs.append("documentation/lore_regles.yaml illisible : contrôle des règles de lore impossible")
            break
        if not regles:
            infos.append(f"{sc} : aucune règle de lore à contrôler")
            continue
        liste = "\\n".join(f"[r{n}] {m}" for n, (_, m) in enumerate(regles, 1))
        user = f"""ÉLÉMENT (wild card, scénario {sc}) : rupture improbable voulue par l'auteur. Elle a le droit de
contredire les fiches et les tendances du monde, mais JAMAIS une règle de lore.
{elem}

RÈGLES DE LORE DU SCÉNARIO (choix de l'auteur, intouchables) :
{liste}

TÂCHE : relève UNIQUEMENT les règles que l'élément contredit, c'est-à-dire que, une fois l'élément ajouté au
lore, ce que la règle établit devient faux (l'élément fait exister ce que la règle dit disparu, donne à un
acteur ce que la règle lui refuse, rétablit ce que la règle dit perdu…). Une règle sans rapport avec
l'élément, ou qu'il laisse vraie, n'est pas contredite. En cas de doute, ne la relève pas : la réponse
attendue est souvent une liste vide.
Réponds UNIQUEMENT en JSON : {{"contredites": [{{"id": "r2", "explication": "une phrase"}}]}}"""
        cle = f"{hyp['id']}::{sc}"
        emp = hashlib.sha1((VERSION_LORE_U4C + user).encode("utf-8")).hexdigest()[:16]
        entree = cache.get(cle) or {}
        brut = entree.get("brut") if (not refaire and entree.get("empreinte") == emp) else None
        if not isinstance(brut, dict):
            try:
                texte = call_llm(system_prompt="Tu vérifies qu'un élément fictif respecte les règles d'auteur "
                                 "d'un monde. Tu réponds uniquement en JSON.",
                                 user_prompt=user, max_tokens=1200, temperature=0.0, task_tier="structured_strict")
                brut = _extraire_json(texte)
            except Exception as e:  # noqa: BLE001
                erreurs.append(f"{sc} : contrôle des règles de lore impossible ({type(e).__name__}: {e}) : "
                               f"relancer la simulation")
                continue
            cache[cle] = {"empreinte": emp, "date": datetime.now().isoformat(timespec="minutes"), "brut": brut}
            try:
                CACHE_LORE_U4C.parent.mkdir(parents=True, exist_ok=True)
                CACHE_LORE_U4C.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            except OSError:
                pass
        n_c = 0
        for c in (brut.get("contredites") or []) if isinstance(brut, dict) else []:
            m = _re.fullmatch(r"r(\\d+)", str((c or {}).get("id") or "").strip()) if isinstance(c, dict) else None
            if not m or not 1 <= int(m.group(1)) <= len(regles):
                continue
            rid, msg = regles[int(m.group(1)) - 1]
            expl = " ".join(str(c.get("explication") or "").split())
            erreurs.append(f"{sc} : la wild card contredit la règle de lore `{rid}` — {expl or msg}")
            n_c += 1
        infos.append(f"{sc} : {len(regles)} règle(s) de lore contrôlée(s), {n_c} contredite(s)")
    return erreurs, infos


def _decider(args, hyps):
'''),
    ("simulation : passe forcée et règles de lore",
     '''        sys.exit(f"✗ --date {args.date:g} antérieure à l'apparition de l'hypothèse ({hyp['date']:g}).")

    resultats = simuler_hypothese(hyp, args.date, [args.scenario] if args.scenario else None)
''',
     '''        sys.exit(f"✗ --date {args.date:g} antérieure à l'apparition de l'hypothèse ({hyp['date']:g}).")
    if hyp.get("wild_card"):   # U4c : lecture IA + Passe exhaustive forcées, règles de lore contrôlées
        if not (args.consequences_ia and args.passe_exhaustive):
            print("ℹ wild card : lecture IA et Passe exhaustive lancées d'office (payant)", file=sys.stderr)
        args.consequences_ia = args.passe_exhaustive = True
        err_lore, infos_lore = controle_regles_lore(hyp, [args.scenario] if args.scenario else hyp["scenarios"],
                                                    refaire=args.refaire)
        for i in infos_lore:
            print(f"ℹ règles de lore — {i}", file=sys.stderr)
        if err_lore:
            print(f"✗ Wild card {args.id!r} refusée, simulation non lancée : une wild card peut contredire "
                  "les fiches et les tendances, jamais une règle de lore.")
            for e in err_lore:
                print(f"  - {e}")
            sys.exit(1)

    resultats = simuler_hypothese(hyp, args.date, [args.scenario] if args.scenario else None)
'''),
    ("entrée d'injection",
     '''        entree["mode_impose"] = "rupture"   # PATCH_S19_CHAINE : écrit `mode: rupture` dans les fiches
''',
     '''        entree["mode_impose"] = "rupture"   # PATCH_S19_CHAINE : écrit `mode: rupture` dans les fiches
    if hyp.get("wild_card"):   # U4c : forces jusqu'à WILD_CARD_FORCE[1], `wild_card: true` dans les fiches
        entree["wild_card_impose"] = True
'''),
    ("entrée d'injection : plafond",
     '''        trop_fort = [f"{i['variable']} ({i['force']:g})" for i in hyp["impacts"] if i["force"] > DELTA_MAX_CONSEILLE]
''',
     '''        plafond_u4c = WILD_CARD_FORCE[1] if hyp.get("wild_card") else DELTA_MAX_CONSEILLE   # U4c
        trop_fort = [f"{i['variable']} ({i['force']:g})" for i in hyp["impacts"] if i["force"] > plafond_u4c]
'''),
]

# ---------------------------------------------------------------------------
# et_si_exhaustif.py
# ---------------------------------------------------------------------------

EX = [
    ("passe : consigne wild card",
     '''        contraintes = ("FAITS À RESPECTER :\\n" + "\\n".join(f"- {c}" for c in hyp["contraintes"]) + "\\n")
    deja = []
''',
     '''        contraintes = ("FAITS À RESPECTER :\\n" + "\\n".join(f"- {c}" for c in hyp["contraintes"]) + "\\n")
    if hyp.get("wild_card"):   # U4c
        contraintes += ("WILD CARD : rupture improbable voulue par l'auteur ; elle a le droit de contredire les "
                        "fiches et les tendances du scénario. Une fiche qu'elle rend fausse est à corriger "
                        "(obligatoire) : ne l'écarte pas parce que l'élément te semble invraisemblable dans "
                        "ce monde.\\n")
    deja = []
'''),
]

# ---------------------------------------------------------------------------
# et_si_dossiers.py
# ---------------------------------------------------------------------------

DO = [
    ("adoption : passe exigée",
     '''    if not sim.get("complet"):
        raise DossierErreur(f"la dernière simulation de {hid} est limitée à''',
     '''    if str(brut.get("wild_card")).strip().lower() in ("true", "oui", "yes", "1") and not sim.get("passe"):   # U4c
        raise DossierErreur(f"{hid} est une wild card : sa dernière simulation doit comporter la Passe "
                            f"exhaustive (la relancer).")
    if not sim.get("complet"):
        raise DossierErreur(f"la dernière simulation de {hid} est limitée à'''),
]

# ---------------------------------------------------------------------------
# inject_custom_events.py
# ---------------------------------------------------------------------------

IN = [
    ("plafond wild card",
     '''MAX_DELTA_LEVEL = 25  # delta_level absolu maximum jugé raisonnable par variable
''',
     '''MAX_DELTA_LEVEL = 25  # delta_level absolu maximum jugé raisonnable par variable
WILD_CARD_FORCE_MAX = 35  # U4c : plafond d'une wild card (simuler_et_si.WILD_CARD_FORCE)
'''),
    ("validation : plafond paramétré",
     '''def validate_instance(instance_data, variables, scenario, registre_text, available_actors):
''',
     '''def validate_instance(instance_data, variables, scenario, registre_text, available_actors,
                      max_delta=MAX_DELTA_LEVEL):   # U4c
'''),
    ("validation : test du plafond",
     '''        if abs(delta) > MAX_DELTA_LEVEL:
            issues.append(
                f"[{var}] delta_level={delta} hors plage raisonnable "
                f"(0 à {MAX_DELTA_LEVEL})"
            )
''',
     '''        if abs(delta) > max_delta:   # U4c
            issues.append(
                f"[{var}] delta_level={delta} hors plage raisonnable "
                f"(0 à {max_delta})"
            )
'''),
    ("fiche : ligne wild_card",
     '''        mode_ligne="\\nmode: rupture" if instance_data.get("mode") == "rupture" else "",
''',
     '''        mode_ligne=("\\nmode: rupture" if instance_data.get("mode") == "rupture" else "")
        + ("\\nwild_card: true" if instance_data.get("wild_card") else ""),   # U4c
'''),
    ("impositions : lecture",
     '''    mode = idea.get("mode_impose")   # PATCH_S19_CHAINE : choc | rupture
''',
     '''    mode = idea.get("mode_impose")   # PATCH_S19_CHAINE : choc | rupture
    wild = idea.get("wild_card_impose") is True   # U4c
    plafond = WILD_CARD_FORCE_MAX if wild else MAX_DELTA_LEVEL
'''),
    ("impositions : plafond",
     '''                if not 1 <= force <= MAX_DELTA_LEVEL:
                    erreurs.append(f"{ou} : delta_level {force:g} hors de 1-{MAX_DELTA_LEVEL}")
''',
     '''                if not 1 <= force <= plafond:   # U4c
                    erreurs.append(f"{ou} : delta_level {force:g} hors de 1-{plafond}")
'''),
    ("impositions : cohérence et retour",
     '''    if erreurs:
        return None, erreurs
    return {"impacts": impacts, "date": date, "via_matrice": via, "mode": mode}, []
''',
     '''    if wild and mode != "rupture":   # U4c
        erreurs.append("wild_card_impose sans mode_impose: rupture (une wild card est une rupture)")
    if erreurs:
        return None, erreurs
    return {"impacts": impacts, "date": date, "via_matrice": via, "mode": mode, "wild_card": wild}, []
'''),
    ("impositions : application",
     '''        instance_data["mode"] = imp["mode"]   # PATCH_S19_CHAINE, écrit par write_instance_file()
''',
     '''        instance_data["mode"] = imp["mode"]   # PATCH_S19_CHAINE, écrit par write_instance_file()
    if imp.get("wild_card"):   # U4c, écrit par write_instance_file()
        instance_data["wild_card"] = True
'''),
    ("impositions : consigne du récit",
     '''    lignes.append("Écris la réalisation, la description et les conséquences pour qu'elles "
                  "correspondent à ces valeurs (ampleur, sens et date).")
''',
     '''    if imp.get("wild_card"):   # U4c
        lignes.append("- WILD CARD : événement improbable voulu par l'auteur. Il SE PRODUIT dans ce scénario "
                      "(impossible_dans_scenario : false), même s'il va contre la logique du monde : raconte-le "
                      "pleinement, sans l'atténuer pour le rendre vraisemblable")
    lignes.append("Écris la réalisation, la description et les conséquences pour qu'elles "
                  "correspondent à ces valeurs (ampleur, sens et date).")
'''),
    ("validation : appel",
     '''                issues = validate_instance(
                    instance_data, variables, scenario, registre_text, available_actors
                )
''',
     '''                issues = validate_instance(
                    instance_data, variables, scenario, registre_text, available_actors,
                    max_delta=(WILD_CARD_FORCE_MAX if idea.get("wild_card_impose") is True
                               else MAX_DELTA_LEVEL),   # U4c
                )
'''),
]

FICHIERS = [(GEN / "simuler_et_si.py", SE), (GEN / "et_si_exhaustif.py", EX),
            (GEN / "et_si_dossiers.py", DO), (GEN / "inject_custom_events.py", IN)]


def main():
    a = argparse.ArgumentParser(description="U4c : wild cards, simulation et injection.")
    a.add_argument("--apply", action="store_true")
    x = a.parse_args()
    if not GEN.is_dir():
        sys.exit("✗ lancer depuis la racine du vault (dossier generator/ introuvable)")
    nouveaux, erreurs = {}, []
    se_txt = (GEN / "simuler_et_si.py").read_text(encoding="utf-8") if (GEN / "simuler_et_si.py").exists() else ""
    if "WILD_CARD_FORCE" not in se_txt:
        erreurs.append("U4a absent de simuler_et_si.py : appliquer d'abord patch_u4a_wild_card_controles.py")
    for chemin, remp in FICHIERS:
        if not chemin.exists():
            erreurs.append(f"{chemin.relative_to(VAULT)} introuvable")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if f"# {TAG}" in texte:
            erreurs.append(f"{chemin.name} : {TAG} déjà appliqué")
            continue
        for libelle, avant, apres in remp:
            n = texte.count(avant)
            if n != 1:
                erreurs.append(f"{chemin.name} [{libelle}] : passage trouvé {n} fois (attendu 1)")
                continue
            texte = texte.replace(avant, apres)
        nouveaux[chemin] = texte
    if erreurs:
        print("✗ Rien n'est écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    for chemin, neuf in nouveaux.items():
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(neuf)
        try:
            py_compile.compile(f.name, doraise=True)
        except py_compile.PyCompileError as e:
            sys.exit(f"✗ {chemin.name} : syntaxe invalide après patch, rien n'est écrit\n{e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    for chemin, remp in FICHIERS:
        print(f"{chemin.relative_to(VAULT)} : {len(remp)} modification(s)")
        for libelle, _, _ in remp:
            print(f"  · {libelle}")
    if not x.apply:
        print("\nDRY-RUN : syntaxe vérifiée sur copie, rien n'est écrit. Relancer avec --apply.")
        return
    faits = []
    try:
        for chemin, neuf in nouveaux.items():
            shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_u4c"))
            chemin.write_text(neuf, encoding="utf-8")
            faits.append(chemin)
            py_compile.compile(str(chemin), doraise=True)
    except Exception as e:  # noqa: BLE001 -- retour arrière complet
        for chemin in faits:
            shutil.copy2(chemin.with_name(chemin.name + ".bak_u4c"), chemin)
        sys.exit(f"✗ échec ({type(e).__name__}: {e}) : fichiers restaurés depuis .bak_u4c")
    print("\n✓ U4c appliqué (sauvegardes .bak_u4c). Aucun redémarrage de Flask nécessaire "
          "(scripts appelés en sous-processus).")


if __name__ == "__main__":
    main()

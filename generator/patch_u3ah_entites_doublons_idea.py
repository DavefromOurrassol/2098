#!/usr/bin/env python3
"""
patch_u3ah_entites_doublons_idea.py — Ourrassol 2098 (14 novembre 2026)

Patch de generator/create_entities_and_instances.py (U3ah) :

  1. Slug déjà pris -> refus mécanique (mode custom). Avant : seul le
     jugement de l'IA ("doublon_detecte") protégeait ; un nom identique à une
     entité existante pouvait réécrire entites/<slug>.md et remplacer son
     entrée du registre. Maintenant : needs_review, AVANT tout appel IA.
  2. "doublon_detecte" n'est plus corrigeable par retry : l'idée part en
     needs_review avec le doublon_slug (avant, la correction pouvait remettre
     le drapeau à faux).
  3. Mode --idea '<json>' [--json] : traite UNE idée sans lire ni écrire
     queue.yaml (comme inject_custom_events.py --idea). Dernière ligne de
     sortie avec --json : un objet JSON de résultat.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3ah_entites_doublons_idea.py            # aperçu
    python3 generator/patch_u3ah_entites_doublons_idea.py --apply    # écrit

Sauvegarde .bak_u3ah ; refuse un second passage ; py_compile après écriture
(restauration automatique en cas d'échec).
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

MARQUEUR = "U3ah"
CIBLE_DEFAUT = Path("generator/create_entities_and_instances.py")

# --------------------------------------------------------------------------
# Remplacements : (nom, ancre unique, remplacement)
# --------------------------------------------------------------------------

HELPER = '''def _slug_deja_pris_u3ah(nom):
    """U3ah (14 nov 2026) : refus mécanique d'un nom dont le slug existe déjà
    (fichier entites/<slug>.md ou entrée du registre _entities_list.json).
    Retourne le motif (str) ou None. Aucun appel IA."""
    slug = slugify(str(nom or ""))
    if not slug:
        return "nom vide ou inutilisable (slug vide)"
    if (ENTITES_DIR / f"{slug}.md").exists():
        return (f"Slug '{slug}' déjà utilisé : entites/{slug}.md existe "
                f"(pour ajouter des instances à une entité existante, "
                f"utiliser generate_instances.py)")
    for e in load_entities_list():
        if e.get("slug") == slug:
            return (f"Slug '{slug}' déjà présent dans le registre "
                    f"entites/_entities_list.json")
    return None


'''

BLOC_SLUG = '''    # U3ah : slug déjà pris -> refus avant tout appel IA
    _motif_slug = _slug_deja_pris_u3ah(nom)
    if _motif_slug:
        print(f"  ✗ Rejetée : {_motif_slug}")
        return {"status": "needs_review", "idea": idea, "reason": _motif_slug}

'''

BLOC_DOUBLON = '''        if archetype.get("doublon_detecte"):
            # U3ah : un doublon signalé n'est pas corrigeable par retry
            print(f"  -> doublon signalé ({archetype.get('doublon_slug')!r}) : "
                  f"pas de nouvelle tentative, idée à relire")
            break
'''

FONCTION_IDEE = '''def run_idea_mode_u3ah(client, idea_json, dry_run, ancrage_temporel, sortie_json):
    """U3ah : traite UNE idée donnée en JSON, sans lire ni écrire queue.yaml.
    Code de sortie : 0 = entité injectée (ou simulée), 1 = refusée / à relire,
    2 = argument illisible. Avec sortie_json : dernière ligne = résumé JSON."""
    try:
        idea = json.loads(idea_json)
    except json.JSONDecodeError as e:
        print(f"✗ --idea : JSON illisible ({e})")
        return 2
    if not isinstance(idea, dict):
        print("✗ --idea : un objet JSON est attendu (une idée au format d'une "
              "entrée de queue.yaml)")
        return 2
    try:
        outcome = process_custom_idea(client, idea, dry_run=dry_run,
                                       ancrage_temporel=ancrage_temporel)
    except Exception as e:
        print(f"  ✗ Exception : {e}")
        outcome = {"status": "needs_review", "idea": idea, "error": str(e)}
    ok = outcome.get("status") == "injected"
    stats = outcome.get("instance_stats") or {}
    if ok and not dry_run and stats.get("created", 0) > 0:
        run_post_injection_cycle()
    if sortie_json:
        resume = {
            "status": outcome.get("status"),
            "slug": outcome.get("slug"),
            "scenarios": outcome.get("scenarios"),
            "instance_stats": stats,
            "issues": outcome.get("issues"),
            "reason": outcome.get("reason"),
            "error": outcome.get("error"),
            "dry_run": bool(dry_run),
        }
        print(json.dumps(resume, ensure_ascii=False, default=str))
    return 0 if ok else 1


'''

ARGS_IDEA = '''    parser.add_argument(
        "--idea", default=None,
        help="U3ah : une idée d'entité au format JSON (champs d'une entrée de "
             "queue.yaml). Traitée seule, sans lire ni écrire la file. Remplace --mode."
    )
    parser.add_argument(
        "--json", action="store_true",
        help="U3ah : avec --idea, dernière ligne de sortie = résumé JSON."
    )
'''

BRANCHE_IDEE = '''    if args.idea:   # U3ah
        sys.exit(run_idea_mode_u3ah(client, args.idea, args.dry_run,
                                    args.ancrage_temporel, args.json))

'''

ANCRE_SCENARIO_REF = (
    '        reason = f"scenario_ref invalide : {scenario_ref!r}"\n'
    '        print(f"  ✗ Rejetée : {reason}")\n'
    '        return {"status": "needs_review", "idea": idea, "reason": reason}\n'
)
ANCRE_DEF_CUSTOM = 'def process_custom_idea(client, idea, dry_run=False, ancrage_temporel="libre"):\n'
ANCRE_RETRY = (
    '        if attempt < MAX_FIX_ATTEMPTS:\n'
    '            archetype = step_custom_derive_archetype(\n'
    '                client, idea, existing_entities, previous=archetype, issues=issues\n'
    '            )\n'
)
ANCRE_DEF_MAIN = 'def main():\n    parser = argparse.ArgumentParser(\n'
ANCRE_PARSE = '    args = parser.parse_args()\n'
ANCRE_MODE = '    mode = args.mode\n    if mode is None:\n'

REMPLACEMENTS = [
    ("helper slug", ANCRE_DEF_CUSTOM, HELPER + ANCRE_DEF_CUSTOM),
    ("refus slug pris", ANCRE_SCENARIO_REF, ANCRE_SCENARIO_REF + "\n" + BLOC_SLUG.rstrip("\n") + "\n"),
    ("doublon sans retry", ANCRE_RETRY, BLOC_DOUBLON + ANCRE_RETRY),
    ("fonction --idea", ANCRE_DEF_MAIN, FONCTION_IDEE + ANCRE_DEF_MAIN),
    ("arguments --idea/--json", ANCRE_PARSE, ARGS_IDEA + ANCRE_PARSE),
    ("branche --idea", ANCRE_MODE, BRANCHE_IDEE + ANCRE_MODE),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="écrit (sinon aperçu)")
    ap.add_argument("--fichier", default=str(CIBLE_DEFAUT))
    args = ap.parse_args()

    cible = Path(args.fichier)
    if not cible.exists():
        print(f"✗ Fichier introuvable : {cible} (lancer depuis la racine du vault)")
        return 2
    texte = cible.read_text(encoding="utf-8")

    if MARQUEUR in texte:
        print(f"✗ {MARQUEUR} déjà appliqué dans {cible} — refus d'un second passage.")
        return 1

    nouveau = texte
    for nom, ancre, remplacement in REMPLACEMENTS:
        n = nouveau.count(ancre)
        if n != 1:
            print(f"✗ Ancre « {nom} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
            return 1
        nouveau = nouveau.replace(ancre, remplacement, 1)
        print(f"  ✓ {nom}")

    if not args.apply:
        print(f"\nAperçu seulement : {len(texte.splitlines())} -> "
              f"{len(nouveau.splitlines())} lignes. Relancer avec --apply pour écrire.")
        return 0

    bak = cible.with_name(cible.name + ".bak_u3ah")
    shutil.copy2(cible, bak)
    cible.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(cible), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, cible)
        print(f"✗ py_compile a échoué, fichier restauré : {e}")
        return 1
    print(f"\n✓ Écrit : {cible} (sauvegarde : {bak.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

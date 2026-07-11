#!/usr/bin/env python3
"""
fix_impact_scale.py — Ourrassol 2098
=======================================

Corrige rétroactivement les fiches instances/*.md dont impact_local et/ou
impact_systemique_global sont hors de l'échelle attendue [0-5] — résidu de
l'ancien generate_entities.py qui ne précisait pas l'échelle dans son
prompt (voir le même bug corrigé dans generate_instances.py le 2026-06-20).

Pour chaque fiche concernée, envoie son contenu existant (description,
rôle, responsabilités, tensions narratives, contexte scénario) au LLM et
lui demande de JUGER deux entiers 0-5 cohérents avec ce qui est déjà écrit
— pas de réécriture du reste de la fiche, seulement ces deux lignes.

Passe par llm_client.py (tier "structured_strict") — voir TASK_TIER_DEFAULTS
dans llm_client.py pour le modèle utilisé par défaut. LLM_PROVIDER/LLM_MODEL
restent disponibles en override manuel total si besoin d'un test ponctuel.

PRÉREQUIS
    pip install mistralai anthropic openai pyyaml --break-system-packages
    (selon le fournisseur configuré — voir llm_client.py)

USAGE
    python3 fix_impact_scale.py --dry-run   # affiche le plan sans écrire
    python3 fix_impact_scale.py              # exécution réelle
"""

import argparse
import json
import re
from pathlib import Path

import yaml

from llm_client import call_llm  # tier structured_strict — champ canonique référencé (matrice d'influence)


VAULT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = VAULT_ROOT / "instances"
SCENARIOS_DIR = VAULT_ROOT / "scenarios"


def parse_md(filepath):
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return {}, raw, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2).strip(), raw


def find_files_out_of_range():
    """Retourne la liste des fichiers instances/*.md avec impact_local
    et/ou impact_systemique_global hors [0-5]."""
    files = []
    for path in sorted(INSTANCES_DIR.glob("*.md")):
        if path.name == "instance_template.md":
            continue
        fm, _, _ = parse_md(path)
        out_of_range = False
        for field in ("impact_local", "impact_systemique_global"):
            val = fm.get(field)
            try:
                v = int(val)
                if not (0 <= v <= 5):
                    out_of_range = True
            except (TypeError, ValueError):
                pass
        if out_of_range:
            files.append(path)
    return files


def get_client():
    """Conservé pour compatibilité de signature — retourne None, call_claude_json
    n'en a plus besoin depuis la migration vers llm_client.py."""
    return None


JUDGE_SYSTEM = """Tu travailles sur Ourrassol 2098, simulateur de presse fictive située \
en 2098. On te donne une fiche "instance" déjà entièrement rédigée (description, rôle, \
responsabilités, tensions narratives) mais dont les champs impact_local et \
impact_systemique_global ont été mal calibrés par un ancien script (échelle 0-10 ou \
0-100 au lieu de 0-5 attendu).

Lis le contenu narratif de la fiche et juge ces deux valeurs sur l'échelle CORRECTE :
- 0 = négligeable / sans influence perceptible
- 5 = maximal / dominant / déterminant à cette échelle

impact_local : influence de cette entité à l'échelle locale/régionale dans ce scénario.
impact_systemique_global : influence de cette entité sur les dynamiques systémiques \
globales du monde (variables systémiques, équilibres géopolitiques/économiques mondiaux).

Les deux valeurs sont indépendantes — une entité peut être très influente localement \
mais négligeable globalement, ou l'inverse.

IMPORTANT : ne montre AUCUN raisonnement, AUCUNE analyse intermédiaire, AUCUN texte \
avant ou après. Pas de "Je lis la fiche...", pas de markdown, pas d'explication. \
Réfléchis intérieurement mais ta réponse complète doit être EXACTEMENT et UNIQUEMENT \
cette ligne JSON, rien d'autre :
{"impact_local": N, "impact_systemique_global": N}
où N est un entier entre 0 et 5 inclus."""


def call_claude_json(client, system, user_content, max_tokens=1024):
    text = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
        task_tier="structured_strict",
    ).strip()

    if not text:
        raise RuntimeError("Réponse LLM vide.")

    # Le modèle raisonne parfois en texte libre avant de donner le JSON final
    # malgré la consigne ("Je lis la fiche... **Impact local** : ..."). On
    # cherche donc le DERNIER bloc {...} du texte plutôt que d'exiger que
    # toute la réponse soit du JSON pur — plus robuste que de lutter contre
    # ce réflexe de raisonnement avec uniquement la consigne système.
    candidate = text
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    matches = re.findall(r"\{[^{}]*\}", text)
    if matches:
        try:
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            pass

    # Heuristique de troncature (pas de resp.stop_reason disponible depuis
    # la migration vers llm_client.py, qui ne retourne qu'une string) :
    likely_truncated = len(text) >= max_tokens * 3  # ~3-4 car/token en français
    if likely_truncated:
        raise RuntimeError(
            f"Réponse LLM probablement tronquée (max_tokens={max_tokens}, "
            f"{len(text)} caractères reçus, aucun JSON complet trouvé) — "
            f"texte reçu: {text[:200]!r}"
        )
    raise RuntimeError(f"Aucun JSON exploitable trouvé dans la réponse : {text[:200]!r}")


def judge_impact(client, fm, body):
    user_content = f"""Nom : {fm.get('name', '')}
Scénario : {fm.get('scenario', '')}
Type : {fm.get('type_dans_scenario', '')}

Rôle dans le scénario :
{fm.get('role_dans_scenario', '')}

Responsabilités :
{fm.get('responsabilites', '')}

Description journalistique :
{fm.get('description_journalistique', '')}

Tensions narratives :
{fm.get('tensions_narratives', '')}

Valeurs actuelles (mal calibrées, à ignorer pour le jugement, juste pour référence) :
impact_local={fm.get('impact_local')}, impact_systemique_global={fm.get('impact_systemique_global')}"""

    return call_claude_json(client, JUDGE_SYSTEM, user_content)


def rewrite_impact_fields(path, new_local, new_global):
    """Remplace uniquement les lignes impact_local: / impact_systemique_global:
    dans le frontmatter, en préservant tout le reste du fichier."""
    raw = path.read_text(encoding="utf-8")
    raw, n1 = re.subn(r"^impact_local:\s*-?\d+\s*$",
                       f"impact_local: {new_local}", raw, count=1, flags=re.MULTILINE)
    raw, n2 = re.subn(r"^impact_systemique_global:\s*-?\d+\s*$",
                       f"impact_systemique_global: {new_global}", raw, count=1, flags=re.MULTILINE)
    if n1 != 1 or n2 != 1:
        raise RuntimeError(
            f"Remplacement inattendu dans {path.name} : "
            f"impact_local matché {n1}x, impact_systemique_global matché {n2}x "
            f"(attendu 1x chacun) — fichier NON modifié par sécurité."
        )
    path.write_text(raw, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Corrige rétroactivement impact_local/impact_systemique_global hors [0-5]"
    )
    parser.add_argument("--dry-run", action="store_true",
                         help="Affiche le plan sans rien écrire")
    args = parser.parse_args()
    dry_run = args.dry_run

    print("=" * 60)
    print("OURRASSOL 2098 — Correction échelle impact_local/global")
    print("=" * 60)
    if dry_run:
        print("(mode --dry-run : rien ne sera écrit)\n")

    files = find_files_out_of_range()
    print(f"\n{len(files)} fichier(s) à corriger.\n")

    if not files:
        print("Rien à corriger.")
        return

    client = get_client()
    corrected = 0
    errors = []

    for i, path in enumerate(files, 1):
        fm, body, _ = parse_md(path)
        old_local = fm.get("impact_local")
        old_global = fm.get("impact_systemique_global")
        print(f"[{i}/{len(files)}] {path.name} "
              f"(actuel : local={old_local}, global={old_global})...", end=" ", flush=True)

        try:
            judged = judge_impact(client, fm, body)
            new_local = int(judged["impact_local"])
            new_global = int(judged["impact_systemique_global"])
            if not (0 <= new_local <= 5) or not (0 <= new_global <= 5):
                raise ValueError(f"Le LLM a renvoyé une valeur hors [0-5] : {judged}")
        except Exception as e:
            print(f"⚠ échec 1ère tentative ({e}), retry...", end=" ", flush=True)
            try:
                judged = judge_impact(client, fm, body)
                new_local = int(judged["impact_local"])
                new_global = int(judged["impact_systemique_global"])
                if not (0 <= new_local <= 5) or not (0 <= new_global <= 5):
                    raise ValueError(f"Le LLM a renvoyé une valeur hors [0-5] : {judged}")
            except Exception as e2:
                print(f"✗ ({e2})")
                errors.append((path.name, str(e2)))
                continue

        if not dry_run:
            try:
                rewrite_impact_fields(path, new_local, new_global)
            except RuntimeError as e:
                print(f"✗ ({e})")
                errors.append((path.name, str(e)))
                continue

        print(f"✓ -> local={new_local}, global={new_global}")
        corrected += 1

    print("\n" + "=" * 60)
    print(f"✓ {corrected}/{len(files)} fiche(s) {'à corriger' if dry_run else 'corrigées'}")
    if errors:
        print(f"✗ {len(errors)} erreur(s) :")
        for fname, err in errors:
            print(f"   - {fname}: {err}")
    if dry_run:
        print("\n(mode --dry-run : rien n'a été écrit sur disque)")
    print("=" * 60)


if __name__ == "__main__":
    main()

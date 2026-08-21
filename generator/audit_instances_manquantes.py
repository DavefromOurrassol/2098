#!/usr/bin/env python3
"""
audit_instances_manquantes.py — Ourrassol 2098  (v2)

PROBLÈME TRAITÉ
----------------
Un échec de génération d'instance pour UN scénario, alors que l'entité
parente a déjà réussi sur d'autres scénarios (ex. réel : "Les Veilleurs
des Nappes Phréatiques" / eco_communalism, bloqué le 15 août 2026 par le
garde-fou ancrage_reel), ne laisse aucune trace persistante et
structurée. Le chemin de code concerné (generate_instances_for_entity()
dans create_entities_and_instances.py) ne fait qu'incrémenter un
compteur d'erreurs interne (stats["errors"]) sans jamais écrire nulle
part QUEL scénario a échoué ni POURQUOI — seul un print() console au
moment du run le montre, capturé (si le run est passé par le GUI) dans
un fichier plat sous gui/logs/, jamais relu ni centralisé ensuite.

CE QUE FAIT CE SCRIPT
----------------------
Diagnostic pur, lecture seule, aucune écriture sur les fiches, aucun
appel LLM — même esprit que trace_injection.py / audit_broken_slugs.py.

1. Pour chaque entité (entites/*.md), lit le frontmatter
   `scenarios_instances:` (liste des scénarios PRÉVUS à la création)
   et compare aux fichiers instances/{slug}_{scenario}.md RÉELLEMENT
   présents sur disque.
2. Pour chaque trou trouvé, tente (best-effort) de retrouver le motif
   d'échec en grepant gui/logs/*.log.

NOUVEAU EN v2 — CLASSIFICATION DES TROUS
------------------------------------------
Un premier run réel a remonté 19 trous sur un vault donné, avec des
profils très hétérogènes (1 seul scénario manquant sur 6 vs. 5 ou 6
manquants d'un coup, slugs visiblement cassés) — traiter ça comme "19
échecs de garde-fou à relancer" serait une erreur de diagnostic. v2
classe chaque trou en 3 catégories plutôt que de tout mettre au même
niveau :

  [FAUX POSITIF PROBABLE — SLUG] Un fichier instance existe bel et bien
  pour ce scénario, mais sous un slug légèrement différent de celui
  enregistré sur la fiche entité (ex. bug d'encodage d'accents non-
  français, corrigé le 14 août 2026 mais pas rétroactivement migré sur
  les fiches déjà générées — voir audit_broken_slugs.py). Détecté par
  (a) recalcul du slug avec la fonction corrigée et (b) recherche de
  fichiers au nom proche (difflib) dans instances/. PAS un échec de
  génération — juste une désynchronisation de nommage. Se règle par un
  renommage, jamais par une relance de génération (qui n'écraserait
  rien mais dupliquerait le contenu sous deux noms).

  [ENTITÉ ENTIÈRE SUSPECTE] La majorité (ou la totalité) des scénarios
  prévus manquent pour cette entité. Un échec de garde-fou (ancrage_reel
  et consorts) ne bloque normalement qu'UN scénario à la fois — un tel
  motif ressemble plutôt à une entité dont le cycle de génération
  d'instances n'a jamais tourné du tout, ou dont le champ
  `scenarios_instances` ne reflète plus la réalité (édition manuelle,
  migration incomplète). À vérifier via `date_creation`/`custom_source`
  avant toute relance en masse.

  [ÉCHEC PONCTUEL PROBABLE] Une minorité de scénarios manquent (le
  profil du cas réel eco_communalism). C'est la catégorie où une simple
  relance de génération sur le(s) scénario(s) manquant(s) est le bon
  réflexe.

USAGE
-----
    python3 audit_instances_manquantes.py --vault-root ..
    python3 audit_instances_manquantes.py --vault-root .. --report
    python3 audit_instances_manquantes.py --vault-root .. --json
"""

import argparse
import difflib
import json
import re
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML requis : pip install pyyaml")


# ---------------------------------------------------------------------------
# Slugification corrigée (14 août 2026) — reprise telle quelle
# d'audit_broken_slugs.py pour garder une seule logique de référence.
# ---------------------------------------------------------------------------

def slugify_fixed(text: str) -> str:
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def parse_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


def find_failure_reason(logs_dir: Path, nom: str, scenario: str) -> str:
    """Best-effort : cherche dans les logs GUI existants le motif
    d'échec de {scenario} pour l'entité {nom}."""
    if not logs_dir.exists():
        return "dossier de logs introuvable"

    header_re = re.compile(r"^===\s*(.+?)\s*===\s*$")
    scenario_fail_re = re.compile(re.escape(scenario) + r".*✗\s*$")

    log_files = sorted(logs_dir.glob("*.log"), reverse=True)

    for log_path in log_files:
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        in_block = False
        for i, line in enumerate(lines):
            m = header_re.match(line.strip())
            if m:
                in_block = (m.group(1).strip() == nom.strip())
                continue
            if not in_block:
                continue
            if scenario_fail_re.search(line):
                raisons = []
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith("-"):
                    raisons.append(lines[j].strip().lstrip("- ").strip())
                    j += 1
                if raisons:
                    return " ; ".join(raisons) + f"  (source : {log_path.name})"
                return f"échec confirmé mais raison non capturée  (source : {log_path.name})"

    return "raison introuvable dans les logs (aucun run archivé ne matche, ou log absent/rotaté)"


def find_slug_mismatch_candidate(instances_dir: Path, nom: str, slug: str, scenario: str):
    """Cherche un fichier instance qui correspondrait à ce scénario sous
    un AUTRE slug que celui enregistré sur la fiche entité — signe d'un
    désaccord de nommage plutôt que d'un vrai échec de génération.

    UNIQUEMENT la passe déterministe : slug recalculé avec la fonction
    corrigée du 14 août (bug connu et vérifiable, pas une estimation).
    Retourne None si rien de probant.

    (v2 avait aussi une passe floue par difflib sur les noms de fichiers
    complets — retirée en v3 : comparer avec le suffixe "_scenario.md"
    inclus gonfle artificiellement la similarité entre deux entités
    SANS AUCUN RAPPORT qui partagent juste ce suffixe, ex. observé en
    conditions réelles : 'nexcore' vs 'nexus_biosyn' à 0.42 de
    similarité réelle sur le nom, mais 0.79 avec le suffixe partagé —
    largement au-dessus du seuil 0.75, donc un faux match automatique.
    3 des 4 cas remontés par v2 sur le vault réel étaient des faux
    positifs de CE mécanisme, pas de vrais désaccords de nommage.)"""
    suffix = f"_{scenario}.md"

    expected_fixed = slugify_fixed(nom)
    if expected_fixed and expected_fixed != slug:
        candidate = instances_dir / f"{expected_fixed}{suffix}"
        if candidate.exists():
            return candidate.name, "slug recalculé (fonction corrigée du 14 août) trouvé sur disque"

    return None


def find_weak_naming_hint(instances_dir: Path, slug: str, scenario: str):
    """Signal FAIBLE, non déterministe, jamais utilisé pour reclasser un
    trou — seulement pour attirer l'attention en note. Compare les noms
    de fichiers SANS le suffixe scénario (pour éviter le biais qui a
    produit les faux positifs de v2), seuil volontairement élevé
    (0.90) pour limiter le bruit. Un score élevé ne prouve rien en soi
    (cf. 'les_gardiens_des_n_uds_hybrides' vs
    'les_gardiens_des_corridors_hybrides' à 0.85 — pattern de nommage
    partagé entre deux entités probablement distinctes, pas une preuve
    de désaccord de slug) : à vérifier à la main, jamais à traiter
    comme acquis."""
    suffix = f"_{scenario}.md"
    stems = [p.name[: -len(suffix)] for p in instances_dir.glob(f"*{suffix}")]
    if not stems:
        return None
    close = difflib.get_close_matches(slug, stems, n=1, cutoff=0.90)
    if close:
        return f"{close[0]}{suffix}"
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Audit en lecture seule des instances manquantes, "
                     "classé par catégorie de trou."
    )
    parser.add_argument("--vault-root", default="..")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--seuil-suspect", type=float, default=0.5,
                         help="Proportion de scénarios manquants à partir de "
                              "laquelle une entité est classée 'entité entière "
                              "suspecte' (défaut 0.5) — ignoré si le nombre total "
                              "de scénarios prévus est trop petit pour qu'une "
                              "proportion soit un signal fiable (voir --seuil-absolu)")
    parser.add_argument("--seuil-absolu", type=int, default=3,
                         help="Nombre absolu de scénarios manquants à partir "
                              "duquel une entité est classée 'suspecte', "
                              "indépendamment de la proportion (défaut 3). "
                              "Corrige le cas d'une entité à 1 seul scénario "
                              "prévu dont l'unique instance manque : proportion "
                              "= 100%% mais ce n'est pas un signal de 'majorité "
                              "manquante', juste un échec ponctuel comme un "
                              "autre — vu en conditions réelles sur 'Les Gardiens "
                              "des Nœuds Hybrides' (1/1), à tort classée "
                              "suspecte avant ce correctif.")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    entites_dir = vault_root / "entites"
    instances_dir = vault_root / "instances"
    logs_dir = vault_root / "gui" / "logs"

    if not entites_dir.exists():
        raise SystemExit(f"Dossier introuvable : {entites_dir}")

    par_entite = {}
    total_entites = 0
    total_scenarios_prevus = 0

    for md_file in sorted(entites_dir.glob("*.md")):
        if md_file.name == "entity_template.md":
            continue
        fm = parse_frontmatter(md_file)
        nom = fm.get("name") or fm.get("nom")
        slug = fm.get("slug")
        scenarios_prevus = fm.get("scenarios_instances") or []
        if not slug or not scenarios_prevus:
            continue
        total_entites += 1

        manquants = []
        for scenario in scenarios_prevus:
            total_scenarios_prevus += 1
            instance_path = instances_dir / f"{slug}_{scenario}.md"
            if not instance_path.exists():
                manquants.append(scenario)

        if not manquants:
            continue

        par_entite[slug] = {
            "nom": nom or slug,
            "slug": slug,
            "date_creation": fm.get("date_creation"),
            "custom_source": fm.get("custom_source"),
            "total_prevu": len(scenarios_prevus),
            "manquants": manquants,
        }

    # --- Classification -----------------------------------------------
    faux_positifs = []
    entites_suspectes = []
    echecs_ponctuels = []

    for slug, info in par_entite.items():
        proportion = len(info["manquants"]) / info["total_prevu"]
        trous_restants = []

        for scenario in info["manquants"]:
            match = find_slug_mismatch_candidate(instances_dir, info["nom"], slug, scenario)
            if match:
                fichier_trouve, methode = match
                faux_positifs.append({
                    **{k: v for k, v in info.items() if k != "manquants"},
                    "scenario": scenario,
                    "fichier_trouve": fichier_trouve,
                    "methode_detection": methode,
                })
            else:
                trous_restants.append(scenario)

        if not trous_restants:
            continue

        # Suspecte si beaucoup de scénarios manquent EN VALEUR ABSOLUE
        # (--seuil-absolu), ou si la proportion est forte ET que le total
        # prévu est assez grand pour qu'une proportion veuille dire
        # quelque chose (sinon 1 manquant sur 1 prévu = 100% à tort).
        is_suspecte = (
            len(trous_restants) >= args.seuil_absolu
            or (info["total_prevu"] >= args.seuil_absolu and proportion >= args.seuil_suspect)
        )

        if is_suspecte:
            hints = {
                sc: find_weak_naming_hint(instances_dir, slug, sc)
                for sc in trous_restants
            }
            hints = {sc: h for sc, h in hints.items() if h}
            entites_suspectes.append({
                **{k: v for k, v in info.items() if k != "manquants"},
                "scenarios_manquants": trous_restants,
                "proportion_manquante": round(proportion, 2),
                "pistes_nommage_incertaines": hints,
            })
        else:
            for scenario in trous_restants:
                raison = find_failure_reason(logs_dir, info["nom"], scenario)
                hint = find_weak_naming_hint(instances_dir, slug, scenario)
                echecs_ponctuels.append({
                    **{k: v for k, v in info.items() if k != "manquants"},
                    "scenario": scenario,
                    "raison": raison,
                    "piste_nommage_incertaine": hint,
                })

    # --- Sortie ------------------------------------------------------
    if args.json:
        print(json.dumps({
            "total_entites_auditees": total_entites,
            "total_scenarios_prevus": total_scenarios_prevus,
            "faux_positifs_slug": faux_positifs,
            "entites_suspectes": entites_suspectes,
            "echecs_ponctuels_probables": echecs_ponctuels,
        }, ensure_ascii=False, indent=2, default=str))
        return

    lignes_rapport = [f"# Instances manquantes — audit du {__import__('datetime').date.today().isoformat()}\n"]
    lignes_rapport.append(
        f"{total_entites} entité(s) auditée(s) ({total_scenarios_prevus} scénario(s) prévu(s) au total).\n"
    )

    def _section(titre, items, formatter):
        print(f"\n{'=' * 70}\n{titre} ({len(items)})\n{'=' * 70}")
        lignes_rapport.append(f"\n## {titre} ({len(items)})\n")
        if not items:
            print("  (aucun)")
        for it in items:
            texte = formatter(it)
            print(texte)
            lignes_rapport.append(texte.replace("\n", "  \n") + "\n")

    _section(
        "FAUX POSITIFS PROBABLES — désaccord de slug (PAS un échec de génération)",
        faux_positifs,
        lambda it: (
            f"  {it['nom']}  (slug fiche : {it['slug']})\n"
            f"    scénario        : {it['scenario']}\n"
            f"    fichier trouvé  : instances/{it['fichier_trouve']}\n"
            f"    détection       : {it['methode_detection']}\n"
            f"    -> solution : vérifier et renommer/fusionner, ne PAS relancer la génération.\n"
        ),
    )

    def _fmt_suspecte(it):
        base = (
            f"  {it['nom']}  (slug : {it['slug']})\n"
            f"    manquants ({len(it['scenarios_manquants'])}/{it['total_prevu']}) : "
            f"{', '.join(it['scenarios_manquants'])}\n"
            f"    date_creation   : {it.get('date_creation') or 'absente (probable socle initial)'}\n"
            f"    custom_source   : {it.get('custom_source') or 'absent (pas une idée custom)'}\n"
            f"    -> solution : NE PAS relancer en masse. Vérifier d'abord si le cycle de "
            f"génération d'instances a réellement tourné pour cette entité (logs), ou si "
            f"scenarios_instances est simplement désynchronisé de la réalité du dossier "
            f"instances/ (édition manuelle, migration incomplète).\n"
        )
        if it.get("pistes_nommage_incertaines"):
            for sc, fichier in it["pistes_nommage_incertaines"].items():
                base += (
                    f"    piste incertaine ({sc}) : instances/{fichier} — nom proche mais "
                    f"NON confirmé (peut être une entité totalement différente au nom "
                    f"similaire) ; à vérifier à la main, ne pas fusionner sans lire les deux fiches.\n"
                )
        return base

    _section(
        "ENTITÉS ENTIÈRES SUSPECTES — majorité/totalité des scénarios manquants",
        entites_suspectes,
        _fmt_suspecte,
    )

    def _fmt_echec(it):
        base = (
            f"  {it['nom']}  (slug : {it['slug']})\n"
            f"    scénario manquant : {it['scenario']}\n"
            f"    raison            : {it['raison']}\n"
            f"    -> solution : relancer la génération de cette instance précise pour ce "
            f"scénario (create_entities_and_instances.py / generate_instances.py).\n"
        )
        if it.get("piste_nommage_incertaine"):
            base += (
                f"    piste incertaine  : instances/{it['piste_nommage_incertaine']} — nom "
                f"proche mais NON confirmé ; vérifier à la main avant de relancer (pourrait "
                f"être une entité différente).\n"
            )
        return base

    _section(
        "ÉCHECS PONCTUELS PROBABLES — 1 ou 2 scénarios manquants sur le total",
        echecs_ponctuels,
        _fmt_echec,
    )

    print("\nRappel : ce script ne relance rien et n'écrit aucune fiche.")

    if args.report:
        report_dir = vault_root / "documentation" / "need_action"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "instances_manquantes.md"
        report_path.write_text("\n".join(lignes_rapport), encoding="utf-8")
        print(f"\nRapport écrit : {report_path}")


if __name__ == "__main__":
    main()

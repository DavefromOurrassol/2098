"""
Ourrassol 2098 — GUI Flask
app.py : serveur principal
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, stream_with_context


def _load_dotenv():
    """Charge les variables depuis gui/.env si présent."""
    env_path = Path(os.getcwd()) / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if value and len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            if key and value and key not in os.environ:
                os.environ[key] = value

_load_dotenv()


# ── Chemins ──────────────────────────────────────────────────────────────────

BASE_DIR = Path(os.path.abspath(__file__)).parent if "__file__" in globals() else Path(os.getcwd())
CONFIG_PATH = BASE_DIR / "config.json"
SCRIPTS_CONFIG_PATH = BASE_DIR / "scripts_config.json"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ── App Flask ─────────────────────────────────────────────────────────────────

app = Flask(__name__)

# P5 (backlog) : /api/dashboard extrait dans routes_dashboard.py pour éviter
# qu'il soit écrasé par les patches récurrents sur ce fichier.
from routes_dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)

# ── État global des runs ──────────────────────────────────────────────────────

# { run_id: { "process": Popen, "lines": [...], "done": bool, "script_id": str } }
_runs: dict = {}
_runs_lock = threading.Lock()


# ── Helpers config ────────────────────────────────────────────────────────────

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_scripts_config() -> list:
    with open(SCRIPTS_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Routes principales ────────────────────────────────────────────────────────

@app.route("/")
def index():
    # CARTO_API_KEY (30 août 2026) : CARTO exige désormais une clé pour
    # ses tuiles raster gratuites (basemaps.cartocdn.com), sinon filigrane
    # "API KEY REQUIRED" sur la carte -- changement de leur côté fin août
    # 2026, rien à voir avec le pipeline. Lue depuis l'environnement
    # (~/.zshrc, même endroit que les autres clés API du projet -- jamais
    # commitée), injectée dans le template plutôt qu'en dur dans app.js.
    # Cette clé est utilisée côté navigateur (Leaflet fait les requêtes de
    # tuiles directement depuis le client) -- comme les clés Google Maps,
    # ce n'est pas un secret serveur à protéger de la même façon qu'une clé
    # LLM, mais on évite quand même de la commiter dans le HTML statique.
    return render_template("index.html", carto_api_key=os.environ.get("CARTO_API_KEY", ""))


@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(load_config())


@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400
    cfg = load_config()
    # Fusion générique (5 juillet, remplace le fix bug #14 par une solution
    # plus large) : pour toute clé dont la valeur actuelle ET la nouvelle
    # valeur sont des dict (ex. "llm"), on fusionne au lieu de remplacer —
    # sinon poster {llm: {provider, model_openai}} effacerait model_mistral,
    # model_claude et les available_* au passage. Les clés simples (chaînes,
    # listes) restent remplacées comme avant.
    for key, value in data.items():
        if key not in cfg:
            continue
        if isinstance(cfg[key], dict) and isinstance(value, dict):
            cfg[key].update(value)
        else:
            cfg[key] = value
    save_config(cfg)
    return jsonify({"ok": True})


@app.route("/api/scripts", methods=["GET"])
def get_scripts():
    return jsonify(load_scripts_config())


@app.route("/api/script/<script_id>", methods=["GET"])
def get_script(script_id: str):
    scripts = load_scripts_config()
    for s in scripts:
        if s["id"] == script_id:
            return jsonify(s)
    return jsonify({"error": "Script introuvable"}), 404


# ── API YAML viewer/editor ───────────────────────────────────────────────────

@app.route("/api/yaml", methods=["GET"])
def get_yaml():
    cfg = load_config()
    # Bug #16 : résolution basée sur vault_root, pas pipeline_dir — plusieurs
    # dossiers (entites_custom/, evenements_custom/, signaux_custom/,
    # instances_custom/) vivent à la racine du vault, pas dans generator/.
    # Comme pipeline_dir = vault_root/generator/, les chemins scripts_config.json
    # correctement relatifs à generator/ sont préfixés "generator/" en conséquence.
    vault_root = Path(cfg.get("vault_root", ""))
    rel_path = request.args.get("path", "")
    if not rel_path:
        return jsonify({"error": "Paramètre path manquant"}), 400
    target = (vault_root / rel_path).resolve()
    try:
        target.relative_to(vault_root.resolve())
    except ValueError:
        return jsonify({"error": "Chemin non autorisé"}), 403
    if not target.exists():
        return jsonify({"content": "", "exists": False, "path": str(target)})
    try:
        content = target.read_text(encoding="utf-8")
        return jsonify({"content": content, "exists": True, "path": str(target)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/yaml", methods=["POST"])
def save_yaml():
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))  # bug #16
    data = request.get_json()
    if not data or "path" not in data or "content" not in data:
        return jsonify({"error": "Données manquantes"}), 400
    rel_path = data["path"]
    file_content = data["content"]
    target = (vault_root / rel_path).resolve()
    try:
        target.relative_to(vault_root.resolve())
    except ValueError:
        return jsonify({"error": "Chemin non autorisé"}), 403
    try:
        if target.exists():
            bak = target.with_suffix(target.suffix + ".bak")
            bak.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file_content, encoding="utf-8")
        return jsonify({"ok": True, "path": str(target)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/yaml/form", methods=["POST"])
def save_yaml_form():
    """
    Sauvegarde des champs individuels dans un fichier YAML.
    Body JSON :
    {
      "path": "generator/config.yaml",
      "fields": {
        "scenario": "breakdown",
        "ligne_editoriale": "opposition",
        "article.longueur": "breve",
        "thematiques": ["politique", "economie_finance"]
      }
    }
    Les clés à point (ex: article.longueur) ciblent des sous-clés YAML imbriquées.
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))  # bug #16
    data = request.get_json()
    if not data or "path" not in data or "fields" not in data:
        return jsonify({"error": "Données manquantes"}), 400

    rel_path = data["path"]
    fields = data["fields"]  # dict clé → valeur

    target = (vault_root / rel_path).resolve()
    try:
        target.relative_to(vault_root.resolve())
    except ValueError:
        return jsonify({"error": "Chemin non autorisé"}), 403

    try:
        # Lire le YAML existant comme texte (pour préserver les commentaires)
        # puis mettre à jour ligne par ligne avec regex
        if target.exists():
            bak = target.with_suffix(target.suffix + ".bak")
            bak.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
            lines = target.read_text(encoding="utf-8").splitlines()
        else:
            lines = []

        lines = _update_yaml_fields(lines, fields)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return jsonify({"ok": True, "path": str(target)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _update_yaml_fields(lines: list, fields: dict) -> list:
    """
    Met à jour les valeurs dans un fichier YAML (préserve les commentaires).
    Gère les clés simples (scenario: value) et imbriquées (article.longueur → sous article:).
    Gère les listes multi-valeurs (thematiques: [a, b, c] ou format bullet).
    """
    import re

    # Séparer clés simples et imbriquées
    simple_fields = {}
    nested_fields = {}  # parent → {subkey: value}

    for key, value in fields.items():
        if "." in key:
            parent, subkey = key.split(".", 1)
            nested_fields.setdefault(parent, {})[subkey] = value
        else:
            simple_fields[key] = value

    result = list(lines)

    # ── Traitement clés simples ──
    for key, value in simple_fields.items():
        result = _replace_yaml_key(result, key, value, indent=0)

    # ── Traitement clés imbriquées ──
    for parent, subfields in nested_fields.items():
        # Trouver le bloc parent
        parent_idx = None
        for i, line in enumerate(result):
            if re.match(rf"^{re.escape(parent)}:\s*$", line.strip()) or \
               re.match(rf"^{re.escape(parent)}:", line):
                parent_idx = i
                break
        if parent_idx is not None:
            for subkey, value in subfields.items():
                result = _replace_yaml_key(result, subkey, value, indent=2,
                                           search_from=parent_idx + 1)

    return result


def _replace_yaml_key(lines: list, key: str, value, indent: int = 0,
                       search_from: int = 0) -> list:
    """Remplace la valeur d'une clé YAML dans les lignes données."""
    import re

    indent_str = " " * indent
    key_re = re.compile(rf"^{re.escape(indent_str)}{re.escape(key)}:(\s.*)?$")

    # Cas liste (thematiques)
    if isinstance(value, list):
        # Trouver la clé et remplacer jusqu'à la prochaine clé de même niveau
        start_idx = None
        for i in range(search_from, len(lines)):
            if key_re.match(lines[i]):
                start_idx = i
                break
        if start_idx is None:
            return lines

        # Trouver la fin du bloc liste
        end_idx = start_idx + 1
        item_re = re.compile(rf"^{re.escape(indent_str)}  - ")
        while end_idx < len(lines) and (
            item_re.match(lines[end_idx]) or lines[end_idx].strip() == ""
        ):
            end_idx += 1

        new_lines = [f"{indent_str}{key}:"]
        for item in value:
            new_lines.append(f"{indent_str}  - {item}")

        return lines[:start_idx] + new_lines + lines[end_idx:]

    # Cas valeur scalaire
    yaml_value = _to_yaml_scalar(value)
    for i in range(search_from, len(lines)):
        if key_re.match(lines[i]):
            lines[i] = f"{indent_str}{key}: {yaml_value}"
            return lines

    return lines


def _to_yaml_scalar(value) -> str:
    """Convertit une valeur Python en représentation YAML scalaire inline."""
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    # Chaîne : guillemets si contient des caractères spéciaux
    s = str(value)
    if any(c in s for c in (": ", "#", "[", "]", "{", "}", ",", "'")):
        return f'"{s}"'
    return s



@app.route("/api/yaml/append", methods=["POST"])
def append_yaml_queue():
    """
    Appende une entrée dans la liste 'queue' d'un fichier YAML.
    Body JSON :
    {
      "path": "entites_custom/queue.yaml",
      "entry": { "nom": "...", "category": "...", ... }
    }
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))  # bug #16
    data = request.get_json()
    if not data or "path" not in data or "entry" not in data:
        return jsonify({"error": "Données manquantes"}), 400

    rel_path = data["path"]
    entry = data["entry"]

    target = (vault_root / rel_path).resolve()
    try:
        target.relative_to(vault_root.resolve())
    except ValueError:
        return jsonify({"error": "Chemin non autorisé"}), 403

    try:
        import yaml as _yaml

        # Backup
        if target.exists():
            bak = target.with_suffix(target.suffix + ".bak")
            bak.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
            existing = _yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        else:
            existing = {}
            target.parent.mkdir(parents=True, exist_ok=True)

        queue = existing.get("queue") or []
        if not isinstance(queue, list):
            queue = []

        # Nettoyer les valeurs vides optionnelles
        clean_entry = {k: v for k, v in entry.items()
                       if v is not None and v != "" and v != []}

        queue.append(clean_entry)
        existing["queue"] = queue

        target.write_text(
            _yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8"
        )
        return jsonify({"ok": True, "path": str(target), "queue_length": len(queue)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/zones/pays-liste", methods=["GET"])
def zones_pays_liste():
    """Retourne la liste des pays 2026 depuis zones_pays.json."""
    gui_dir = Path(__file__).parent
    zones_pays_path = gui_dir / "zones_pays.json"
    if not zones_pays_path.exists():
        return jsonify({"pays": [], "error": "zones_pays.json introuvable"})
    try:
        import json as _json
        data = _json.loads(zones_pays_path.read_text(encoding="utf-8"))
        # Correctif du 16 août 2026 : pays_liste n'était jamais triée (ordre
        # d'écriture arbitraire du JSON) -- réutilise _fold() (déjà existant,
        # normalisation NFD) comme clé de tri plutôt qu'un sorted() naïf, qui
        # placerait mal les entrées accentuées (ex. "Écosse" après les mots
        # en Z au lieu d'à côté des mots en E).
        pays = sorted(data.get("pays_liste", []), key=_fold)
        return jsonify({"pays": pays})
    except Exception as e:
        return jsonify({"pays": [], "error": str(e)})



@app.route("/api/zones/manquantes", methods=["GET"])
def zones_manquantes_get():
    """Liste les zones manquantes (pays sans zone 2098), groupées par scénario."""
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    log_path = vault_root / "documentation" / "need_action" / "zones_manquantes.yaml"

    if not log_path.exists():
        return jsonify({"manquantes": [], "par_scenario": {}})

    try:
        import yaml as _yaml
        data = _yaml.safe_load(log_path.read_text(encoding="utf-8")) or {}
        entries = data.get("zones_manquantes", [])

        par_scenario = {}
        for e in entries:
            sc = e.get("scenario", "?")
            par_scenario.setdefault(sc, []).append(e)

        return jsonify({"manquantes": entries, "par_scenario": par_scenario})
    except Exception as e:
        return jsonify({"manquantes": [], "par_scenario": {}, "error": str(e)})


@app.route("/api/zones/manquantes", methods=["POST"])
def zones_manquantes_update():
    """
    Met à jour le statut d'une entrée zones_manquantes.
    Body JSON : { "pays": "Allemagne", "scenario": "breakdown", "statut": "blanc_intentionnel" }
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    log_path = vault_root / "documentation" / "need_action" / "zones_manquantes.yaml"

    data = request.get_json()
    if not data or "pays" not in data or "scenario" not in data or "statut" not in data:
        return jsonify({"error": "Données manquantes (pays, scenario, statut requis)"}), 400

    valid_statuts = ("blanc_a_evaluer", "blanc_intentionnel", "a_enrichir")
    if data["statut"] not in valid_statuts:
        return jsonify({"error": f"Statut invalide, attendu : {valid_statuts}"}), 400

    if not log_path.exists():
        return jsonify({"error": "zones_manquantes.yaml introuvable"}), 404

    try:
        import yaml as _yaml
        existing = _yaml.safe_load(log_path.read_text(encoding="utf-8")) or {}
        entries = existing.get("zones_manquantes", [])

        found = False
        for e in entries:
            if e.get("pays") == data["pays"] and e.get("scenario") == data["scenario"]:
                e["statut"] = data["statut"]
                found = True
                break

        if not found:
            return jsonify({"error": "Entrée introuvable"}), 404

        existing["zones_manquantes"] = entries
        log_path.write_text(
            _yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8"
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/zones/recheck", methods=["POST"])
def zones_recheck():
    """
    Revérifie tous les pays manquants d'un scénario en relisant directement
    la fiche geographie/{scenario}.md (origine_reelle à jour, post-enrichissement).
    Retire de zones_manquantes.yaml les entrées désormais résolues.
    Body JSON : { "scenario": "breakdown" }
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()

    if not scenario:
        return jsonify({"error": "scenario requis"}), 400

    log_path = vault_root / "documentation" / "need_action" / "zones_manquantes.yaml"
    if not log_path.exists():
        return jsonify({"resolved": [], "still_missing": [], "message": "zones_manquantes.yaml introuvable"})

    try:
        import yaml as _yaml

        existing = _yaml.safe_load(log_path.read_text(encoding="utf-8")) or {}
        entries = existing.get("zones_manquantes", [])

        # Entrées de ce scénario, non intentionnelles
        to_check = [e for e in entries if e.get("scenario") == scenario
                    and e.get("statut") != "blanc_intentionnel"]

        if not to_check:
            return jsonify({"resolved": [], "still_missing": [],
                            "message": "Aucune entrée à revérifier pour ce scénario"})

        # Reconstruire l'index origine_reelle à jour depuis la fiche
        fresh_index = _build_origine_reelle_index(vault_root, scenario)

        # Charger aussi zones_pays.json pour le fallback
        gui_dir = Path(__file__).parent
        zones_pays_path = gui_dir / "zones_pays.json"
        zones_pays = {}
        if zones_pays_path.exists():
            import json as _json
            zones_pays = _json.loads(zones_pays_path.read_text(encoding="utf-8"))
        scenario_fallback = zones_pays.get(scenario, {})

        resolved = []
        still_missing = []

        for e in to_check:
            pays = e["pays"]
            n = _normalise_pays(pays)
            zone = fresh_index.get(n) or scenario_fallback.get(pays)
            if zone:
                resolved.append({"pays": pays, "zone": zone})
            else:
                still_missing.append(pays)

        # Retirer les entrées résolues de zones_manquantes.yaml
        if resolved:
            resolved_pays = {r["pays"] for r in resolved}
            entries = [e for e in entries
                       if not (e.get("scenario") == scenario and e.get("pays") in resolved_pays)]
            existing["zones_manquantes"] = entries
            log_path.write_text(
                _yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
                encoding="utf-8"
            )

        return jsonify({
            "resolved": resolved,
            "still_missing": still_missing,
            "scenario": scenario,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _normalise_pays(s: str) -> str:
    """Normalise un nom de pays pour le matching (cohérent avec generate_zones_pays)."""
    s = s.lower().strip()
    remap = {
        "états-unis d'amérique": "états-unis",
        "russie (sibérie orientale)": "russie",
        "danemark (groenland)": "danemark",
        "danemark / groenland": "danemark",
        "canada (nunavut)": "canada",
        "norvège (svalbard)": "norvège",
        "brésil (amazonie)": "brésil",
        "suisse (genève)": "suisse",
        "kenya (nairobi)": "kenya",
        "sibérie (entité fédérale russe)": "russie",
        "danemark (groenland inclus)": "danemark",
        "arctique russe (mourmansk)": "russie",
    }
    return remap.get(s, s)


def _build_origine_reelle_index(vault_root: Path, scenario: str) -> dict:
    """
    Parse la fiche geographie/{scenario}.md et construit un index
    pays_normalise -> slug_zone à partir de origine_reelle, à jour.
    """
    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return {}
    try:
        import yaml as _yaml
        raw = geo_file.read_text(encoding="utf-8")
        parts = raw.split("---")
        fm_str = parts[1] if len(parts) >= 2 else raw
        fm = _yaml.safe_load(fm_str) or {}
        raw_zones = fm.get("zones") or []
    except Exception:
        return {}

    # Un pays peut légitimement apparaître dans l'origine_reelle de sa zone N1
    # ET de sous-zones narratives (N2/N3) qui le documentent (ex. une ville).
    # On priorise explicitement les zones N1 plutôt que de dépendre de l'ordre
    # d'écriture du YAML (ancien comportement : premier trouvé gagne, fragile
    # si une sous-zone est écrite avant sa zone N1 parente).
    index = {}
    index_non_n1 = {}
    for z in raw_zones:
        if not isinstance(z, dict):
            continue
        slug = z.get("slug", "")
        niveau = z.get("niveau", 1)
        origine = z.get("origine_reelle") or []
        for o in origine:
            if isinstance(o, dict):
                entite = o.get("entite", "")
                n = _normalise_pays(entite)
                if not n:
                    continue
                if niveau == 1:
                    if n not in index:
                        index[n] = slug
                else:
                    if n not in index_non_n1:
                        index_non_n1[n] = slug
    # Fallback sur une sous-zone seulement si aucune zone N1 ne couvre ce pays
    for n, slug in index_non_n1.items():
        index.setdefault(n, slug)
    return index


@app.route("/api/zones/lookup", methods=["GET"])
def zones_lookup():
    """
    Cherche la zone 2098 correspondant à un pays 2026.
    GET /api/zones/lookup?pays=France&scenario=breakdown
    Retourne { zone: slug | null, confiance: haute|moyenne|nulle, source: origine_reelle|fallback|null }
    """
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    vault_root   = Path(cfg.get("vault_root", ""))
    pays  = request.args.get("pays", "").strip()
    scenario = request.args.get("scenario", "").strip()

    if not pays or not scenario:
        return jsonify({"error": "pays et scenario requis"}), 400

    # Charger zones_pays.json (dans gui/)
    gui_dir = Path(__file__).parent
    zones_pays_path = gui_dir / "zones_pays.json"
    if not zones_pays_path.exists():
        return jsonify({"zone": None, "confiance": "nulle", "source": "no_table",
                        "message": "zones_pays.json introuvable dans gui/"})

    try:
        import json as _json
        zones_pays = _json.loads(zones_pays_path.read_text(encoding="utf-8"))
    except Exception as e:
        return jsonify({"zone": None, "confiance": "nulle", "source": "error",
                        "message": str(e)})

    # 1. Chercher d'abord dans la fiche géographie à jour (origine_reelle)
    fresh_index = _build_origine_reelle_index(vault_root, scenario)
    n = _normalise_pays(pays)
    zone = fresh_index.get(n)
    if zone:
        return jsonify({"zone": zone, "confiance": "haute", "source": "origine_reelle"})

    # 2. Fallback table statique
    scenario_data = zones_pays.get(scenario, {})
    zone = scenario_data.get(pays)
    if zone:
        return jsonify({"zone": zone, "confiance": "moyenne", "source": "table"})

    # Log dans zones_manquantes si absent
    _log_zone_manquante(vault_root, pays, scenario)
    return jsonify({"zone": None, "confiance": "nulle", "source": "null",
                    "message": f"Aucune zone 2098 trouvée pour '{pays}' dans {scenario}"})


def _log_zone_manquante(vault_root: Path, pays: str, scenario: str):
    """Ajoute une entrée dans documentation/need_action/zones_manquantes.yaml si absente."""
    try:
        import yaml as _yaml
        log_path = vault_root / "documentation" / "need_action" / "zones_manquantes.yaml"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if log_path.exists():
            existing = _yaml.safe_load(log_path.read_text(encoding="utf-8")) or {}
        entries = existing.get("zones_manquantes", [])
        # Vérifier doublon
        already = any(e.get("pays") == pays and e.get("scenario") == scenario
                      for e in entries)
        if not already:
            entries.append({
                "pays": pays,
                "scenario": scenario,
                "statut": "blanc_a_evaluer",
            })
            existing["zones_manquantes"] = entries
            log_path.write_text(
                _yaml.dump(existing, allow_unicode=True, sort_keys=False,
                           default_flow_style=False),
                encoding="utf-8"
            )
    except Exception:
        pass  # Log silencieux — ne pas bloquer le workflow


# ── API Carte géographique interactive ──────────────────────────────────────

def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """h, s, l dans [0, 1] -> couleur hex."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


PATTERN_THRESHOLD = 8  # au-delà de N zones, ajoute des motifs en plus de la couleur
N_PATTERNS = 5          # nombre de motifs distincts définis côté frontend


def _scan_n1_zones_with_desc(vault_root: Path, scenario: str) -> list:
    """
    Zones niveau 1 avec nom + description (pour légende carte + prompt LLM).
    Couleurs réparties uniformément sur la roue teinte (jamais de collision, contrairement
    à un hash qui peut faire tomber deux zones sur la même couleur). Au-delà de
    PATTERN_THRESHOLD zones, un index de motif est aussi assigné pour renforcer la
    distinction visuelle (deux teintes proches + motifs différents restent différenciables).
    """
    if not scenario:
        return []
    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return []
    try:
        import yaml as _yaml
        raw = geo_file.read_text(encoding="utf-8")
        parts = raw.split("---")
        fm_str = parts[1] if len(parts) >= 2 else raw
        fm = _yaml.safe_load(fm_str) or {}
        raw_zones = fm.get("zones") or []
    except Exception:
        return []
    result = []
    for z in raw_zones:
        if not isinstance(z, dict):
            continue
        if int(z.get("niveau", 1)) != 1:
            continue
        slug = str(z.get("slug", "")).strip()
        if not slug:
            continue
        result.append({
            "slug": slug,
            "nom": str(z.get("nom", slug)).strip(),
            "description": str(z.get("description", "")).strip(),
        })
    result.sort(key=lambda x: x["slug"])

    n = len(result)
    use_patterns = n > PATTERN_THRESHOLD
    # Alterner luminosité/saturation légèrement à chaque tour de roue pour que même
    # avec beaucoup de zones, deux teintes voisines ne soient jamais identiques.
    for i, z in enumerate(result):
        hue = (i / n) if n else 0
        lightness = 0.50 if i % 2 == 0 else 0.42
        z["color"] = _hsl_to_hex(hue, 0.60, lightness)
        z["pattern"] = (i % N_PATTERNS) if use_patterns else None

    return result


@app.route("/api/carte/affectations", methods=["GET"])
def carte_affectations():
    """
    Retourne, pour un scénario, la liste des zones N1 (avec couleur stable) et
    l'affectation zone de chaque pays de pays_liste (fiche à jour > table statique > null).
    GET /api/carte/affectations?scenario=breakdown
    """
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    vault_root   = Path(cfg.get("vault_root", ""))
    scenario = request.args.get("scenario", "").strip()
    if not scenario:
        return jsonify({"error": "scenario requis"}), 400

    gui_dir = Path(__file__).parent
    zones_pays_path = gui_dir / "zones_pays.json"
    zones_pays = {}
    pays_liste = []
    if zones_pays_path.exists():
        try:
            zones_pays = json.loads(zones_pays_path.read_text(encoding="utf-8"))
            pays_liste = zones_pays.get("pays_liste", [])
        except Exception:
            pass

    fresh_index = _build_origine_reelle_index(vault_root, scenario)
    scenario_fallback = zones_pays.get(scenario, {})

    affectations = {}
    for pays in pays_liste:
        n = _normalise_pays(pays)
        zone = fresh_index.get(n) or scenario_fallback.get(pays)
        affectations[pays] = zone

    zones_n1 = _scan_n1_zones_with_desc(vault_root, scenario)

    return jsonify({
        "scenario": scenario,
        "pays_liste": pays_liste,
        "affectations": affectations,
        "zones_n1": zones_n1,
    })


def _call_llm_text(prompt: str) -> str:
    """
    Appelle le LLM configuré (provider/model dans config.json) avec un prompt simple.
    Retourne le texte brut de la réponse. Lève une exception avec un message détaillé
    (y compris le corps de la réponse HTTP en cas d'erreur API) en cas d'échec.
    """
    import urllib.request
    import urllib.error

    cfg = load_config()
    llm = cfg.get("llm", {})
    provider = llm.get("provider", "mistral")

    def _ssl_context():
        """Contexte SSL utilisant les certificats certifi si le paquet est installé
        (contourne le problème classique macOS où les certificats racine ne sont
        pas liés au Python installé depuis python.org)."""
        try:
            import certifi
            import ssl
            return ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            return None  # utilise le contexte SSL par défaut du système

    def _do_request(url, body, headers):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        ctx = _ssl_context()
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                err_body = ""
            raise RuntimeError(f"Erreur API {provider} (HTTP {e.code}) : {err_body[:500]}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Erreur réseau vers l'API {provider} : {e.reason}") from e

    if provider == "mistral":
        model = llm.get("model_mistral", "mistral-medium-latest")
        api_key = os.environ.get("MISTRAL_API_KEY", "")
        if not api_key:
            raise RuntimeError("MISTRAL_API_KEY manquante dans .env")
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }).encode("utf-8")
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        data = _do_request("https://api.mistral.ai/v1/chat/completions", body, headers)
        if "choices" not in data:
            raise RuntimeError(f"Réponse Mistral inattendue : {json.dumps(data)[:500]}")
        return data["choices"][0]["message"]["content"]

    else:  # claude
        model = llm.get("model_claude", "claude-sonnet-4-6")
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY manquante dans .env")
        body = json.dumps({
            "model": model,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        data = _do_request("https://api.anthropic.com/v1/messages", body, headers)
        if "content" not in data:
            raise RuntimeError(f"Réponse Claude inattendue : {json.dumps(data)[:500]}")
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


@app.route("/api/carte/propose", methods=["POST"])
def carte_propose():
    """
    Propose une affectation de zone pour un pays donné (appel LLM unique, pas de batch).
    Body JSON : { "pays": "Allemagne", "scenario": "breakdown" }
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    pays = data.get("pays", "").strip()
    scenario = data.get("scenario", "").strip()
    if not pays or not scenario:
        return jsonify({"error": "pays et scenario requis"}), 400

    zones_n1 = _scan_n1_zones_with_desc(vault_root, scenario)

    # Index pays -> zone (à jour, source de vérité = geographie/{scenario}.md) pour
    # afficher au LLM les pays déjà rattachés à chaque zone. La description narrative
    # seule peut ne citer aucun nom de pays explicite (villes, concepts, factions), ce
    # qui laisse le LLM sans signal géographique fiable pour rattacher un nouveau pays.
    fresh_index = _build_origine_reelle_index(vault_root, scenario)
    zone_to_pays = {}
    for pays_norm, slug in fresh_index.items():
        zone_to_pays.setdefault(slug, []).append(pays_norm)

    zones_desc = "\n".join(
        f"- {z['slug']} ({z['nom']}) : {z['description'][:300]}"
        + (f" [pays déjà affectés : {', '.join(sorted(zone_to_pays[z['slug']])[:10])}]"
           if z['slug'] in zone_to_pays else "")
        for z in zones_n1
    ) or "(aucune zone existante)"

    prompt = f"""Tu travailles sur l'univers narratif spéculatif "Ourrassol 2098", scénario "{scenario}".
Voici les zones géopolitiques de niveau 1 (N1) déjà définies pour ce scénario :

{zones_desc}

Le pays réel (2026) "{pays}" n'a pas encore d'affectation à une zone 2098 dans ce scénario.

Réponds UNIQUEMENT en JSON valide (rien avant, rien après), avec ce format exact :
{{
  "zone_existante_recommandee": "slug_de_zone_ou_null",
  "nouvelle_zone_proposee": {{"slug": "nouveau_slug", "nom": "Nom de la zone", "description": "1-2 phrases"}} ou null,
  "justification": "1-3 phrases expliquant le choix, cohérentes avec la logique narrative du scénario"
}}

Recommande une zone existante si "{pays}" y a narrativement sa place. Base ta décision en priorité sur la proximité géographique/continentale avec les pays déjà affectés listés entre crochets (quand ils sont présents) — la description narrative seule peut ne pas mentionner tous les pays membres. Propose une nouvelle zone N1 uniquement si aucune zone existante ne convient géographiquement ni narrativement."""

    try:
        raw_response = _call_llm_text(prompt)
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        proposal = json.loads(cleaned)
        return jsonify({"ok": True, "proposal": proposal})
    except Exception as e:
        import traceback
        traceback.print_exc()  # trace complète dans le terminal Flask
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500


@app.route("/api/carte/assign", methods=["POST"])
def carte_assign():
    """
    Applique une affectation pays -> zone.
    Body JSON : {
      "pays": "Allemagne", "scenario": "breakdown", "action": "absorber"|"creer",
      "zone_slug": "arc_sahelo_mediterraneen",                       (si absorber)
      "nouvelle_zone": {"slug":..., "nom":..., "description":...}    (si creer)
    }
    Écrit dans geographie/{scenario}.md (origine_reelle) ET zones_pays.json (fallback).
    """
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    vault_root   = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    pays = data.get("pays", "").strip()
    scenario = data.get("scenario", "").strip()
    action = data.get("action", "").strip()

    if not pays or not scenario or action not in ("absorber", "creer"):
        return jsonify({"error": "pays, scenario, action (absorber|creer) requis"}), 400

    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return jsonify({"error": f"Fiche géographie introuvable : {geo_file}"}), 404

    try:
        import yaml as _yaml
        raw = geo_file.read_text(encoding="utf-8")
        parts = raw.split("---")
        if len(parts) < 3:
            return jsonify({"error": "Format de fiche géographie inattendu"}), 500
        fm = _yaml.safe_load(parts[1]) or {}
        zones = fm.get("zones") or []

        if action == "absorber":
            zone_slug = data.get("zone_slug", "").strip()
            if not zone_slug:
                return jsonify({"error": "zone_slug requis pour absorber"}), 400
            target = next((z for z in zones if z.get("slug") == zone_slug), None)
            if not target:
                return jsonify({"error": f"Zone '{zone_slug}' introuvable dans la fiche"}), 404

            # Retirer le pays de toute autre zone (cas d'une bascule d'affectation)
            for z in zones:
                if z is target:
                    continue
                origine = z.get("origine_reelle")
                if isinstance(origine, list):
                    z["origine_reelle"] = [
                        o for o in origine
                        if not (isinstance(o, dict) and o.get("entite") == pays)
                    ]

            origine = target.setdefault("origine_reelle", [])
            if not any(isinstance(o, dict) and o.get("entite") == pays for o in origine):
                origine.append({"entite": pays})
            final_slug = zone_slug

        else:  # creer
            nz = data.get("nouvelle_zone") or {}
            slug = str(nz.get("slug", "")).strip()
            nom = str(nz.get("nom", "")).strip()
            description = str(nz.get("description", "")).strip()
            if not slug or not nom:
                return jsonify({"error": "nouvelle_zone.slug et .nom requis"}), 400
            if any(z.get("slug") == slug for z in zones):
                return jsonify({"error": f"Le slug '{slug}' existe déjà"}), 409

            # Retirer le pays de toute zone existante (cas d'une bascule vers une nouvelle zone)
            for z in zones:
                origine = z.get("origine_reelle")
                if isinstance(origine, list):
                    z["origine_reelle"] = [
                        o for o in origine
                        if not (isinstance(o, dict) and o.get("entite") == pays)
                    ]

            zones.append({
                "slug": slug,
                "nom": nom,
                "niveau": 1,
                "parent": None,
                "description": description,
                "origine_reelle": [{"entite": pays}],
            })
            final_slug = slug

        fm["zones"] = zones

        # Backup + réécriture (frontmatter YAML régénéré, reste du fichier inchangé)
        bak = geo_file.with_suffix(geo_file.suffix + ".bak")
        bak.write_text(raw, encoding="utf-8")

        new_fm = _yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
        rest = "---".join(parts[2:])
        new_content = "---\n" + new_fm + "---" + rest
        geo_file.write_text(new_content, encoding="utf-8")

        # Mise à jour du fallback zones_pays.json
        gui_dir = Path(__file__).parent
        zones_pays_path = gui_dir / "zones_pays.json"
        if zones_pays_path.exists():
            zp = json.loads(zones_pays_path.read_text(encoding="utf-8"))
            zp.setdefault(scenario, {})[pays] = final_slug
            zones_pays_path.write_text(json.dumps(zp, indent=2, ensure_ascii=False), encoding="utf-8")

        # Retirer de zones_manquantes.yaml si présent
        try:
            log_path = vault_root / "documentation" / "need_action" / "zones_manquantes.yaml"
            if log_path.exists():
                existing = _yaml.safe_load(log_path.read_text(encoding="utf-8")) or {}
                entries = existing.get("zones_manquantes", [])
                entries = [e for e in entries
                           if not (e.get("pays") == pays and e.get("scenario") == scenario)]
                existing["zones_manquantes"] = entries
                log_path.write_text(
                    _yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
                    encoding="utf-8"
                )
        except Exception:
            pass

        return jsonify({"ok": True, "zone": final_slug})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/carte/ignorer", methods=["POST"])
def carte_ignorer():
    """Marque un pays comme blanc intentionnel pour ce scénario (crée l'entrée si absente)."""
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    pays = data.get("pays", "").strip()
    scenario = data.get("scenario", "").strip()
    if not pays or not scenario:
        return jsonify({"error": "pays et scenario requis"}), 400

    _log_zone_manquante(vault_root, pays, scenario)

    try:
        import yaml as _yaml
        log_path = vault_root / "documentation" / "need_action" / "zones_manquantes.yaml"
        existing = _yaml.safe_load(log_path.read_text(encoding="utf-8")) or {}
        entries = existing.get("zones_manquantes", [])
        for e in entries:
            if e.get("pays") == pays and e.get("scenario") == scenario:
                e["statut"] = "blanc_intentionnel"
        existing["zones_manquantes"] = entries
        log_path.write_text(
            _yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8"
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Rapport d'impact — bascule de pays vers une autre zone ──────────────────

def _fold(s: str) -> str:
    """Normalisation simple pour recherche substring insensible à la casse/accents."""
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()


def _load_all_zones(vault_root: Path, scenario: str) -> list:
    """Charge TOUTES les zones (tous niveaux) de la fiche geographie/{scenario}.md."""
    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return []
    try:
        import yaml as _yaml
        raw = geo_file.read_text(encoding="utf-8")
        parts = raw.split("---")
        fm = _yaml.safe_load(parts[1]) if len(parts) >= 2 else {}
        return (fm or {}).get("zones") or []
    except Exception:
        return []


def _zone_descendants(zones: list, root_slug: str) -> list:
    """Retourne tous les slugs descendants (N2, N3...) d'une zone, root inclus."""
    by_parent = {}
    for z in zones:
        p = z.get("parent")
        if p:
            by_parent.setdefault(p, []).append(z)
    result = []
    def _walk(slug):
        result.append(slug)
        for child in by_parent.get(slug, []):
            _walk(child.get("slug"))
    _walk(root_slug)
    return result


def _scan_registre_evenements(vault_root: Path, scenario: str, pays_folded: str) -> list:
    """Cherche le nom du pays dans les lignes evenement_cle de registre_evenements.md,
    limité à la section du scénario concerné."""
    reg_path = vault_root / "documentation" / "registre_evenements.md"
    if not reg_path.exists():
        # essaye aussi à la racine du vault sans sous-dossier documentation
        reg_path = vault_root / "registre_evenements.md"
        if not reg_path.exists():
            return []
    hits = []
    current_section = None
    try:
        for line in reg_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                current_section = stripped[3:].strip()
                continue
            if current_section != scenario:
                continue
            if stripped.startswith("|") and pays_folded in _fold(stripped):
                hits.append(stripped)
    except Exception:
        pass
    return hits[:30]


def _scan_instances_events(vault_root: Path, scenario: str, pays_folded: str,
                            zone_slugs_liees: set) -> tuple:
    """
    Parcourt instances/ et event_instances/ pour ce scénario :
    - instances_liees : localisation.zone dans zone_slugs_liees
    - mentions_texte : pays mentionné n'importe où dans le fichier (texte libre)
    Retourne (instances_liees, mentions_texte).
    """
    import yaml as _yaml
    instances_liees = []
    mentions_texte = []

    for dossier in ("instances", "event_instances"):
        d = vault_root / dossier
        if not d.exists():
            continue
        for f in d.glob("*.md"):
            try:
                raw = f.read_text(encoding="utf-8")
            except Exception:
                continue

            parts = raw.split("---")
            fm = {}
            if len(parts) >= 2:
                try:
                    fm = _yaml.safe_load(parts[1]) or {}
                except Exception:
                    fm = {}

            if fm.get("scenario") != scenario:
                continue

            slug = fm.get("slug", f.stem)
            zone = (fm.get("localisation") or {}).get("zone")

            if zone in zone_slugs_liees:
                instances_liees.append({"slug": slug, "zone": zone, "type": fm.get("type", dossier)})

            folded_raw = _fold(raw)
            if pays_folded in folded_raw:
                idx = folded_raw.find(pays_folded)
                extrait = raw[max(0, idx - 60):idx + 60].replace("\n", " ").strip()
                mentions_texte.append({"slug": slug, "type": fm.get("type", dossier), "extrait": f"…{extrait}…"})

    return instances_liees[:100], mentions_texte[:50]


@app.route("/api/carte/impact", methods=["POST"])
def carte_impact():
    """
    Rapport d'impact en lecture seule pour une bascule de zone.
    Body JSON : {
      "pays": "Russie", "scenario": "breakdown",
      "action": "absorber"|"creer",
      "zone_slug": "..."           (si absorber, la zone cible)
      "nouvelle_zone": {...}       (si creer)
    }
    N'écrit RIEN sur les fiches — sauf le rapport lui-même dans documentation/need_action/.
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    pays = data.get("pays", "").strip()
    scenario = data.get("scenario", "").strip()
    action = data.get("action", "").strip()

    if not pays or not scenario:
        return jsonify({"error": "pays et scenario requis"}), 400

    zones = _load_all_zones(vault_root, scenario)
    pays_folded = _fold(pays)

    # Zone actuelle du pays (avant bascule)
    ancienne_zone = None
    for z in zones:
        for o in (z.get("origine_reelle") or []):
            if isinstance(o, dict) and o.get("entite") == pays:
                ancienne_zone = z.get("slug")
                break
        if ancienne_zone:
            break

    cible_slug = data.get("zone_slug", "").strip() if action == "absorber" else \
        (data.get("nouvelle_zone") or {}).get("slug", "")

    # Sous-zones potentiellement orphelines : descendantes de l'ancienne zone
    # dont l'origine_reelle mentionne ce pays
    sous_zones_orphelines = []
    if ancienne_zone:
        descendants = set(_zone_descendants(zones, ancienne_zone)) - {ancienne_zone}
        by_slug = {z.get("slug"): z for z in zones}
        for slug in descendants:
            z = by_slug.get(slug)
            if not z:
                continue
            for o in (z.get("origine_reelle") or []):
                entite = o.get("entite", "") if isinstance(o, dict) else ""
                if pays_folded in _fold(entite):
                    sous_zones_orphelines.append({
                        "slug": slug, "nom": z.get("nom", slug),
                        "niveau": z.get("niveau"), "origine": entite,
                    })
                    break

    # Zones structurellement liées (ancienne + cible) pour le scan instances/events
    zone_slugs_liees = set()
    if ancienne_zone:
        zone_slugs_liees |= set(_zone_descendants(zones, ancienne_zone))
    if cible_slug:
        zone_slugs_liees |= set(_zone_descendants(zones, cible_slug))

    instances_liees, mentions_texte = _scan_instances_events(
        vault_root, scenario, pays_folded, zone_slugs_liees
    )
    registre_hits = _scan_registre_evenements(vault_root, scenario, pays_folded)

    rapport = {
        "pays": pays,
        "scenario": scenario,
        "ancienne_zone": ancienne_zone,
        "nouvelle_zone": cible_slug,
        "sous_zones_orphelines": sous_zones_orphelines,
        "instances_liees": instances_liees,
        "mentions_texte": mentions_texte,
        "registre_hits": registre_hits,
        "rien_detecte": not (sous_zones_orphelines or instances_liees or mentions_texte or registre_hits),
    }

    # Sauvegarde du rapport (lecture seule, écrase le précédent pour ce pays/scénario)
    try:
        out_dir = vault_root / "documentation" / "need_action"
        out_dir.mkdir(parents=True, exist_ok=True)
        slug_pays = re.sub(r"[^a-z0-9]+", "_", _fold(pays)).strip("_")
        out_path = out_dir / f"impact_bascule_{slug_pays}_{scenario}.md"
        lignes = [
            f"# Rapport d'impact — {pays} ({scenario})",
            f"",
            f"Bascule évaluée : `{ancienne_zone or '—'}` → `{cible_slug or '—'}`",
            f"",
            f"## Sous-zones potentiellement orphelines ({len(sous_zones_orphelines)})",
        ]
        for sz in sous_zones_orphelines:
            lignes.append(f"- `{sz['slug']}` ({sz['nom']}, niveau {sz['niveau']}) — origine : {sz['origine']}")
        lignes.append(f"\n## Instances/événements liés structurellement ({len(instances_liees)})")
        for it in instances_liees:
            lignes.append(f"- `{it['slug']}` — zone : {it['zone']}")
        lignes.append(f"\n## Mentions textuelles de « {pays} » ({len(mentions_texte)})")
        for m in mentions_texte:
            lignes.append(f"- `{m['slug']}` — {m['extrait']}")
        lignes.append(f"\n## Registre des événements ({len(registre_hits)})")
        for r in registre_hits:
            lignes.append(f"- {r}")
        out_path.write_text("\n".join(lignes) + "\n", encoding="utf-8")
        rapport["rapport_path"] = str(out_path)
    except Exception:
        pass

    return jsonify(rapport)


# ── P7 étape 1 : renommage de zone (slug + nom), propagation vérifiée le 12 juillet
#    2026 : YAML zones[].slug/.nom + zones[].parent des enfants directs + wikilinks
#    "sous [[slug]]" dans le corps markdown du MÊME fichier geographie/{scenario}.md
#    (jamais ailleurs dans le vault, vérifié par grep exhaustif) + instances/*.md +
#    event_instances/*.md (localisation.zone) + zones_pays.json. entites/ est HORS
#    scope : aucune référence de zone n'y a été trouvée, seulement des collisions de
#    nommage (une entité peut porter le même slug qu'une zone du même lieu réel,
#    ex: nairobi_crrc existe des deux côtés) — d'où le contrôle de collision
#    ci-dessous, en avertissement et non en blocage puisque cette collision existe
#    déjà légitimement ailleurs dans le vault.

def _rename_zone_body_text(body, old_slug, new_slug, old_nom=None, new_nom=None):
    """
    Renomme dans le corps markdown (hors frontmatter) :
    1) tous les wikilinks "sous [[old_slug]]" des enfants directs -> new_slug
    2) le header de la zone elle-même ("### {nom}" niveau 1, ou "#### {nom} — sous
       [[parent]]" / "##### {nom} — sous [[parent]]" niveau 2/3) si le nom change
    3) les lignes "**Rivaux** : slug1, slug2" / "**Alliés** : ..." — texte brut,
       PAS des wikilinks (découvert le 12 juillet 2026 en testant sur un vrai
       fichier : relations.allies/rivaux peut référencer n'importe quelle zone du
       scénario, pas seulement les enfants directs de la zone renommée)
    Retourne (nouveau_body, a_change: bool).
    """
    changed = False

    pattern_sous = re.compile(r"sous \[\[" + re.escape(old_slug) + r"\]\]")
    new_body, n = pattern_sous.subn(f"sous [[{new_slug}]]", body)
    if n:
        changed = True
        body = new_body

    if old_nom and new_nom and old_nom != new_nom:
        header_pattern = re.compile(
            r"^(#{1,6}) " + re.escape(old_nom) + r"( — sous \[\[.+?\]\])?$",
            re.MULTILINE
        )
        new_body2, n2 = header_pattern.subn(
            lambda m: f"{m.group(1)} {new_nom}{m.group(2) or ''}", body
        )
        if n2:
            changed = True
            body = new_body2

    relations_pattern = re.compile(
        r"^(\*\*(?:Rivaux|Alliés)\*\* : .*)$", re.MULTILINE
    )
    slug_boundary = re.compile(r"(?<![a-z0-9_])" + re.escape(old_slug) + r"(?![a-z0-9_])")

    def _sub_relations_line(m):
        nonlocal changed
        line, n3 = slug_boundary.subn(new_slug, m.group(1))
        if n3:
            changed = True
        return line

    body = relations_pattern.sub(_sub_relations_line, body)

    return body, changed


def _apply_rename_geographie(vault_root, scenario, ancien_slug, nouveau_slug,
                              nouveau_nom, dry_run):
    """
    dry_run=True  : ne modifie rien, retourne juste {"zone":..., "enfants_directs":...}
    dry_run=False : applique réellement (avec .bak), retourne {"ok":True, ...}
    Dans les deux cas, {"error": "..."} si la zone/le slug cible pose problème.
    """
    import yaml as _yaml
    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return {"error": f"Fiche géographie introuvable : {geo_file}"}

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {"error": "Format de fiche géographie inattendu"}
    fm = _yaml.safe_load(parts[1]) or {}
    body = parts[2]
    zones = fm.get("zones") or []

    target = next((z for z in zones if z.get("slug") == ancien_slug), None)
    if not target:
        return {"error": f"Zone '{ancien_slug}' introuvable dans {scenario}"}

    if nouveau_slug != ancien_slug and any(z.get("slug") == nouveau_slug for z in zones):
        return {"error": f"Le slug '{nouveau_slug}' existe déjà dans ce scénario"}

    enfants = [z for z in zones if z.get("parent") == ancien_slug]
    ancien_nom = target.get("nom")

    # relations.allies/rivaux peut référencer n'importe quelle zone du scénario,
    # pas seulement les enfants directs de la zone renommée (ex: deux zones
    # niveau 1 rivales) — découvert le 12 juillet 2026 en testant sur un vrai
    # fichier (arc_eurasien_central référencé comme rival par 9 zones sans lien
    # de parenté avec elle).
    zones_relations_maj = []
    if not dry_run:
        for z in zones:
            rel = z.get("relations")
            if not isinstance(rel, dict):
                continue
            touched = False
            for cle in ("allies", "rivaux"):
                lst = rel.get(cle)
                if isinstance(lst, list) and ancien_slug in lst:
                    rel[cle] = [nouveau_slug if s == ancien_slug else s for s in lst]
                    touched = True
            if touched:
                zones_relations_maj.append(z.get("slug"))

    if dry_run:
        zones_relations_liees = [
            z.get("slug") for z in zones
            if isinstance(z.get("relations"), dict) and (
                ancien_slug in (z["relations"].get("allies") or []) or
                ancien_slug in (z["relations"].get("rivaux") or [])
            )
        ]
        return {
            "zone": {"slug": ancien_slug, "nom": ancien_nom,
                     "niveau": target.get("niveau"), "parent": target.get("parent")},
            "enfants_directs": [{"slug": e.get("slug"), "nom": e.get("nom")} for e in enfants],
            "zones_relations_liees": zones_relations_liees,
        }

    target["slug"] = nouveau_slug
    if nouveau_nom:
        target["nom"] = nouveau_nom
    for e in enfants:
        e["parent"] = nouveau_slug

    new_body, body_maj = _rename_zone_body_text(
        body, ancien_slug, nouveau_slug, ancien_nom, nouveau_nom
    )

    fm["zones"] = zones
    bak = geo_file.with_suffix(geo_file.suffix + ".bak")
    bak.write_text(raw, encoding="utf-8")

    new_fm = _yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    geo_file.write_text("---\n" + new_fm + "---" + new_body, encoding="utf-8")

    return {"ok": True, "ancien_nom": ancien_nom, "enfants_maj": len(enfants),
             "body_maj": body_maj, "zones_relations_maj": len(zones_relations_maj)}


def _rename_zone_in_instances(vault_root, scenario, ancien_slug, nouveau_slug, dry_run):
    """Scanne instances/ + event_instances/ pour ce scénario : localisation.zone ==
    ancien_slug. dry_run=True : liste seulement. dry_run=False : réécrit aussi."""
    import yaml as _yaml
    touches = []
    for dossier in ("instances", "event_instances"):
        d = vault_root / dossier
        if not d.exists():
            continue
        for f in d.glob("*.md"):
            try:
                raw = f.read_text(encoding="utf-8")
            except Exception:
                continue
            parts = raw.split("---", 2)
            if len(parts) < 3:
                continue
            try:
                fm = _yaml.safe_load(parts[1]) or {}
            except Exception:
                continue
            if fm.get("scenario") != scenario:
                continue
            loc = fm.get("localisation") or {}
            if loc.get("zone") != ancien_slug:
                continue
            touches.append({"slug": fm.get("slug", f.stem), "type": fm.get("type", dossier)})
            if not dry_run:
                loc["zone"] = nouveau_slug
                fm["localisation"] = loc
                new_fm = _yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
                f.write_text("---\n" + new_fm + "---" + parts[2], encoding="utf-8")
    return touches


def _rename_zone_in_zones_pays(zones_pays_path, scenario, ancien_slug, nouveau_slug, dry_run):
    if not zones_pays_path.exists():
        return []
    zp = json.loads(zones_pays_path.read_text(encoding="utf-8"))
    sc = zp.get(scenario, {})
    touches = [pays for pays, slug in sc.items() if slug == ancien_slug]
    if not dry_run and touches:
        for pays in touches:
            sc[pays] = nouveau_slug
        zp[scenario] = sc
        zones_pays_path.write_text(json.dumps(zp, indent=2, ensure_ascii=False), encoding="utf-8")
    return touches


@app.route("/api/carte/impact_renommage_zone", methods=["POST"])
def carte_impact_renommage_zone():
    """
    Rapport d'impact en lecture seule pour un renommage de zone (P7 étape 1).
    Body JSON : { "scenario":..., "ancien_slug":...,
                  "nouveau_slug":... (optionnel, pour vérifier une collision de slug),
                  "nouveau_nom":... (optionnel) }
    N'écrit RIEN.
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    ancien_slug = data.get("ancien_slug", "").strip()
    nouveau_slug = data.get("nouveau_slug", "").strip()

    if not scenario or not ancien_slug:
        return jsonify({"error": "scenario et ancien_slug requis"}), 400

    geo_report = _apply_rename_geographie(
        vault_root, scenario, ancien_slug, nouveau_slug or ancien_slug, None, dry_run=True
    )
    if "error" in geo_report:
        return jsonify(geo_report), 404

    instances_liees = _rename_zone_in_instances(vault_root, scenario, ancien_slug, "—", dry_run=True)

    gui_dir = Path(__file__).parent
    zones_pays_path = gui_dir / "zones_pays.json"
    pays_lies = _rename_zone_in_zones_pays(zones_pays_path, scenario, ancien_slug, "—", dry_run=True)

    collision_entite = None
    if nouveau_slug and (vault_root / "entites" / f"{nouveau_slug}.md").exists():
        collision_entite = nouveau_slug

    return jsonify({
        "zone": geo_report["zone"],
        "enfants_directs": geo_report["enfants_directs"],
        "zones_relations_liees": geo_report["zones_relations_liees"],
        "instances_liees": instances_liees,
        "pays_zones_pays_json": pays_lies,
        "collision_slug_entite": collision_entite,
        "rien_detecte": not (geo_report["enfants_directs"] or geo_report["zones_relations_liees"]
                              or instances_liees or pays_lies),
    })


@app.route("/api/carte/renommer_zone", methods=["POST"])
def carte_renommer_zone():
    """
    Applique le renommage d'un slug (et éventuellement du nom affiché) d'une zone.
    Body JSON : { "scenario":..., "ancien_slug":..., "nouveau_slug":...,
                  "nouveau_nom":... (optionnel) }
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    ancien_slug = data.get("ancien_slug", "").strip()
    nouveau_slug = data.get("nouveau_slug", "").strip()
    nouveau_nom = data.get("nouveau_nom", "").strip() or None

    if not scenario or not ancien_slug or not nouveau_slug:
        return jsonify({"error": "scenario, ancien_slug, nouveau_slug requis"}), 400
    if not re.match(r"^[a-z0-9_]+$", nouveau_slug):
        return jsonify({"error": "nouveau_slug : lettres minuscules, chiffres, underscores uniquement"}), 400

    geo_result = _apply_rename_geographie(
        vault_root, scenario, ancien_slug, nouveau_slug, nouveau_nom, dry_run=False
    )
    if "error" in geo_result:
        code = 409 if "existe déjà" in geo_result["error"] else 404
        return jsonify(geo_result), code

    instances_touchees = _rename_zone_in_instances(vault_root, scenario, ancien_slug, nouveau_slug, dry_run=False)

    gui_dir = Path(__file__).parent
    zones_pays_path = gui_dir / "zones_pays.json"
    pays_touches = _rename_zone_in_zones_pays(zones_pays_path, scenario, ancien_slug, nouveau_slug, dry_run=False)

    return jsonify({
        "ok": True,
        "nouveau_slug": nouveau_slug,
        "enfants_maj": geo_result["enfants_maj"],
        "zones_relations_maj": geo_result["zones_relations_maj"],
        "body_maj": geo_result["body_maj"],
        "instances_maj": len(instances_touchees),
        "pays_maj": len(pays_touches),
    })


# ── P7 étape 2, phase 1 : visualisation en arbre des sous-zones (lecture seule,
#    12 juillet 2026). Les zones niveau 2/3 n'ont ni coordonnées lat/lng ni
#    correspondance polygone sur la carte Leaflet (elles ne sont pas géocodées) —
#    la structure parent/niveau/slug déjà présente dans le YAML EST un arbre,
#    donc autant l'afficher tel quel plutôt que d'inventer un positionnement
#    géographique peu fiable pour du contenu fictif. Aucune action pour l'instant
#    (renommer/reparent des niveaux 2/3 viendra dans une phase 2 séparée).

def _build_zone_tree(zones, root_slug):
    """Construit un arbre imbriqué {slug, nom, niveau, type, statut, enfants:[...]}
    à partir de la liste plate de zones (tous niveaux) d'un scénario."""
    by_parent = {}
    for z in zones:
        p = z.get("parent")
        if p:
            by_parent.setdefault(p, []).append(z)
    by_slug = {z.get("slug"): z for z in zones}

    def _node(slug):
        z = by_slug.get(slug)
        if not z:
            return None
        enfants = [_node(c.get("slug")) for c in by_parent.get(slug, [])]
        return {
            "slug": z.get("slug"),
            "nom": z.get("nom"),
            "niveau": z.get("niveau"),
            "type": z.get("type"),
            "statut": z.get("statut"),
            "origine_reelle": z.get("origine_reelle") or [],
            "enfants": [e for e in enfants if e is not None],
        }

    return _node(root_slug)


def _chemin_vers_racine(zone: dict, by_slug: dict) -> list:
    """
    Chemin complet de la racine N1 jusqu'à `zone` (zone incluse), sous
    forme de liste [{slug, nom, niveau}, ...] dans l'ordre racine -> zone.
    Sert de fil d'Ariane pour savoir quelle zone N1 ouvrir dans la Carte
    pour atteindre une zone niveau 2/3, invisible dans la liste principale
    (voir _scan_n1_zones_with_desc, qui ne retient que niveau == 1). Cas
    réel qui a motivé cette route (14 juillet 2026) : delta_rhone_fermes_
    verticales, niveau 3, invisible sans savoir qu'il fallait d'abord
    ouvrir nouveau_califat_barcelone dans la Carte -- son parent immédiat
    (corridor_iberique_energetique) est lui-même une sous-zone niveau 2,
    pas la racine attendue. Anti-cycle : s'arrête si un slug est revisité.
    """
    chemin = []
    courant = zone
    vus = set()
    while courant is not None:
        slug = courant.get("slug")
        if slug in vus:
            break
        vus.add(slug)
        chemin.append({
            "slug": slug,
            "nom": courant.get("nom"),
            "niveau": courant.get("niveau"),
        })
        parent_slug = courant.get("parent")
        courant = by_slug.get(parent_slug) if parent_slug else None
    return list(reversed(chemin))


@app.route("/api/carte/rechercher_zone", methods=["GET"])
def carte_rechercher_zone():
    """
    Recherche une zone par nom ou slug, TOUS NIVEAUX confondus -- contrairement
    à la liste principale de la Carte (/api/carte/affectations, zones_n1) qui
    n'affiche que les zones niveau 1. Pour chaque résultat, retourne le
    chemin complet depuis la racine N1 (celle à ouvrir dans la Carte) jusqu'à
    la zone trouvée, pour ne plus avoir à deviner ou remonter la chaîne
    `parent` à la main.

    GET /api/carte/rechercher_zone?scenario=new_sustainability&q=rhone
    Retourne { scenario, q, resultats: [ { slug, nom, niveau, chemin: [...] } ] }
    Recherche insensible à la casse et aux accents (voir _fold). Triés par
    niveau puis nom -- les zones N1 correspondantes remontent en premier.
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    scenario = request.args.get("scenario", "").strip()
    q = request.args.get("q", "").strip()

    if not scenario or not q:
        return jsonify({"error": "scenario et q requis"}), 400
    if len(q) < 2:
        return jsonify({"error": "q trop court (minimum 2 caractères)"}), 400

    zones = _load_all_zones(vault_root, scenario)
    if not zones:
        return jsonify({"error": f"Aucune zone trouvée pour le scénario '{scenario}'"}), 404

    by_slug = {z.get("slug"): z for z in zones if z.get("slug")}
    q_fold = _fold(q)

    resultats = []
    for z in zones:
        slug = str(z.get("slug", ""))
        nom = str(z.get("nom", ""))
        if q_fold in _fold(nom) or q_fold in _fold(slug):
            resultats.append({
                "slug": slug,
                "nom": nom,
                "niveau": z.get("niveau"),
                "chemin": _chemin_vers_racine(z, by_slug),
            })

    resultats.sort(key=lambda r: (r["niveau"] if isinstance(r["niveau"], int) else 1, r["nom"] or ""))

    return jsonify({"scenario": scenario, "q": q, "resultats": resultats})


@app.route("/api/carte/arbre_zone", methods=["GET"])
def carte_arbre_zone():
    """
    GET /api/carte/arbre_zone?scenario=breakdown&slug=arc_eurasien_central
    Arbre hiérarchique en lecture seule d'une zone (niveau 1 en pratique, mais
    fonctionne pour n'importe quel slug) et de tous ses descendants niveau 2/3.
    N'écrit rien.
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    scenario = request.args.get("scenario", "").strip()
    slug = request.args.get("slug", "").strip()

    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400

    zones = _load_all_zones(vault_root, scenario)
    if not zones:
        return jsonify({"error": f"Aucune zone trouvée pour le scénario '{scenario}'"}), 404

    arbre = _build_zone_tree(zones, slug)
    if arbre is None:
        return jsonify({"error": f"Zone '{slug}' introuvable dans '{scenario}'"}), 404

    return jsonify({"arbre": arbre})


# ── P7 étape 2, phase 2 : reparent (13 juillet 2026). Déplace une zone niveau
#    2/3 (et tout son sous-arbre, qui suit — décision explicite de l'utilisateur)
#    vers un nouveau parent, à n'importe quelle profondeur (pas seulement le même
#    niveau) : le niveau de toute la branche est recalculé en cascade selon le
#    delta de profondeur induit par le nouveau parent. Contrairement au
#    renommage, le SLUG de la zone déplacée ne change jamais, donc aucune
#    propagation vers instances/event_instances/zones_pays.json n'est
#    nécessaire ici — seul geographie/{scenario}.md est concerné (YAML +
#    en-têtes markdown des zones dont le niveau change).

def _zone_header_regex(nom):
    return re.compile(r"^(#{1,6}) " + re.escape(nom) + r"( — sous \[\[.+?\]\])?$", re.MULTILINE)


def _reparent_zone_body_text(body, slug, nouveau_parent_slug, sous_arbre_by_slug):
    """
    sous_arbre_by_slug : {slug: zone_dict} pour tout le sous-arbre déplacé
    (racine incluse), avec le NIVEAU DÉJÀ MIS À JOUR sur chaque entrée.
    nouveau_parent_slug=None : la zone déplacée devient racine (niveau 1) —
    son header perd le suffixe "— sous [[...]]" entièrement, comme toute
    zone niveau 1 sans parent.
    Met à jour le niveau du header (#### vs #####...) pour chaque zone du
    sous-arbre dont la profondeur a changé, et change la cible du wikilink
    "sous [[...]]" uniquement pour la zone déplacée elle-même (ses
    descendants gardent le même parent immédiat, donc le même wikilink texte,
    seul le niveau de titre peut changer).
    """
    changed = False
    for s, z in sous_arbre_by_slug.items():
        nom = z.get("nom")
        niveau = z.get("niveau")
        if not nom or not niveau:
            continue
        new_hashes = "#" * (niveau + 2)

        def _repl(m, s=s, new_hashes=new_hashes):
            nonlocal changed
            suffix = m.group(2) or ""
            if s == slug:
                suffix = f" — sous [[{nouveau_parent_slug}]]" if nouveau_parent_slug else ""
            changed = True
            return f"{new_hashes} {nom}{suffix}"

        body = _zone_header_regex(nom).sub(_repl, body)

    return body, changed


def _apply_reparent_zone(vault_root, scenario, slug, nouveau_parent_slug, dry_run):
    """
    nouveau_parent_slug=None (ou "") : PROMOTION en zone niveau 1 autonome
    (parent: null), plutôt qu'un rattachement à un parent existant — cas
    ajouté le 13 juillet 2026 quand aucune zone existante ne convient
    sémantiquement (ex: le cas Barcelone, où aucune zone Europe n'existait
    dans le scénario).
    """
    import yaml as _yaml
    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return {"error": f"Fiche géographie introuvable : {geo_file}"}

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {"error": "Format de fiche géographie inattendu"}
    fm = _yaml.safe_load(parts[1]) or {}
    body = parts[2]
    zones = fm.get("zones") or []
    by_slug = {z.get("slug"): z for z in zones}

    target = by_slug.get(slug)
    if not target:
        return {"error": f"Zone '{slug}' introuvable"}

    devient_racine = not nouveau_parent_slug
    nouveau_parent = None
    if not devient_racine:
        if slug == nouveau_parent_slug:
            return {"error": "Une zone ne peut pas devenir son propre parent"}
        nouveau_parent = by_slug.get(nouveau_parent_slug)
        if not nouveau_parent:
            return {"error": f"Nouveau parent '{nouveau_parent_slug}' introuvable"}

    ancien_parent_slug = target.get("parent")
    if (devient_racine and ancien_parent_slug is None) or \
       (not devient_racine and ancien_parent_slug == nouveau_parent_slug):
        return {"error": "Cette zone est déjà rattachée à ce parent"}

    sous_arbre_slugs = _zone_descendants(zones, slug)  # racine (slug) incluse
    if not devient_racine and nouveau_parent_slug in sous_arbre_slugs:
        return {"error": f"Cycle détecté : '{nouveau_parent_slug}' est un descendant de '{slug}', "
                          f"impossible de déplacer une zone sous l'une de ses propres sous-zones"}

    ancien_niveau = target.get("niveau") or 1
    nouveau_niveau_racine = 1 if devient_racine else (nouveau_parent.get("niveau") or 1) + 1
    delta = nouveau_niveau_racine - ancien_niveau

    if dry_run:
        return {
            "zone": {"slug": slug, "nom": target.get("nom"), "niveau": ancien_niveau,
                     "ancien_parent": ancien_parent_slug},
            "nouveau_parent": {"slug": nouveau_parent_slug, "nom": nouveau_parent.get("nom"),
                                "niveau": nouveau_parent.get("niveau")} if not devient_racine else None,
            "devient_racine": devient_racine,
            "nouveau_niveau_zone": nouveau_niveau_racine,
            "changement_de_profondeur": delta != 0,
            "descendants_impactes": [
                {"slug": s, "nom": by_slug[s].get("nom"),
                 "ancien_niveau": by_slug[s].get("niveau"),
                 "nouveau_niveau": (by_slug[s].get("niveau") or 1) + delta}
                for s in sous_arbre_slugs if s != slug
            ],
        }

    ancien_nom = target.get("nom")
    for s in sous_arbre_slugs:
        z = by_slug[s]
        z["niveau"] = (z.get("niveau") or 1) + delta
    target["parent"] = None if devient_racine else nouveau_parent_slug

    fm["zones"] = zones
    bak = geo_file.with_suffix(geo_file.suffix + ".bak")
    bak.write_text(raw, encoding="utf-8")

    sous_arbre_by_slug = {s: by_slug[s] for s in sous_arbre_slugs}
    new_body, body_maj = _reparent_zone_body_text(
        body, slug, nouveau_parent_slug if not devient_racine else None, sous_arbre_by_slug
    )

    new_fm = _yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    geo_file.write_text("---\n" + new_fm + "---" + new_body, encoding="utf-8")

    return {
        "ok": True, "ancien_nom": ancien_nom, "nouveau_niveau": nouveau_niveau_racine,
        "devient_racine": devient_racine,
        "changement_de_profondeur": delta != 0,
        "descendants_maj": len(sous_arbre_slugs) - 1, "body_maj": body_maj,
    }


@app.route("/api/carte/impact_reparent_zone", methods=["POST"])
def carte_impact_reparent_zone():
    """Rapport d'impact en lecture seule pour un reparent (P7 étape 2 phase 2).
    Body JSON : { "scenario":..., "slug":..., "nouveau_parent_slug":... }
    nouveau_parent_slug vide/absent = promotion en zone niveau 1 (parent: null).
    N'écrit rien."""
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug = data.get("slug", "").strip()
    nouveau_parent_slug = (data.get("nouveau_parent_slug") or "").strip() or None

    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400

    rapport = _apply_reparent_zone(vault_root, scenario, slug, nouveau_parent_slug, dry_run=True)
    if "error" in rapport:
        return jsonify(rapport), 404
    return jsonify(rapport)


@app.route("/api/carte/reparent_zone", methods=["POST"])
def carte_reparent_zone():
    """Applique le déplacement d'une zone (et son sous-arbre) vers un nouveau parent.
    Body JSON : { "scenario":..., "slug":..., "nouveau_parent_slug":... }
    nouveau_parent_slug vide/absent = promotion en zone niveau 1 (parent: null)."""
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug = data.get("slug", "").strip()
    nouveau_parent_slug = (data.get("nouveau_parent_slug") or "").strip() or None

    if not scenario or not slug:
        return jsonify({"error": "scenario et slug requis"}), 400

    result = _apply_reparent_zone(vault_root, scenario, slug, nouveau_parent_slug, dry_run=False)
    if "error" in result:
        return jsonify(result), 409 if "Cycle" in result["error"] else 404
    return jsonify(result)


# ── P7 étape 2, phase 3 : créer une nouvelle zone niveau 1 à la volée (13
#    juillet 2026), pour le cas où aucun parent existant ne convient
#    sémantiquement lors d'un reparent (ex: le cas Barcelone — aucune zone
#    Europe n'existait dans new_sustainability). Champs alignés sur le
#    schéma réellement produit par enrich_geographie_recursive.py (ZONE_TYPES,
#    ZONE_STATUTS, TYPE_ENTITE_REELLE).

ZONE_TYPES = ["bloc_continental", "union_regionale", "territoire_autonome",
              "territoire_herite", "region", "ville", "infrastructure",
              "site_strategique", "zone_sinistree", "autre"]
ZONE_STATUTS = ["dominant", "stable", "fragmenté", "en_declin", "disparu", "emergent"]
TYPE_ENTITE_REELLE = ["pays", "etat_federe", "province", "region_administrative", "autre"]


def _creer_zone_in_zones_pays(zones_pays_path, scenario, origine_reelle, nouveau_slug, dry_run):
    """
    Synchronise zones_pays.json lors de la création d'une zone niveau 1
    (carte_creer_zone_niveau1). Même principe que _rename_zone_in_zones_pays
    et _split_zone_in_zones_pays, appliqué ici à la création : sans cette
    fonction, un pays inclus dans l'origine_reelle d'une toute nouvelle zone
    n'apparaissait JAMAIS dans zones_pays.json (bug trouvé le 25 juillet en
    scopant P24 étape C -- carte_creer_zone_niveau1 n'a jamais eu
    l'équivalent du fix appliqué à rename/split le 15 juillet). Symptôme
    identique au cas Écosse du 15 juillet : la fiche geographie/{scenario}.md
    est correcte, mais la carte affiche l'ancienne couleur (ou aucune)
    jusqu'à une réassignation manuelle via un clic sur la carte.

    Pour chaque entrée origine_reelle de type_entite == "pays" dont le nom
    normalisé correspond à un pays de pays_liste (peu importe la casse
    exacte -- une zone nouvellement créée porte en général un nom de pays
    déjà canonique, contrairement aux entrées extraites du corpus narratif
    brut ailleurs dans le pipeline, mais on tolère la variation de casse par
    prudence) : affecte ce pays à `nouveau_slug` dans zones_pays.json,
    QUELLE QUE SOIT SON AFFECTATION ACTUELLE -- contrairement au split (qui
    ne déplace que ce qui appartenait déjà à la zone source), la création
    explicite d'une zone avec ce pays dans son origine_reelle signifie que
    l'utilisateur (ou le générateur top-down, P24 étape C.2) veut
    précisément ce rattachement, même si le pays avait déjà une zone
    ailleurs.

    Retourne la liste des pays effectivement affectés (ou qui le seraient
    en dry_run).
    """
    if not zones_pays_path.exists():
        return []
    zp = json.loads(zones_pays_path.read_text(encoding="utf-8"))
    pays_liste = zp.get("pays_liste", [])
    index_norm_vers_canonique = {_normalise_pays(p): p for p in pays_liste}

    touches = []
    for o in origine_reelle:
        if not isinstance(o, dict) or o.get("type_entite") != "pays":
            continue
        n = _normalise_pays(o.get("entite", ""))
        pays_canonique = index_norm_vers_canonique.get(n)
        if pays_canonique:
            touches.append(pays_canonique)

    if not dry_run and touches:
        sc = zp.get(scenario, {})
        for pays in touches:
            sc[pays] = nouveau_slug
        zp[scenario] = sc
        zones_pays_path.write_text(json.dumps(zp, indent=2, ensure_ascii=False), encoding="utf-8")
    return touches


@app.route("/api/carte/creer_zone_niveau1", methods=["POST"])
def carte_creer_zone_niveau1():
    """
    Crée une nouvelle zone niveau 1 (parent: null) à la volée.
    Body JSON : { "scenario":..., "slug":..., "nom":..., "type":..., "statut":...,
                  "origine_reelle": [{"entite":..., "type_entite":...}, ...],
                  "description":... (optionnel) }
    """
    import yaml as _yaml
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug = data.get("slug", "").strip()
    nom = data.get("nom", "").strip()
    type_zone = data.get("type", "").strip()
    statut = data.get("statut", "").strip()
    origine_reelle = data.get("origine_reelle") or []
    description = (data.get("description") or "").strip()

    if not scenario or not slug or not nom or not type_zone or not statut:
        return jsonify({"error": "scenario, slug, nom, type, statut requis"}), 400
    if not re.match(r"^[a-z0-9_]+$", slug):
        return jsonify({"error": "slug : lettres minuscules, chiffres, underscores uniquement"}), 400
    if type_zone not in ZONE_TYPES:
        return jsonify({"error": f"type invalide, doit être parmi : {', '.join(ZONE_TYPES)}"}), 400
    if statut not in ZONE_STATUTS:
        return jsonify({"error": f"statut invalide, doit être parmi : {', '.join(ZONE_STATUTS)}"}), 400
    if not origine_reelle:
        return jsonify({"error": "origine_reelle requis (au moins une entrée) — "
                                  "voir la logique de validate_zone() dans enrich_geographie_recursive.py"}), 400
    for o in origine_reelle:
        if not o.get("entite") or o.get("type_entite") not in TYPE_ENTITE_REELLE:
            return jsonify({"error": f"origine_reelle invalide : {o!r} "
                                      f"(type_entite doit être parmi {', '.join(TYPE_ENTITE_REELLE)})"}), 400

    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return jsonify({"error": f"Fiche géographie introuvable : {geo_file}"}), 404

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return jsonify({"error": "Format de fiche géographie inattendu"}), 500
    fm = _yaml.safe_load(parts[1]) or {}
    zones = fm.get("zones") or []

    if any(z.get("slug") == slug for z in zones):
        return jsonify({"error": f"Le slug '{slug}' existe déjà dans ce scénario"}), 409

    # Champs enrichis optionnels (tensions_internes, lieux_emblematiques, relations,
    # periode_transition, sources_attestees) -- ajoutés le 25 juillet pour P24 étape
    # C.4 : le formulaire manuel P7 étape 2 ne les envoie jamais (valeurs vides par
    # défaut, comportement inchangé), mais generer_zone_topdown() (C.2) en produit
    # de réels -- avant ce fix, ils étaient silencieusement écrasés ici quoi que le
    # body contienne, perte de contenu invisible pour l'appelant.
    nouvelle_zone = {
        "slug": slug, "nom": nom, "niveau": 1, "type": type_zone, "parent": None,
        "origine_reelle": origine_reelle,
        "description": description,
        "statut": statut,
        "tensions_internes": (data.get("tensions_internes") or "").strip(),
        "periode_transition": data.get("periode_transition") or None,
        "evenement_transition": None,
        "lieux_emblematiques": data.get("lieux_emblematiques") or [],
        "relations": data.get("relations") or {"allies": [], "rivaux": []},
        "sources_attestees": data.get("sources_attestees") or [],
    }
    zones.append(nouvelle_zone)
    fm["zones"] = zones

    bak = geo_file.with_suffix(geo_file.suffix + ".bak")
    bak.write_text(raw, encoding="utf-8")

    new_fm = _yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    # Nouvelle zone niveau 1 : header "### {nom}" ajouté en fin de corps, sans
    # wikilink (comme toute zone niveau 1 dans le corps existant).
    new_body = parts[2].rstrip("\n") + f"\n\n### {nom}\n{description}\n"
    geo_file.write_text("---\n" + new_fm + "---" + new_body, encoding="utf-8")

    gui_dir = Path(__file__).parent
    zones_pays_path = gui_dir / "zones_pays.json"
    pays_synchronises = _creer_zone_in_zones_pays(
        zones_pays_path, scenario, origine_reelle, slug, dry_run=False
    )

    # Propagation des sous-zones orphelines (P24 étape C, ajouté le 25 juillet
    # suite au cas réel valence_tours_rirec/Espagne, cf. commentaire détaillé
    # dans generator/reparenter_sous_zones_orphelines.py). Sous-processus +
    # JSON plutôt qu'import direct -- gui/ et generator/ restent deux
    # codebases séparées ; ce script a besoin de resoudre_pays()/VILLE_PAYS
    # (check_origine_reelle_coherence.py), qu'on ne duplique pas ici. Pas
    # d'appel LLM derrière (résolution par table + cache seulement) -- timeout
    # court, contrairement à /api/carte/generer_zone_topdown.
    sous_zones_reparentees = []
    try:
        pipeline_dir = Path(cfg.get("pipeline_dir", ""))
        resultat_reparent = subprocess.run(
            [sys.executable, "reparenter_sous_zones_orphelines.py",
             "--scenario", scenario, "--zone-cible", slug, "--json"],
            cwd=pipeline_dir, capture_output=True, text=True,
            timeout=15, stdin=subprocess.DEVNULL,
        )
        sortie_reparent = resultat_reparent.stdout.strip()
        if sortie_reparent:
            payload_reparent = json.loads(sortie_reparent.splitlines()[-1])
            if payload_reparent.get("ok"):
                sous_zones_reparentees = payload_reparent.get("reparentees", [])
            # Un échec ici (payload.get("ok") False, ou JSON illisible) n'empêche
            # jamais la création de la zone elle-même -- déjà écrite avec succès
            # au-dessus. On le signale juste dans la réponse, sans lever d'erreur.
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, IndexError):
        pass  # même principe : la création a déjà réussi, ne jamais la faire échouer ici

    return jsonify({
        "ok": True, "slug": slug, "nom": nom,
        "pays_zones_pays_json": pays_synchronises,
        "sous_zones_reparentees": sous_zones_reparentees,
    })


# ── P24 étape C.4 (25 juillet 2026) -- générateur top-down, intégration GUI.
#    Deux routes distinctes, cohérentes avec la décision d'architecture actée
#    en scopant C.4 : le GUI appelle generator/zoning_topdown.py en
#    sous-processus + échange JSON (--json, ajouté à cet effet), jamais en
#    import direct -- gui/ et generator/ restent deux codebases séparées.
#
#    1. /api/carte/generer_zone_topdown : GÉNÉRATION SEULE, n'écrit jamais
#       rien. Pré-remplit le formulaire de création (cas pays_sans_zone,
#       écriture ensuite via /api/carte/creer_zone_niveau1, déjà existante)
#       ou le formulaire de révision (cas zone_suspecte, écriture via la
#       route suivante -- aucune route de création ne convient à une
#       révision en place).
#
#    2. /api/carte/appliquer_zone_topdown_suspecte : ÉCRITURE, réservée au
#       cas zone_suspecte. Duplique consciemment _appliquer_zone_suspecte()
#       de generator/generer_zones_topdown.py (C.3) -- même principe que
#       _tokens_entite()/_creer_zone_in_zones_pays() ci-dessus, deux
#       codebases séparées sans import croisé.

TIMEOUT_GENERATION_TOPDOWN = 90  # secondes -- appel LLM réel derrière, pas instantané


@app.route("/api/carte/generer_zone_topdown", methods=["POST"])
def carte_generer_zone_topdown():
    """
    Génère une proposition de zone top-down (P24 étape C.2, via
    generator/zoning_topdown.py --json en sous-processus). N'écrit JAMAIS
    dans le vault -- purement génératif, à pré-remplir dans le formulaire
    côté frontend pour relecture humaine avant tout /api/carte/creer_zone_niveau1
    ou /api/carte/appliquer_zone_topdown_suspecte.

    Body JSON :
      pays_sans_zone : { "scenario":..., "raison": "pays_sans_zone", "pays": [...] }
      zone_suspecte  : { "scenario":..., "raison": "zone_suspecte", "slug":...,
                          "raison_suspicion":... }
    """
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}
    scenario = (data.get("scenario") or "").strip()
    raison = (data.get("raison") or "").strip()

    if not scenario or raison not in ("pays_sans_zone", "zone_suspecte"):
        return jsonify({"error": "scenario requis, raison doit être "
                                  "'pays_sans_zone' ou 'zone_suspecte'"}), 400

    cmd = [sys.executable, "zoning_topdown.py", "--scenario", scenario, "--json"]
    if raison == "pays_sans_zone":
        pays = data.get("pays") or []
        if not pays:
            return jsonify({"error": "pays requis (liste non vide) pour raison=pays_sans_zone"}), 400
        cmd += ["--pays", *pays]
    else:
        slug = (data.get("slug") or "").strip()
        raison_suspicion = (data.get("raison_suspicion") or "").strip()
        if not slug or not raison_suspicion:
            return jsonify({"error": "slug et raison_suspicion requis pour raison=zone_suspecte"}), 400
        cmd += ["--zone-suspecte", slug, "--raison-suspicion", raison_suspicion]

    try:
        resultat = subprocess.run(
            cmd, cwd=pipeline_dir, capture_output=True, text=True,
            timeout=TIMEOUT_GENERATION_TOPDOWN, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Génération expirée après {TIMEOUT_GENERATION_TOPDOWN}s "
                                  f"(appel LLM trop lent ou bloqué)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"zoning_topdown.py introuvable dans {pipeline_dir}"}), 500

    sortie = resultat.stdout.strip()
    if not sortie:
        return jsonify({"error": f"Aucune sortie du sous-processus "
                                  f"(code {resultat.returncode}) : {resultat.stderr[-500:]}"}), 500
    try:
        payload = json.loads(sortie.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return jsonify({"error": f"Sortie non-JSON du sous-processus : {sortie[-500:]}"}), 500

    if not payload.get("ok"):
        return jsonify({"error": payload.get("error", "Erreur inconnue côté générateur")}), 500

    return jsonify({"ok": True, "proposition": payload["proposition"], "issues": payload["issues"]})


@app.route("/api/carte/appliquer_zone_topdown_suspecte", methods=["POST"])
def carte_appliquer_zone_topdown_suspecte():
    """
    Applique EN PLACE une proposition de révision générée pour le cas
    zone_suspecte (P24 étape C.4). Duplique consciemment
    _appliquer_zone_suspecte() de generator/generer_zones_topdown.py (C.3) --
    voir le commentaire au-dessus de cette route pour le pourquoi de la
    duplication plutôt qu'un import.

    Body JSON : { "scenario":..., "proposition": {...zone complète, même
                  slug qu'une zone existante...} }

    Ne modifie QUE description/type/statut/tensions_internes/relations sur
    la zone existante -- tout le reste (slug, nom, origine_reelle, niveau,
    parent, lieux_emblematiques, sources_attestees) reste celui déjà présent
    dans le vault, quoi que contienne `proposition` pour ces champs-là.
    """
    import yaml as _yaml
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = (data.get("scenario") or "").strip()
    proposition = data.get("proposition") or {}
    slug = (proposition.get("slug") or "").strip()

    if not scenario or not slug:
        return jsonify({"error": "scenario et proposition.slug requis"}), 400

    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return jsonify({"error": f"Fiche géographie introuvable : {geo_file}"}), 404

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return jsonify({"error": "Format de fiche géographie inattendu"}), 500
    fm = _yaml.safe_load(parts[1]) or {}
    zones = fm.get("zones") or []

    idx = next((i for i, z in enumerate(zones) if isinstance(z, dict) and z.get("slug") == slug), None)
    if idx is None:
        return jsonify({"error": f"Zone introuvable dans {scenario} : {slug!r}"}), 404

    bak = geo_file.with_suffix(geo_file.suffix + ".bak")
    bak.write_text(raw, encoding="utf-8")

    champs_revisables = ("description", "type", "statut", "tensions_internes", "relations")
    for champ in champs_revisables:
        if champ in proposition:
            zones[idx][champ] = proposition[champ]
    fm["zones"] = zones

    new_fm = _yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    geo_file.write_text("---\n" + new_fm + "---" + parts[2], encoding="utf-8")

    # Même mise à jour de suivi que C.3 -- statut distinct de "corrige_manuellement"
    # (généré puis validé humainement, pas tapé à la main).
    suspectes_file = vault_root / "documentation" / "need_action" / "patron_spatial_suspectes.yaml"
    statut_maj = False
    if suspectes_file.exists():
        sdata = _yaml.safe_load(suspectes_file.read_text(encoding="utf-8")) or {}
        entrees = sdata.get("zones_suspectes") or []
        for e in entrees:
            if e.get("scenario") == scenario and e.get("slug") == slug:
                e["statut"] = "corrige_via_c2"
                statut_maj = True
        if statut_maj:
            suspectes_file.write_text(
                _yaml.dump({"zones_suspectes": entrees}, allow_unicode=True,
                           sort_keys=False, default_flow_style=False),
                encoding="utf-8",
            )

    return jsonify({"ok": True, "slug": slug, "statut_suivi_maj": statut_maj})


# ── P7 étape 4 : split de zone (14 juillet 2026) -- extrait une ou plusieurs
#    entités origine_reelle d'une zone existante vers une nouvelle zone
#    niveau 1 ou une zone niveau 1 existante. Chaînon manquant identifié en
#    scopant P24 : ni rename ni reparent ne permettent de sortir un
#    SOUS-ENSEMBLE de l'origine_reelle d'une zone -- les deux déplacent
#    toujours la zone entière. Motivé concrètement par
#    check_conventions_territoires.py : un territoire (ex. Groenland) fondu
#    avec son souverain (Danemark) dans la même zone doit être séparé pour
#    se conformer à la convention décidée le 14 juillet (territoires
#    dépendants toujours distincts de leur souverain réel).
#
#    Les sous-zones (niveau 2/3) dont la PROPRE origine_reelle référence
#    aussi une entité extraite suivent automatiquement vers la zone cible
#    -- elles ne restaient cohérentes avec la zone source que grâce à cette
#    entité, qui n'y est plus après le split. Les autres enfants (liés à
#    d'autres pays de la zone source) restent en place. Détecté via le même
#    principe de correspondance que le reste du pipeline de cohérence
#    (voir check_origine_reelle_coherence.py), pas deviné.

def _tokens_entite(texte: str) -> list:
    """
    Découpe une chaîne `entite` en tokens comparables à un nom de pays :
    gère les virgules, les slashes, et le contenu entre parenthèses --
    même logique que _tokens() dans check_origine_reelle_coherence.py
    (generator/), dupliquée ici car app.py (gui/) est un codebase séparé.
    Nécessaire pour le split de zone : "Groenland", "Danemark (Groenland)"
    et "Groenland (Danemark / Kalaallit Nunaat)" doivent tous les trois
    être reconnus comme référant au Groenland (cas réel trouvé le 14
    juillet 2026 -- une correspondance sur chaîne exacte ratait 2 des 3).
    """
    texte = (texte or "").lower()
    interieur_parentheses = re.findall(r"\(([^)]*)\)", texte)
    texte_sans_parentheses = re.sub(r"\([^)]*\)", "", texte)
    morceaux = [texte_sans_parentheses] + interieur_parentheses
    tokens = []
    for m in morceaux:
        tokens += [t.strip() for t in re.split(r"[,/]", m)]
    return [t for t in tokens if t]


def _entite_references_pays(entite: str, pays_normalises: set) -> bool:
    """True si `entite` (n'importe quelle formulation) référence un des
    pays de `pays_normalises` (déjà en minuscules, via _normalise_pays)."""
    return any(_normalise_pays(t) in pays_normalises for t in _tokens_entite(entite))


def _split_zone_in_zones_pays(zones_pays_path, scenario, slug_source, pays_normalises, cible_slug, dry_run):
    """
    Met à jour zones_pays.json pour les pays extraits par un split de zone
    (même principe que _rename_zone_in_zones_pays, appliqué ici au split).
    Un pays de zones_pays.json est concerné si : il est actuellement affecté
    à slug_source ET son nom normalisé fait partie des pays extraits.
    """
    if not zones_pays_path.exists():
        return []
    zp = json.loads(zones_pays_path.read_text(encoding="utf-8"))
    sc = zp.get(scenario, {})
    touches = [
        pays for pays, slug in sc.items()
        if slug == slug_source and _normalise_pays(pays) in pays_normalises
    ]
    if not dry_run and touches:
        for pays in touches:
            sc[pays] = cible_slug
        zp[scenario] = sc
        zones_pays_path.write_text(json.dumps(zp, indent=2, ensure_ascii=False), encoding="utf-8")
    return touches


def _apply_split_zone(vault_root, scenario, slug_source, pays_a_extraire, cible, dry_run):
    """
    dry_run=True  : ne modifie rien, retourne un rapport d'impact.
    dry_run=False : applique réellement (avec .bak).
    {"error": "..."} dans les deux cas si la requête est invalide.

    pays_a_extraire : noms de pays normalisés (ex. ["groenland"]) -- pas
    des chaînes `entite` exactes. Toute entrée origine_reelle dont un token
    (une fois parenthèses/virgules/slashes séparés) matche un de ces pays
    est extraite, quelle que soit sa formulation exacte (voir
    _entite_references_pays). Idem pour détecter les enfants à suivre.

    cible = {"mode": "nouvelle_zone_n1", "slug":..., "nom":..., "type":...,
             "statut":..., "description": "..." (optionnel)}
         ou {"mode": "zone_existante", "slug_existant": "..."}
    """
    import yaml as _yaml
    gui_dir = Path(__file__).parent
    zones_pays_path = gui_dir / "zones_pays.json"
    geo_file = vault_root / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return {"error": f"Fiche géographie introuvable : {geo_file}"}

    raw = geo_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {"error": "Format de fiche géographie inattendu"}
    fm = _yaml.safe_load(parts[1]) or {}
    body = parts[2]
    zones = fm.get("zones") or []

    source = next((z for z in zones if z.get("slug") == slug_source), None)
    if not source:
        return {"error": f"Zone '{slug_source}' introuvable dans {scenario}"}

    pays_normalises = {_normalise_pays(p) for p in pays_a_extraire}

    origine = source.get("origine_reelle") or []
    a_extraire = [
        o for o in origine
        if isinstance(o, dict) and _entite_references_pays(o.get("entite") or "", pays_normalises)
    ]
    restantes = [o for o in origine if o not in a_extraire]

    if not a_extraire:
        return {"error": f"Aucune entrée de origine_reelle de '{slug_source}' ne référence "
                          f"{', '.join(pays_a_extraire)} (sous quelque formulation que ce soit)"}
    if not restantes:
        return {"error": f"Le split viderait complètement origine_reelle de '{slug_source}' "
                          f"-- au moins une entrée doit rester (voir validate_zone())"}

    enfants_a_suivre = []
    enfants_restants = []
    for e in zones:
        if e.get("parent") != slug_source:
            continue
        e_origine = e.get("origine_reelle") or []
        lie = any(
            isinstance(o, dict) and _entite_references_pays(o.get("entite") or "", pays_normalises)
            for o in e_origine
        )
        if lie:
            enfants_a_suivre.append(e)
        else:
            enfants_restants.append(e)

    mode = cible.get("mode")
    if mode == "nouvelle_zone_n1":
        cible_slug = cible.get("slug", "").strip()
        cible_nom = cible.get("nom", "").strip()
        cible_type = cible.get("type", "").strip()
        cible_statut = cible.get("statut", "").strip()
        cible_description = (cible.get("description") or "").strip()
        if not cible_slug or not cible_nom or not cible_type or not cible_statut:
            return {"error": "cible.slug, nom, type, statut requis pour une nouvelle zone niveau 1"}
        if not re.match(r"^[a-z0-9_]+$", cible_slug):
            return {"error": "cible.slug : lettres minuscules, chiffres, underscores uniquement"}
        if cible_type not in ZONE_TYPES:
            return {"error": f"cible.type invalide, doit être parmi : {', '.join(ZONE_TYPES)}"}
        if cible_statut not in ZONE_STATUTS:
            return {"error": f"cible.statut invalide, doit être parmi : {', '.join(ZONE_STATUTS)}"}
        if any(z.get("slug") == cible_slug for z in zones):
            return {"error": f"Le slug '{cible_slug}' existe déjà dans ce scénario"}
        cible_info = {"mode": mode, "slug": cible_slug, "nom": cible_nom,
                      "type": cible_type, "statut": cible_statut, "description": cible_description}
    elif mode == "zone_existante":
        slug_existant = cible.get("slug_existant", "").strip()
        cible_zone = next((z for z in zones if z.get("slug") == slug_existant), None)
        if not cible_zone:
            return {"error": f"Zone cible '{slug_existant}' introuvable dans {scenario}"}
        if cible_zone.get("niveau", 1) != 1:
            return {"error": f"'{slug_existant}' n'est pas une zone niveau 1 -- "
                              f"le split ne cible que des zones N1 (reparenter ensuite si besoin)"}
        if slug_existant == slug_source:
            return {"error": "La zone cible ne peut pas être la zone source"}
        cible_info = {"mode": mode, "slug": slug_existant, "nom": cible_zone.get("nom")}
    else:
        return {"error": "cible.mode doit être 'nouvelle_zone_n1' ou 'zone_existante'"}

    if dry_run:
        pays_zones_pays_json = _split_zone_in_zones_pays(
            zones_pays_path, scenario, slug_source, pays_normalises,
            cible_info["slug"], dry_run=True
        )
        return {
            "source": {"slug": slug_source, "nom": source.get("nom"),
                       "origine_reelle_avant": origine, "origine_reelle_apres": restantes},
            "entites_extraites": a_extraire,
            "enfants_qui_suivront": [{"slug": e.get("slug"), "nom": e.get("nom")} for e in enfants_a_suivre],
            "enfants_qui_restent": [{"slug": e.get("slug"), "nom": e.get("nom")} for e in enfants_restants],
            "cible": cible_info,
            "pays_zones_pays_json": pays_zones_pays_json,
        }

    source["origine_reelle"] = restantes

    if mode == "nouvelle_zone_n1":
        nouvelle_zone = {
            "slug": cible_info["slug"], "nom": cible_info["nom"], "niveau": 1,
            "type": cible_info["type"], "parent": None,
            "origine_reelle": a_extraire,
            "description": cible_info["description"],
            "statut": cible_info["statut"],
            "tensions_internes": "",
            "periode_transition": None,
            "evenement_transition": None,
            "lieux_emblematiques": [],
            "relations": {"allies": [], "rivaux": []},
            "sources_attestees": [],
        }
        zones.append(nouvelle_zone)
    else:
        existantes = cible_zone.get("origine_reelle") or []
        cible_zone["origine_reelle"] = existantes + [o for o in a_extraire if o not in existantes]

    # Les enfants dont la propre origine_reelle référence aussi une entité
    # extraite suivent automatiquement -- ils restaient cohérents avec la
    # zone source uniquement grâce à cette entité, qui n'y est plus.
    for e in enfants_a_suivre:
        e["parent"] = cible_info["slug"]

    fm["zones"] = zones
    bak = geo_file.with_suffix(geo_file.suffix + ".bak")
    bak.write_text(raw, encoding="utf-8")

    new_fm = _yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    new_body = body
    if mode == "nouvelle_zone_n1":
        new_body = body.rstrip("\n") + f"\n\n### {cible_info['nom']}\n{cible_info['description']}\n"
    geo_file.write_text("---\n" + new_fm + "---" + new_body, encoding="utf-8")

    pays_zones_pays_json = _split_zone_in_zones_pays(
        zones_pays_path, scenario, slug_source, pays_normalises,
        cible_info["slug"], dry_run=False
    )

    return {
        "ok": True,
        "slug_source": slug_source,
        "origine_reelle_source_restante": len(restantes),
        "entites_deplacees": len(a_extraire),
        "cible": cible_info,
        "enfants_reparentes_automatiquement": [e.get("slug") for e in enfants_a_suivre],
        "enfants_restes_sous_source": [e.get("slug") for e in enfants_restants],
        "pays_zones_pays_json_maj": pays_zones_pays_json,
    }


@app.route("/api/carte/impact_split_zone", methods=["POST"])
def carte_impact_split_zone():
    """
    Rapport d'impact en lecture seule pour un split de zone.
    Body JSON : { "scenario":..., "slug_source":..., "pays_a_extraire": [...],
                  "cible": {"mode": "nouvelle_zone_n1"|"zone_existante", ...} }
    pays_a_extraire : noms de pays normalisés (ex. ["groenland"]), pas des
    chaînes origine_reelle exactes -- toute formulation référençant ce pays
    est détectée (voir _entite_references_pays). N'écrit rien.
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug_source = data.get("slug_source", "").strip()
    pays_a_extraire = data.get("pays_a_extraire") or []
    cible = data.get("cible") or {}

    if not scenario or not slug_source or not pays_a_extraire:
        return jsonify({"error": "scenario, slug_source, pays_a_extraire requis"}), 400

    rapport = _apply_split_zone(vault_root, scenario, slug_source, pays_a_extraire, cible, dry_run=True)
    if "error" in rapport:
        return jsonify(rapport), 404
    return jsonify(rapport)


@app.route("/api/carte/split_zone", methods=["POST"])
def carte_split_zone():
    """Applique le split. Mêmes paramètres que impact_split_zone."""
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    scenario = data.get("scenario", "").strip()
    slug_source = data.get("slug_source", "").strip()
    pays_a_extraire = data.get("pays_a_extraire") or []
    cible = data.get("cible") or {}

    if not scenario or not slug_source or not pays_a_extraire:
        return jsonify({"error": "scenario, slug_source, pays_a_extraire requis"}), 400

    result = _apply_split_zone(vault_root, scenario, slug_source, pays_a_extraire, cible, dry_run=False)
    if "error" in result:
        code = 409 if "existe déjà" in result["error"] else 400
        return jsonify(result), code
    return jsonify(result)


# ── API Chantiers géographie (point 4.5, 26 juillet 2026) ─────────────────────
#
# Lit/écrit chantiers_geographie.yaml directement (pattern déjà établi par
# /api/zones/manquantes : import yaml local à la fonction, pas d'import de
# generator/chantiers.py -- gui/ et generator/ restent deux codebases
# séparées sans import croisé, point de vigilance déjà noté ailleurs dans ce
# fichier pour _tokens_entite()/zoning_topdown.py). Le SCHÉMA d'une entrée
# (id, scenario, type, cible, probleme, source_diagnostic, date_detection,
# statut, proposition, proposition_approuvee, date_proposition,
# date_traitement) et les 3 statuts valides (a_traiter/ignore/traite)
# reproduisent exactement ceux de generator/chantiers.py -- à garder en
# synchro si ce schéma évolue côté generator/.

CHANTIERS_STATUTS_VALIDES = ("a_traiter", "ignore", "traite")


def _chantiers_path(vault_root: Path) -> Path:
    return vault_root / "documentation" / "need_action" / "chantiers_geographie.yaml"


def _charger_chantiers(vault_root: Path) -> list:
    path = _chantiers_path(vault_root)
    if not path.exists():
        return []
    import yaml as _yaml
    data = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("chantiers") or []


def _sauver_chantiers(vault_root: Path, chantiers: list) -> None:
    import yaml as _yaml
    path = _chantiers_path(vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _yaml.dump({"chantiers": chantiers}, allow_unicode=True,
                   sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


@app.route("/api/chantiers", methods=["GET"])
def chantiers_liste():
    """
    GET /api/chantiers?scenario=...&type=...&statut=...
    Tous les paramètres sont optionnels -- sans filtre, retourne les
    chantiers de tous les scénarios et statuts (le tri/filtre par défaut
    "a_traiter seulement" est une décision d'affichage, laissée au
    frontend plutôt que masquée côté API).
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    scenario = request.args.get("scenario", "").strip()
    type_ = request.args.get("type", "").strip()
    statut = request.args.get("statut", "").strip()

    try:
        chantiers = _charger_chantiers(vault_root)
    except Exception as e:
        return jsonify({"chantiers": [], "error": str(e)}), 500

    if scenario:
        chantiers = [c for c in chantiers if c.get("scenario") == scenario]
    if type_:
        chantiers = [c for c in chantiers if c.get("type") == type_]
    if statut:
        chantiers = [c for c in chantiers if c.get("statut") == statut]

    return jsonify({"chantiers": chantiers})


@app.route("/api/chantiers/generer", methods=["POST"])
def chantiers_generer():
    """
    Génère (ou régénère) une proposition IA pour UN chantier précis --
    granularité que generer_zones_topdown.py --review-topdown n'offre pas
    (il traite toujours tous les chantiers éligibles d'un coup). Réutilise
    le même sous-processus zoning_topdown.py --json que
    /api/carte/generer_zone_topdown (voir cette route pour le détail du
    contrat JSON), avec les paramètres tirés directement de l'entrée
    chantier plutôt que d'un formulaire.

    Body JSON : { "id": "<scenario>__<cible_slugifiee>" }
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}
    chantier_id = (data.get("id") or "").strip()
    if not chantier_id:
        return jsonify({"error": "id requis"}), 400

    try:
        chantiers = _charger_chantiers(vault_root)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    chantier = next((c for c in chantiers if c.get("id") == chantier_id), None)
    if chantier is None:
        return jsonify({"error": f"Chantier introuvable : {chantier_id!r}"}), 404

    scenario = chantier["scenario"]
    type_ = chantier["type"]
    cible = chantier["cible"]

    cmd = [sys.executable, "zoning_topdown.py", "--scenario", scenario, "--json"]
    if type_ == "pays_sans_zone":
        cmd += ["--pays", cible]
    else:
        cmd += ["--zone-suspecte", cible, "--raison-suspicion", chantier.get("probleme", "")]

    try:
        resultat = subprocess.run(
            cmd, cwd=pipeline_dir, capture_output=True, text=True,
            timeout=TIMEOUT_GENERATION_TOPDOWN, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Génération expirée après {TIMEOUT_GENERATION_TOPDOWN}s "
                                  f"(appel LLM trop lent ou bloqué)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"zoning_topdown.py introuvable dans {pipeline_dir}"}), 500

    sortie = resultat.stdout.strip()
    if not sortie:
        return jsonify({"error": f"Aucune sortie du sous-processus "
                                  f"(code {resultat.returncode}) : {resultat.stderr[-500:]}"}), 500
    try:
        payload = json.loads(sortie.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return jsonify({"error": f"Sortie non-JSON du sous-processus : {sortie[-500:]}"}), 500

    if not payload.get("ok"):
        return jsonify({"error": payload.get("error", "Erreur inconnue côté générateur")}), 500

    # Réattache la proposition au chantier -- mêmes champs que
    # reviewer_scenario() dans generer_zones_topdown.py (mettre_a_jour_
    # chantier(..., proposition=..., proposition_approuvee=False,
    # date_proposition=...)), réimplémenté ici en YAML direct pour la même
    # raison de séparation de codebase que le reste de ce fichier.
    from datetime import date as _date
    for c in chantiers:
        if c.get("id") == chantier_id:
            c["proposition"] = payload["proposition"]
            c["proposition_issues"] = payload.get("issues") or []
            c["proposition_approuvee"] = False
            c["date_proposition"] = _date.today().isoformat()
            break
    _sauver_chantiers(vault_root, chantiers)

    return jsonify({"ok": True, "proposition": payload["proposition"], "issues": payload.get("issues") or []})


@app.route("/api/chantiers/approuver", methods=["POST"])
def chantiers_approuver():
    """
    Approuve ou retire l'approbation d'une proposition déjà générée --
    ne touche jamais au statut du chantier lui-même (reste 'a_traiter'
    jusqu'à application effective).
    Body JSON : { "id":..., "approuve": true|false }
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    chantier_id = (data.get("id") or "").strip()
    approuve = bool(data.get("approuve"))
    if not chantier_id:
        return jsonify({"error": "id requis"}), 400

    try:
        chantiers = _charger_chantiers(vault_root)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    trouve = False
    for c in chantiers:
        if c.get("id") == chantier_id:
            if c.get("proposition") is None:
                return jsonify({"error": "Aucune proposition à approuver pour ce chantier -- "
                                          "génère-en une d'abord."}), 400
            c["proposition_approuvee"] = approuve
            trouve = True
            break
    if not trouve:
        return jsonify({"error": f"Chantier introuvable : {chantier_id!r}"}), 404

    _sauver_chantiers(vault_root, chantiers)
    return jsonify({"ok": True})


@app.route("/api/chantiers/statut", methods=["POST"])
def chantiers_statut():
    """
    Change le statut d'un chantier à la main (ignore/traite/a_traiter) --
    couvre "marquer ignoré" et "marquer traité manuellement" (ex.
    correction faite directement dans l'onglet Carte, sans passer par une
    proposition générée ici).
    Body JSON : { "id":..., "statut": "ignore"|"traite"|"a_traiter" }
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    data = request.get_json() or {}
    chantier_id = (data.get("id") or "").strip()
    statut = (data.get("statut") or "").strip()
    if not chantier_id or statut not in CHANTIERS_STATUTS_VALIDES:
        return jsonify({"error": f"id requis, statut doit être dans {CHANTIERS_STATUTS_VALIDES}"}), 400

    try:
        chantiers = _charger_chantiers(vault_root)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    from datetime import date as _date
    trouve = False
    for c in chantiers:
        if c.get("id") == chantier_id:
            c["statut"] = statut
            c["date_traitement"] = _date.today().isoformat() if statut == "traite" else c.get("date_traitement")
            trouve = True
            break
    if not trouve:
        return jsonify({"error": f"Chantier introuvable : {chantier_id!r}"}), 404

    _sauver_chantiers(vault_root, chantiers)
    return jsonify({"ok": True})


@app.route("/api/chantiers/appliquer", methods=["POST"])
def chantiers_appliquer():
    """
    Applique EN LOT les chantiers prêts (statut a_traiter + proposition
    approuvée) d'un scénario, OU un seul chantier précis via "id" -- délègue
    à generer_zones_topdown.py --apply-topdown en sous-processus plutôt que
    de dupliquer sa logique d'écriture ici. Pas d'appel LLM ici (propositions
    déjà générées) : synchrone, comme les autres routes /api/carte/*, pas
    besoin de passer par /api/run + SSE.

    Body JSON : { "scenario": "breakdown" } ou { "all": true }
      ou { "id": "<scenario>__<cible>" } -- granularité fine ajoutée le 1er
      août 2026 (--cible côté generer_zones_topdown.py) : résout scenario et
      cible depuis l'entrée de chantiers_geographie.yaml correspondant à cet
      id, applique uniquement ce chantier-là plutôt que tout le scénario.
    """
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}
    scenario = (data.get("scenario") or "").strip()
    tous = bool(data.get("all"))
    chantier_id = (data.get("id") or "").strip()

    cible = None
    if chantier_id:
        try:
            chantiers = _charger_chantiers(vault_root)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        chantier = next((c for c in chantiers if c.get("id") == chantier_id), None)
        if chantier is None:
            return jsonify({"error": f"Chantier introuvable : {chantier_id!r}"}), 404
        scenario = chantier.get("scenario", "")
        cible = chantier.get("cible", "")

    if not scenario and not tous:
        return jsonify({"error": "scenario, all ou id requis"}), 400

    cmd = [sys.executable, "generer_zones_topdown.py", "--apply-topdown"]
    cmd += ["--all"] if tous else ["--scenario", scenario]
    if cible:
        cmd += ["--cible", cible]

    try:
        resultat = subprocess.run(
            cmd, cwd=pipeline_dir, capture_output=True, text=True,
            timeout=60, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Application expirée après 60s"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"generer_zones_topdown.py introuvable dans {pipeline_dir}"}), 500

    if resultat.returncode != 0:
        return jsonify({"error": resultat.stderr[-800:] or resultat.stdout[-800:],
                         "returncode": resultat.returncode}), 500

    return jsonify({"ok": True, "log": resultat.stdout[-4000:]})


# ── API Rédaction — table journalistes/orateurs (30 août 2026) ────────────────
#
# Nouvel onglet GUI (pas une entrée scripts_config.json -- même famille que
# Carte/Chantiers ci-dessus) : consultation/édition des journalistes et
# orateur·rices de journaux.yaml. Design complet dans BACKLOG_ACTIF.md
# (point 3, 30 août 2026). V1 = affichage de tous les champs + édition de
# ton_personnel uniquement (les autres champs -- thématiques, séniorité,
# communautés desservies -- n'ont aucun mécanisme d'écriture existant en
# dehors de la création, décision actée de ne pas les rendre éditables ici
# tant qu'un vrai besoin ne se manifeste pas).
#
# --all-manquants (rattrapage par lot sur une zone entière) reste
# volontairement CLI-only -- pas de route ici pour ce mode, voir le
# docstring de set_ton_personnel.py et BACKLOG_ACTIF.md pour le détail de
# cette décision.

def _lire_journaux(pipeline_dir: Path) -> dict:
    """Lecture directe de journaux.yaml, même pattern (sans cache) que
    _zones_avec_journal()/_scan_intervenants_eligibles() ci-dessus."""
    journaux_path = pipeline_dir / "journaux.yaml"
    if not journaux_path.exists():
        return {}
    import yaml as _yaml
    try:
        return _yaml.safe_load(journaux_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


@app.route("/api/redaction/personnes", methods=["GET"])
def redaction_personnes():
    """
    GET /api/redaction/personnes?scenario=...&ligne=...&zone_slug=...
        &role=journaliste|orateur&ton_status=vide|rempli

    Retourne une ligne par journaliste ET par orateur·rice, tous scénarios
    confondus par défaut -- tous les paramètres de filtre sont optionnels,
    appliqués côté serveur pour réduire la charge utile (le tri/pagination
    fins restent côté frontend, comme pour /api/chantiers).

    type_diffusion de zone : "oral" ou "ecrit" (valeur par défaut du champ
    quand absent) -- "mixte" n'existe pas comme état stocké sur la zone,
    c'est un tirage fait par generate.py au moment de la génération d'un
    article sur une zone déjà "oral" (voir BACKLOG_ACTIF.md, point 3).
    """
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    f_scenario = request.args.get("scenario", "").strip()
    f_ligne = request.args.get("ligne", "").strip()
    f_zone = request.args.get("zone_slug", "").strip()
    f_role = request.args.get("role", "").strip()
    f_ton = request.args.get("ton_status", "").strip()

    journaux = _lire_journaux(pipeline_dir)
    personnes = []

    for scenario, scenario_data in journaux.items():
        if f_scenario and scenario != f_scenario:
            continue
        if not isinstance(scenario_data, dict):
            continue
        for ligne, ligne_data in scenario_data.items():
            if f_ligne and ligne != f_ligne:
                continue
            if not isinstance(ligne_data, dict):
                continue
            zones = ligne_data.get("zones") or {}
            for zone_slug, zone_data in zones.items():
                if f_zone and zone_slug != f_zone:
                    continue
                if not isinstance(zone_data, dict):
                    continue
                type_diffusion = zone_data.get("type_diffusion") or "ecrit"
                zone_nom = zone_data.get("nom", zone_slug)
                zone_ton = zone_data.get("ton", "")

                if f_role in ("", "journaliste"):
                    for j in (zone_data.get("journalistes") or []):
                        ton = j.get("ton_personnel") or ""
                        if f_ton == "vide" and ton:
                            continue
                        if f_ton == "rempli" and not ton:
                            continue
                        personnes.append({
                            "scenario": scenario, "ligne": ligne,
                            "zone_slug": zone_slug, "zone_nom": zone_nom,
                            "zone_ton": zone_ton,
                            "type_diffusion": type_diffusion,
                            "nom": j.get("nom", ""), "role": "journaliste",
                            "thematiques": j.get("thematiques") or [],
                            "seniorite": j.get("seniorite"),
                            "ton_personnel": ton,
                        })
                if f_role in ("", "orateur"):
                    for o in (zone_data.get("orateurs") or []):
                        ton = o.get("ton_personnel") or ""
                        if f_ton == "vide" and ton:
                            continue
                        if f_ton == "rempli" and not ton:
                            continue
                        personnes.append({
                            "scenario": scenario, "ligne": ligne,
                            "zone_slug": zone_slug, "zone_nom": zone_nom,
                            "zone_ton": zone_ton,
                            "type_diffusion": type_diffusion,
                            "nom": o.get("nom", ""), "role": "orateur",
                            "communautes_desservies": o.get("communautes_desservies") or [],
                            "reputation_orale": o.get("reputation_orale", ""),
                            "seniorite": o.get("seniorite"),
                            "ton_personnel": ton,
                        })

    return jsonify({"personnes": personnes, "total": len(personnes)})


@app.route("/api/redaction/ton_personnel", methods=["POST"])
def redaction_ton_personnel():
    """
    Appelle set_ton_personnel.py --json en sous-processus pour UNE personne
    précise -- panneau de détail de l'onglet Rédaction.

    Body JSON :
      { "scenario", "ligne", "zone_slug", "nom",
        "mode": "ia" | "custom",
        "texte": "..."   (requis seulement si mode == "custom"),
        "overwrite": bool }   (true si la personne a déjà un ton_personnel
                                -- décidé côté frontend, le panneau doit
                                avertir avant d'envoyer overwrite=true)

    Réutilise le même sous-processus synchrone que /api/chantiers/generer
    (appel LLM réel en mode "ia", donc pas instantané -- même timeout).
    """
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}

    scenario = (data.get("scenario") or "").strip()
    ligne = (data.get("ligne") or "").strip()
    zone_slug = (data.get("zone_slug") or "").strip()
    nom = (data.get("nom") or "").strip()
    mode = (data.get("mode") or "ia").strip()
    texte = (data.get("texte") or "").strip()
    overwrite = bool(data.get("overwrite"))

    if not (scenario and ligne and zone_slug and nom):
        return jsonify({"error": "scenario, ligne, zone_slug et nom requis"}), 400
    if mode == "custom" and not texte:
        return jsonify({"error": "texte requis en mode custom"}), 400
    if mode not in ("ia", "custom"):
        return jsonify({"error": "mode doit être 'ia' ou 'custom'"}), 400

    cmd = [sys.executable, "set_ton_personnel.py",
           "--scenario", scenario, "--ligne", ligne, "--zone-slug", zone_slug,
           "--nom", nom, "--json"]
    if mode == "custom":
        cmd += ["--ton-personnel", texte]
    if overwrite:
        cmd += ["--overwrite"]

    try:
        resultat = subprocess.run(
            cmd, cwd=pipeline_dir, capture_output=True, text=True,
            timeout=TIMEOUT_GENERATION_TOPDOWN, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Génération expirée après {TIMEOUT_GENERATION_TOPDOWN}s "
                                  f"(appel LLM trop lent ou bloqué)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"set_ton_personnel.py introuvable dans {pipeline_dir}"}), 500

    sortie = resultat.stdout.strip()
    if not sortie:
        return jsonify({"error": f"Aucune sortie du sous-processus "
                                  f"(code {resultat.returncode}) : {resultat.stderr[-500:]}"}), 500
    try:
        payload = json.loads(sortie.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return jsonify({"error": f"Sortie non-JSON du sous-processus : {sortie[-500:]}"}), 500

    if not payload.get("ok"):
        return jsonify({"error": payload.get("error", "Erreur inconnue")}), 500

    return jsonify({"ok": True, "ton_personnel": payload.get("ton_personnel", "")})


@app.route("/api/redaction/champs", methods=["POST"])
def redaction_champs():
    """
    Patch direct de journaux.yaml pour thematiques (journalistes
    uniquement -- les orateurs n'ont pas ce champ, voir communautes_
    desservies) et/ou seniorite (les deux rôles) -- décision du 30 août
    2026 (retour de David) d'étendre l'édition au-delà de ton_personnel.

    Contrairement à /api/redaction/ton_personnel, pas d'appel LLM : édition
    directe façon _sauver_chantiers()/_zones_avec_journal() ci-dessus
    (import yaml local, lecture/écriture directe du fichier), avec la même
    sauvegarde horodatée que set_ton_personnel.py pour rester cohérent en
    cas d'erreur.

    Body JSON :
      { "scenario", "ligne", "zone_slug", "nom", "role": "journaliste"|"orateur",
        "thematiques": [...]   (optionnel, journaliste uniquement),
        "seniorite": int }      (optionnel, les deux rôles)
    Au moins un des deux champs doit être fourni.
    """
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}

    scenario = (data.get("scenario") or "").strip()
    ligne = (data.get("ligne") or "").strip()
    zone_slug = (data.get("zone_slug") or "").strip()
    nom = (data.get("nom") or "").strip()
    role = (data.get("role") or "").strip()
    thematiques = data.get("thematiques")
    seniorite = data.get("seniorite")

    if not (scenario and ligne and zone_slug and nom and role):
        return jsonify({"error": "scenario, ligne, zone_slug, nom et role requis"}), 400
    if role not in ("journaliste", "orateur"):
        return jsonify({"error": "role doit être 'journaliste' ou 'orateur'"}), 400
    if thematiques is not None and role != "journaliste":
        return jsonify({"error": "thematiques n'existe que pour les journalistes"}), 400
    if thematiques is None and seniorite is None:
        return jsonify({"error": "au moins thematiques ou seniorite requis"}), 400
    if seniorite is not None:
        try:
            seniorite = int(seniorite)
        except (TypeError, ValueError):
            return jsonify({"error": "seniorite doit être un entier"}), 400

    journaux_path = pipeline_dir / "journaux.yaml"
    if not journaux_path.exists():
        return jsonify({"error": f"journaux.yaml introuvable dans {pipeline_dir}"}), 500

    import yaml as _yaml
    try:
        journaux = _yaml.safe_load(journaux_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        return jsonify({"error": f"Lecture journaux.yaml impossible : {e}"}), 500

    try:
        zone_data = journaux[scenario][ligne]["zones"][zone_slug]
    except KeyError:
        return jsonify({"error": f"Zone introuvable : {scenario}/{ligne}/{zone_slug}"}), 404

    liste_champ = "journalistes" if role == "journaliste" else "orateurs"
    entree = next((e for e in (zone_data.get(liste_champ) or []) if e.get("nom") == nom), None)
    if entree is None:
        return jsonify({"error": f"'{nom}' introuvable dans cette zone"}), 404

    if thematiques is not None:
        entree["thematiques"] = list(thematiques)
    if seniorite is not None:
        entree["seniorite"] = seniorite

    from datetime import datetime as _datetime
    import shutil as _shutil
    backup_path = str(journaux_path) + ".backup_" + _datetime.now().strftime("%Y%m%d_%H%M%S")
    _shutil.copy2(journaux_path, backup_path)
    journaux_path.write_text(
        _yaml.dump(journaux, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    return jsonify({"ok": True, "thematiques": entree.get("thematiques"),
                     "seniorite": entree.get("seniorite")})


# Vraie liste canonique, recopiée depuis inject_journaliste_custom.py (même
# garde-fou que ce script -- 30 août 2026, remplace la version provisoire
# dérivée des données qui était en place avant que ce fichier soit fourni).
# À garder en synchro si THEMATIQUES_CONNUES change côté
# inject_journaliste_custom.py (même point de vigilance que les autres
# constantes dupliquées entre gui/ et generator/ dans ce fichier).
THEMATIQUES_CONNUES = [
    "actualites_a_la_une", "politique", "economie_finance", "international",
    "environnement_climat", "sante", "societe", "culture", "musique",
    "sports", "faits_divers", "opinions_editoriaux", "lifestyle_art_de_vivre",
    "education", "histoire_patrimoine", "medias_communication",
    "religion_spiritualite", "petites_annonces_services", "meteo",
    "sciences_technologies",
]
MAX_THEMATIQUES_PAR_JOURNALISTE = 6


@app.route("/api/redaction/thematiques", methods=["GET"])
def redaction_thematiques():
    """Liste des thématiques valides, pour le multi-select du panneau --
    vraie constante THEMATIQUES_CONNUES depuis le 30 août 2026 (voir
    commentaire ci-dessus)."""
    return jsonify({"thematiques": THEMATIQUES_CONNUES,
                     "max_par_journaliste": MAX_THEMATIQUES_PAR_JOURNALISTE})


# ── API Slugs ─────────────────────────────────────────────────────────────────

@app.route("/api/slugs", methods=["GET"])
def get_slugs():
    """
    GET /api/slugs?type=instances&scenario=breakdown
    GET /api/slugs?type=zones&scenario=breakdown
    GET /api/slugs?type=entities
    GET /api/slugs?type=zones_all&scenario=breakdown
    GET /api/slugs?type=signals
    GET /api/slugs?type=evenements
    GET /api/slugs?type=zones_a_reparenter&scenario=breakdown
    GET /api/slugs?type=zones_candidates_oral&scenario=breakdown
    GET /api/slugs?type=fiches_a_localiser&scenario=breakdown
    """
    slug_type = request.args.get("type", "instances")
    scenario = request.args.get("scenario", "")
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))

    slugs = []
    # labels (26 août 2026) : dict optionnel {valeur: texte_affiché},
    # lu par app.js si présent (data.labels && data.labels[slug]) --
    # vide par défaut pour toutes les branches qui n'en ont pas besoin,
    # non-régression totale. Voir la branche intervenants_eligibles
    # plus bas pour l'unique usage actuel.
    labels = {}

    try:
        if slug_type == "instances":
            slugs = _scan_instance_slugs(vault_root, scenario)
        elif slug_type == "entities":
            slugs = _scan_entity_slugs(vault_root, pipeline_dir)
        elif slug_type in ("zones", "zones_all"):
            n1_only = (slug_type == "zones")
            slugs = _scan_zone_slugs(vault_root, scenario, n1_only)
        elif slug_type == "zones_hier":
            zones = _scan_zone_slugs_hier(vault_root, scenario)
            return jsonify({"slugs": [z["slug"] for z in zones], "zones": zones})
        elif slug_type == "zones_hier_journal":
            # Ajouté le 11 août 2026, spécifique à --zone-slug de generate.py
            # (mode Semi-guidé) -- voir _zones_avec_journal() pour le détail
            # du bug corrigé. zones_hier ci-dessus reste inchangé : zone_hint
            # (create_entities/inject_events) a légitimement besoin de la
            # hiérarchie complète, sans ce filtre.
            zones = _scan_zone_slugs_hier(vault_root, scenario)
            zones_ok = _zones_avec_journal(pipeline_dir, scenario)
            zones = [z for z in zones if z["slug"] in zones_ok]
            return jsonify({"slugs": [z["slug"] for z in zones], "zones": zones})
        elif slug_type == "forcer_scenarios":
            # Ajouté le 2 août 2026 pour le mode "forcer" de generate.py.
            # slug_type_field="--forcer-slug" garantit que le slug de
            # l'élément arrive via ?slug=... (mécanisme déjà prouvé,
            # trace_injection.py) ; le type (instance/evenement/signal) est
            # lu de façon défensive sous plusieurs noms possibles, la
            # convention exacte de transmission des champs frères n'étant
            # pas vérifiable sans gui/app.js -- à confirmer/corriger en
            # conditions réelles si la liste ne s'actualise pas.
            forcer_type = (request.args.get("element_type") or request.args.get("forcer_type")
                           or request.args.get("--forcer-type") or request.args.get("type_element") or "")
            slug_element = request.args.get("slug", "")
            code = (
                "import sys, json; sys.path.insert(0, '.'); import loader; "
                "print(json.dumps(loader.scenarios_disponibles_pour_element({!r}, {!r})))"
            ).format(forcer_type, slug_element)
            resultat = subprocess.run(
                [sys.executable, "-c", code], cwd=pipeline_dir,
                capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL,
            )
            if resultat.returncode != 0:
                return jsonify({"slugs": [], "error": resultat.stderr.strip()[-500:]})
            try:
                dispo = json.loads(resultat.stdout.strip())
            except json.JSONDecodeError:
                dispo = []
            # "tous" en premier choix, explicite -- voir generate.py qui
            # résout ce mot-clé vers `dispo` en entier (pas les 6 scénarios
            # sans distinction).
            return jsonify({"slugs": ["tous"] + dispo,
                             "labels": {"tous": "— Tous les scénarios disponibles ({}) —".format(len(dispo))}})
        elif slug_type == "forcer_zones":
            # Réécrit le 2 août 2026 (retour de David) : le menu Zone ne doit
            # dépendre QUE de l'élément choisi (entité/événement/signal), pas
            # des scénarios cochés à côté -- l'ancienne version dépendait des
            # deux, ce qui rendait le menu vide tant qu'aucun scénario précis
            # n'était sélectionné. Comportement voulu :
            #   - pas d'élément choisi encore -> ["tous"] seul (mode par
            #     défaut, rien à restreindre)
            #   - élément choisi mais sans zone nulle part (signal, ou
            #     instance/événement sans localisation renseignée) ->
            #     ["tous"] seul, pas d'erreur ni de liste vide
            #   - élément choisi avec des zones -> ["tous"] + zones trouvées,
            #     sur TOUS les scénarios où l'élément existe (pas seulement
            #     ceux actuellement cochés dans --forcer-scenarios)
            forcer_type = (request.args.get("element_type") or request.args.get("forcer_type")
                           or request.args.get("--forcer-type") or request.args.get("type_element") or "")
            slug_element = request.args.get("slug", "")

            if not forcer_type or not slug_element:
                return jsonify({"slugs": ["tous"]})

            code = (
                "import sys, json; sys.path.insert(0, '.'); import loader; "
                "sc = loader.scenarios_disponibles_pour_element({0!r}, {1!r}); "
                "print(json.dumps(loader.zones_disponibles_pour_element({0!r}, {1!r}, sc)))"
            ).format(forcer_type, slug_element)
            resultat = subprocess.run(
                [sys.executable, "-c", code], cwd=pipeline_dir,
                capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL,
            )
            if resultat.returncode != 0:
                return jsonify({"slugs": ["tous"], "error": resultat.stderr.strip()[-500:]})
            try:
                zones_par_scenario = json.loads(resultat.stdout.strip())
            except json.JSONDecodeError:
                zones_par_scenario = {}
            toutes_zones = sorted({z for zs in zones_par_scenario.values() for z in zs})
            if not toutes_zones:
                # Élément sans aucun rattachement zone/scénario (signal, ou
                # instance/événement jamais localisé) -- reste en mode
                # "tous" par défaut, pas de liste vide affichée.
                return jsonify({"slugs": ["tous"], "zones_par_scenario": {}})
            return jsonify({"slugs": ["tous"] + toutes_zones, "zones_par_scenario": zones_par_scenario})
        elif slug_type == "zones_candidates_oral":
            # Ajouté le 29 août 2026 (P21, retour de David) : liste les
            # zones du scénario n'ayant pas encore type_diffusion en
            # oral/mixte, pour le nouveau mode "convertir" de
            # inject_orateur_custom.py -- multi-select GUI, David
            # choisit lui-même quelles zones convertir plutôt qu'un
            # balayage aveugle (voir _zones_candidates_oral() pour le
            # raisonnement complet). Même forme de réponse que
            # zones_a_reparenter ci-dessous (slugs + objets candidats
            # riches pour l'affichage), + labels lisibles (le composite
            # "ligne::zone_slug" seul serait illisible affiché tel quel
            # sur une chip -- même convention que intervenants_eligibles
            # ci-dessus, qui ajoute déjà des labels au texte affiché).
            candidats = _zones_candidates_oral(pipeline_dir, scenario)
            labels = {
                c["slug"]: "{} ({})".format(c["nom"], c["ligne"])
                for c in candidats
            }
            return jsonify({
                "slugs": [c["slug"] for c in candidats],
                "candidats": candidats,
                "labels": labels,
            })
        elif slug_type == "zones_a_reparenter":
            # Ajouté le 31 juillet 2026 (remarque de David : proposer les
            # 16-42 zones N1 d'un scénario dans --zone-cible était peu
            # exploitable, l'immense majorité n'ayant jamais de sous-zone
            # orpheline). Sous-processus + JSON vers le nouveau mode
            # --scan-candidates de reparenter_sous_zones_orphelines.py --
            # même principe que l'appel automatique post-reparent Carte
            # ci-dessus (gui/ et generator/ restent deux codebases
            # séparées). Lecture seule, aucun appel LLM (resoudre_pays()
            # ne consulte que table + cache), timeout court.
            candidats = _scan_reparent_candidats(pipeline_dir, scenario)
            return jsonify({
                "slugs": [c["slug"] for c in candidats],
                "candidats": candidats,
            })
        elif slug_type == "fiches_a_localiser":
            # Ajouté le 31 juillet 2026, même principe que zones_a_reparenter
            # ci-dessus : --slug sur extract_localisation listait toutes les
            # instances sans distinguer celles déjà localisées. Sous-processus
            # + JSON vers le nouveau mode --scan-pending, purement mécanique
            # (collect_fiches() ne fait que lire du frontmatter, aucun appel
            # LLM) côté extract_localisation.py.
            #
            # Paramètre force ajouté le 14 août 2026 (backlog Partie 2 : le
            # menu ne se rafraîchissait jamais en cochant "Retraiter même si
            # déjà fait", contournable seulement via --scenario). Cause
            # réelle en 3 parties : (1) --slug n'avait pas de slug_extra_params
            # déclaré côté scripts_config.json pour --force, (2) même une
            # fois déclaré, lireValeurChamp() (app.js) lisait .value sur la
            # checkbox au lieu de .checked -- toujours "on" quel que soit
            # l'état -- et (3) même le paramètre correctement transmis
            # n'était de toute façon jamais lu ni transmis au sous-processus
            # ici. Les trois corrigés ensemble le même jour.
            force = request.args.get("force", "").lower() == "true"
            candidats = _scan_localisation_candidats(pipeline_dir, scenario, force=force)
            return jsonify({
                "slugs": [c["slug"] for c in candidats],
                "candidats": candidats,
            })
        elif slug_type == "signals":
            slugs = _scan_signal_slugs(vault_root)
        elif slug_type == "evenements":
            slugs = _scan_event_slugs(vault_root)
        elif slug_type == "intervenants_eligibles":
            # Ajouté le 25 août 2026 pour le nouveau champ GUI "Forcer un
            # intervenant précis" (generate.py --intervenant, P21). ligne
            # et zone lus en plus de scenario (déjà lu plus haut) --
            # mode == "mixte"/"auto"/vide affiche les deux listes
            # mélangées (décision explicite de David, plus simple que
            # de relire le vrai type_diffusion de la zone).
            #
            # thematique (26 août 2026, retour de David) : filtre les
            # journalistes exactement comme get_journal_profile() le
            # ferait au moment réel de la génération (voir
            # _scan_intervenants_eligibles() pour le détail complet).
            #
            # labels (26 août 2026) : "(journaliste)"/"(orateur)" affiché
            # dans le menu déroulant pour distinguer les deux quand la
            # liste les mélange -- la valeur soumise reste le nom exact,
            # sans suffixe.
            ligne = request.args.get("ligne", "")
            zone = request.args.get("zone", "")
            mode = request.args.get("mode", "")
            thematique = request.args.get("thematique", "")
            slugs, labels = _scan_intervenants_eligibles(
                pipeline_dir, scenario, ligne, zone, mode, thematique
            )
    except Exception as e:
        return jsonify({"slugs": [], "error": str(e)})

    return jsonify({"slugs": slugs, "labels": labels})


def _scan_localisation_candidats(pipeline_dir: Path, scenario: str, force: bool = False) -> list:
    """Appelle extract_localisation.py --scan-pending en sous-processus
    (lecture seule, aucun appel LLM) et retourne la liste des fiches n'ayant
    pas encore de champ localisation. scenario vide = tous les scénarios
    (contrairement à zones_a_reparenter, --scenario est optionnel côté
    script). force=True ajouté le 14 août 2026 : liste aussi les fiches déjà
    traitées, en cohérence avec --force côté script (collect_fiches())."""
    try:
        cmd = [sys.executable, "extract_localisation.py", "--scan-pending", "--json"]
        if scenario:
            cmd += ["--scenario", scenario]
        if force:
            cmd += ["--force"]
        resultat = subprocess.run(
            cmd, cwd=pipeline_dir, capture_output=True, text=True,
            timeout=15, stdin=subprocess.DEVNULL,
        )
        sortie = resultat.stdout.strip()
        if not sortie:
            return []
        payload = json.loads(sortie.splitlines()[-1])
        if not payload.get("ok"):
            return []
        return payload.get("candidats", [])
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, IndexError):
        return []


def _scan_reparent_candidats(pipeline_dir: Path, scenario: str) -> list:
    """Appelle reparenter_sous_zones_orphelines.py --scan-candidates en
    sous-processus (lecture seule) et retourne la liste des zones N1 ayant
    actuellement des sous-zones orphelines en attente. Échec silencieux
    (liste vide) plutôt que de casser le menu déroulant -- même logique
    de tolérance que l'appel automatique post-reparent plus haut."""
    if not scenario:
        return []
    try:
        resultat = subprocess.run(
            [sys.executable, "reparenter_sous_zones_orphelines.py",
             "--scenario", scenario, "--scan-candidates", "--json"],
            cwd=pipeline_dir, capture_output=True, text=True,
            timeout=15, stdin=subprocess.DEVNULL,
        )
        sortie = resultat.stdout.strip()
        if not sortie:
            return []
        payload = json.loads(sortie.splitlines()[-1])
        if not payload.get("ok"):
            return []
        return payload.get("candidats", [])
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, IndexError):
        return []




def _scan_instance_slugs(vault_root: Path, scenario: str) -> list:
    """Scan instances/*.md, extrait frontmatter slug."""
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        return []
    slugs = []
    pattern = re.compile(r"^slug:\s*(.+)$", re.MULTILINE)
    sc_pattern = re.compile(r"^scenario:\s*(.+)$", re.MULTILINE)
    for md_file in instances_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            slug_m = pattern.search(content)
            if not slug_m:
                continue
            slug = slug_m.group(1).strip()
            if scenario and scenario != "all":
                sc_m = sc_pattern.search(content)
                if sc_m and sc_m.group(1).strip() != scenario:
                    continue
            slugs.append(slug)
        except Exception:
            continue
    return sorted(slugs)


def _scan_event_slugs(vault_root: Path) -> list:
    """
    Scan evenements/*.md (archétypes, pas event_instances/ qui sont les
    déclinaisons par scénario), extrait le frontmatter `slug`. Ajouté le
    2 août 2026 pour le sélecteur de trace_injection.py -- même principe
    que _scan_signal_slugs ci-dessus.
    """
    evenements_dir = vault_root / "evenements"
    if not evenements_dir.exists():
        return []
    slugs = []
    pattern = re.compile(r"^slug:\s*(.+)$", re.MULTILINE)
    for md_file in evenements_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            m = pattern.search(content)
            if m:
                slugs.append(m.group(1).strip())
        except Exception:
            continue
    return sorted(slugs)


def _scan_signal_slugs(vault_root: Path) -> list:
    """
    Scan signaux_custom/*.md (fiches d'audit de inject_custom_signals.py),
    extrait le frontmatter `slug`. Ajouté le 26 juillet 2026 pour le
    nouveau type `signal` de undo_custom.py -- glob("*.md") exclut déjà
    naturellement processed.yaml/needs_review.yaml (extension .yaml), pas
    besoin de les filtrer explicitement.
    """
    signaux_dir = vault_root / "signaux_custom"
    if not signaux_dir.exists():
        return []
    slugs = []
    pattern = re.compile(r"^slug:\s*(.+)$", re.MULTILINE)
    for md_file in signaux_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            m = pattern.search(content)
            if m:
                slugs.append(m.group(1).strip())
        except Exception:
            continue
    return sorted(slugs)


def _scan_entity_slugs(vault_root: Path, pipeline_dir: Path) -> list:
    """Lit _entities_list.json."""
    candidates = [
        pipeline_dir / "_entities_list.json",
        vault_root / "_entities_list.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return sorted(data)
                if isinstance(data, dict):
                    return sorted(data.keys())
            except Exception:
                pass
    # Fallback corrigé le 2 août 2026 : l'ancien fallback appelait
    # _scan_instance_slugs(vault_root, ""), qui retourne le slug propre à
    # CHAQUE INSTANCE (entité + suffixe scénario, ex.
    # "administrations_hybrides_..._reference") -- pas le slug d'entité
    # attendu par tous les appelants de type=entities (trace_injection.py,
    # generate.py mode forcer). Symptôme observé : le menu "Élément à
    # forcer" proposait des instances au lieu d'entités dès que
    # _entities_list.json était absent/périmé. Dérive maintenant le vrai
    # slug d'entité depuis le champ `entite:` de chaque fiche instance,
    # dédupliqué -- coûte un scan complet d'instances/ (pas de cache),
    # acceptable pour un menu GUI peuplé à la demande.
    return _scan_entity_slugs_from_instances(vault_root)


def _scan_entity_slugs_from_instances(vault_root: Path) -> list:
    """Dérive les slugs d'entités depuis le champ `entite:` des fiches
    instances/*.md -- fallback de _scan_entity_slugs() ci-dessus quand
    _entities_list.json est absent. Exclut instance_template.md (même
    pollution que celle corrigée dans routes_dashboard.py le 2 août
    2026 -- le gabarit n'a pas de champ `entite:` de toute façon, mais
    autant l'exclure explicitement plutôt que de compter sur l'absence
    du champ pour le filtrer silencieusement)."""
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        return []
    entite_pattern = re.compile(r"^entite:\s*(.+)$", re.MULTILINE)
    entites = set()
    for md_file in instances_dir.glob("*.md"):
        if md_file.name == "instance_template.md":
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
            m = entite_pattern.search(content)
            if m:
                entites.add(m.group(1).strip())
        except Exception:
            continue
    return sorted(entites)


def _scan_zone_slugs(pipeline_dir: Path, scenario: str, n1_only: bool) -> list:
    """Parse geographie/{scenario}.md pour extraire les slugs de zones.

    Corrigé le 31 juillet 2026 -- l'ancienne implémentation utilisait un
    découpage par regex (`re.split` sur les délimiteurs `---`) suivi de
    `.search()` (qui ne renvoie que la PREMIÈRE occurrence) sur chaque
    bloc. Or geographie/{scenario}.md ne contient que 2 délimiteurs `---`
    au total (un seul bloc de frontmatter YAML englobant TOUTE la liste
    des zones, pas un bloc par zone) -- résultat : une seule zone
    remontée par fichier, peu importe leur nombre réel (bug signalé par
    David : "je n'ai qu'une zone N1 dans le menu"). Remplacé par un vrai
    parsing YAML, sur le même principe que _scan_zone_slugs_hier
    ci-dessous (qui n'avait pas ce bug -- codé correctement dès le
    départ)."""
    if not scenario:
        return []
    geo_file = pipeline_dir / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return []
    try:
        import yaml as _yaml
        raw = geo_file.read_text(encoding="utf-8")
        parts = raw.split("---")
        fm_str = parts[1] if len(parts) >= 2 else raw
        fm = _yaml.safe_load(fm_str) or {}
        raw_zones = fm.get("zones") or []
    except Exception:
        return []

    slugs = []
    for z in raw_zones:
        if not isinstance(z, dict):
            continue
        slug = str(z.get("slug", "")).strip()
        if not slug:
            continue
        if n1_only and int(z.get("niveau", 1)) != 1:
            continue
        slugs.append(slug)
    return sorted(set(slugs))


def _zones_avec_journal(pipeline_dir: Path, scenario: str) -> set:
    """Retourne l'ensemble des slugs de zone ayant un journal dans
    journaux.yaml pour ce scénario (union des deux lignes éditoriales
    pro_pouvoir/opposition).

    Ajouté le 11 août 2026 : --zone-slug (generate.py, mode Semi-guidé)
    utilisait jusqu'ici la même liste zones_hier que zone_hint
    (create_entities/inject_events), qui inclut toutes les sous-zones
    N2/N3 -- alors que journaux.yaml n'a jamais qu'une entrée par zone
    N1. Une sous-zone sélectionnée dans ce menu faisait donc
    systématiquement échouer validate_config_semi_guide() au lancement
    du script, après coup, plutôt que d'être filtrée en amont (cas réel :
    archives_neutres_geneve, niveau 2 sous geneve_bunker_institutions).

    Filtre sur le contenu réel de journaux.yaml (structure :
    data[scenario][ligne]['zones'] = {slug: {...}}) plutôt que sur
    niveau==1, pour rester correct même si la convention de niveaux
    changeait un jour.
    """
    journaux_path = pipeline_dir / "journaux.yaml"
    if not journaux_path.exists():
        return set()
    try:
        import yaml as _yaml
        data = _yaml.safe_load(journaux_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return set()

    scenario_data = data.get(scenario) or {}
    result = set()
    for ligne, contenu in scenario_data.items():
        if not isinstance(contenu, dict):
            continue
        result.update((contenu.get("zones") or {}).keys())
    return result


def _zones_candidates_oral(pipeline_dir: Path, scenario: str) -> list:
    """Retourne les zones du scénario (les deux lignes éditoriales)
    n'ayant pas encore type_diffusion en oral/mixte -- candidates à la
    conversion via le nouveau mode "convertir" de
    inject_orateur_custom.py (29 août 2026, P21, retour de David).

    Contexte : le mode auto de inject_orateur_custom.py ne crée des
    orateur·rices QUE sur des zones déjà oral/mixte (décision
    délibérée -- créer des orateur·rices sur une zone "ecrit" les
    laisserait inutilisé·es). Basculer une zone en oral/mixte reste
    donc un choix éditorial curaté, zone par zone -- jamais automatisé
    en aveugle (même raisonnement que le refus du --all multi-
    scénarios sur le mode auto). Ce scan alimente un multi-select GUI
    où David choisit lui-même quelles zones convertir, plutôt que
    d'éditer journaux.yaml à la main une par une.

    Chaque candidat a un "slug" composite "{ligne}::{zone_slug}" --
    nécessaire car le même zone_slug peut exister sous les deux lignes
    éditoriales avec un statut type_diffusion différent (indépendant
    par ligne, voir zone afrique_centrale_australe : oral côté
    pro_pouvoir, jamais vérifié côté opposition).

    Même pattern de lecture directe de journaux.yaml (sans cache) que
    _zones_avec_journal()/_scan_intervenants_eligibles() ci-dessus."""
    if not scenario:
        return []
    journaux_path = pipeline_dir / "journaux.yaml"
    if not journaux_path.exists():
        return []
    try:
        import yaml as _yaml
        data = _yaml.safe_load(journaux_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return []

    scenario_data = data.get(scenario) or {}
    candidats = []
    for ligne, contenu in scenario_data.items():
        if not isinstance(contenu, dict):
            continue
        zones = contenu.get("zones") or {}
        for zone_slug, zone_data in sorted(zones.items()):
            if not isinstance(zone_data, dict):
                continue
            type_diffusion = zone_data.get("type_diffusion", "ecrit")
            if type_diffusion in ("oral", "mixte"):
                continue
            candidats.append({
                "slug": "{}::{}".format(ligne, zone_slug),
                "ligne": ligne,
                "zone_slug": zone_slug,
                "nom": zone_data.get("nom", zone_slug),
                "n_journalistes": len(zone_data.get("journalistes") or []),
                "n_orateurs": len(zone_data.get("orateurs") or []),
            })
    return candidats


def _scan_intervenants_eligibles(pipeline_dir: Path, scenario: str, ligne: str,
                                  zone: str, mode: str, thematique: str = "") -> tuple:
    """Retourne (noms, labels) des journalistes/orateurs éligibles pour
    une combinaison scenario/ligne/zone précise, selon le mode de
    diffusion choisi dans le GUI (champ --type-diffusion) -- pour le
    nouveau champ "Forcer un intervenant précis" de generate.py
    (--intervenant, P21, 25 août 2026).

    mode == "ecrit"  -> uniquement les journalistes de la zone
    mode == "oral"   -> uniquement les orateurs de la zone
    tout le reste ("mixte", "auto", vide) -> les deux mélangés, décision
    explicite de David (25 août 2026) : plus simple que de relire le
    vrai type_diffusion configuré sur la zone pour trancher au cas par
    cas.

    thematique (26 août 2026, retour de David) : filtre les
    JOURNALISTES sur cette thématique, EXACTEMENT comme le fait
    get_journal_profile() (prompt_builder.py) au moment réel de la
    génération -- même repli si aucun·e journaliste ne correspond
    (retombe sur la liste complète plutôt qu'une liste vide, pour ne
    jamais proposer moins d'options que ce que la génération réelle
    accepterait). Les ORATEURS ne sont jamais filtrés par thématique --
    ce concept n'existe pas pour eux dans le modèle de données (ils sont
    caractérisés par communautes_desservies à la place, scoping P21 du
    12 juillet).

    labels (26 août 2026, retour de David) : "(journaliste)"/"(orateur)"
    ajouté au texte AFFICHÉ dans le menu déroulant uniquement -- la
    valeur réellement soumise (noms) reste le nom exact tel que dans
    journaux.yaml, pour continuer à matcher intervenant_override côté
    prompt_builder.py sans transformation.

    Même pattern de lecture directe de journaux.yaml (sans cache) que
    _zones_avec_journal() ci-dessus, pour rester cohérent.
    """
    if not scenario or not ligne or not zone:
        return [], {}
    journaux_path = pipeline_dir / "journaux.yaml"
    if not journaux_path.exists():
        return [], {}
    try:
        import yaml as _yaml
        data = _yaml.safe_load(journaux_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return [], {}

    zone_data = (
        (data.get(scenario) or {})
        .get(ligne, {})
        .get("zones", {})
        .get(zone, {})
    )
    if not zone_data:
        return [], {}

    journalistes_data = zone_data.get("journalistes") or []
    orateurs_data = zone_data.get("orateurs") or []

    # Filtrage par thématique -- même logique que get_journal_profile()
    # (prompt_builder.py) : filtre d'abord, repli sur la liste complète
    # si le filtre ne retient personne.
    if thematique:
        journalistes_filtres = [
            j for j in journalistes_data
            if thematique in (j.get("thematiques") or [])
        ]
        if not journalistes_filtres:
            journalistes_filtres = journalistes_data
    else:
        journalistes_filtres = journalistes_data

    journalistes = [j.get("nom", "") for j in journalistes_filtres if j.get("nom")]
    orateurs = [o.get("nom", "") for o in orateurs_data if o.get("nom")]

    if mode == "ecrit":
        noms = journalistes
    elif mode == "oral":
        noms = orateurs
    else:
        noms = journalistes + orateurs

    labels = {}
    for n in journalistes:
        if n in noms:
            labels[n] = "{} (journaliste)".format(n)
    for n in orateurs:
        if n in noms:
            labels[n] = "{} (orateur)".format(n)

    return noms, labels


def _scan_zone_slugs_hier(pipeline_dir: Path, scenario: str) -> list:
    """Retourne toutes les zones hiérarchiquement (N1 -> N2 -> N3)."""
    if not scenario:
        return []
    geo_file = pipeline_dir / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return []
    try:
        import yaml as _yaml
        raw = geo_file.read_text(encoding="utf-8")
        # Le fichier est un frontmatter YAML entre --- délimiteurs
        parts = raw.split("---")
        fm_str = parts[1] if len(parts) >= 2 else raw
        fm = _yaml.safe_load(fm_str) or {}
        raw_zones = fm.get("zones") or []
    except Exception as e:
        return []

    zones = []
    for z in raw_zones:
        if not isinstance(z, dict):
            continue
        slug = str(z.get("slug", "")).strip()
        if not slug:
            continue
        nom    = str(z.get("nom", slug)).strip()
        niveau = int(z.get("niveau", 1))
        parent = z.get("parent")
        if parent in (None, "null", "~", ""):
            parent = None
        else:
            parent = str(parent).strip()
        zones.append({"slug": slug, "nom": nom, "niveau": niveau, "parent": parent})

    # Tri hiérarchique
    n1 = [z for z in zones if z["niveau"] == 1]
    by_parent: dict = {}
    for z in zones:
        if z["niveau"] > 1 and z["parent"]:
            by_parent.setdefault(z["parent"], []).append(z)

    result = []
    def add_zone(z):
        result.append(z)
        for child in sorted(by_parent.get(z["slug"], []), key=lambda x: x["nom"]):
            add_zone(child)

    for z in sorted(n1, key=lambda x: x["nom"]):
        add_zone(z)

    seen = {z["slug"] for z in result}
    for z in zones:
        if z["slug"] not in seen:
            result.append(z)

    return result


# ── Traçabilité ──────────────────────────────────────────────────────────────

@app.route("/api/forcer/scenarios", methods=["GET"])
def get_forcer_scenarios():
    """
    GET /api/forcer/scenarios?type=instance|evenement|signal&slug=<slug>
    Restreint le menu de sélection des scénarios (mode "forcer" de
    generate.py) à ceux où l'élément existe réellement -- ajouté le
    2 août 2026. Appelle generator/loader.py en sous-processus (pas
    d'import direct dans app.py, même principe que les autres routes
    /api/slugs de ce fichier) pour rester découplé du process Flask.
    """
    type_ = (request.args.get("type") or "").strip()
    slug  = (request.args.get("slug") or "").strip()
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))

    code = (
        "import sys, json; sys.path.insert(0, '.'); import loader; "
        "print(json.dumps(loader.scenarios_disponibles_pour_element({!r}, {!r})))"
    ).format(type_, slug)
    try:
        resultat = subprocess.run(
            [sys.executable, "-c", code], cwd=pipeline_dir,
            capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Résolution des scénarios expirée après 15s"}), 504

    if resultat.returncode != 0:
        return jsonify({"error": resultat.stderr.strip() or "Échec"}), 500
    try:
        return jsonify({"scenarios": json.loads(resultat.stdout.strip())})
    except json.JSONDecodeError:
        return jsonify({"error": "Sortie non-JSON", "raw": resultat.stdout[-500:]}), 500


@app.route("/api/forcer/zones", methods=["GET"])
def get_forcer_zones():
    """
    GET /api/forcer/zones?type=instance|evenement|signal&slug=<slug>&scenarios=a,b,c
    Restreint le menu Zone aux zones où l'élément est effectivement
    localisé, parmi les scénarios fournis. Ajouté le 2 août 2026. Un
    signal n'a jamais de zone -- retourne {} normalement, pas une erreur.
    """
    type_      = (request.args.get("type") or "").strip()
    slug       = (request.args.get("slug") or "").strip()
    scenarios  = [s for s in (request.args.get("scenarios") or "").split(",") if s.strip()]
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))

    code = (
        "import sys, json; sys.path.insert(0, '.'); import loader; "
        "print(json.dumps(loader.zones_disponibles_pour_element({!r}, {!r}, {!r})))"
    ).format(type_, slug, scenarios)
    try:
        resultat = subprocess.run(
            [sys.executable, "-c", code], cwd=pipeline_dir,
            capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Résolution des zones expirée après 15s"}), 504

    if resultat.returncode != 0:
        return jsonify({"error": resultat.stderr.strip() or "Échec"}), 500
    try:
        return jsonify({"zones": json.loads(resultat.stdout.strip())})
    except json.JSONDecodeError:
        return jsonify({"error": "Sortie non-JSON", "raw": resultat.stdout[-500:]}), 500


@app.route("/api/trace/<slug>", methods=["GET"])
def get_trace(slug):
    """
    Reconstitue le parcours complet d'un slug (instance/événement/signal) via
    generator/trace_injection.py --json en sous-processus (même pattern que
    zoning_topdown.py --json ci-dessus). Query params optionnels :
    ?type=instance|evenement|signal (force le type si l'auto-détection
    échoue) et ?skip_articles=1 (saute le scan aval, plus rapide).
    """
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))

    cmd = [sys.executable, "trace_injection.py", "--slug", slug, "--json"]
    type_ = (request.args.get("type") or "").strip()
    if type_:
        cmd += ["--type", type_]
    if request.args.get("skip_articles"):
        cmd.append("--skip-articles")

    try:
        resultat = subprocess.run(
            cmd, cwd=pipeline_dir, capture_output=True, text=True,
            timeout=30, stdin=subprocess.DEVNULL,  # pas d'appel LLM -- purement mécanique, doit être rapide
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "trace_injection.py expiré après 30s"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"trace_injection.py introuvable dans {pipeline_dir}"}), 500

    if resultat.returncode != 0:
        return jsonify({"error": resultat.stderr.strip() or f"Échec (code {resultat.returncode})"}), 404

    sortie = resultat.stdout.strip()
    if not sortie:
        return jsonify({"error": f"Aucune sortie du sous-processus : {resultat.stderr[-500:]}"}), 500

    try:
        return jsonify(json.loads(sortie))
    except json.JSONDecodeError:
        return jsonify({"error": "Sortie non-JSON de trace_injection.py", "raw": sortie[-1000:]}), 500


# ── Revue ─────────────────────────────────────────────────────────────────────

@app.route("/api/review", methods=["GET"])
def get_review():
    cfg = load_config()
    # Bug #15 : ces 3 fonctions cherchaient dans pipeline_dir (generator/),
    # alors que enrich_minimal.py / inject_custom_events.py / extract_localisation.py
    # écrivent tous ces fichiers à la racine du vault (vault_root).
    vault_root = Path(cfg.get("vault_root", ""))
    items = []
    items += _parse_needs_review_enrich(vault_root)
    items += _parse_needs_review_events(vault_root)
    items += _parse_needs_review_entites(vault_root)   # ajouté le 2 août 2026 — manquait entièrement
    items += _parse_needs_review_signaux(vault_root)    # ajouté le 2 août 2026 — manquait entièrement
    items += _parse_localisation_review(vault_root)
    return jsonify({"items": items, "total": len(items)})


def _parse_needs_review_enrich(vault_root: Path) -> list:
    """
    needs_review_enrich.yaml (dans instances_custom/, à la racine du vault) :
      needs_review:
        - slug: xxx
          scenario: yyy
          date: 2026-06-27
          errors: [...]
    """
    candidates = [
        vault_root / "instances_custom" / "needs_review_enrich.yaml",
        vault_root / "needs_review_enrich.yaml",
    ]
    for p in candidates:
        if p.exists():
            return _read_needs_review_yaml(p, "enrich")
    return []


def _parse_needs_review_events(vault_root: Path) -> list:
    """
    needs_review.yaml (dans evenements_custom/, à la racine du vault) :
      needs_review:
        - idea: {...}
          failed_scenarios: [...]
          status: needs_review
    """
    candidates = [
        vault_root / "evenements_custom" / "needs_review.yaml",
        vault_root / "needs_review.yaml",
    ]
    for p in candidates:
        if p.exists():
            return _read_needs_review_yaml(p, "events")
    return []


def _parse_needs_review_entites(vault_root: Path) -> list:
    """
    needs_review.yaml (dans entites_custom/, à la racine du vault) — ajouté
    le 2 août 2026, manquait entièrement (ni le fichier ni le format
    n'étaient couverts par /api/review, contrairement au badge de
    routes_dashboard.py qui, lui, comptait déjà ce fichier) :
      needs_review:
        - status: needs_review
          idea: {...}
          error: ...
    Contrairement aux sources enrich/events, la première clé de chaque
    entrée est "status", pas "slug" ni "idea" (create_entity.py /
    create_entities_and_instances.py, sort_keys=False à l'écriture donc
    l'ordre "status, idea, error" est fiable).
    """
    candidates = [
        vault_root / "entites_custom" / "needs_review.yaml",
        vault_root / "needs_review.yaml",
    ]
    for p in candidates:
        if p.exists():
            return _read_needs_review_yaml(p, "entites", start_marker="- status:", slug_placeholder="(entité)")
    return []


def _parse_needs_review_signaux(vault_root: Path) -> list:
    """
    needs_review.yaml (dans signaux_custom/, à la racine du vault) — ajouté
    le 2 août 2026, même trou que ci-dessus (inject_custom_signals.py,
    même format "status" en tête d'entrée).
    """
    candidates = [
        vault_root / "signaux_custom" / "needs_review.yaml",
        vault_root / "needs_review.yaml",
    ]
    for p in candidates:
        if p.exists():
            return _read_needs_review_yaml(p, "signaux", start_marker="- status:", slug_placeholder="(signal)")
    return []


def _read_needs_review_yaml(path: Path, source: str, start_marker: str = None, slug_placeholder: str = None) -> list:
    items = []
    try:
        txt = path.read_text(encoding="utf-8")
        # Parser naïf sans pyyaml : extraire les blocs sous "needs_review:"
        # Chaque entrée commence par "- slug:" ou "- idea:"
        in_list = False
        current: dict = {}

        for line in txt.splitlines():
            stripped = line.strip()

            # Entrée dans la liste needs_review
            if stripped == "needs_review:":
                in_list = True
                continue

            if not in_list:
                continue

            # Nouvelle entrée
            if stripped.startswith("- slug:"):
                if current:
                    items.append(current)
                current = {
                    "source": source,
                    "slug": stripped[len("- slug:"):].strip(),
                    "scenario": "",
                    "error": "",
                }
            elif stripped.startswith("- idea:") or (stripped.startswith("- ") and "idea:" in stripped):
                if current:
                    items.append(current)
                current = {
                    "source": source,
                    "slug": "(événement)",
                    "scenario": "",
                    "error": "",
                }
            elif start_marker and stripped.startswith(start_marker):
                # Source entites/signaux (ajouté le 2 août 2026) : la
                # première clé de chaque entrée est "status", pas
                # "slug"/"idea" — même mécanisme de flush que ci-dessus.
                if current:
                    items.append(current)
                current = {
                    "source": source,
                    "slug": slug_placeholder or "(?)",
                    "scenario": "",
                    "error": "",
                }
            elif current:
                if stripped.startswith("scenario:"):
                    current["scenario"] = stripped[len("scenario:"):].strip()
                elif stripped.startswith("date:"):
                    current["date"] = stripped[len("date:"):].strip()
                elif stripped.startswith("failed_scenarios:"):
                    val = stripped[len("failed_scenarios:"):].strip()
                    if val and val != "[]":
                        current["scenario"] = val
                elif stripped.startswith("- ") and current.get("slug") == "(événement)" and not current.get("scenario"):
                    # item de liste failed_scenarios
                    current["scenario"] = stripped[2:].strip()
                elif stripped.startswith("errors:"):
                    pass
                # Repli générique des 3 scripts d'injection (create_entities_
                # and_instances.py, inject_custom_events.py, inject_custom_
                # signals.py) sur une exception imprévue : `{"error": str(e)}`,
                # une clé SCALAIRE unique — à ne pas confondre avec "errors:"
                # (pluriel, liste) déjà géré ci-dessus. Jusqu'ici non reconnu
                # du tout : une entrée needs_review née de ce chemin de repli
                # affichait toujours DÉTAIL vide, sur les 3 pipelines. Ajouté
                # le 12 août 2026, même session que le correctif nom:/
                # scenario_ref:/reason: ci-dessous.
                elif stripped.startswith("error:") and not current.get("error"):
                    val = stripped[len("error:"):].strip()
                    if val.startswith("'") and val.endswith("'"):
                        val = val[1:-1].replace("''", "'")
                    elif val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    current["error"] = val
                # Champs propres à entites_custom/signaux_custom (12 août 2026) :
                # jusqu'ici le placeholder posé par start_marker (ex. "(entité)")
                # n'était jamais remplacé par le vrai nom, faute de reconnaître
                # les clés "nom:"/"scenario_ref:"/"reason:" utilisées par ce
                # format (imbriquées sous "idea:", contrairement au format
                # événements/enrichissement) — le parseur ignore de toute façon
                # l'indentation (stripped = line.strip()), donc les lire au même
                # niveau que les autres clés ne pose pas de problème structurel.
                elif stripped.startswith("nom:") and current.get("slug", "").startswith("(") and current.get("slug", "").endswith(")"):
                    current["slug"] = stripped[len("nom:"):].strip()
                elif stripped.startswith("scenario_ref:") and not current.get("scenario"):
                    current["scenario"] = stripped[len("scenario_ref:"):].strip()
                elif stripped.startswith("reason:") and not current.get("error"):
                    val = stripped[len("reason:"):].strip()
                    if val.startswith("'") and val.endswith("'"):
                        val = val[1:-1].replace("''", "'")
                    elif val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    current["error"] = val
                elif stripped.startswith("- ") and current.get("slug") != "(événement)":
                    # Item d'une liste errors
                    err = stripped[2:].strip()
                    if err and not current["error"]:
                        current["error"] = err

        if current:
            items.append(current)

    except Exception as e:
        items.append({"source": source, "slug": "?", "scenario": "", "error": str(e)})

    return items


def _parse_localisation_review(vault_root: Path) -> list:
    """
    localisation_review.md (documentation/need_action/, à la racine du vault) :
      ## scenario (N)
      ### slug
      - type: ...
      - zone candidate: ...
    """
    review_md = vault_root / "documentation" / "need_action" / "localisation_review.md"
    if not review_md.exists():
        return []
    items = []
    try:
        txt = review_md.read_text(encoding="utf-8")
        current_scenario = ""
        current_slug = ""
        current_details: list = []

        for line in txt.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                # Nouveau scénario
                current_scenario = stripped[3:].split("(")[0].strip()
            elif stripped.startswith("### "):
                # Nouveau slug — flush précédent
                if current_slug:
                    items.append({
                        "source": "localisation",
                        "slug": current_slug,
                        "scenario": current_scenario,
                        "error": " · ".join(current_details[:2]),
                    })
                current_slug = stripped[4:].strip()
                current_details = []
            elif stripped.startswith("- **") and current_slug:
                # Détail : - **zone candidate** : xxx
                current_details.append(stripped.lstrip("- ").strip())

        # Flush dernier
        if current_slug:
            items.append({
                "source": "localisation",
                "slug": current_slug,
                "scenario": current_scenario,
                "error": " · ".join(current_details[:2]),
            })

    except Exception as e:
        pass

    return items


# ── Exécution des scripts ─────────────────────────────────────────────────────

@app.route("/api/run", methods=["POST"])
def run_script():
    """
    Lance un script en subprocess.
    Body JSON :
    {
      "script_id": "enrich_minimal",
      "args": ["--limit", "5", "--dry-run"]
    }
    """
    # Vérifier qu'aucun script ne tourne déjà
    with _runs_lock:
        for run in _runs.values():
            if not run.get("done"):
                return jsonify({"error": "Un script est déjà en cours"}), 409

    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON manquant"}), 400

    script_id = data.get("script_id")
    extra_args = data.get("args", [])

    # Trouver le script dans la config
    scripts = load_scripts_config()
    script_cfg = next((s for s in scripts if s["id"] == script_id), None)
    if not script_cfg:
        return jsonify({"error": f"Script inconnu : {script_id}"}), 404

    cfg = load_config()
    pipeline_dir = cfg.get("pipeline_dir", ".")

    # Construire la commande
    cmd = ["python3", script_cfg["script"]] + [str(a) for a in extra_args]

    # Injecter les variables LLM + clés API
    env = os.environ.copy()

    # Override manuel du modèle — seulement si explicitement demandé pour ce
    # run précis (force_llm_override: true dans le body). Par défaut (absent
    # ou false), on n'injecte PAS LLM_PROVIDER/LLM_MODEL : chaque script migré
    # vers le routing par tier (llm_client.TASK_TIER_DEFAULTS) résout alors
    # son propre modèle selon le tier de la tâche, au lieu d'être écrasé
    # silencieusement par la valeur par défaut de gui/config.json.
    #
    # Avant le 11 juillet 2026, ces variables étaient injectées de façon
    # inconditionnelle à chaque run — ce qui neutralisait le routing par tier
    # pour tout script lancé depuis le GUI (bug découvert le même jour :
    # articles générés sur mistral-small malgré le tier "strict" configuré
    # sur mistral-large).
    if data.get("force_llm_override"):
        llm = cfg.get("llm", {})
        env["LLM_PROVIDER"] = llm.get("provider", "mistral")
        if llm.get("provider") == "mistral":
            env["LLM_MODEL"] = llm.get("model_mistral", "mistral-medium")
        else:
            env["LLM_MODEL"] = llm.get("model_claude", "claude-sonnet-4-6")

    run_id = str(uuid.uuid4())[:8]
    run_entry = {
        "script_id": script_id,
        "cmd": cmd,
        "lines": [],
        "done": False,
        "return_code": None,
        "process": None,
    }

    with _runs_lock:
        _runs[run_id] = run_entry

    t = threading.Thread(
        target=_execute_script,
        args=(run_id, cmd, pipeline_dir, env),
        daemon=True,
    )
    t.start()

    return jsonify({"run_id": run_id})


def _execute_script(run_id: str, cmd: list, cwd: str, env: dict) -> None:
    """Thread worker : exécute le subprocess et accumule les lignes de log."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    script_id = _runs[run_id]["script_id"]
    log_path = LOGS_DIR / f"{script_id}_{timestamp}.log"

    try:
        # stdin=DEVNULL (et non l'héritage par défaut) : sans ça, le
        # subprocess hérite du stdin du terminal ayant lancé Flask lui-même
        # (visible dans `ps aux` : TTY réel type s014, pas '??'). Un input()
        # oublié dans un script (ex: fallback CLI d'un flag optionnel non
        # renseigné) bloque alors indéfiniment le run — silencieusement,
        # sans erreur ni log, %CPU à 0 — puisque personne ne peut jamais
        # taper dans ce terminal pour répondre à la place de l'utilisateur
        # GUI. DEVNULL coupe l'héritage à la racine pour tous les scripts,
        # présents et futurs (bug découvert le 12 juillet 2026 sur
        # inject_custom_events.py --mode auto, mais générique à tout script
        # lancé via ce Popen).
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        _runs[run_id]["process"] = process

        with open(log_path, "w", encoding="utf-8") as log_file:
            for line in process.stdout:
                line = line.rstrip("\n")
                _runs[run_id]["lines"].append(line)
                log_file.write(line + "\n")
                log_file.flush()

        process.wait()
        _runs[run_id]["return_code"] = process.returncode

    except Exception as e:
        _runs[run_id]["lines"].append(f"[ERROR] Échec lancement : {e}")
        _runs[run_id]["return_code"] = -1
    finally:
        _runs[run_id]["done"] = True


@app.route("/api/stream/<run_id>")
def stream_log(run_id: str):
    """Server-Sent Events — diffuse les lignes de log en temps réel."""
    def generate():
        last_idx = 0
        while True:
            run = _runs.get(run_id)
            if not run:
                yield f"data: [ERROR] run_id inconnu\n\n"
                break
            lines = run["lines"]
            while last_idx < len(lines):
                line = lines[last_idx]
                yield f"data: {line}\n\n"
                last_idx += 1
            if run["done"] and last_idx >= len(lines):
                rc = run.get("return_code", 0)
                yield f"data: [DONE] code={rc}\n\n"
                break
            time.sleep(0.1)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/stop/<run_id>", methods=["POST"])
def stop_script(run_id: str):
    run = _runs.get(run_id)
    if not run:
        return jsonify({"error": "run_id inconnu"}), 404
    process = run.get("process")
    if process and not run["done"]:
        process.terminate()
        run["done"] = True
        run["lines"].append("[STOP] Script interrompu par l'utilisateur")
        return jsonify({"ok": True})
    return jsonify({"error": "Aucun process actif"}), 400


@app.route("/api/status", methods=["GET"])
def get_status():
    with _runs_lock:
        for run_id, run in _runs.items():
            if not run.get("done"):
                return jsonify({"active": True, "run_id": run_id, "script_id": run["script_id"]})
    return jsonify({"active": False})


# ── Lancement ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  OURRASSOL 2098 — GUI")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000, threaded=True)

"""
Ourrassol 2098 — GUI Flask
app.py : serveur principal
"""

import json
import os
import re
import subprocess
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
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(load_config())


@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400
    cfg = load_config()
    # Mise à jour partielle — seules les clés envoyées
    for key, value in data.items():
        if key in cfg:
            cfg[key] = value
        # Support nested: llm.*
    if "llm" in data:
        # Préserver les clés available_* qui ne sont pas envoyées par le frontend
        preserved = {k: v for k, v in cfg["llm"].items() if k.startswith("available_")}
        cfg["llm"].update(data["llm"])
        for k, v in preserved.items():
            cfg["llm"].setdefault(k, v)
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
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    rel_path = request.args.get("path", "")
    if not rel_path:
        return jsonify({"error": "Paramètre path manquant"}), 400
    target = (pipeline_dir / rel_path).resolve()
    try:
        target.relative_to(pipeline_dir.resolve())
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
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json()
    if not data or "path" not in data or "content" not in data:
        return jsonify({"error": "Données manquantes"}), 400
    rel_path = data["path"]
    file_content = data["content"]
    target = (pipeline_dir / rel_path).resolve()
    try:
        target.relative_to(pipeline_dir.resolve())
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
      "path": "config.yaml",
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
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json()
    if not data or "path" not in data or "fields" not in data:
        return jsonify({"error": "Données manquantes"}), 400

    rel_path = data["path"]
    fields = data["fields"]  # dict clé → valeur

    target = (pipeline_dir / rel_path).resolve()
    try:
        target.relative_to(pipeline_dir.resolve())
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
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json()
    if not data or "path" not in data or "entry" not in data:
        return jsonify({"error": "Données manquantes"}), 400

    rel_path = data["path"]
    entry = data["entry"]

    target = (pipeline_dir / rel_path).resolve()
    try:
        target.relative_to(pipeline_dir.resolve())
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
        return jsonify({"pays": data.get("pays_liste", [])})
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


# ── API Slugs ─────────────────────────────────────────────────────────────────

@app.route("/api/slugs", methods=["GET"])
def get_slugs():
    """
    GET /api/slugs?type=instances&scenario=breakdown
    GET /api/slugs?type=zones&scenario=breakdown
    GET /api/slugs?type=entities
    GET /api/slugs?type=zones_all&scenario=breakdown
    """
    slug_type = request.args.get("type", "instances")
    scenario = request.args.get("scenario", "")
    cfg = load_config()
    vault_root = Path(cfg.get("vault_root", ""))
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))

    slugs = []

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
    except Exception as e:
        return jsonify({"slugs": [], "error": str(e)})

    return jsonify({"slugs": slugs})


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
    # Fallback : scan instances
    return _scan_instance_slugs(vault_root, "")


def _scan_zone_slugs(pipeline_dir: Path, scenario: str, n1_only: bool) -> list:
    """Parse geographie/{scenario}.md pour extraire les slugs de zones."""
    if not scenario:
        return []
    geo_file = pipeline_dir / "geographie" / f"{scenario}.md"
    if not geo_file.exists():
        return []
    content = geo_file.read_text(encoding="utf-8")
    slugs = []
    # Recherche des blocs YAML inline ou frontmatter de zone
    # Format attendu : slug: xxx  +  niveau: 1 (optionnel)
    slug_pat = re.compile(r"slug:\s*(\S+)")
    niveau_pat = re.compile(r"niveau:\s*(\d+)")
    # On cherche les blocs délimités par ---
    blocks = re.split(r"^---+$", content, flags=re.MULTILINE)
    for block in blocks:
        slug_m = slug_pat.search(block)
        if not slug_m:
            continue
        slug = slug_m.group(1).strip()
        if n1_only:
            niveau_m = niveau_pat.search(block)
            if niveau_m and int(niveau_m.group(1)) != 1:
                continue
        slugs.append(slug)
    return sorted(set(slugs))


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
        for child in sorted(by_parent.get(z["slug"], []), key=lambda x: x["slug"]):
            add_zone(child)

    for z in sorted(n1, key=lambda x: x["slug"]):
        add_zone(z)

    seen = {z["slug"] for z in result}
    for z in zones:
        if z["slug"] not in seen:
            result.append(z)

    return result


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    cfg = load_config()
    vault_root   = Path(cfg.get("vault_root", ""))
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    llm          = cfg.get("llm", {})

    stats = {
        "llm": {
            "provider": llm.get("provider", "—"),
            "model": llm.get("model_mistral") if llm.get("provider") == "mistral"
                     else llm.get("model_claude", "—"),
        },
        "articles":       _stats_articles(vault_root),
        "instances":      _stats_instances(vault_root),
        "entites":        _stats_entites(vault_root, pipeline_dir),
        "journaux":       _stats_journaux(pipeline_dir),
        "enrichissement": _stats_enrichissement(vault_root),
        "thematiques":    _stats_thematiques(vault_root),
        "zones":          _stats_zones(pipeline_dir, cfg.get("scenarios", [])),
        "review_count":   _count_review_items(pipeline_dir),
        "vault_ok":       vault_root.exists() and pipeline_dir.exists(),
    }
    return jsonify(stats)


def _stats_articles(vault_root: Path) -> dict:
    articles_dir = vault_root / "articles"
    if not articles_dir.exists():
        return {"total": 0, "by_scenario": {}, "by_ligne": {}}
    total = 0
    by_scenario: dict = {}
    by_ligne: dict = {}
    sc_pat    = re.compile(r"^scenario:\s*(.+)$", re.MULTILINE)
    ligne_pat = re.compile(r"^ligne_editoriale:\s*(.+)$", re.MULTILINE)
    for f in sorted(articles_dir.glob("*.md")):
        try:
            txt = f.read_text(encoding="utf-8")
            total += 1
            sc_m = sc_pat.search(txt)
            sc   = sc_m.group(1).strip() if sc_m else "inconnu"
            by_scenario[sc] = by_scenario.get(sc, 0) + 1
            ligne_m = ligne_pat.search(txt)
            ligne   = ligne_m.group(1).strip() if ligne_m else "inconnu"
            by_ligne[ligne] = by_ligne.get(ligne, 0) + 1
        except Exception:
            continue
    return {"total": total, "by_scenario": by_scenario, "by_ligne": by_ligne}


def _stats_instances(vault_root: Path) -> dict:
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        return {"total": 0, "by_scenario": {}}
    total = 0
    by_scenario: dict = {}
    sc_pat = re.compile(r"^scenario:\s*(.+)$", re.MULTILINE)
    for f in instances_dir.glob("*.md"):
        try:
            txt = f.read_text(encoding="utf-8")
            total += 1
            sc_m = sc_pat.search(txt)
            sc   = sc_m.group(1).strip() if sc_m else "inconnu"
            by_scenario[sc] = by_scenario.get(sc, 0) + 1
        except Exception:
            continue
    return {"total": total, "by_scenario": by_scenario}


def _stats_entites(vault_root: Path, pipeline_dir: Path) -> dict:
    for p in [pipeline_dir / "_entities_list.json", vault_root / "_entities_list.json"]:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return {"total": len(data)}
                if isinstance(data, dict):
                    return {"total": len(data)}
            except Exception:
                pass
    entites_dir = vault_root / "entites"
    if entites_dir.exists():
        return {"total": len(list(entites_dir.glob("*.md")))}
    return {"total": 0}


def _stats_journaux(pipeline_dir: Path) -> dict:
    """
    Format journaux.yaml :
      breakdown:
        pro_pouvoir:
          _reseau:
            nom: ...
            zones:
              - zone_slug
    Compter le nombre de réseaux (journaux) par scénario.
    """
    journaux_path = pipeline_dir / "journaux.yaml"
    if not journaux_path.exists():
        return {"total": 0, "missing": True, "by_scenario": {}}
    try:
        txt = journaux_path.read_text(encoding="utf-8")
        # Chaque journal = un bloc "_reseau:" ou une clé de réseau sous une ligne éditoriale
        # On compte les occurrences de "nom:" au niveau réseau (indentation 3)
        # Format : scenario > ligne > reseau_key > { nom: ... }
        # Compter les clés de scénario (niveau 0, pas d'indentation, se termine par ":")
        by_scenario: dict = {}
        current_sc = None
        sc_re  = re.compile(r"^(\w+):$")
        # Compter les réseaux : ligne "    _reseau:" ou "    nom_journal:" à indent 4
        reseau_re = re.compile(r"^    \w")
        for line in txt.splitlines():
            sc_m = sc_re.match(line)
            if sc_m:
                current_sc = sc_m.group(1)
                if current_sc not in by_scenario:
                    by_scenario[current_sc] = 0
            elif current_sc and reseau_re.match(line) and line.strip().endswith(":"):
                # Clé de réseau (indent 4, pas de valeur inline)
                by_scenario[current_sc] = by_scenario.get(current_sc, 0) + 1
        total = sum(by_scenario.values())
        return {"total": total, "missing": False, "by_scenario": by_scenario}
    except Exception:
        return {"total": 0, "missing": False, "by_scenario": {}}


def _stats_enrichissement(vault_root: Path) -> dict:
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        return {"minimal": 0, "enrichi": 0, "autre": 0, "total": 0}
    minimal = enrichi = autre = 0
    status_pat = re.compile(r"^statut:\s*(.+)$", re.MULTILINE)
    for f in instances_dir.glob("*.md"):
        try:
            txt = f.read_text(encoding="utf-8")
            m = status_pat.search(txt)
            if m:
                s = m.group(1).strip()
                if "enrichi" in s:
                    enrichi += 1
                elif "minimal" in s:
                    minimal += 1
                else:
                    autre += 1
            else:
                autre += 1
        except Exception:
            continue
    return {"minimal": minimal, "enrichi": enrichi, "autre": autre,
            "total": minimal + enrichi + autre}


def _stats_thematiques(vault_root: Path) -> dict:
    articles_dir = vault_root / "articles"
    if not articles_dir.exists():
        return {}
    by_th: dict = {}
    th_pat = re.compile(r"^thematique:\s*(.+)$", re.MULTILINE)
    for f in articles_dir.glob("*.md"):
        try:
            txt = f.read_text(encoding="utf-8")
            m = th_pat.search(txt)
            th = m.group(1).strip() if m else "inconnu"
            by_th[th] = by_th.get(th, 0) + 1
        except Exception:
            continue
    return dict(sorted(by_th.items(), key=lambda x: -x[1]))


def _stats_zones(pipeline_dir: Path, scenarios: list) -> dict:
    """
    Format geographie/{scenario}.md :
      zones:
        - slug: afrique_centrale_australe
          nom: ...
          niveau: 1
    Compter les zones de niveau 1 par scénario.
    """
    geo_dir = pipeline_dir / "geographie"
    if not geo_dir.exists():
        return {"total": 0, "by_scenario": {}}
    niveau_pat = re.compile(r"^\s+niveau:\s*(\d+)")
    by_scenario: dict = {}
    total = 0
    for sc in scenarios:
        geo_file = geo_dir / f"{sc}.md"
        if not geo_file.exists():
            continue
        txt   = geo_file.read_text(encoding="utf-8")
        count = sum(1 for m in niveau_pat.finditer(txt) if int(m.group(1)) == 1)
        by_scenario[sc] = count
        total += count
    return {"total": total, "by_scenario": by_scenario}


def _count_review_items(pipeline_dir: Path) -> int:
    count = 0
    for fname in ("needs_review.yaml", "needs_review_enrich.yaml"):
        p = pipeline_dir / fname
        if p.exists():
            try:
                count += len(re.findall(r"^- ", p.read_text(encoding="utf-8"), re.MULTILINE))
            except Exception:
                pass
    review_md = pipeline_dir / "documentation" / "need_action" / "localisation_review.md"
    if review_md.exists():
        try:
            count += len(re.findall(r"review_manuelle", review_md.read_text(encoding="utf-8")))
        except Exception:
            pass
    return count
# ── Revue ─────────────────────────────────────────────────────────────────────

@app.route("/api/review", methods=["GET"])
def get_review():
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    items = []
    items += _parse_needs_review_enrich(pipeline_dir)
    items += _parse_needs_review_events(pipeline_dir)
    items += _parse_localisation_review(pipeline_dir)
    return jsonify({"items": items, "total": len(items)})


def _parse_needs_review_enrich(pipeline_dir: Path) -> list:
    """
    needs_review_enrich.yaml (dans instances_custom/) :
      needs_review:
        - slug: xxx
          scenario: yyy
          date: 2026-06-27
          errors: [...]
    """
    # Chercher dans instances_custom/ ou directement dans pipeline_dir
    candidates = [
        pipeline_dir / "instances_custom" / "needs_review_enrich.yaml",
        pipeline_dir / "needs_review_enrich.yaml",
    ]
    for p in candidates:
        if p.exists():
            return _read_needs_review_yaml(p, "enrich")
    return []


def _parse_needs_review_events(pipeline_dir: Path) -> list:
    """
    needs_review.yaml (dans evenements_custom/) :
      needs_review:
        - idea: {...}
          failed_scenarios: [...]
          status: needs_review
    """
    candidates = [
        pipeline_dir / "evenements_custom" / "needs_review.yaml",
        pipeline_dir / "needs_review.yaml",
    ]
    for p in candidates:
        if p.exists():
            return _read_needs_review_yaml(p, "events")
    return []


def _read_needs_review_yaml(path: Path, source: str) -> list:
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


def _parse_localisation_review(pipeline_dir: Path) -> list:
    """
    localisation_review.md :
      ## scenario (N)
      ### slug
      - type: ...
      - zone candidate: ...
    """
    review_md = pipeline_dir / "documentation" / "need_action" / "localisation_review.md"
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
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
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

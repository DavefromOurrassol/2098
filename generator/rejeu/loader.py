"""Remplace loader.py pendant le rejeu : les fiches viennent de l'export, pas du vault."""
import json, os
_CHEMIN = os.environ.get("EXPORT_ET_SI") or os.path.join(os.path.dirname(__file__), "..", "state", "export_et_si.json")
_D = json.load(open(_CHEMIN, encoding="utf-8"))
_P = {c["scenario"]: c for c in _D["couples"]}
VALID_VARS = []
VAULT_PATH = "."
def load_instances_for_scenario(sc): return _P[sc]["instances"]
def load_event_instances_for_scenario(sc): return _P[sc]["evenements"]
def load_scenario(sc): return _P[sc]["scenario_data"]

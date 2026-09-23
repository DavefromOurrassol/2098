"""
Test du Blueprint routes_carte.py contre le vrai vault, via le client de
test Flask (aucun serveur réel ne tourne). N'exerce que des routes GET
(lecture seule) et des POST en dry_run=True -- aucune écriture.

Usage, depuis gui/ (là où vivent app.py, config.json, zone_repository.py,
routes_carte.py) :
    python3 test_routes_carte.py [scenario] [slug_zone]

Important : ce script enregistre carte_bp sur une Flask app JETABLE, PAS sur
l'app réelle de app.py -- donc aucun risque de conflit avec les routes
existantes, et aucun serveur n'est lancé.
"""

import json
import sys

from flask import Flask

from routes_carte import carte_bp

app = Flask(__name__)
app.register_blueprint(carte_bp)
client = app.test_client()

scenario = sys.argv[1] if len(sys.argv) > 1 else "fortress_world"
slug = sys.argv[2] if len(sys.argv) > 2 else "zone_euro_sud"


def show(label, resp):
    print(f"\n=== {label} -> {resp.status_code} ===")
    data = resp.get_json()
    txt = json.dumps(data, indent=2, ensure_ascii=False)
    print(txt[:1500] + ("... (tronqué)" if len(txt) > 1500 else ""))


show("GET affectations", client.get(f"/api/carte/affectations?scenario={scenario}"))
show("GET zones_toutes", client.get(f"/api/carte/zones_toutes?scenario={scenario}"))
show("GET overlays", client.get(f"/api/carte/overlays?scenario={scenario}"))
show("GET rechercher_zone", client.get(f"/api/carte/rechercher_zone?scenario={scenario}&q={slug[:5]}"))
show("GET arbre_zone", client.get(f"/api/carte/arbre_zone?scenario={scenario}&slug={slug}"))

show("POST renommer_zone (dry_run)", client.post("/api/carte/renommer_zone", json={
    "scenario": scenario, "ancien_slug": slug, "dry_run": True
}))

show("POST reparent_zone (dry_run, promotion en N1)", client.post("/api/carte/reparent_zone", json={
    "scenario": scenario, "slug": slug, "nouveau_parent_slug": None, "dry_run": True
}))

show("POST renommer_zone sur un slug inexistant (doit être 404)", client.post("/api/carte/renommer_zone", json={
    "scenario": scenario, "ancien_slug": "ce_slug_n_existe_surement_pas_xyz", "dry_run": True
}))

print("\nTerminé -- aucune route d'écriture réelle n'a été appelée (tout en dry_run=True).")

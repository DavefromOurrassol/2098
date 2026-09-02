#!/usr/bin/env python3
"""
test_retry_metadonnees.py — test isolé du retry ciblé chapo/tags/image_prompt
(30 août 2026, backlog point 2).

Appelle directement _retry_missing_metadata() avec un vrai appel LLM,
sans passer par tout le pipeline de génération (pas besoin de
snapshot.py/config.yaml) -- teste le mécanisme lui-même en conditions
réelles, déterministe (pas besoin d'attendre qu'un cas naturel de bloc
absent survienne, ~2,4% de chance par génération).

Usage : python3 test_retry_metadonnees.py
(à lancer depuis le dossier generator/, comme les autres scripts)
"""
import sys

from api import _retry_missing_metadata, _bloc_metadonnees_absent

# Un system_prompt minimal suffit ici -- le but est de tester le
# mécanisme (appel LLM + parsing), pas la qualité journalistique fine.
prompt_data = {
    "system_prompt": (
        "Tu es un·e journaliste du journal Le Phare de Lomé, ligne "
        "éditoriale pro_pouvoir, ton posé et factuel."
    ),
}

# Extrait d'article fictif court -- suffisant pour que le LLM produise
# un chapo/tags/image_prompt cohérents avec le contenu.
article_text = """# Nouvelle canalisation d'eau potable inaugurée à Lomé-Nord

12 mars 2098 — Lomé, Togo

Marie Adjovi — Le Phare de Lomé

La municipalité de Lomé-Nord a inauguré ce matin une nouvelle
canalisation d'eau potable desservant douze mille foyers auparavant
dépendants de citernes mobiles. Le projet, financé conjointement par
le fonds régional de résilience climatique et la coopérative locale
des artisans, a nécessité dix-huit mois de travaux.

« C'est la fin d'une attente de vingt ans », a déclaré Kossi Mensah,
porte-parole du comité de quartier, lors de la cérémonie. Les
autorités locales prévoient une extension du réseau vers les quartiers
voisins d'ici deux ans."""

print("Appel de _retry_missing_metadata() -- vrai appel LLM en cours...")
meta = _retry_missing_metadata(prompt_data, article_text, "ecrit")

print()
print("=" * 60)
print("RÉSULTAT")
print("=" * 60)
print("chapo        :", repr(meta.get("chapo")))
print("tags         :", meta.get("tags"))
print("image_prompt :", repr(meta.get("image_prompt")))
print()
print("Bloc toujours absent après retry ?", _bloc_metadonnees_absent(meta))

if _bloc_metadonnees_absent(meta):
    print("\n✗ ÉCHEC : le retry n'a pas réussi à produire le bloc.")
    sys.exit(1)
else:
    print("\n✓ SUCCÈS : le retry a bien produit les 3 champs.")

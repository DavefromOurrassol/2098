#!/usr/bin/env python3
"""
patch_s24_journaux_fallback.py — S24, 31 oct 2026

Corrige generator/generate_journaux.py :
  1. plus de rédaction factice : un lot échoué n'écrit plus « Édition … » vide
     (qui bloquait --update et, en mode complet, écrasait un bon journal) ;
     les zones ratées restent absentes et sont listées → relancer --update ;
  2. parse JSON tolérant (_parse_liste_json) : texte autour, virgules finales,
     et récupération des entrées complètes d'une réponse tronquée ;
  3. zones manquantes d'un lot → nouvel essai zone par zone (une fois) ;
  4. réponse illisible gardée dans gui/logs/llm_json_echec_journaux_*.txt ;
  5. sauvegarde journaux.yaml.bak avant chaque écriture ;
  6. --fill-journalistes : compte réel des rédactions ajoutées.

Usage (depuis la racine du projet) :
  python3 generator/patch_s24_journaux_fallback.py           # aperçu
  python3 generator/patch_s24_journaux_fallback.py --apply   # applique (.bak créé)
  option : --fichier <chemin>  (défaut : generator/generate_journaux.py)
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

MARQUE = "Correctif du 31 oct 2026 (S24, journaux)"

ANCIEN_GENERATE = '''def generate_journals_for_zones(scenario, ligne, reseau, zones, batch_size=3):
    """
    Génère les profils de journaux pour toutes les zones via API (par lots).
    Retourne un dict {zone_slug: {nom, ton, langue_style}}.
    """
    results = {}
    batches = [zones[i:i+batch_size] for i in range(0, len(zones), batch_size)]

    _provider, _model = resolve_for_tier(TASK_TIER)
    print("  → {} zones | {} lot(s) de {} | {} ({}, tier={})".format(
        len(zones), len(batches), batch_size, _provider, _model, TASK_TIER
    ))

    for i, batch in enumerate(batches):
        print("    Lot {}/{}...".format(i + 1, len(batches)))
        prompt = build_prompt(scenario, ligne, reseau, batch)

        try:
            raw = call_llm(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                max_tokens=8000,  # augmenté le 6 juillet : le schéma "journalistes"
                                  # (6 par zone) produit un JSON bien plus long
                                  # qu'avant — 2000 tokens tronquait systématiquement
                                  # les lots de 5 zones (erreur JSON invalide).
                temperature=0.7,
                task_tier=TASK_TIER,
            ).strip()

            raw = re.sub(r"^```(?:json)?\\s*", "", raw)
            raw = re.sub(r"\\s*```$", "", raw).strip()
            data, _ = json.JSONDecoder().raw_decode(raw)

            for entry in data:
                idx = entry.get("index")
                if idx is not None and 0 <= idx < len(batch):
                    zone_slug = batch[idx]["slug"]
                    results[zone_slug] = {
                        "nom":          entry.get("nom", "Édition locale"),
                        "ton":          entry.get("ton", ""),
                        "langue_style": entry.get("langue_style", ""),
                        "journalistes": entry.get("journalistes", []),
                    }
            print("    OK — {} journaux générés".format(len(data)))

        except Exception as e:
            print("    [WARN] Lot {} échoué : {}".format(i + 1, e))
            # Fallback : entrées vides pour les zones du lot
            for z in batch:
                results[z["slug"]] = {
                    "nom":          "Édition {}".format(z.get("nom", z["slug"])),
                    "ton":          "",
                    "langue_style": "",
                    "journalistes": [],
                }

    return results
'''

NOUVEAU_GENERATE = '''# ''' + MARQUE + ''' : plus aucune rédaction factice.
# Avant : un lot au JSON cassé écrivait « Édition … » vide pour chaque zone du
# lot ; en --update ces zones passaient ensuite pour présentes (jamais
# régénérées, nettoyage par clean_fallback_journaux.py) et en mode complet
# elles écrasaient un journal existant. Désormais une zone ratée reste absente
# du résultat : elle est listée en fin de lot et reprise au prochain --update.

LOGS_DIR = os.path.join(VAULT_ROOT, "gui", "logs")


def _log_echec_json(raw, contexte):
    """Garde la réponse illisible pour diagnostic (même convention que
    instance_generation_common.extraire_json : gui/logs/llm_json_echec_*)."""
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        path = os.path.join(LOGS_DIR, "llm_json_echec_journaux_{}.txt".format(
            datetime.now().strftime("%Y%m%d_%H%M%S_%f")))
        with open(path, "w", encoding="utf-8") as f:
            f.write("# {}\\n\\n{}".format(contexte, raw))
        print("      réponse brute gardée : {}".format(path))
    except Exception as e:
        print("      (log impossible : {})".format(e))


def _parse_liste_json(raw):
    """
    Lit une liste JSON d'objets dans une réponse LLM, avec tolérance :
    balises ```json, texte avant/après, virgules finales, et réponse tronquée
    (les objets complets avant la coupure sont récupérés).
    Retourne (liste, complete) ; complete=False si la liste a été récupérée
    partiellement ou pas du tout.
    """
    texte = re.sub(r"^```(?:json)?\\s*", "", (raw or "").strip())
    texte = re.sub(r"\\s*```$", "", texte).strip()
    debut = texte.find("[")
    if debut < 0:
        return [], False
    texte = texte[debut:]
    dec = json.JSONDecoder()

    for candidat in (texte, re.sub(r",(\\s*[\\]}])", r"\\1", texte)):
        try:
            data, _ = dec.raw_decode(candidat)
            if isinstance(data, list):
                return [e for e in data if isinstance(e, dict)], True
        except ValueError:
            pass

    # Récupération objet par objet (réponse tronquée)
    objets, pos = [], 1
    while pos < len(texte):
        while pos < len(texte) and texte[pos] in " \\t\\r\\n,":
            pos += 1
        if pos >= len(texte) or texte[pos] != "{":
            break
        try:
            obj, pos = dec.raw_decode(texte, pos)
        except ValueError:
            break
        if isinstance(obj, dict):
            objets.append(obj)
    return objets, False


def _entree_valide(entry, zone):
    """Une entrée n'est gardée que si elle a un nom de journal, autre que le
    motif factice de l'ancien fallback (« Édition <nom de la zone> »)."""
    nom = (entry.get("nom") or "").strip() if isinstance(entry, dict) else ""
    factice = "Édition {}".format(zone.get("nom", zone["slug"]))
    return bool(nom) and nom.lower() != factice.lower()


def _appel_lot(scenario, ligne, reseau, batch, etiquette):
    """Un appel LLM pour un lot ; retourne {zone_slug: entrée} (zones réussies seulement)."""
    prompt = build_prompt(scenario, ligne, reseau, batch)
    try:
        raw = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=8000,  # augmenté le 6 juillet : le schéma "journalistes"
                              # (6 par zone) produit un JSON bien plus long
                              # qu'avant — 2000 tokens tronquait systématiquement
                              # les lots de 5 zones (erreur JSON invalide).
            temperature=0.7,
            task_tier=TASK_TIER,
        )
    except Exception as e:
        print("    [WARN] {} : appel échoué ({})".format(etiquette, e))
        return {}

    data, complete = _parse_liste_json(raw)
    ok = {}
    for entry in data:
        idx = entry.get("index")
        if isinstance(idx, int) and 0 <= idx < len(batch) and _entree_valide(entry, batch[idx]):
            ok[batch[idx]["slug"]] = {
                "nom":          entry["nom"].strip(),
                "ton":          entry.get("ton", ""),
                "langue_style": entry.get("langue_style", ""),
                "journalistes": entry.get("journalistes", []) or [],
            }
    if not complete:
        print("    [WARN] {} : JSON {} ({} zone(s) récupérée(s) sur {})".format(
            etiquette, "tronqué" if data else "illisible", len(ok), len(batch)))
        _log_echec_json(raw, "{} / {} / {} — {}".format(scenario, ligne, etiquette,
                                                       ", ".join(z["slug"] for z in batch)))
    return ok


def generate_journals_for_zones(scenario, ligne, reseau, zones, batch_size=3):
    """
    Génère les profils de journaux pour toutes les zones via API (par lots).
    Retourne un dict {zone_slug: {nom, ton, langue_style, journalistes}}
    contenant UNIQUEMENT les zones réussies. Une zone absente d'un lot est
    retentée seule une fois ; si elle échoue encore, elle reste absente
    (reprise par un prochain --update), jamais remplacée par une entrée factice.
    """
    results = {}
    batches = [zones[i:i+batch_size] for i in range(0, len(zones), batch_size)]

    _provider, _model = resolve_for_tier(TASK_TIER)
    print("  → {} zones | {} lot(s) de {} | {} ({}, tier={})".format(
        len(zones), len(batches), batch_size, _provider, _model, TASK_TIER
    ))

    echecs = []
    for i, batch in enumerate(batches):
        etiquette = "Lot {}/{}".format(i + 1, len(batches))
        print("    {}...".format(etiquette))
        ok = _appel_lot(scenario, ligne, reseau, batch, etiquette)
        results.update(ok)

        manquantes = [z for z in batch if z["slug"] not in ok]
        if manquantes and len(batch) > 1:
            print("    {} zone(s) manquante(s) — nouvel essai zone par zone.".format(len(manquantes)))
            for z in manquantes:
                ok1 = _appel_lot(scenario, ligne, reseau, [z], "{} / {}".format(etiquette, z["slug"]))
                results.update(ok1)
        echecs += [z["slug"] for z in batch if z["slug"] not in results]
        print("    OK — {} journal(aux) sur {}".format(
            sum(1 for z in batch if z["slug"] in results), len(batch)))

    if echecs:
        print("  [WARN] {} zone(s) sans journal (rien écrit pour elles) : {}".format(
            len(echecs), ", ".join(echecs)))
        print("         → relancer avec --update pour les reprendre.")

    return results
'''

REMPLACEMENTS = [
    ("generate_journals_for_zones sans fallback factice", ANCIEN_GENERATE, NOUVEAU_GENERATE),
    (
        "import datetime",
        "import re\nimport sys\n\nimport yaml\n",
        "import re\nimport shutil\nimport sys\nfrom datetime import datetime\n\nimport yaml\n",
    ),
    (
        "sauvegarde .bak avant écriture",
        '''    with open(JOURNAUX_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
''',
        '''    if os.path.exists(JOURNAUX_PATH):
        shutil.copy2(JOURNAUX_PATH, JOURNAUX_PATH + ".bak")
    with open(JOURNAUX_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
''',
    ),
    (
        "--fill-journalistes : compte réel",
        '''        for slug, data in nouveaux.items():
            if slug in existing_zones:
                existing_zones[slug]["journalistes"] = data.get("journalistes", [])

        journaux[scenario][ligne]["zones"] = existing_zones
        print("  {} rédaction(s) ajoutée(s) pour {}/{}.".format(
            len(a_completer_slugs), scenario, ligne
        ))
''',
        '''        ajoutees = 0
        for slug, data in nouveaux.items():
            if slug in existing_zones and data.get("journalistes"):
                existing_zones[slug]["journalistes"] = data["journalistes"]
                ajoutees += 1

        journaux[scenario][ligne]["zones"] = existing_zones
        print("  {} rédaction(s) ajoutée(s) sur {} pour {}/{}.".format(
            ajoutees, len(a_completer_slugs), scenario, ligne
        ))
''',
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fichier", default=os.path.join("generator", "generate_journaux.py"))
    args = ap.parse_args()

    if not os.path.exists(args.fichier):
        sys.exit("Fichier introuvable : {}".format(args.fichier))
    with open(args.fichier, encoding="utf-8") as f:
        src = f.read()

    if MARQUE in src:
        print("Déjà appliqué : rien à faire.")
        return

    for nom, old, new in REMPLACEMENTS:
        n = src.count(old)
        if n != 1:
            sys.exit("ÉCHEC « {} » : {} occurrence(s) au lieu de 1. "
                     "Rien n'a été modifié.".format(nom, n))
        src = src.replace(old, new)
        print("OK  {}".format(nom))

    if not args.apply:
        print("\nAperçu seulement. Relancer avec --apply.")
        return

    bak = "{}.bak_{}".format(args.fichier, datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(args.fichier, bak)
    with open(args.fichier, "w", encoding="utf-8") as f:
        f.write(src)
    print("\nAppliqué. Sauvegarde : {}".format(bak))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
patch_u4r_nettoyage_u4k.py — Ourrassol 2098 (22 novembre 2026)
==============================================================

Nettoyage après U4k (fermeture des « Outils directs ») : depuis U4k, plus aucun
formulaire du GUI n'écrit dans une queue.yaml (événements, signaux, entités) ; tout
passe par « et si ? ». Ce patch retire le code devenu mort. 3 fichiers, tout ou rien.

gui/static/app.js
  1. Formulaire guidé : l'assistant « ✨ Compléter les autres champs » (texte libre)
     n'est plus branché.
  2. Bouton « Ajouter à la queue » : si un formulaire de file réapparaissait, il
     refuse avec un message (au lieu d'écrire par /api/yaml/append).
  3. Fonctions retirées : _buildAssistantTexteLibre, _carteProposition,
     _remplirYamlForm, _appendYamlQueue (≈ 270 lignes).
  4. Onglet 🔭 Veille : commentaire d'en-tête périmé (« Envoyer en queue ») réécrit ;
     propriété inutilisée VeilleState.propositions retirée ; commentaire de
     _veilleTexteProposition corrigé (hypothese_depuis_texte.py, pas idees_vers_queue.py).

gui/app.py
  5. Routes /api/yaml/append et /api/idees/proposer retirées (et la constante
     TIMEOUT_IDEES_TEXTE_LIBRE).

generator/et_si_main.py
  6. En-tête : les nouvelles entités deviennent des hypothèses « et si ? » (U3be).
  7. Message « déjà dans entites_custom/queue.yaml » : renvoie vers « Traiter la file
     des entités (fantômes) » (groupe Entretien, U4k) au lieu de « Créer des entités ».

Non touchés (à décider plus tard) : generator/idees_vers_queue.py, désormais appelé par
rien dans le GUI (le fichier reste) ; commentaires d'en-tête de
gui/routes_veille_signaux.py et generator/import_signaux_faibles.py qui le citent.

Après --apply : relancer Flask (app.py change), puis Cmd-Maj-R.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4r_nettoyage_u4k.py           # dry-run
    python3 generator/patch_u4r_nettoyage_u4k.py --apply   # écrit (.bak_u4r)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

TAG = "u4r"

# ("remplacer", nom, ancien, neuf) ou ("couper", nom, debut, fin, neuf) :
# « couper » remplace tout le texte de `debut` (inclus) jusqu'à `fin` (exclu) par `neuf`.
OPERATIONS = {
    Path("gui/static/app.js"): [
        ("couper", "1. formulaire guidé : assistant « texte libre » débranché",
         "  // ── Assistant \"Depuis un texte libre\" (27 septembre 2026) ──\n",
         "  wrapper.appendChild(formZone);\n",
         ""),
        ("remplacer", "2. « Ajouter à la queue » : refus au lieu de /api/yaml/append",
         "        await _appendYamlQueue(wrapper, yf.path, statusMsg);\n",
         "        // U4r : l'écriture directe dans une file (queue.yaml) est fermée depuis U4k.\n"
         "        showYamlStatus(statusMsg, 'error', 'Ajout direct à une file fermé : passer par l\\'onglet « Et si ? ».');\n"),
        ("couper", "3. fonctions retirées (_buildAssistantTexteLibre … _appendYamlQueue)",
         "/** Appende une nouvelle entrée dans une queue YAML via /api/yaml/append. */\n",
         "// ══════════════════════════════════════════════════\n// DOUBLE SELECT ZONE 2098 / PAYS 2026\n",
         "// U4r : assistant « Depuis un texte libre » (_buildAssistantTexteLibre, _carteProposition,\n"
         "// _remplirYamlForm) et ajout à une file (_appendYamlQueue) retirés : plus aucun\n"
         "// formulaire n'écrit dans une queue.yaml depuis U4k ; tout passe par « et si ? ».\n\n"),
        ("couper", "4a. veille : commentaire d'en-tête « Envoyer en queue »",
         "//   - Envoyer en queue : 1) /api/idees/proposer (idees_vers_queue.py, UN\n",
         "// Tout texte venant des IA passe par _veilleEsc (jamais d'innerHTML brut) ;\n",
         "//   - ✨ Envoyer vers « et si ? » (U3a) : /api/et_si/proposer (hypothese_depuis_texte.py,\n"
         "//     UN appel IA ; date d'observation imposée, U4q), puis Vérifier / Ajouter à\n"
         "//     hypotheses.yaml ; statut en_hypothese. La suite se fait dans l'onglet « Et si ? ».\n"),
        ("remplacer", "3b. commentaires : _appendYamlQueue() noté comme retiré",
         "  // \":not([data-optional])\" utilisé par _appendYamlQueue() pour repérer\n",
         "  // \":not([data-optional])\" utilisé par _appendYamlQueue (retiré en U4r) pour repérer\n"),
        ("remplacer", "3c. commentaire de _markOptional",
         " * marqué optionnel dans scripts_config.json. Sans ça, `_appendYamlQueue()`\n",
         " * marqué optionnel dans scripts_config.json. Sans ça, `_appendYamlQueue` (retiré en U4r)\n"),
        ("remplacer", "4b. veille : propriété VeilleState.propositions retirée",
         "  propositions: {},   // id candidat -> résultat de /api/idees/proposer\n",
         ""),
        ("remplacer", "4c. veille : commentaire de _veilleTexteProposition",
         "  // Texte envoyé à idees_vers_queue.py : le candidat tel quel, plus la\n",
         "  // Texte envoyé à hypothese_depuis_texte.py (U3a) : le candidat tel quel, plus la\n"),
    ],
    Path("gui/app.py"): [
        ("couper", "5a. route /api/yaml/append retirée",
         '@app.route("/api/yaml/append", methods=["POST"])\n',
         '@app.route("/api/zones/pays-liste", methods=["GET"])\n',
         "# U4r : route /api/yaml/append retirée (plus aucun formulaire n'écrit dans une\n"
         "# queue.yaml depuis U4k ; tout passe par « et si ? »).\n\n\n"),
        ("couper", "5b. route /api/idees/proposer retirée",
         "TIMEOUT_IDEES_TEXTE_LIBRE = 180",
         "# ---------------------------------------------------------------------------\n"
         "# Chantier \"Suite narrative des événements\", point B",
         "# U4r : route /api/idees/proposer (idees_vers_queue.py) retirée : une idée en texte\n"
         "# libre passe par « et si ? » (/api/et_si/proposer).\n\n\n"),
    ],
    Path("generator/et_si_main.py"): [
        ("remplacer", "6. en-tête : entités -> hypothèses « et si ? » (U3be)",
         "  1. Nouvelles entités proposées par la lecture IA : choisir une catégorie, puis\n"
         "     les ajouter à entites_custom/queue.yaml (même format que la création\n"
         "     d'entités ; garde-fou anti-doublon). La création elle-même reste\n"
         "     « Créer des entités » (create_entities_and_instances.py --mode custom).\n",
         "  1. Nouvelles entités proposées par la lecture IA : choisir une catégorie ; elles\n"
         "     deviennent des hypothèses « et si ? » de type entité dans et_si/hypotheses.yaml\n"
         "     (U3be ; garde-fou anti-doublon). La suite se fait dans l'onglet « Et si ? »\n"
         "     (Vérifier, Adopter, Injecter).\n"),
        ("remplacer", "7. message « déjà dans la file » : bon bouton (U4k)",
         "        return \"dans la file\", \"déjà dans entites_custom/queue.yaml (ancien chemin) : lancer « Créer des entités »\"\n",
         "        return \"dans la file\", (\"déjà dans entites_custom/queue.yaml (ancien chemin) : lancer \"   # U4r\n"
         "                                \"« Traiter la file des entités (fantômes) » (groupe Entretien)\")\n"),
    ],
}


def appliquer_op(texte, op):
    """Retourne (texte modifié, message d'erreur ou None)."""
    if op[0] == "remplacer":
        _, nom, ancien, neuf = op
        n = texte.count(ancien)
        if n != 1:
            return texte, f"ancre trouvée {n} fois (attendu 1)"
        return texte.replace(ancien, neuf), None
    _, nom, debut, fin, neuf = op
    nd, nf = texte.count(debut), texte.count(fin)
    if nd != 1 or nf != 1:
        return texte, f"ancres début/fin trouvées {nd}/{nf} fois (attendu 1/1)"
    i, j = texte.index(debut), texte.index(fin)
    if j <= i:
        return texte, "ancre de fin avant l'ancre de début"
    return texte[:i] + neuf + texte[j:], None


def main():
    ap = argparse.ArgumentParser(description="Patch U4r : nettoyage après U4k.")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon dry-run)")
    args = ap.parse_args()
    manquants = [str(f) for f in OPERATIONS if not f.is_file()]
    if manquants:
        sys.exit("✗ introuvable(s) : " + ", ".join(manquants) + " (lancer depuis la racine du vault)")
    if "# U4r :" in Path("gui/app.py").read_text(encoding="utf-8"):
        sys.exit("✗ U4r déjà appliqué : rien à faire.")
    a_ecrire, ok = {}, True
    for chemin, ops in OPERATIONS.items():
        texte = chemin.read_text(encoding="utf-8")
        avant = len(texte.splitlines())
        for op in ops:
            texte, err = appliquer_op(texte, op)
            if err:
                print(f"✗ {chemin} : {op[1]} — {err}")
                ok = False
            else:
                print(f"✓ {chemin} : {op[1]}")
        if chemin.suffix == ".py":
            try:
                compile(texte, str(chemin), "exec")
            except SyntaxError as e:
                print(f"✗ {chemin} ne compile plus : {e}")
                ok = False
        print(f"    {chemin} : {avant} → {len(texte.splitlines())} lignes")
        a_ecrire[chemin] = texte
    js = a_ecrire[Path("gui/static/app.js")]
    restes = [m for m in ("_appendYamlQueue(", "_buildAssistantTexteLibre(", "_remplirYamlForm(",
                          "_carteProposition(", "/api/idees/proposer", "/api/yaml/append") if m in js]
    if restes:
        print("✗ app.js : références restantes : " + ", ".join(restes))
        ok = False
    if ok:
        try:   # contrôle de syntaxe JS si node est disponible
            def node_ok(texte):
                tmp = Path("gui/static/.app_u4r_check.js")
                tmp.write_text(texte, encoding="utf-8")
                r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
                tmp.unlink()
                return r.returncode == 0, r.stderr[-800:]
            orig_ok, _ = node_ok(Path("gui/static/app.js").read_text(encoding="utf-8"))
            if not orig_ok:   # node trop ancien (||= …) : l'original échoue aussi
                print("· node trop ancien pour app.js (l'original échoue aussi) : syntaxe JS non vérifiée")
            else:
                neuf_ok, err = node_ok(js)
                if not neuf_ok:
                    print("✗ app.js : node --check en échec :\n" + err)
                    ok = False
                else:
                    print("✓ app.js : node --check OK")
        except FileNotFoundError:
            print("· node absent : syntaxe JS non vérifiée")
    if not ok:
        sys.exit("✗ Patch non appliqué : aucun fichier n'a été modifié.")
    print("✓ Toutes les ancres trouvées ; les fichiers Python patchés compilent.")
    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    for chemin, texte in a_ecrire.items():
        shutil.copy(chemin, chemin.with_name(chemin.name + f".bak_{TAG}"))
        chemin.write_text(texte, encoding="utf-8")
        print(f"→ {chemin} écrit (sauvegarde {chemin.name}.bak_{TAG})")
    print("\nSuite : relancer Flask (app.py a changé), puis Cmd-Maj-R dans le navigateur.")


if __name__ == "__main__":
    main()

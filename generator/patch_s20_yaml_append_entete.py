"""
patch_s20_yaml_append_entete.py — Ourrassol 2098 (S20, 30 octobre 2026)

Problème : /api/yaml/append (gui/app.py) relit queue.yaml avec
yaml.safe_load puis le réécrit avec yaml.dump, ce qui efface tous les
commentaires, donc l'en-tête modèle (« # evenements_custom/queue.yaml …
CHAMPS … ») jusqu'au prochain run de l'injecteur.

Correctif : avant la réécriture, on garde le bloc de commentaires et de
lignes vides du DÉBUT du fichier (tout ce qui précède la première ligne
de données, ici « queue: ») et on le remet en tête. Les entrées restent
écrites par yaml.dump comme avant.

Usage (depuis la racine du vault) :
  python3 generator/patch_s20_yaml_append_entete.py            # aperçu
  python3 generator/patch_s20_yaml_append_entete.py --apply    # écrit, avec .bak
Puis redémarrer Flask entièrement.
"""

import shutil
import sys
from pathlib import Path

CIBLE = Path("gui/app.py")
MARQUE = "PATCH_S20_ENTETE"

R1_AVANT = (
    "        # Backup\n"
    "        if target.exists():\n"
    "            bak = target.with_suffix(target.suffix + \".bak\")\n"
    "            bak.write_text(target.read_text(encoding=\"utf-8\"), encoding=\"utf-8\")\n"
    "            existing = _yaml.safe_load(target.read_text(encoding=\"utf-8\")) or {}\n"
    "        else:\n"
    "            existing = {}\n"
)
R1_APRES = (
    "        # Backup\n"
    "        entete = \"\"  # PATCH_S20_ENTETE : commentaires de tête conservés\n"
    "        if target.exists():\n"
    "            bak = target.with_suffix(target.suffix + \".bak\")\n"
    "            texte_avant = target.read_text(encoding=\"utf-8\")\n"
    "            bak.write_text(texte_avant, encoding=\"utf-8\")\n"
    "            existing = _yaml.safe_load(texte_avant) or {}\n"
    "            lignes_tete = []\n"
    "            for _l in texte_avant.splitlines():\n"
    "                if _l.strip() == \"\" or _l.lstrip().startswith(\"#\"):\n"
    "                    lignes_tete.append(_l)\n"
    "                else:\n"
    "                    break\n"
    "            if any(_l.lstrip().startswith(\"#\") for _l in lignes_tete):\n"
    "                entete = \"\\n\".join(lignes_tete).rstrip() + \"\\n\\n\"\n"
    "        else:\n"
    "            existing = {}\n"
)

R2_AVANT = (
    "        target.write_text(\n"
    "            _yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),\n"
    "            encoding=\"utf-8\"\n"
    "        )\n"
    "        return jsonify({\"ok\": True, \"path\": str(target), \"queue_length\": len(queue)})\n"
)
R2_APRES = (
    "        target.write_text(\n"
    "            entete + _yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),\n"
    "            encoding=\"utf-8\"\n"
    "        )\n"
    "        return jsonify({\"ok\": True, \"path\": str(target), \"queue_length\": len(queue)})\n"
)


def main():
    appliquer = "--apply" in sys.argv
    if not CIBLE.exists():
        sys.exit(f"Introuvable : {CIBLE} (lancer depuis la racine du vault)")
    texte = CIBLE.read_text(encoding="utf-8")
    if MARQUE in texte:
        print("  · déjà appliqué, rien à faire.")
        return
    for nom, avant in (("lecture + en-tête", R1_AVANT), ("écriture", R2_AVANT)):
        n = texte.count(avant)
        if n != 1:
            sys.exit(f"  ⚠ {nom} : passage trouvé {n} fois (attendu 1), fichier non modifié.")
    nouveau = texte.replace(R1_AVANT, R1_APRES).replace(R2_AVANT, R2_APRES)
    print("  ✓ lecture : en-tête de commentaires mis de côté")
    print("  ✓ écriture : en-tête remis avant les entrées")
    if not appliquer:
        print("Aperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CIBLE, CIBLE.with_suffix(".py.bak"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"Écrit : {CIBLE} (sauvegarde {CIBLE.name}.bak). Redémarrer Flask entièrement.")


if __name__ == "__main__":
    main()

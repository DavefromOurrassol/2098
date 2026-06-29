#!/bin/zsh
# ── Ourrassol 2098 — Lancement GUI ──────────────────
# Source .zshrc pour charger MISTRAL_API_KEY et autres variables
source ~/.zshrc

echo "=================================================="
echo "  OURRASSOL 2098 — GUI"
echo "  http://localhost:5000"
echo "=================================================="

# Aller dans le dossier gui et lancer Flask
cd "/Users/davidlopez2005/Documents/Obsidian Vault/Ourrassol2098/gui"
python3 app.py

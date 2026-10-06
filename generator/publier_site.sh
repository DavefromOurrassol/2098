#!/bin/bash
# publier_site.sh — Ourrassol 2098 : construit le site des revues et le met en ligne.
#
#   1. export_revues.py --build   → site/ dans le vault
#   2. copie de site/ vers le dépôt ourrassol-site (à côté du vault)
#   3. commit + push → Cloudflare Pages republie tout seul
#
# Usage (depuis n'importe où) :
#   bash generator/publier_site.sh --dry-run   # construit et montre ce qui changerait, n'envoie rien
#   bash generator/publier_site.sh             # construit et publie
#
# Le dépôt de destination peut être changé : SITE_REPO=/autre/chemin bash generator/publier_site.sh
set -euo pipefail

VAULT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_REPO="${SITE_REPO:-$(cd "$VAULT/.." && pwd)/ourrassol-site}"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

echo "Vault        : $VAULT"
echo "Dépôt du site: $SITE_REPO"

if [ ! -d "$SITE_REPO/.git" ]; then
  echo "❌ $SITE_REPO n'est pas un dépôt git (clone ourrassol-site à côté du vault)."
  exit 1
fi

# 1. Construction
python3 "$VAULT/generator/export_revues.py" --build --out "$VAULT/site"

# 2. Copie miroir de site/ vers le dépôt (on garde .git et le README du dépôt).
#    Faite en Python pour ne dépendre d'aucun outil externe.
python3 - "$VAULT/site" "$SITE_REPO" "$DRY" <<'PY'
import filecmp, os, shutil, sys
src, dst, dry = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
GARDER = {".git", "README.md", ".export_revues"}
def fichiers(racine):
    out = set()
    for d, dirs, fs in os.walk(racine):
        rel = os.path.relpath(d, racine)
        if rel.split(os.sep)[0] in GARDER:
            dirs[:] = []
            continue
        dirs[:] = [x for x in dirs if not (rel == "." and x in GARDER)]
        for f in fs:
            r = os.path.normpath(os.path.join(rel, f))
            if r not in GARDER:
                out.add(r)
    return out
a, b = fichiers(src), fichiers(dst)
nouveaux = sorted(a - b)
modifies = sorted(f for f in a & b if not filecmp.cmp(os.path.join(src, f), os.path.join(dst, f), shallow=False))
supprimes = sorted(b - a)
print(f"\nCopie vers le dépôt : {len(nouveaux)} nouveau(x), {len(modifies)} modifié(s), {len(supprimes)} supprimé(s)")
if dry:
    for t, l in (("+", nouveaux), ("~", modifies), ("-", supprimes)):
        for f in l[:20]:
            print(f"  {t} {f}")
        if len(l) > 20:
            print(f"  {t} … et {len(l) - 20} autre(s)")
    sys.exit(0)
for f in nouveaux + modifies:
    os.makedirs(os.path.dirname(os.path.join(dst, f)) or dst, exist_ok=True)
    shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
for f in supprimes:
    os.remove(os.path.join(dst, f))
for d, dirs, fs in sorted(os.walk(dst, topdown=False)):   # dossiers devenus vides
    if ".git" not in d.split(os.sep) and d != dst and not os.listdir(d):
        os.rmdir(d)
PY
if [ $DRY -eq 1 ]; then
  echo "(simulation : rien n'a été copié ni envoyé)"
  exit 0
fi

# 3. Commit + push, seulement s'il y a du changement
cd "$SITE_REPO"
git add -A
if git diff --cached --quiet; then
  echo "✓ Aucun changement depuis la dernière publication : rien à envoyer."
  exit 0
fi
N=$(git diff --cached --name-only | wc -l | tr -d ' ')
git commit -q -m "Publication du $(date '+%Y-%m-%d %H:%M') — $N fichier(s)"
git push -q
echo "✓ Publié : $N fichier(s) envoyé(s). Cloudflare Pages republie le site d'ici une à deux minutes."

#!/usr/bin/env python3
"""
rename_journalistes_retroactif.py
----------------------------------
Renomme rétroactivement, dans les articles déjà publiés, les 6
journalistes opposition renommés le 7 septembre 2026 (noms trop proches
du pendant pro_pouvoir de leur zone). Corrige journaliste_slug
(frontmatter) et la signature dans le corps de l'article.

Ne suppose jamais la formule de slugification de l'ANCIEN nom : lit le
journaliste_slug existant tel quel dans chaque fichier concerné (repéré
par présence du nom complet dans le texte), et ne recalcule qu'un
NOUVEAU slug propre à partir du nouveau nom.

Usage :
    python3 rename_journalistes_retroactif.py --articles-dir articles --dry-run
    python3 rename_journalistes_retroactif.py --articles-dir articles --apply

Sauvegarde .bak automatique de chaque fichier modifié en mode --apply,
même convention que le reste du pipeline (editer_sujets.py, etc.).
"""
import argparse
import re
import unicodedata
from pathlib import Path

RENOMMAGES = [
    ("Samira Al-Khatib", "Yasmine Chahine"),
    ("Samir El-Masri", "Tariq Mansour"),
    ("Mei-Ling Chen", "Xiaoyu Tan"),
    ("Maëlle Le Goff", "Solène Guillou"),
    ("Farhana Akter", "Nasima Begum"),
    ("Marisol Quispe Mamani", "Nayra Quispe Mamani"),
]


def slugify(nom):
    """Slug du NOUVEAU nom uniquement -- minuscule, accents retirés,
    tout séparateur non alphanumérique -> underscore."""
    s = unicodedata.normalize("NFD", nom)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                         help="Écrit réellement les fichiers (sinon dry-run par défaut)")
    parser.add_argument("--articles-dir", default="articles",
                         help="Dossier racine contenant les sous-dossiers par scénario")
    args = parser.parse_args()

    root = Path(args.articles_dir)
    if not root.exists():
        print(f"Dossier introuvable : {root}")
        return

    total = 0

    for ancien_nom, nouveau_nom in RENOMMAGES:
        nouveau_slug = slugify(nouveau_nom)
        fichiers = [
            f for f in root.rglob("*.md")
            if ancien_nom in f.read_text(encoding="utf-8", errors="ignore")
        ]

        print(f"\n=== {ancien_nom} -> {nouveau_nom} "
              f"({len(fichiers)} article(s) trouvé(s)) ===")

        for f in fichiers:
            contenu = f.read_text(encoding="utf-8")

            m = re.search(r"^journaliste_slug:\s*(\S*)\s*$", contenu, re.MULTILINE)
            ancien_slug = m.group(1) if m else None

            nouveau_contenu = contenu.replace(ancien_nom, nouveau_nom)
            if ancien_slug:
                nouveau_contenu = re.sub(
                    r"^journaliste_slug:\s*\S*\s*$",
                    f"journaliste_slug: {nouveau_slug}",
                    nouveau_contenu, count=1, flags=re.MULTILINE,
                )
            else:
                print(f"  ⚠ {f} : nom trouvé mais AUCUN journaliste_slug "
                      f"dans le frontmatter -- signature seule remplacée, "
                      f"vérifier ce cas à la main")

            print(f"  {f}  (slug {ancien_slug!r} -> {nouveau_slug!r})")
            if args.apply:
                f.with_suffix(f.suffix + ".bak").write_text(contenu, encoding="utf-8")
                f.write_text(nouveau_contenu, encoding="utf-8")
                total += 1

    if args.apply:
        print(f"\nAppliqué : {total} fichier(s) modifié(s) (.bak créé pour chacun).")
    else:
        print(f"\nDry-run terminé -- aucune écriture. Relance avec --apply pour appliquer.")


if __name__ == "__main__":
    main()

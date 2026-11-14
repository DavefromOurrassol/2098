#!/usr/bin/env python3
"""
patch_u3ak_entite_doublons_etape1.py — Ourrassol 2098 (14 novembre 2026)

Patch 2/4 du type « entité » dans « Et si ? » : contrôle des doublons à
l'étape ① (sans IA), dans generator/hypothese_depuis_texte.py. Prérequis : U3aj.

Pour une hypothèse `type: entite`, à la proposition (--proposer) et à la
vérification / l'ajout (--verifier, --ajouter), le nom est comparé au registre
entites/_entities_list.json et aux fichiers entites/*.md :

  ERREUR (bloque l'ajout)
    - le slug du nom existe déjà ;
    - le nom est identique à une entité existante « à l'article près »
      (« les Archives de la Marée » / « archives_de_la_maree »).
  AVERTISSEMENT (n'empêche rien, nomme les entités proches avec leur catégorie)
    - slug très ressemblant (similarité >= 0,85) ;
    - mots du nom contenus dans ceux d'une entité existante (ou l'inverse) :
      au moins 2 mots, ou 1 mot de 6 lettres et plus rare (< 4 entités).

Le contrôle de l'IA (« doublon_detecte ») et le refus du slug exact à
l'injection (U3ah) restent en place derrière.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3ak_entite_doublons_etape1.py            # aperçu
    python3 generator/patch_u3ak_entite_doublons_etape1.py --apply    # écrit

Sauvegarde .bak_u3ak ; refuse un second passage ; py_compile (restauration
automatique en cas d'échec).
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

MARQUEUR = "U3ak"
HYP = Path("generator/hypothese_depuis_texte.py")

HELPERS = '''# ---------------------------------------------------------------------------
# U3ak (14 nov 2026) : doublons d'entités à l'étape ① -- sans IA
# ---------------------------------------------------------------------------

ARTICLES_ENTITE = {"le", "la", "les", "l", "un", "une", "des", "du", "de", "d"}
SEUIL_SIMILAIRE = 0.85


def _slug_entite(nom):
    """Même slug que create_entities_and_instances.py (slugs.slugify)."""
    try:
        from slugs import slugify as _s
        return _s(str(nom or ""))
    except Exception:  # noqa: BLE001 -- repli : slug local
        return slugifier(nom)


def _mots(slug):
    return [m for m in slug.split("_") if m]


def _base_slug(slug):
    """Slug sans ses articles de tête : les_archives_de_la_maree -> archives_de_la_maree."""
    m = _mots(slug)
    while len(m) > 1 and m[0] in ARTICLES_ENTITE:
        m.pop(0)
    return "_".join(m)


def entites_existantes():
    """{slug: categorie} d'après le registre ET les fichiers entites/*.md."""
    import json as _json
    dossier = se.VAULT_ROOT / "entites"
    res = {}
    try:
        for e in _json.loads((dossier / "_entities_list.json").read_text(encoding="utf-8")):
            if isinstance(e, dict) and e.get("slug"):
                res[str(e["slug"])] = str(e.get("categorie") or e.get("category") or "?")
    except (OSError, ValueError):
        pass
    if dossier.is_dir():
        for f in dossier.glob("*.md"):
            if not f.name.startswith("_"):
                res.setdefault(f.stem, "?")
    return res


def controle_doublon_entite(nom, existantes=None):
    """(erreurs, avertissements) pour le nom d'une entité à créer."""
    import difflib
    erreurs, avert = [], []
    slug = _slug_entite(nom)
    if not slug:
        return ["nom inutilisable (slug vide)"], []
    existantes = entites_existantes() if existantes is None else existantes
    base = _base_slug(slug)
    if slug in existantes:
        erreurs.append(f"l'entité {slug!r} existe déjà ({existantes[slug]}) : "
                       "pour lui ajouter des instances, utiliser generate_instances.py")
    else:
        memes = [s for s in existantes if _base_slug(s) == base]
        for s in memes[:3]:
            erreurs.append(f"même nom que l'entité {s!r} ({existantes[s]}), à l'article près")
    mots = {m for m in _mots(base) if m not in ARTICLES_ENTITE}
    freq = {}
    for s in existantes:
        for m in set(_mots(s)):
            freq[m] = freq.get(m, 0) + 1
    proches = []
    for s, cat in existantes.items():
        if s == slug or _base_slug(s) == base:
            continue
        score = difflib.SequenceMatcher(None, base, _base_slug(s)).ratio()
        autres = {m for m in _mots(_base_slug(s)) if m not in ARTICLES_ENTITE}
        petit, grand = (mots, autres) if len(mots) <= len(autres) else (autres, mots)
        inclus = bool(petit) and petit <= grand
        if inclus and len(petit) < 2:
            m = next(iter(petit))
            inclus = len(m) >= 6 and freq.get(m, 0) < 4
        if score >= SEUIL_SIMILAIRE or inclus:
            proches.append((max(score, 0.9 if inclus else 0), s, cat))
    for _, s, cat in sorted(proches, reverse=True)[:5]:
        avert.append(f"entité proche : {s!r} ({cat}) -- vérifier qu'il ne s'agit pas de la même")
    if len(proches) > 5:
        avert.append(f"... et {len(proches) - 5} autre(s) entité(s) proche(s)")
    return erreurs, avert


'''

ANCRE_HELPERS = 'def construire_prompt_entite(texte):\n'

ANCRE_VERIF = '    _, err2, avert = se.verifier_hypothese(dict(h), valid_vars(), dyn)\n'
NOUV_VERIF = ('    if str(h.get("type") or "").strip().lower() == "entite":   # U3ak\n'
              '        e_dup, a_dup = controle_doublon_entite(h.get("nom"))\n'
              '        erreurs += e_dup\n'
              '        avert_dup = a_dup\n'
              '    else:\n'
              '        avert_dup = []\n') + ANCRE_VERIF + '    avert = avert_dup + list(avert)\n'

ANCRE_PROP = '    _, erreurs, av2 = se.verifier_hypothese(dict(h), valid_vars(), dyn)\n'
NOUV_PROP = ANCRE_PROP + ('    e_dup, a_dup = controle_doublon_entite(h.get("nom"))   # U3ak\n'
                          '    erreurs = list(erreurs) + e_dup\n'
                          '    av2 = a_dup + list(av2)\n')

REMPL = [
    ("fonctions de contrôle", ANCRE_HELPERS, HELPERS + ANCRE_HELPERS),
    ("contrôle dans verifier_bloc", ANCRE_VERIF, NOUV_VERIF),
    ("contrôle dans proposer_entite", ANCRE_PROP, NOUV_PROP),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="écrit (sinon aperçu)")
    ap.add_argument("--fichier", default=str(HYP))
    a = ap.parse_args()
    cible = Path(a.fichier)
    if not cible.exists():
        print(f"✗ Fichier introuvable : {cible} (lancer depuis la racine du vault)")
        return 2
    texte = cible.read_text(encoding="utf-8")
    if "U3aj" not in texte:
        print("✗ U3aj absent : appliquer d'abord patch_u3aj_type_entite.py.")
        return 1
    if MARQUEUR in texte:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1
    nouveau = texte
    for nom, ancre, rempl in REMPL:
        n = nouveau.count(ancre)
        if n != 1:
            print(f"✗ Ancre « {nom} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
            return 1
        nouveau = nouveau.replace(ancre, rempl, 1)
        print(f"  ✓ {nom}")
    if not a.apply:
        print(f"\nAperçu seulement : {len(texte.splitlines())} -> {len(nouveau.splitlines())} lignes. "
              "Relancer avec --apply pour écrire.")
        return 0
    bak = cible.with_name(cible.name + ".bak_u3ak")
    shutil.copy2(cible, bak)
    cible.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(cible), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, cible)
        print(f"✗ py_compile a échoué, fichier restauré : {e}")
        return 1
    print(f"\n✓ Écrit : {cible} (sauvegarde : {bak.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

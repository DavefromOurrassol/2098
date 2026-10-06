"""
reattribuer_signatures.py -- S23, 3 octobre 2026.

Réattribue un·e journaliste curaté·e aux articles hérités mal signés
(journaliste_slug vide, ou absent de la rédaction de la zone N1) --
articles générés avant les correctifs du 23-25 août 2026 (remontée N1,
metadata["journaliste"]), voir audit_signatures.py.

Pour chaque article concerné :
  - zone N1 = _resoudre_zone_n1(zone_principale), comme le pipeline ;
  - journaliste tiré dans zone_data["journalistes"], filtré par
    thématique puis pondéré par séniorité (_select_journaliste_pondere,
    état de rotation LOCAL à ce script -- trajectory_usage.json n'est
    jamais modifié) ;
  - frontmatter : journaliste_slug réécrit (même _slugify qu'api.py) ;
  - corps : la ligne de signature "Nom — Journal" des 8 premières lignes
    non vides est remplacée ; si aucune n'existe (ou si la ligne trouvée
    n'est pas une vraie signature, ex. titre de petite annonce), une
    signature est insérée sous la ligne de date.

Écartés (listés, jamais modifiés) : articles sans zone ou dont la N1
n'existe pas dans journaux.yaml ; zones sans journalistes ; articles
sans ligne de date repérable quand une insertion est nécessaire.

Usage (depuis generator/) :
  python3 reattribuer_signatures.py            # aperçu, n'écrit rien
  python3 reattribuer_signatures.py --apply    # écrit, .bak_signature avant
"""
import argparse
import functools
import glob
import re
import shutil
import unicodedata

import yaml

import prompt_builder as pb

pb._load_geographie = functools.lru_cache(None)(pb._load_geographie)


def _slugify(text):
    """Copie exacte de api.py::_slugify."""
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


# Ligne de signature : "Prénom Nom — Journal", gras optionnel autour.
BYLINE_RE = re.compile(r"^(\**)\s*([A-ZÀ-ÖØ-Ý][^—\n]*?)\s+—\s+(.+?)\s*(\**)\s*$")
DATE_RE = re.compile(r"\b(20\d\d|2098)\b")


def est_signature(nom, journal_cite=""):
    """Vraie signature "Prénom Nom — Journal" -- pas une dateline (« Mbandaka,
    Bassin Congo — 18 juin 2098 », « Le Fil Commun — …, 12 octobre 2098 ») :
    ni virgule dans le nom, ni année dans la partie droite (S23, 3 octobre)."""
    if "," in nom or DATE_RE.search(journal_cite or ""):
        return False
    mots = nom.split()
    return 2 <= len(mots) <= 4 and all(m[:1].isupper() for m in mots)


def traiter(chemin, J, etat, apply):
    texte = open(chemin, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", texte, re.S)
    if not m:
        return None
    fm = yaml.safe_load(m.group(1)) or {}
    sc = chemin.split("/")[2]
    li = fm.get("ligne_editoriale") or "pro_pouvoir"
    z = fm.get("zone_principale") or ""
    js = fm.get("journaliste_slug") or ""
    th = fm.get("thematique") or ""

    # Même résolution que le pipeline (S23) : rédaction de la sous-zone en
    # priorité, sinon celle d'un parent, sinon la N1.
    n1 = pb._resoudre_zone_redaction(z, sc, li) if z else ""
    zd = (J.get(sc, {}).get(li, {}).get("zones") or {}).get(n1)
    journalistes = (zd or {}).get("journalistes") or []
    noms_ok = {_slugify(p.get("nom", "")) for p in journalistes + ((zd or {}).get("orateurs") or [])}
    if js and js in noms_ok:
        return None  # déjà correct

    court = chemin.split("/")[-1][:60]
    if not z:
        return ("ECARTE", court, "sans zone_principale")
    if not zd:
        return ("ECARTE", court, "N1 '{}' absente de journaux.yaml".format(n1))
    if not journalistes:
        return ("ECARTE", court, "zone '{}' sans journalistes".format(n1))

    journal = zd["nom"]
    entete, corps = texte[:m.end()], texte[m.end():]
    lignes = corps.split("\n")
    non_vides = [i for i, l in enumerate(lignes) if l.strip()][:8]

    # Signature déjà présente avec un nom de la rédaction (cas réel :
    # Timur Akhmetov, seul le slug était faux) : on garde le nom.
    nom = None
    noms_redac = {_slugify(j.get("nom", "")): j.get("nom") for j in journalistes}
    for i in non_vides:
        b = BYLINE_RE.match(lignes[i].strip())
        if b and est_signature(b.group(2).strip("* "), b.group(3)):
            nom = noms_redac.get(_slugify(b.group(2).strip("* ")))
            break
    if nom is None:
        candidats = [j for j in journalistes if th and th in (j.get("thematiques") or [])] or journalistes
        namespace = "journalistes::{}::{}".format(li, n1)
        nom = pb._select_journaliste_pondere(candidats, etat, sc, namespace)
    nouvelle_sig = "{} — {}".format(nom, journal)

    action = None
    for i in non_vides:
        b = BYLINE_RE.match(lignes[i].strip())
        if b and est_signature(b.group(2).strip("* "), b.group(3)):
            ancienne = lignes[i].strip()
            lignes[i] = "{}{}{}".format(b.group(1), nouvelle_sig, b.group(4))
            action = "remplace « {} »".format(ancienne)
            break
    if action is None:
        # Pas de vraie signature : insertion sous la ligne de date
        # (première ligne courte contenant une année, hors titre).
        date_i = next((i for i in non_vides[1:] if DATE_RE.search(lignes[i]) and len(lignes[i]) < 60), None)
        if date_i is None:
            # Ancien format (juin-juillet) sans ligne de date courte : la
            # signature va juste sous le titre (position d'une byline).
            if not non_vides:
                return ("ECARTE", court, "article vide")
            date_i = non_vides[0]
        lignes.insert(date_i + 1, "")
        lignes.insert(date_i + 2, nouvelle_sig)
        action = "insère sous « {} »".format(lignes[date_i].strip()[:60])

    nouveau_slug = _slugify(nom)
    if re.search(r"^journaliste_slug:.*$", entete, re.M):
        entete = re.sub(r"^journaliste_slug:.*$", "journaliste_slug: " + nouveau_slug, entete, count=1, flags=re.M)
    else:
        entete = entete[:-4] + "journaliste_slug: {}\n---\n".format(nouveau_slug)

    if apply:
        shutil.copy2(chemin, chemin + ".bak_signature")
        open(chemin, "w", encoding="utf-8").write(entete + "\n".join(lignes))

    return ("OK", court, "[{} -> {}] {} | {}".format(js or "vide", nouveau_slug, action, journal))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon aperçu)")
    args = ap.parse_args()

    J = yaml.safe_load(open("journaux.yaml", encoding="utf-8"))
    etat = {}  # rotation locale, jamais persistée
    ok, ecartes = [], []
    for f in sorted(glob.glob("../articles/*/*.md")):
        if f.endswith("_index.md"):
            continue
        r = traiter(f, J, etat, args.apply)
        if r:
            (ok if r[0] == "OK" else ecartes).append(r)

    print("=== {} ({} articles) ===".format("ÉCRIT" if args.apply else "APERÇU, rien n'est écrit", len(ok)))
    for _, c, d in ok:
        print("-", c, "\n   ", d)
    print("\n=== ÉCARTÉS ({}) ===".format(len(ecartes)))
    for _, c, d in ecartes:
        print("-", c, ":", d)


if __name__ == "__main__":
    main()

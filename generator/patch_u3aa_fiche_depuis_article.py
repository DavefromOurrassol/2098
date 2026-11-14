#!/usr/bin/env python3
"""
patch_u3aa_fiche_depuis_article.py — Ourrassol 2098 (14 novembre 2026)
=====================================================================

Chantier « source mince -> invention » (B9). Pour un événement tiré d'un article
(passage retrouvé par U3s), les textes de la fiche ne sont plus GÉNÉRÉS par l'IA :

  - realisation et description_complete = la description de l'hypothèse (déjà tirée de
    l'article) ; l'IA n'écrit plus rien dans ces champs ;
  - consequences = formule fixe (l'article ne documente pas de conséquences) ;
  - note_coherence = renvoi à l'article d'origine + citation exacte ;
  - date_label : l'année seule, sauf si les mots du libellé (mois, saison) sont dans l'article.
  L'IA garde le nom, la clé d'événement et le choix des acteurs ; les impacts restent ceux
  de la simulation.

Contrôle ajouté (⚠, non bloquant, sans IA) : noms propres et sigles du texte absents de
l'article ET des noms du vault (instances du scénario, entités, zones).

Sans article retrouvé : rien ne change. Interrupteur : FICHE_DEPUIS_ARTICLE_U3AA.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3aa_fiche_depuis_article.py            # dry-run
    python3 generator/patch_u3aa_fiche_depuis_article.py --apply    # écrit (.bak_u3aa)
"""
import argparse
import py_compile
import re
import shutil
import sys
import tempfile
from pathlib import Path

CIBLE = Path("generator/inject_custom_events.py")

BLOC = r'''# U3aa (14 novembre 2026) -- fiche d'un événement d'article : textes repris, jamais générés.
# Quand l'article ne donne qu'une phrase, tout texte écrit par l'IA autour est de l'invention
# (constat du 11 nov. sur 4 fiches). Sans passage d'article retrouvé, rien ne change.
FICHE_DEPUIS_ARTICLE_U3AA = True
CONSEQUENCES_ARTICLE_U3AA = "L'article d'origine ne précise pas de conséquences de cet événement."
_VAULT_NOMS_U3AA = {}   # cache : scénario -> liste de noms normalisés (entourés d'espaces)

_CAP_U3AA = r"[A-ZÀ-ÖØ-Þ][\w'’-]*"
_LIEN_U3AA = r"(?:\s+(?:de|du|des|la|le|les|et|pour|sur|au|aux|en)\s+|\s+d['’]\s*|\s+l['’]\s*|\s+)"
_SEQ_NOMS_U3AA = re.compile(_CAP_U3AA + "(?:" + _LIEN_U3AA + _CAP_U3AA + ")*")
_DEBUTS_U3AA = {"le", "la", "les", "l", "un", "une", "des", "dans", "en", "ce", "cet", "cette", "ces",
                "depuis", "aujourd", "pour", "sur", "avec", "mais", "et", "ainsi", "alors", "puis",
                "il", "elle", "ils", "elles", "son", "sa", "ses", "leur", "leurs", "au", "aux", "du"}


def _noms_propres_u3aa(texte):
    """Séquences de mots capitalisés (noms propres, sigles). Un mot capitalisé isolé en
    début de phrase n'est pas retenu ; un article ou une préposition en tête est retiré."""
    out = []
    for phrase in re.split(r"(?<=[.!?])\s+", str(texte or "")):
        for m in _SEQ_NOMS_U3AA.finditer(phrase):
            mots = m.group(0).split()
            if m.start() == 0:
                while mots and re.sub(r"['’].*$", "", mots[0]).lower() in _DEBUTS_U3AA:
                    mots = mots[1:]
                if len(mots) < 2 and (m.start() == 0 and len(m.group(0).split()) <= 1 or not mots):
                    continue
                if len(mots) == 1 and not mots[0].isupper():
                    continue
            if mots:
                out.append(" ".join(mots))
    return out


def _noms_vault_u3aa(scenario):
    """Noms (normalisés, entourés d'espaces) des instances du scénario, des entités et des zones."""
    if scenario in _VAULT_NOMS_U3AA:
        return _VAULT_NOMS_U3AA[scenario]
    noms = set()
    try:
        for a in load_available_actors(scenario):
            noms.add(" " + _norm_ctx_u3s(a.get("name")) + " ")
        d = VAULT_ROOT / "entites"
        if d.is_dir():
            for p in d.glob("*.md"):
                fm, _ = parse_md(p)
                if fm.get("name"):
                    noms.add(" " + _norm_ctx_u3s(fm["name"]) + " ")
        for z in load_all_zones_event(scenario).values():
            for k in ("nom", "name"):
                if z.get(k):
                    noms.add(" " + _norm_ctx_u3s(z[k]) + " ")
    except Exception:  # noqa: BLE001 -- contrôle d'information, jamais un blocage
        pass
    noms.discard("  ")
    _VAULT_NOMS_U3AA[scenario] = noms
    return noms


def appliquer_fiche_article_u3aa(instance_data, idea, scenario):
    """U3aa : remplace les textes écrits par l'IA par ceux de l'article (voir l'en-tête du patch).
    Appelé après chaque réponse de l'IA (essai initial et relances), avant la validation."""
    if not FICHE_DEPUIS_ARTICLE_U3AA:
        return
    article = _DERNIER_ARTICLE_U3S.get(scenario)
    desc = " ".join(str(idea.get("description") or "").split())
    if not article or not desc:
        return
    info = _ARTICLE_INFO_U3AA.get(scenario) or {}
    instance_data["realisation"] = desc
    instance_data["description_complete"] = desc
    instance_data["consequences"] = CONSEQUENCES_ARTICLE_U3AA
    cit = " ".join(str(info.get("citation") or "").split())
    instance_data["note_coherence"] = (
        "Événement tiré de l'article d'origine" + (f" ({info['fichier']})" if info.get("fichier") else "")
        + (f" : « {cit} »." if cit else ".") + " Textes repris de l'hypothèse, sans ajout."
    )
    try:
        an = int(float(instance_data.get("date")))
    except (TypeError, ValueError):
        an = None
    if an:
        label = str(instance_data.get("date_label") or "")
        base = set(_norm_ctx_u3s(article).split())
        mots = [w for w in _norm_ctx_u3s(re.sub(r"\d+", " ", label)).split() if len(w) >= 3]
        if not label or any(w not in base for w in mots):
            instance_data["date_label"] = str(an)
    print(f"  [fiche article] {scenario} : textes repris de l'hypothèse et de l'article (U3aa)")


def _noms_absents_u3aa(instance_data, scenario):
    """U3aa : noms propres / sigles du texte absents de l'article ET du vault. Liste (vide sinon)."""
    article = _DERNIER_ARTICLE_U3S.get(scenario)
    if not article:
        return []
    base = " " + _norm_ctx_u3s(article) + " "
    vault = _noms_vault_u3aa(scenario)
    vus, out = set(), []
    for k in ("realisation", "description_complete", "consequences"):
        for c in _noms_propres_u3aa(instance_data.get(k)):
            n = _norm_ctx_u3s(c)
            if not n or n in vus:
                continue
            vus.add(n)
            if (" " + n + " ") in base or any((" " + n + " ") in v for v in vault):
                continue
            out.append(c)
    return out


'''

def appliquer(src):
    """Retourne (nouveau texte, liste de messages) ou lève ValueError."""
    msgs = []

    def une_fois(texte, ancre, nouveau, nb=1):
        n = texte.count(ancre)
        if n != nb:
            raise ValueError(f"ancre trouvée {n} fois (attendu {nb}) : {ancre[:70]!r}")
        return texte.replace(ancre, nouveau)

    # 1. dictionnaire d'infos sur l'article
    a = '_DERNIER_ARTICLE_U3S = {}   # U3t : scénario -> texte de l\'article trouvé (pour le contrôle des citations)\n'
    src = une_fois(src, a, a + '_ARTICLE_INFO_U3AA = {}   # U3aa : scénario -> {fichier, citation}\n')
    msgs.append("dictionnaire _ARTICLE_INFO_U3AA ajouté")
    # 2. remise à zéro au début de _texte_contexte_article
    a = '    _DERNIER_ARTICLE_U3S.pop(scenario, None)   # U3t\n'
    src = une_fois(src, a, a + '    _ARTICLE_INFO_U3AA.pop(scenario, None)   # U3aa\n')
    msgs.append("remise à zéro dans _texte_contexte_article")
    # 3. mémorisation du fichier et de la citation
    a = '            _DERNIER_ARTICLE_U3S[scenario] = " ".join(paras)   # U3t\n'
    src = une_fois(src, a, a + '            _ARTICLE_INFO_U3AA[scenario] = {"fichier": f.name, "citation": cand}   # U3aa\n')
    msgs.append("mémorisation du fichier et de la citation")
    # 4. fonctions, avant process_idea
    a = 'def process_idea(client, idea, dry_run=False):\n'
    src = une_fois(src, a, BLOC + a)
    msgs.append("fonctions U3aa insérées avant process_idea")
    # 5. appel après chaque appliquer_impositions (essai initial et relances)
    motif = re.compile(r'^([ \t]+)appliquer_impositions\(instance_data, idea, scenario\)[ \t]*$', re.M)
    n = len(motif.findall(src))
    if n != 2:
        raise ValueError(f"appels à appliquer_impositions : {n} trouvés (attendu 2)")
    src = motif.sub(lambda m: (m.group(0) + "\n" + m.group(1)
                               + "appliquer_fiche_article_u3aa(instance_data, idea, scenario)   # U3aa"), src)
    msgs.append("appliquer_fiche_article_u3aa appelé aux 2 endroits")
    # 6. contrôle des noms propres, après les anachronismes
    a = ('            for msg in _anachronismes_u3y(instance_data, idea, scenario):   # U3y\n'
         '                print(f"  ⚠ [{scenario}] {msg}")\n')
    src = une_fois(src, a, a +
                   '            for nom_abs in _noms_absents_u3aa(instance_data, scenario):   # U3aa\n'
                   '                print(f"  ⚠ [{scenario}] nom propre absent de l\'article et du vault : « {nom_abs} »")\n')
    msgs.append("contrôle des noms propres ajouté")
    return src, msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.exists():
        sys.exit(f"{CIBLE} introuvable : lancer depuis la racine du vault.")
    src = CIBLE.read_text(encoding="utf-8")
    if "U3aa" in src:
        sys.exit("U3aa déjà appliqué : rien à faire.")
    try:
        neuf, msgs = appliquer(src)
    except ValueError as e:
        sys.exit(f"Abandon, rien écrit : {e}")
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "inject_custom_events.py"
        t.write_text(neuf, encoding="utf-8")
        try:
            py_compile.compile(str(t), doraise=True)
        except py_compile.PyCompileError as e:
            sys.exit(f"Abandon, le résultat ne compile pas : {e}")
    for m in msgs:
        print(" ·", m)
    if not args.apply:
        print("\nDry-run : le résultat compile, rien n'est écrit. Relancer avec --apply.")
        return
    sauvegarde = CIBLE.with_name(CIBLE.name + ".bak_u3aa")
    shutil.copy2(CIBLE, sauvegarde)
    CIBLE.write_text(neuf, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"\nÉcrit : {CIBLE} (sauvegarde : {sauvegarde.name}). py_compile OK.")


if __name__ == "__main__":
    main()

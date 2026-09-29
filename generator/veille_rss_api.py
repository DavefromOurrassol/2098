"""
veille_rss_api.py — Ourrassol 2098
===================================

Veille signaux faibles dans les FLUX RSS des sources (S21, « option 2 »,
décision David 29 sept 2026). Troisième canal, construit comme la lecture
des livres (veille_livres_api.py) : les pages d'un livre y sont remplacées
par les articles récents des sources de sources_signaux_faibles.yaml qui
ont un champ « rss » (rempli par verifier_flux_rss.py).

Pourquoi : un essai de recherche web par API (Mistral, 29 sept 2026) a
montré que l'IA déclare « consultées » des sources qu'elle n'a pas lues.
Ici le script lit lui-même les flux : chaque signal est vérifié contre le
texte réellement envoyé.

  1. COLLECTE : les articles des N derniers jours (défaut 30) de chaque
     flux, pas encore envoyés (mémoire state/rss_veille.json). Texte =
     résumé ou contenu fourni par le flux (pas la page complète), ~1 200
     caractères ; un article sans texte (ex. Hacker News : titre seul) est
     ignoré.
  2. ANALYSE : un appel call_llm() classique, SANS recherche web, par lot
     d'articles (défaut 40), mélangés entre sources. 0 à 3 signaux par lot.
  3. CONTRÔLE : chaque signal doit citer le numéro d'un article du lot
     ([A12]) et une citation exacte de son texte, sinon il est rejeté. La
     ligne source est réécrite avec l'URL réelle de l'article.
  4. SORTIE : documentation/need_action/veille_signaux_reponses/
     veille_signaux_reponse_rss.md (ia: rss), fusionnée avec les autres
     réponses par « Signaux faibles — 2. Importer les réponses ».

Les articles d'un lot ne sont marqués « lus » que si l'appel de CE lot a
réussi et que sa réponse est lisible : un lot en échec est retenté à la
passe suivante.

USAGE
-----
    python3 veille_rss_api.py                    # collecte + appels LLM
    python3 veille_rss_api.py --dry-run          # collecte + prompt du 1er lot, aucun appel
    python3 veille_rss_api.py --lister           # articles disponibles par source, aucun appel
    python3 veille_rss_api.py --jours 60         # fenêtre de collecte
    python3 veille_rss_api.py --source grist     # une source (texte du nom)
    python3 veille_rss_api.py --relire           # oublie les articles déjà envoyés

PRÉREQUIS
---------
    Dans generator/ : llm_client.py, export_prompt_signaux.py,
    export_prompt_veille.py, veille_livres_api.py, livres_veille.py,
    verifier_flux_rss.py, sources_signaux_faibles.yaml ; feedparser.
"""

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

import yaml

try:
    import feedparser
except ImportError:
    raise SystemExit("[ERREUR] feedparser manquant : pip3 install feedparser")

from export_prompt_signaux import (
    GENERATOR_DIR, NEED_ACTION_DIR, SOURCES_PATH, VAULT_ROOT,
    bloc_champs_signal, bloc_definition, bloc_evaluation, bloc_variables,
    charger_candidats_vus, charger_signaux_existants, format_date_fr,
)
from veille_livres_api import blocs_signaux, reponse_valide
from verifier_flux_rss import telecharger

REPONSES_DIR = NEED_ACTION_DIR / "veille_signaux_reponses"
REPONSE_PATH = REPONSES_DIR / "veille_signaux_reponse_rss.md"
IA_NOM = "rss"
TASK_TIER = "structured_strict"
JOURS_DEFAUT = 30
TAILLE_LOT = 40
MAX_SIGNAUX_PAR_LOT = 3
MAX_TOKENS_REPONSE = 4000
LONGUEUR_TEXTE = 1200          # caractères par article envoyé
LONGUEUR_MIN = 150             # en dessous : pas de texte exploitable
OUBLI_JOURS = 120              # mémoire : les URL plus anciennes sont oubliées
TIMEOUT = 20

SYSTEM_PROMPT = (
    "Tu es un analyste de veille prospective rigoureux. Tu lis des articles "
    "récents et tu en tires uniquement des signaux faibles réels, au sens "
    "strict, dans le format demandé, sans aucun texte hors format. Tu "
    "n'inventes rien : chaque signal s'appuie sur un article précis de la "
    "liste, dont tu cites le numéro et un passage exact."
)


def memoire_path() -> Path:
    """Même règle de dossier state/ que les autres outils de veille."""
    for d in (VAULT_ROOT / "state", GENERATOR_DIR / "state"):
        if d.exists():
            return d / "rss_veille.json"
    return VAULT_ROOT / "state" / "rss_veille.json"


def charger_memoire(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def enregistrer_envois(path: Path, articles: list) -> None:
    """Marque des articles comme lus ; oublie les entrées trop anciennes."""
    data = charger_memoire(path)
    vus = data.setdefault("articles", {})
    maintenant = datetime.now()
    for a in articles:
        vus[a["url"]] = {"source": a["source"], "lu_le": maintenant.strftime("%Y-%m-%d")}
    limite = (maintenant - timedelta(days=OUBLI_JOURS)).strftime("%Y-%m-%d")
    data["articles"] = {u: v for u, v in vus.items() if v.get("lu_le", "") >= limite}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------------------
# Collecte
# ---------------------------------------------------------------------------

def nettoyer(html: str) -> str:
    """HTML d'un flux -> texte sur une ligne."""
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html or "", flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return " ".join(unescape(t).split())


def couper(texte: str, n: int) -> str:
    if len(texte) <= n:
        return texte
    return texte[:n].rsplit(" ", 1)[0] + "…"


def texte_article(e) -> str:
    """Le plus long entre le contenu complet et le résumé fournis par le flux."""
    candidats = [c.get("value", "") for c in (e.get("content") or [])]
    candidats.append(e.get("summary", ""))
    return max((nettoyer(c) for c in candidats), key=len, default="")


def collecter(sources: list, jours: int, deja_lus: set):
    """(articles à lire, rapport par source)."""
    limite = datetime.now(timezone.utc) - timedelta(days=jours)
    articles, rapport = [], []
    for s in sources:
        nom = s.get("nom", s["rss"])
        contenu, info = telecharger(s["rss"], TIMEOUT)
        if contenu is None:
            rapport.append((nom, None, f"flux illisible ({info})"))
            continue
        f = feedparser.parse(contenu)
        n_vieux = n_vides = n_lus = 0
        pris = []
        for e in f.entries:
            url = (e.get("link") or "").strip()
            if not url:
                continue
            d = e.get("published_parsed") or e.get("updated_parsed")
            date = datetime(*d[:6], tzinfo=timezone.utc) if d else None
            if date and date < limite:
                n_vieux += 1
                continue
            if url in deja_lus:
                n_lus += 1
                continue
            texte = texte_article(e)
            if len(texte) < LONGUEUR_MIN:
                n_vides += 1
                continue
            pris.append({"source": nom, "url": url,
                         "titre": nettoyer(e.get("title", "")),
                         "date": date.strftime("%Y-%m-%d") if date else "date inconnue",
                         "texte": couper(texte, LONGUEUR_TEXTE),
                         "texte_complet": texte})
        articles.extend(pris)
        detail = []
        if n_lus:
            detail.append(f"{n_lus} déjà lu(s)")
        if n_vieux:
            detail.append(f"{n_vieux} trop ancien(s)")
        if n_vides:
            detail.append(f"{n_vides} sans texte")
        rapport.append((nom, len(pris), ", ".join(detail)))
    return articles, rapport


def repartir(articles: list, taille: int) -> list:
    """Lots mélangés entre sources (un article de chaque source à tour de
    rôle), pour qu'un lot ne soit pas occupé par une seule source."""
    par_source = {}
    for a in articles:
        par_source.setdefault(a["source"], []).append(a)
    ordre = []
    while any(par_source.values()):
        for nom in list(par_source):
            if par_source[nom]:
                ordre.append(par_source[nom].pop(0))
    return [ordre[i:i + taille] for i in range(0, len(ordre), taille)]


# ---------------------------------------------------------------------------
# Prompt d'un lot
# ---------------------------------------------------------------------------

def construire_prompt(lot: list, today_str: str, signaux: list, candidats_vus: list) -> str:
    L = [f"# Veille signaux faibles dans des articles récents — {today_str}", ""]
    L.append("## MISSION")
    L.append("")
    L.append(
        "Tu fais de la veille pour un projet de fiction spéculative "
        "(« Ourrassol 2098 ») qui imagine l'évolution du monde d'aujourd'hui "
        "jusqu'en 2098. Tu lis les ARTICLES RÉCENTS numérotés en fin de "
        "message (résumés tirés des flux RSS de médias et centres de "
        "prospective). La plupart ne contiennent AUCUN signal faible : c'est "
        "normal."
    )
    L.append("")
    L.extend(l.replace("la section « DÉJÀ CONNU » ci-dessous", "la liste « DÉJÀ REPÉRÉS » ci-dessous")
             for l in bloc_definition())
    L.append(
        f"Objectif : 0 à {MAX_SIGNAUX_PAR_LOT} signaux pour cette liste. Ne "
        "remplis pas un quota. Un article d'actualité générale, un débat, "
        "une opinion, un sondage ou une statistique n'est pas un signal ; "
        "un fait précis qu'il rapporte peut l'être."
    )
    L.append("")
    L.append("RÈGLES ABSOLUES (un signal qui ne les respecte pas est rejeté "
             "automatiquement) :")
    L.append("  - Chaque signal vient UNIQUEMENT d'un article de la liste, "
             "jamais de tes connaissances ni du reste de ce message.")
    L.append("  - N'ajoute AUCUN exemple, lieu, date, chiffre ou acteur absent "
             "de l'article cité.")
    L.append("  - observe_le = date du fait rapporté (à défaut, date de "
             "l'article), au format AAAA-MM.")
    L.append("  - La source cite le numéro EXACT de l'article entre crochets "
             "([A12]), suivi d'une courte citation EXACTE de son texte "
             "(10 à 25 mots recopiés mot pour mot, dans la langue de l'article).")
    L.append("")
    L.extend(bloc_variables())
    if signaux or candidats_vus:
        L.append("## DÉJÀ REPÉRÉS (titres seulement, à ne pas reproposer)")
        L.append("")
        for slug, _ in signaux:
            L.append(f"- {slug}")
        for t in candidats_vus:
            L.append(f"- {t}")
        L.append("")
    L.extend(bloc_evaluation())
    L.append("## FORMAT DE SORTIE STRICT")
    L.append("")
    L.append(
        f"Première ligne : « ia: {IA_NOM} ». Puis un bloc par signal, numéroté. "
        "UNE SEULE LIGNE par champ, sauf « sources » (une ligne par source, "
        "commençant par « - »). Termine par la ligne « ### FIN », une seule "
        "fois. Aucun autre texte, pas de bloc de code. S'il n'y a aucun "
        f"signal : seulement « ia: {IA_NOM} » puis « ### FIN »."
    )
    L.append("")
    L.append(f"ia: {IA_NOM}")
    L.append("")
    L.extend(bloc_champs_signal())
    L.append("sources:  (OBLIGATOIRE : numéro exact de l'article + citation exacte)")
    L.append("- [A1] — « [10 à 25 mots recopiés de cet article] »")
    L.append("")
    L.append("### FIN")
    L.append("")
    L.append("## ARTICLES RÉCENTS")
    L.append("")
    for n, a in enumerate(lot, 1):
        L.append(f"[A{n}] {a['source']} — {a['date']} — {a['titre']}")
        L.append(a["texte"])
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Contrôle anti-invention
# ---------------------------------------------------------------------------

SOURCES_RE = re.compile(r"^\s*sources?\s*:.*$", re.I | re.M)


def _mots(t: str) -> list:
    return re.findall(r"[a-zà-ÿ0-9]{3,}", t.lower())


def verifier_bloc(bloc: str, lot: list):
    """(article, None) si une source cite un article du lot avec une citation
    présente dans son texte ; sinon (None, motif)."""
    m = SOURCES_RE.search(bloc)
    partie = bloc[m.start():] if m else bloc
    lignes = [l for l in partie.splitlines() if re.search(r"\[A\d+\]", l)]
    if not lignes:
        return None, "aucune référence [A…]"
    motif = "numéro d'article absent de la liste envoyée"
    for l in lignes:
        n = int(re.search(r"\[A(\d+)\]", l).group(1))
        if not 1 <= n <= len(lot):
            continue
        art = lot[n - 1]
        c = re.search(r"[«\"“](.+?)[»\"”]", l)
        if not c:
            motif = "citation absente"
            continue
        cites = _mots(c.group(1))
        if not cites:
            motif = "citation vide"
            continue
        presents = set(_mots(art["titre"] + " " + art["texte_complet"]))
        if sum(1 for w in cites if w in presents) / len(cites) >= 0.8:
            return art, None
        motif = "citation introuvable dans l'article cité"
    return None, motif


def reecrire_sources(bloc: str, art: dict) -> str:
    """Remplace la partie « sources » par l'URL réelle de l'article, au format
    des réponses web (« - URL — nom »), que l'import sait lire."""
    m = SOURCES_RE.search(bloc)
    tete = bloc[:m.start()].rstrip() if m else bloc.rstrip()
    return f"{tete}\nsources:\n- {art['url']} — {art['source']}"


# ---------------------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------------------

def ecrire_reponse(nouveaux: list, modele: str) -> int:
    """Ajoute les blocs au fichier de réponse RSS (ceux d'une passe précédente
    pas encore importée sont conservés). Renvoie le total."""
    anciens = []
    if REPONSE_PATH.exists():
        anciens = blocs_signaux(REPONSE_PATH.read_text(encoding="utf-8"))
    tous = anciens + nouveaux
    L = [f"ia: {IA_NOM}", f"# lu par API ({modele}) le {format_date_fr(datetime.now())}", ""]
    for k, b in enumerate(tous, 1):
        L.append(f"### SIGNAL {k}")
        L.append(b)
        L.append("")
    L.append("### FIN")
    REPONSES_DIR.mkdir(parents=True, exist_ok=True)
    REPONSE_PATH.write_text("\n".join(L) + "\n", encoding="utf-8")
    return len(tous)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def sources_rss(filtre: str = None) -> list:
    data = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8")) or {}
    res = [s for s in data.get("sources") or []
           if isinstance(s, dict) and s.get("rss") and s.get("actif") is not False]
    if filtre:
        res = [s for s in res if filtre.lower() in s.get("nom", "").lower()]
    return res


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Collecte et montre le prompt du 1er lot, sans appel ni écriture.")
    parser.add_argument("--lister", action="store_true",
                        help="Articles disponibles par source, sans appel.")
    parser.add_argument("--jours", type=int, default=JOURS_DEFAUT,
                        help=f"Fenêtre de collecte en jours (défaut {JOURS_DEFAUT}).")
    parser.add_argument("--taille-lot", type=int, default=TAILLE_LOT,
                        help=f"Articles par appel LLM (défaut {TAILLE_LOT}).")
    parser.add_argument("--source", default=None,
                        help="Ne lit que les sources dont le nom contient ce texte.")
    parser.add_argument("--relire", action="store_true",
                        help="Ignore la mémoire : renvoie aussi les articles déjà lus.")
    args = parser.parse_args()

    sources = sources_rss(args.source)
    if not sources:
        print("[ERREUR] Aucune source avec un champ « rss » (lancer verifier_flux_rss.py --apply).")
        return
    mem_path = memoire_path()
    deja_lus = set() if args.relire else set(charger_memoire(mem_path).get("articles", {}))

    print(f"[COLLECTE] {len(sources)} flux, articles des {args.jours} derniers jours…", flush=True)
    articles, rapport = collecter(sources, args.jours, deja_lus)
    for nom, n, detail in rapport:
        if n is None:
            print(f"  ✗ {nom} : {detail}")
        else:
            print(f"  {'✓' if n else '·'} {nom} : {n} article(s) à lire"
                  + (f" ({detail})" if detail else ""))
    lots = repartir(articles, max(1, args.taille_lot))
    print(f"[COLLECTE] {len(articles)} article(s) à lire → {len(lots)} lot(s) "
          f"de {args.taille_lot} au plus.")
    if args.lister:
        return
    if not lots:
        print("[OK] Rien de nouveau à lire.")
        return

    today_str = format_date_fr(datetime.now())
    signaux = charger_signaux_existants()
    candidats_vus = charger_candidats_vus()

    if args.dry_run:
        prompt = construire_prompt(lots[0], today_str, signaux, candidats_vus)
        print("\n--- SYSTEM ---\n" + SYSTEM_PROMPT)
        print("\n--- PROMPT (1er lot) ---\n" + prompt)
        print(f"\n[dry-run] {len(lots)} appel(s) seraient faits, ~{len(prompt.split())} mots "
              "pour ce lot. Aucun appel, rien d'écrit, aucun article marqué lu.")
        return

    from llm_client import call_llm, resolve_for_tier
    provider, model = resolve_for_tier(TASK_TIER)
    modele = f"{provider}/{model}"
    print(f"[API] {modele} — {len(lots)} lot(s), un appel par lot.", flush=True)

    nouveaux, n_ok, echecs = [], 0, 0
    for k, lot in enumerate(lots, 1):
        prompt = construire_prompt(lot, today_str, signaux, candidats_vus)
        print(f"[API] lot {k}/{len(lots)} ({len(lot)} articles)…", flush=True)
        try:
            texte = call_llm(SYSTEM_PROMPT, prompt, max_tokens=MAX_TOKENS_REPONSE,
                             temperature=0.3, task_tier=TASK_TIER)
        except Exception as ex:
            echecs += 1
            print(f"        ✗ appel échoué : {ex} — articles NON marqués lus")
            continue
        if not reponse_valide(texte or ""):
            echecs += 1
            brut = REPONSES_DIR / "archive" / f"rss_reponse_illisible_{datetime.now():%Y%m%d_%H%M%S}.txt"
            brut.parent.mkdir(parents=True, exist_ok=True)
            brut.write_text(texte or "", encoding="utf-8")
            print(f"        ✗ réponse illisible (gardée dans {brut.name}) — articles NON marqués lus")
            continue
        blocs, rejetes = [], 0
        for b in blocs_signaux(texte):
            art, motif = verifier_bloc(b, lot)
            if motif:
                rejetes += 1
                t = re.search(r"^titre\s*:\s*(.+)$", b, re.M | re.I)
                print(f"        ✗ rejeté ({motif}) : {t.group(1)[:70] if t else '?'}")
            else:
                blocs.append(reecrire_sources(b, art))
        nouveaux.extend(blocs)
        n_ok += 1
        enregistrer_envois(mem_path, lot)       # lot par lot : un échec plus loin ne perd rien
        print(f"        ✓ {len(blocs)} signal(aux)" + (f", {rejetes} rejeté(s)" if rejetes else ""))

    if n_ok:
        total = ecrire_reponse(nouveaux, modele) if nouveaux or REPONSE_PATH.exists() else 0
        print(f"\n[OK] {len(nouveaux)} signal(aux) tiré(s) de {n_ok} lot(s).")
        if total:
            print(f"     Écrits dans {REPONSE_PATH.relative_to(VAULT_ROOT)} "
                  f"({total} au total en attente d'import).")
            print("     Prochaine étape : « Signaux faibles — 2. Importer les réponses ».")
        print(f"     Articles marqués lus : {mem_path.relative_to(VAULT_ROOT)}")
    if echecs:
        print(f"\n[AVERTISSEMENT] {echecs} lot(s) en échec, retentés à la prochaine passe.")


if __name__ == "__main__":
    main()

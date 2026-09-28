"""
veille_livres_api.py — Ourrassol 2098
======================================

Veille signaux faibles dans les LIVRES, par API (décision David,
28 septembre 2026). Complète la veille web à coller dans les IA de chat
(export_prompt_signaux.py) : lire des pages fournies ne demande pas
d'accès au web, un appel call_llm() classique suffit (LLM par défaut,
routage par tier de llm_client.py, comme les autres scripts).

Pour chaque PDF/EPUB déposé dans documentation/livres/ :
  0. REPÉRAGE (une fois par livre, 28 sept 2026) : le LLM reçoit le début
     de chaque page (~200 caractères) et désigne celles qui peuvent décrire
     un phénomène précis (cas, expérience, technologie nommée, pratique).
     Mémorisé dans state/livres_veille.json (« plan ») ; refait seulement si
     le fichier change ou avec --refaire-reperage. Constat à l'origine : une
     note « faits concrets » choisissait, dans le rapport JRC, des pages de
     statistiques de publications, riches en chiffres mais sans signal ;
  1. livres_veille.py prend les pages du plan PAS ENCORE LUES (rotation,
     dans l'ordre du livre) ; sans plan (repérage en échec), la note
     « faits concrets » sert de solution de secours ;
  2. un appel LLM par livre applique la définition stricte (3 tests), les
     12 variables et le « déjà connu », et renvoie 0 à 3 signaux au format
     de la veille web ;
  3. les signaux de tous les livres sont écrits dans
        documentation/need_action/veille_signaux_reponses/
        veille_signaux_reponse_livres.md   (ia: livres)
     puis « Signaux faibles — 2. Importer les réponses » les fusionne avec
     les réponses des IA de chat, comme n'importe quelle réponse.

Les pages ne sont marquées « lues » (state/livres_veille.json) que si
l'appel de CE livre a réussi et que sa réponse est lisible. Un livre dont
l'appel échoue est retenté à la passe suivante, sur les mêmes pages.

Limite : sans web, le LLM ne peut pas vérifier que le phénomène est encore
marginal AUJOURD'HUI (4e test des livres). Les candidats arrivent avec
l'avertissement 📖 « état actuel non vérifié » : à trancher au tri.

USAGE
-----
    python3 veille_livres_api.py                  # lit les livres, appelle le LLM
    python3 veille_livres_api.py --dry-run        # montre le prompt du 1er livre, aucun appel
    python3 veille_livres_api.py --lister-livres  # état des livres, aucun appel
    python3 veille_livres_api.py --relire-livres  # oublie les pages déjà lues
    python3 veille_livres_api.py --livre JRC      # un seul livre (texte contenu dans le nom)

PRÉREQUIS
---------
    Dans generator/ : llm_client.py, export_prompt_signaux.py,
    export_prompt_veille.py, import_signaux_faibles.py, livres_veille.py,
    sources_signaux_faibles.yaml ; pypdf pour les PDF (pip3 install pypdf).
"""

import argparse
import re
from datetime import datetime

import yaml

from export_prompt_signaux import (
    HORS_VARIABLES, NEED_ACTION_DIR, SOURCES_PATH, VAULT_ROOT,
    bloc_champs_signal, bloc_definition, bloc_deja_connu, bloc_evaluation,
    bloc_variables, charger_candidats_vus, charger_deja_connu,
    charger_signaux_existants, format_date_fr, memoire_livres_path,
)
from livres_veille import (charger_memoire, decouvrir, dossier_livres,
                           enregistrer_envois, enregistrer_plan, extraire_tous,
                           lister_livres, noter, oublier_plans, plan_connu)

REPONSES_DIR = NEED_ACTION_DIR / "veille_signaux_reponses"
REPONSE_PATH = REPONSES_DIR / "veille_signaux_reponse_livres.md"
IA_NOM = "livres"
TASK_TIER = "structured_strict"
MAX_SIGNAUX_PAR_LIVRE = 3
MAX_TOKENS_REPONSE = 4000

SYSTEM_PROMPT = (
    "Tu es un analyste de veille prospective rigoureux. Tu lis des extraits "
    "de livres et tu en tires uniquement des signaux faibles réels, au sens "
    "strict, dans le format demandé, sans aucun texte hors format. Tu "
    "n'inventes rien : chaque signal s'appuie sur un passage précis des "
    "extraits, dont tu cites la référence exacte."
)


# ---------------------------------------------------------------------------
# Prompt d'un livre
# ---------------------------------------------------------------------------

def construire_prompt(extrait: dict, today_str: str, deja_connu: dict,
                      signaux: list, candidats_vus: list) -> str:
    titre = extrait["titre"]
    qui = titre + (f" — {extrait['auteur']}" if extrait["auteur"] else "")
    if extrait["annee"]:
        qui += f" ({extrait['annee']})"
    L = [f"# Veille signaux faibles dans un livre — {today_str}", ""]
    L.append("## MISSION")
    L.append("")
    L.append(
        "Tu fais de la veille pour un projet de fiction spéculative "
        "(« Ourrassol 2098 ») qui imagine l'évolution du monde d'aujourd'hui "
        "jusqu'en 2098. Tu lis des EXTRAITS DU LIVRE ci-dessous (en fin de "
        f"message) : « {qui} ». Les pages ont été choisies automatiquement "
        "parce qu'elles contiennent des faits concrets ; elles peuvent ne "
        "contenir AUCUN signal faible, c'est normal."
    )
    L.append("")
    L.extend(l.replace("la section « DÉJÀ CONNU » ci-dessous", "la liste « DÉJÀ REPÉRÉS » ci-dessous")
             for l in bloc_definition())
    L.append(
        "4e test propre aux livres : un livre date de son écriture. Ce qui "
        "était un signal faible à l'époque peut être devenu une tendance "
        "banale, ou avoir disparu. Tu n'as pas accès au web : écarte ce qui, "
        "à ta connaissance, est devenu courant ; pour le reste, dis dans la "
        "justification ce qu'il faudrait vérifier aujourd'hui."
    )
    L.append("")
    L.append(
        f"Objectif : 0 à {MAX_SIGNAUX_PAR_LIVRE} signaux. La plupart des "
        "extraits en contiennent 0 ou 1 : ne remplis pas un quota. Ne propose "
        "jamais une idée, une prédiction ou un scénario de l'auteur : "
        "seulement des faits observés qu'il rapporte."
    )
    L.append("")
    L.append("RÈGLES ABSOLUES (constat du 28 sept 2026 : des signaux inventés "
             "ou recopiés d'ailleurs ont été rejetés) :")
    L.append("  - Chaque signal vient UNIQUEMENT des EXTRAITS DU LIVRE en fin de "
             "message, jamais du reste de ce message ni de tes connaissances.")
    L.append("  - N'ajoute AUCUN exemple, lieu, date, chiffre ou acteur absent de "
             "l'extrait cité.")
    L.append("  - observe_le = date du fait rapporté dans l'extrait (AAAA-MM ou "
             "AAAA), jamais la date d'aujourd'hui.")
    L.append("  - La source cite la référence EXACTE entre crochets d'un passage "
             "fourni, suivie d'une courte citation EXACTE de ce passage "
             "(10 à 25 mots, recopiés mot pour mot, dans la langue du livre). "
             "Un signal dont la citation ne figure pas dans l'extrait est "
             "rejeté automatiquement.")
    L.append("")
    L.extend(bloc_variables())
    # Pas le « déjà connu » de l'état du monde ici (constat du 28 sept 2026 :
    # le LLM en tirait des « signaux » — Ebola, Ceuta, Hugging Face —
    # attribués à de fausses pages). Les doublons avec les signaux existants
    # et les veilles précédentes restent détectés à l'import.
    if signaux or candidats_vus:
        L.append("## DÉJÀ REPÉRÉS (titres seulement, à ne pas reproposer)")
        L.append("")
        for slug, resume in signaux:
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
    L.append("sources:  (OBLIGATOIRE : référence exacte entre crochets + citation exacte)")
    ex_ref = extrait["segments"][0][0] if extrait["segments"] else "p. 52"
    L.append(f"- livre: {titre}, {ex_ref} — « [10 à 25 mots recopiés de ce passage] »")
    L.append("")
    L.append("### FIN")
    L.append("")
    L.append(f"## EXTRAITS DU LIVRE : {qui}")
    L.append("")
    L.append("Texte extrait automatiquement (mise en page perdue). Chaque "
             "passage commence par sa référence entre crochets.")
    L.append("")
    for ref, texte in extrait["segments"]:
        L.append(f"[{ref}] {texte}")
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Réponses
# ---------------------------------------------------------------------------

BLOC_RE = re.compile(r"^###\s*SIGNAL\b.*?(?=^###\s*SIGNAL\b|^#{2,4}\s*FIN\s*$|\Z)",
                     re.I | re.M | re.S)


def blocs_signaux(texte: str) -> list:
    """Blocs « ### SIGNAL … » d'une réponse (sans numéro, renumérotés à
    l'écriture). Coupe au dernier « ### FIN »."""
    fins = list(re.finditer(r"^\s*#{2,4}\s*FIN\s*$", texte, re.I | re.M))
    corps = texte[:fins[-1].start()] if fins else texte
    corps = re.sub(r"^```\w*\s*$", "", corps, flags=re.M)
    return [re.sub(r"^###\s*SIGNAL\b[^\n]*\n", "", b.strip(), flags=re.I)
            for b in BLOC_RE.findall(corps)]


def _mots(t: str) -> list:
    return re.findall(r"[a-zà-ÿ0-9]{3,}", t.lower())


def verifier_bloc(bloc: str, extrait: dict):
    """
    Contrôle anti-invention (28 sept 2026) : la source « livre: » doit citer
    une référence réellement envoyée ET une citation dont les mots figurent
    dans ce passage. Renvoie None si le bloc est valable, sinon le motif.
    """
    refs = {ref: texte for ref, texte in extrait["segments"]}
    lignes = [l for l in bloc.splitlines() if re.match(r"\s*[-*]?\s*livre\s*:", l, re.I)]
    if not lignes:
        return "aucune source « livre: »"
    for l in lignes:
        passage = None
        for ref, texte in refs.items():
            num = re.escape(ref.split("«")[0].strip())       # « p. 106 », « chap. 3 »
            if re.search(num + r"(?![0-9])", l):
                passage = texte
                break
        if passage is None:
            continue
        m = re.search(r"[«\"“](.+?)[»\"”]", l)
        if not m:
            return "citation absente"
        cites = _mots(m.group(1))
        if not cites:
            return "citation vide"
        presents = set(_mots(passage))
        if sum(1 for w in cites if w in presents) / len(cites) >= 0.8:
            return None
        return "citation introuvable dans le passage cité"
    return "référence de page absente des extraits envoyés"


def reponse_valide(texte: str) -> bool:
    """Lisible = au moins un bloc SIGNAL, ou une réponse vide explicite
    (« ### FIN » sans signal)."""
    return bool(blocs_signaux(texte)) or bool(
        re.search(r"^\s*#{2,4}\s*FIN\s*$", texte, re.I | re.M))


def ecrire_reponse(nouveaux: list, modele: str) -> int:
    """Ajoute les blocs au fichier de réponse livres (ceux d'une passe
    précédente pas encore importée sont conservés). Renvoie le total."""
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
# Repérage des pages utiles (une fois par livre)
# ---------------------------------------------------------------------------

LONGUEUR_APERCU = 200
MAX_PAGES_PLAN = 60

SYSTEM_REPERAGE = (
    "Tu es un documentaliste de veille prospective. On te donne le début de "
    "chaque page d'un document. Tu désignes les pages qui peuvent contenir un "
    "phénomène précis et observable. Tu réponds uniquement par la ligne demandée."
)


def construire_prompt_reperage(livre) -> str:
    unites = livre.unites()
    titre = livre.meta.get("titre", livre.rel)
    L = [f"# Repérage des pages utiles — « {titre} »", ""]
    L.extend(bloc_definition())
    L.append(
        "Ci-dessous, le DÉBUT de chaque page (ou bloc) du document, précédé de "
        "son numéro. Désigne les numéros des pages qui peuvent décrire un "
        "phénomène PRÉCIS et OBSERVABLE susceptible d'être un signal faible : "
        "une technologie ou une pratique nommée, un cas, une expérience, un "
        "premier usage, un acteur nouveau, une règle nouvelle, une liste de "
        "technologies ou de tendances émergentes."
    )
    L.append(
        "N'en retiens PAS : couverture, sommaire, remerciements, introduction "
        "générale, méthodologie, statistiques ou classements (parts de pays, "
        "nombres de publications ou de brevets, réseaux de collaboration), "
        "prédictions et scénarios, conclusions, bibliographie, annexes "
        "techniques. Les pages de liste ou de tableau de TECHNOLOGIES NOMMÉES "
        "sont en revanche à retenir."
    )
    L.append(
        f"Retiens au plus {MAX_PAGES_PLAN} numéros, les plus prometteurs. Si "
        "aucune page ne convient, c'est une bonne réponse."
    )
    L.append("")
    L.append("Réponds par UNE seule ligne, sans autre texte :")
    L.append("pages: 12, 15, 40-44")
    L.append("ou, si rien ne convient :")
    L.append("pages: aucune")
    L.append("")
    L.append("## DÉBUT DES PAGES")
    L.append("")
    for i, (ref, texte) in enumerate(unites, 1):
        if not texte:
            continue
        if noter(texte) == 0 and len(texte) >= 400:
            continue                          # bibliographie détectée : inutile d'envoyer
        apercu = " ".join(texte.split())[:LONGUEUR_APERCU]
        L.append(f"{i} | {ref} | {apercu}")
    return "\n".join(L)


def lire_plan(reponse: str, maximum: int):
    """« pages: 12, 15, 40-44 » -> [12, 15, 40..44] ; « aucune » -> [] ;
    illisible -> None."""
    m = re.search(r"pages?\s*:\s*(.+)", reponse or "", re.I)
    if not m:
        return None
    brut = m.group(1).strip().strip(".")
    if re.match(r"(?i)aucune|none|rien", brut):
        return []
    nums = []
    for a, b in re.findall(r"(\d+)\s*(?:[-–]\s*(\d+))?", brut):
        a = int(a)
        b = int(b) if b else a
        nums.extend(range(min(a, b), max(a, b) + 1))
    nums = sorted({n for n in nums if 1 <= n <= maximum})
    return nums[:MAX_PAGES_PLAN * 2] if nums else None


def reperer(livres: list, memoire_path, call_llm) -> None:
    """Repère les livres sans plan à jour ; mémorise chaque plan réussi."""
    memoire = charger_memoire(memoire_path)
    for livre, reglages in livres:
        if livre is None or reglages.get("pages") or reglages.get("chapitres"):
            continue
        if plan_connu(memoire, livre):
            continue
        try:
            if livre.scanne():
                continue
            prompt = construire_prompt_reperage(livre)
        except Exception as ex:
            print(f"[REPÉRAGE] {livre.rel} : lecture impossible ({ex})")
            continue
        titre = livre.meta.get("titre", livre.rel)
        print(f"[REPÉRAGE] {titre}…", flush=True)
        try:
            reponse = call_llm(SYSTEM_REPERAGE, prompt, max_tokens=400,
                               temperature=0.0, task_tier=TASK_TIER)
        except Exception as ex:
            print(f"        ✗ appel échoué ({ex}) : note « faits concrets » utilisée à la place")
            continue
        plan = lire_plan(reponse, len(livre.unites()))
        if plan is None:
            print(f"        ✗ réponse illisible ({(reponse or '')[:80]!r}) : note « faits "
                  "concrets » utilisée à la place")
            continue
        enregistrer_plan(memoire_path, livre, plan)
        print(f"        ✓ {len(plan)} page(s) retenue(s) sur {len(livre.unites())}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Montre le prompt du premier livre, sans appel ni écriture.")
    parser.add_argument("--lister-livres", action="store_true",
                        help="État des livres (densité de faits, pages lues), sans appel.")
    parser.add_argument("--relire-livres", action="store_true",
                        help="Oublie les pages déjà lues : reprend les livres au début.")
    parser.add_argument("--refaire-reperage", action="store_true",
                        help="Refait le repérage LLM des pages utiles de chaque livre.")
    parser.add_argument("--livre", default=None,
                        help="Ne traite que le(s) livre(s) dont le nom de fichier contient ce texte.")
    args = parser.parse_args()

    data_yaml = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8")) or {}
    dossier = dossier_livres(data_yaml, VAULT_ROOT)
    memoire_path = memoire_livres_path()
    if args.lister_livres:
        print(lister_livres(dossier, data_yaml.get("livres") or [], memoire_path))
        return

    decouverts = decouvrir(dossier, data_yaml.get("livres") or [])
    if args.livre:
        # Cherché dans le nom de fichier (décodé : « %20 » = espace) et le titre.
        from urllib.parse import unquote
        cle = args.livre.lower().strip()
        decouverts = ([(l, r) for l, r in decouverts[0]
                       if l is not None and (cle in unquote(l.rel).lower()
                                             or cle in l.meta.get("titre", "").lower())],
                      decouverts[1])

    if args.refaire_reperage and not args.dry_run:
        oublier_plans(memoire_path)
    if args.dry_run:
        memoire = charger_memoire(memoire_path)
        a_reperer = [l.meta.get("titre", l.rel) for l, r in decouverts[0]
                     if l is not None and not (r.get("pages") or r.get("chapitres"))
                     and (args.refaire_reperage or not plan_connu(memoire, l))]
        if a_reperer:
            print("[REPÉRAGE] à faire au lancement réel (1 petit appel par livre) : "
                  + " ; ".join(a_reperer))
            print("           En attendant, l'aperçu utilise la note « faits concrets ».")
    else:
        from llm_client import call_llm
        reperer(decouverts[0], memoire_path, call_llm)

    extraits, _ = extraire_tous(dossier, data_yaml.get("livres") or [], memoire_path,
                                relire=args.relire_livres, partage=False,
                                decouverts=decouverts)
    a_lire = []
    for e in extraits:
        if e["segments"]:
            unite = "page(s)" if e["fichier"].lower().endswith(".pdf") else "bloc(s)"
            print(f"[LIVRE] {e['titre']} : {len(e['segments'])} {unite}, "
                  f"{e['caracteres']} car."
                  + ("" if e["impose"] else
                     (", pages du repérage" if e["plan"] else f", densité {e['densite']} (sans repérage)")
                     + f", {e['restantes']} restante(s) après cette passe"))
            a_lire.append(e)
        else:
            print(f"[LIVRE] {e['titre']} : rien à lire")
        for a in e["avertissements"]:
            print(f"        ⚠ {a}")
    if not a_lire:
        print(f"[OK] Aucun livre à lire (dossier : {dossier}).")
        return

    today_str = format_date_fr(datetime.now())
    deja_connu = charger_deja_connu()
    signaux = charger_signaux_existants()
    candidats_vus = charger_candidats_vus()

    if args.dry_run:
        prompt = construire_prompt(a_lire[0], today_str, deja_connu, signaux, candidats_vus)
        print("\n--- SYSTEM ---\n" + SYSTEM_PROMPT)
        print("\n--- PROMPT (1er livre) ---\n" + prompt)
        print(f"\n[dry-run] {len(a_lire)} livre(s) seraient lus, ~{len(prompt.split())} mots "
              "pour ce livre. Aucun appel, rien d'écrit, aucune page marquée lue.")
        return

    from llm_client import call_llm, resolve_for_tier
    provider, model = resolve_for_tier(TASK_TIER)
    modele = f"{provider}/{model}"
    print(f"[API] {modele} — {len(a_lire)} livre(s), un appel par livre.", flush=True)

    reussis, nouveaux, echecs = [], [], []
    for e in a_lire:
        prompt = construire_prompt(e, today_str, deja_connu, signaux, candidats_vus)
        print(f"[API] {e['titre']}…", flush=True)
        try:
            texte = call_llm(SYSTEM_PROMPT, prompt, max_tokens=MAX_TOKENS_REPONSE,
                             temperature=0.3, task_tier=TASK_TIER)
        except Exception as ex:
            echecs.append(e["titre"])
            print(f"        ✗ appel échoué : {ex} — pages NON marquées lues, "
                  "retentées à la prochaine passe")
            continue
        if not reponse_valide(texte or ""):
            echecs.append(e["titre"])
            brut = REPONSES_DIR / "archive" / f"livres_reponse_illisible_{datetime.now():%Y%m%d_%H%M%S}.txt"
            brut.parent.mkdir(parents=True, exist_ok=True)
            brut.write_text(texte or "", encoding="utf-8")
            print(f"        ✗ réponse illisible (gardée dans {brut.name}) — pages NON "
                  "marquées lues")
            continue
        blocs, rejetes = [], 0
        for b in blocs_signaux(texte):
            motif = verifier_bloc(b, e)
            if motif:
                rejetes += 1
                titre_b = re.search(r"^titre\s*:\s*(.+)$", b, re.M | re.I)
                print(f"        ✗ rejeté ({motif}) : {titre_b.group(1)[:70] if titre_b else '?'}")
            else:
                blocs.append(b)
        nouveaux.extend(blocs)
        reussis.append(e)
        print(f"        ✓ {len(blocs)} signal(aux)" + (f", {rejetes} rejeté(s)" if rejetes else ""))

    if reussis:
        total = ecrire_reponse(nouveaux, modele) if nouveaux or REPONSE_PATH.exists() else 0
        enregistrer_envois(memoire_path, reussis)
        print(f"\n[OK] {len(nouveaux)} signal(aux) tiré(s) de {len(reussis)} livre(s).")
        if nouveaux or total:
            print(f"     Écrits dans {REPONSE_PATH.relative_to(VAULT_ROOT)} "
                  f"({total} au total en attente d'import).")
            print("     Prochaine étape : « Signaux faibles — 2. Importer les réponses ».")
        print(f"     Pages marquées lues : {memoire_path.relative_to(VAULT_ROOT)}")
    if echecs:
        print(f"\n[AVERTISSEMENT] {len(echecs)} livre(s) en échec : {', '.join(echecs)}")


if __name__ == "__main__":
    main()

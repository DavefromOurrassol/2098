"""
livres_veille.py — Ourrassol 2098
==================================

Livres de la veille signaux faibles, mode « dépose et oublie » (décision
David, 28 septembre 2026). Utilisé par export_prompt_signaux.py.

Principe :
  1. Tout PDF (avec texte), EPUB, .txt ou .md déposé dans le dossier des
     livres (documentation/livres par défaut) est pris en compte, sans
     entrée YAML. Titre et auteur : métadonnées du fichier, sinon son nom.
  2. Le livre est découpé en unités (page pour un PDF, bloc d'environ
     3000 caractères pour un EPUB ou un texte). Chaque unité reçoit une
     note « faits concrets » : années, chiffres, noms propres, mots
     d'expérimentation (premier, pilote, first, trial…), moins les mots de
     spéculation (pourrait, scénario, could…) et les pages de références.
  3. À chaque veille, les meilleures unités PAS ENCORE ENVOYÉES entrent dans
     le prompt, dans la limite d'un budget de caractères. Le livre est ainsi
     parcouru en plusieurs veilles, puis « épuisé ». Mémoire :
     state/livres_veille.json (à supprimer, ou --relire-livres, pour
     repartir de zéro).
  4. Le YAML (section « livres: ») ne sert plus qu'aux exceptions : mettre
     un livre de côté (actif: false), corriger titre/auteur, imposer des
     pages (« pages: "45-80" » PDF) ou des blocs (« chapitres: "3-5" »
     EPUB). Des pages imposées sont envoyées telles quelles à chaque veille.

PDF : nécessite pypdf (pip3 install pypdf). PDF scanné (sans texte) :
détecté et signalé, pas encore lu (OCR à venir).

La note est une règle simple, pas une lecture : une page pertinente sans
chiffres peut être mal classée. La rotation compense en partie.
"""

import json
import logging
import re
import warnings
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

DOSSIER_LIVRES_DEFAUT = "documentation/livres"
EXTENSIONS = (".pdf", ".epub", ".txt", ".md")
MAX_CARACTERES_PAR_LIVRE = 30000     # ~10 pages denses
MAX_CARACTERES_TOTAL = 80000         # tous livres confondus (taille du prompt)
TAILLE_BLOC = 3000                   # découpage EPUB / texte
SEUIL_PAGE_VIDE = 40                 # en dessous : page sans texte
LONGUEUR_MIN_UNITE = 400             # en dessous : unité ignorée (titre, blanc)
SEUIL_NOTE = 3.0                     # note minimale pour être envoyée (calibrée : théorie ≈ 2, étude de cas ≈ 20)


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------

def parse_plage(texte, maximum: int) -> list:
    """« 45-80, 90, 100-102 » -> [45..80, 90, 100..102] (bornés à maximum).
    Vide/None -> tout."""
    if texte is None or str(texte).strip() == "":
        return list(range(1, maximum + 1))
    res = []
    for morceau in str(texte).split(","):
        morceau = morceau.strip()
        if not morceau:
            continue
        m = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", morceau)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            res.extend(range(min(a, b), max(a, b) + 1))
        elif morceau.isdigit():
            res.append(int(morceau))
        else:
            raise ValueError(f"plage illisible : « {morceau} »")
    vus, propres = set(), []
    for n in res:
        if 1 <= n <= maximum and n not in vus:
            vus.add(n)
            propres.append(n)
    return propres


def nettoyer(texte: str) -> str:
    texte = texte.replace("­", "")                       # césures molles
    texte = re.sub(r"(\w)-\n(\w)", r"\1\2", texte)            # mot coupé en fin de ligne
    texte = re.sub(r"[ \t ]+", " ", texte)
    texte = re.sub(r"\s*\n\s*\n\s*", "\n\n", texte)           # paragraphes
    texte = re.sub(r"(?<!\n)\n(?!\n)", " ", texte)            # retours à la ligne internes
    return texte.strip()


def decouper(texte: str, taille: int = TAILLE_BLOC) -> list:
    """Découpe en blocs d'environ `taille` caractères, aux paragraphes."""
    blocs, courant = [], ""
    for para in texte.split("\n\n"):
        if courant and len(courant) + len(para) > taille:
            blocs.append(courant.strip())
            courant = ""
        courant += para + "\n\n"
    if courant.strip():
        blocs.append(courant.strip())
    return blocs


# ---------------------------------------------------------------------------
# Note « faits concrets »
# ---------------------------------------------------------------------------

ANNEE_RE = re.compile(r"\b(?:19[5-9]\d|2[01]\d\d)\b")
ANNEE_COURANTE = __import__("datetime").date.today().year
CHIFFRE_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:%|€|\$|£|km|kg|t\b|mw|gw|kwh|twh|"
                        r"millions?|milliards?|million|billion|thousand)", re.I)
NOM_PROPRE_RE = re.compile(r"(?<=[a-zà-ÿ,;] )[A-Z][a-zà-ÿ]{2,}")
MOTS_FAITS = re.compile(
    r"\b(?:premi(?:er|ère)s?|pour la première fois|pilotes?|expériment\w*|"
    r"prototypes?|start-?ups?|lancée?s?|testée?s?|essais?|laboratoires?|brevets?|"
    r"projet de loi|ordonnance|coopératives?|municipalit\w+|village|communauté|"
    r"first|pilots?|trials?|experiment\w*|launched|tested|patents?|bill\b|"
    r"ordinance|startups?|researchers?|study found|case study|étude de cas)\b", re.I)
MOTS_SPECULATION = re.compile(
    r"\b(?:\w{2,}(?:rait|raient)|scénarios?|hypoth\w+|imaginons|sans doute|"
    r"horizon|à l'avenir|d'ici|could|might|would|will|scenarios?|hypothetical|"
    r"imagine|perhaps|likely|by 20\d\d)\b", re.I)
MOTS_REFERENCES = re.compile(r"\b(?:doi|et al\.|https?://|pp\.|ibid|op\. cit|isbn|vol\.)", re.I)
# Marques de bibliographie / notes de fin (constat du 28 sept 2026 sur les
# vrais PDF de David : les pages de références, pleines d'années, sortaient
# en tête du classement). Au-delà d'une certaine densité, la page vaut 0.
BIBLIO_RE = re.compile(
    r"\(\d{4}[a-z]?\)|\b\d{4}[a-z]?\)[.,]|\bwww\.|\.(?:eu|org|com|int|gov|edu)\b|/[a-z0-9_-]+/|"
    r"\b(?:accessed|retrieved|available at|consulté|disponible sur|journal of|"
    r"proceedings|working paper|press release|report|rapport|publications? office|"
    r"university press|ed(?:s)?\.|in:)|\b\d+\s?\(\d+\)|\b\d+[–-]\d+\.|"
    r"\b(?:doi|et al\.|ibid|op\. cit|isbn)", re.I)
SEUIL_BIBLIO = 6.0          # marques pour 1000 caractères


def noter(texte: str) -> float:
    """Densité de faits concrets pour 1000 caractères (0 si trop court)."""
    n = len(texte)
    if n < LONGUEUR_MIN_UNITE:
        return 0.0
    if len(BIBLIO_RE.findall(texte)) * 1000 / n >= SEUIL_BIBLIO:
        return 0.0                           # bibliographie, notes de fin
    # Pages de tableaux / figures chiffrées (constat du 28 sept 2026 sur le
    # rapport JRC : pages de parts de brevets notées ~58, dont le LLM a tiré
    # des statistiques, pas des signaux) : proportion de chiffres élevée ou
    # nombreuses légendes « Figure n » / « Table n ».
    chiffres = sum(c.isdigit() for c in texte)
    lettres = sum(c.isalpha() for c in texte) or 1
    legendes = len(re.findall(r"\b(?:figure|fig\.|table|tableau|graphique|chart)\s*\d+", texte, re.I))
    tableau = chiffres / lettres > 0.08 or legendes >= 3
    annees = [int(a) for a in ANNEE_RE.findall(texte)]
    passees = sum(1 for a in annees if a <= ANNEE_COURANTE)
    futures = len(annees) - passees          # 2040, 2050… : prospective
    faits = (1.0 * passees
             + min(0.5 * len(CHIFFRE_RE.findall(texte)), 4.0)   # plafonné
             + 1.5 * len(MOTS_FAITS.findall(texte))
             + 0.3 * len(NOM_PROPRE_RE.findall(texte)))
    moins = (1.0 * len(MOTS_SPECULATION.findall(texte)) + 1.0 * futures
             + 2.0 * len(MOTS_REFERENCES.findall(texte)))
    note = max(0.0, faits - moins) * 1000 / n
    if tableau:
        note *= 0.3
    return round(note, 2)


def densite(notes: list) -> str:
    """Appréciation d'un livre d'après ses 10 meilleures unités."""
    top = sorted(notes, reverse=True)[:10]
    if not top:
        return "aucune"
    moy = sum(top) / len(top)
    return "forte" if moy >= 10 else "moyenne" if moy >= 5 else "faible"


# ---------------------------------------------------------------------------
# Lecture des formats -> unités [(ref, texte)]
# ---------------------------------------------------------------------------

def _pypdf():
    try:
        import pypdf
        # pypdf signale chaque police qu'il décode mal (« fontTools is
        # required… ») : sans effet sur le texte utile, ça noyait le journal.
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        warnings.filterwarnings("ignore", module="pypdf")
        return pypdf
    except ImportError:
        return None


def _titre_plausible(t) -> str:
    t = (str(t) if t else "").strip()
    if len(t) < 4 or re.match(r"(?i)^(microsoft word|untitled|sans titre|document\d*)\b", t) \
            or re.search(r"\.(docx?|pdf|indd|tex)$", t, re.I):
        return ""
    return t


class _TexteHTML(HTMLParser):
    BLOCS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
             "blockquote", "section", "tr"}
    IGNORES = {"script", "style", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.morceaux, self.titre, self._ignore, self._dans_titre = [], "", 0, False

    def handle_starttag(self, tag, attrs):
        if tag in self.IGNORES:
            self._ignore += 1
        if tag in self.BLOCS:
            self.morceaux.append("\n\n")
        if tag in ("h1", "h2") and not self.titre:
            self._dans_titre = True

    def handle_endtag(self, tag):
        if tag in self.IGNORES and self._ignore:
            self._ignore -= 1
        if tag in self.BLOCS:
            self.morceaux.append("\n\n")
        if tag in ("h1", "h2"):
            self._dans_titre = False

    def handle_data(self, data):
        if self._ignore:
            return
        self.morceaux.append(data)
        if self._dans_titre:
            self.titre += data


NS_EPUB = {"c": "urn:oasis:names:tc:opendocument:xmlns:container",
           "o": "http://www.idpf.org/2007/opf",
           "dc": "http://purl.org/dc/elements/1.1/"}


def _lire_epub(chemin: Path):
    """-> (meta {titre, auteur, annee}, chapitres [(titre, texte)])."""
    with zipfile.ZipFile(chemin) as z:
        conteneur = ET.fromstring(z.read("META-INF/container.xml"))
        opf_chemin = conteneur.find(".//c:rootfile", NS_EPUB).get("full-path")
        opf = ET.fromstring(z.read(opf_chemin))
        meta = {}
        md = opf.find("o:metadata", NS_EPUB)
        if md is not None:
            for cle, balise in (("titre", "dc:title"), ("auteur", "dc:creator"), ("annee", "dc:date")):
                el = md.find(balise, NS_EPUB)
                if el is not None and (el.text or "").strip():
                    meta[cle] = el.text.strip()[:4] if cle == "annee" else el.text.strip()
        base = PurePosixPath(opf_chemin).parent
        manifest = {it.get("id"): it.get("href") for it in opf.find("o:manifest", NS_EPUB)}
        chapitres = []
        for ref in opf.find("o:spine", NS_EPUB):
            href = manifest.get(ref.get("idref"))
            if not href:
                continue
            nom = str(base / href) if str(base) != "." else href
            try:
                html = z.read(nom).decode("utf-8", errors="replace")
            except KeyError:
                continue
            p = _TexteHTML()
            p.feed(html)
            chapitres.append((" ".join(p.titre.split()) or PurePosixPath(href).stem,
                              nettoyer("".join(p.morceaux))))
    return meta, chapitres


class Livre:
    """Un fichier du dossier, lu à la demande."""

    def __init__(self, chemin: Path, rel: str):
        self.chemin, self.rel = chemin, rel
        self.ext = chemin.suffix.lower()
        self.meta = {}
        self.avertissements = []
        self._unites = None       # [(ref, texte)]
        self._lecteur = None

    def empreinte(self) -> str:
        st = self.chemin.stat()
        return f"{st.st_size}-{int(st.st_mtime)}"

    def lire_meta(self):
        try:
            if self.ext == ".pdf":
                pypdf = _pypdf()
                if pypdf:
                    self._lecteur = pypdf.PdfReader(str(self.chemin))
                    info = self._lecteur.metadata or {}
                    self.meta["titre"] = _titre_plausible(info.get("/Title"))
                    self.meta["auteur"] = (str(info.get("/Author") or "")).strip()
            elif self.ext == ".epub":
                self.meta.update(_lire_epub(self.chemin)[0])
        except Exception as e:
            self.avertissements.append(f"métadonnées illisibles : {e}")
        if not self.meta.get("titre"):
            from urllib.parse import unquote
            self.meta["titre"] = re.sub(r"[_]+", " ", unquote(self.chemin.stem)).strip()
        return self.meta

    def unites(self) -> list:
        """[(ref, texte)] pour tout le livre (numérotées à partir de 1)."""
        if self._unites is not None:
            return self._unites
        u = []
        if self.ext == ".pdf":
            pypdf = _pypdf()
            if pypdf is None:
                raise RuntimeError("pypdf absent : lance « pip3 install pypdf »")
            lecteur = self._lecteur or pypdf.PdfReader(str(self.chemin))
            n = len(lecteur.pages)
            try:
                labels = list(lecteur.page_labels)
            except Exception:
                labels = []
            if len(labels) != n:
                labels = [str(i) for i in range(1, n + 1)]
            for i, page in enumerate(lecteur.pages):
                brut = page.extract_text() or ""
                u.append((f"p. {labels[i]}",
                          nettoyer(brut) if len(brut.strip()) >= SEUIL_PAGE_VIDE else ""))
        elif self.ext == ".epub":
            _, chapitres = _lire_epub(self.chemin)
            for k, (titre, texte) in enumerate(chapitres, 1):
                blocs = decouper(texte)
                for j, b in enumerate(blocs, 1):
                    suffixe = f", partie {j}/{len(blocs)}" if len(blocs) > 1 else ""
                    u.append((f"chap. {k} « {titre[:50]} »{suffixe}", b))
        else:
            for j, b in enumerate(decouper(nettoyer(self.chemin.read_text(encoding="utf-8"))), 1):
                u.append((f"§ {j}", b))
        self._unites = u
        return u

    def scanne(self) -> bool:
        u = self.unites()
        return self.ext == ".pdf" and bool(u) and all(not t for _, t in u)


# ---------------------------------------------------------------------------
# Découverte : dossier + exceptions du YAML
# ---------------------------------------------------------------------------

def dossier_livres(data_yaml: dict, vault_root: Path) -> Path:
    return vault_root / (data_yaml.get("dossier_livres") or DOSSIER_LIVRES_DEFAUT)


def decouvrir(dossier: Path, livres_yaml: list):
    """
    Renvoie (livres, listes_seulement) :
      livres : [(Livre, reglages)] pour chaque fichier du dossier non mis de
               côté ; reglages = entrée YAML correspondante (ou {}) ;
      listes_seulement : entrées YAML actives sans « fichier: » (livres à
               joindre à la main, ancien fonctionnement).
    """
    par_fichier, listes = {}, []
    for b in livres_yaml or []:
        if not isinstance(b, dict):
            continue
        if b.get("fichier"):
            par_fichier[str(b["fichier"])] = b
        elif b.get("titre") and b.get("actif") is not False:
            listes.append(b)
    res = []
    if dossier.exists():
        for p in sorted(dossier.rglob("*")):
            if p.suffix.lower() not in EXTENSIONS or p.name.startswith("."):
                continue
            rel = str(p.relative_to(dossier))
            reglages = par_fichier.get(rel, {})
            if reglages.get("actif") is False:
                continue
            livre = Livre(p, rel)
            livre.lire_meta()
            for cle in ("titre", "auteur", "annee"):
                if reglages.get(cle):
                    livre.meta[cle] = str(reglages[cle])
            res.append((livre, reglages))
    for rel, b in par_fichier.items():
        if b.get("actif") is not False and not (dossier / rel).exists():
            res.append((None, dict(b, _introuvable=str(dossier / rel))))
    return res, listes


# ---------------------------------------------------------------------------
# Mémoire des unités déjà envoyées
# ---------------------------------------------------------------------------

def charger_memoire(chemin: Path) -> dict:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def enregistrer_envois(chemin: Path, extraits: list) -> None:
    """Ajoute les unités envoyées dans ce prompt (appelé seulement quand le
    prompt est réellement écrit)."""
    memoire = charger_memoire(chemin)
    for e in extraits:
        if not e.get("envoyees"):
            continue
        m = memoire.setdefault(e["fichier"], {})
        if m.get("empreinte") != e["empreinte"]:
            m.clear()
            m["empreinte"] = e["empreinte"]
        # Le titre sert aussi à l'import (vérification des sources « livre: »).
        m["titre"] = e["titre"]
        m["total"] = e["total"]
        if not e.get("impose"):       # pages imposées : pas de rotation
            m["envoyees"] = sorted(set(m.get("envoyees", [])) | set(e["envoyees"]))
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(memoire, ensure_ascii=False, indent=2), encoding="utf-8")


def plan_connu(memoire: dict, livre) -> bool:
    m = memoire.get(livre.rel, {})
    return m.get("empreinte") == livre.empreinte() and m.get("plan") is not None


def enregistrer_plan(chemin: Path, livre, plan: list) -> None:
    """Mémorise les pages retenues par le repérage LLM d'un livre (une fois
    pour toutes, tant que le fichier ne change pas)."""
    memoire = charger_memoire(chemin)
    m = memoire.setdefault(livre.rel, {})
    if m.get("empreinte") != livre.empreinte():
        m.clear()
        m["empreinte"] = livre.empreinte()
    m["titre"] = livre.meta.get("titre", livre.rel)
    m["total"] = len(livre.unites())
    m["plan"] = sorted(set(plan))
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(memoire, ensure_ascii=False, indent=2), encoding="utf-8")


def oublier_plans(chemin: Path) -> None:
    memoire = charger_memoire(chemin)
    for m in memoire.values():
        if isinstance(m, dict):
            m.pop("plan", None)
    if memoire:
        chemin.write_text(json.dumps(memoire, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Sélection pour le prompt
# ---------------------------------------------------------------------------

def _dict_extrait(livre, reglages) -> dict:
    meta = livre.meta if livre else {}
    return {"titre": meta.get("titre") or reglages.get("titre") or "?",
            "auteur": meta.get("auteur") or reglages.get("auteur") or "",
            "annee": meta.get("annee") or reglages.get("annee") or "",
            "note": reglages.get("note") or "",
            "fichier": livre.rel if livre else reglages.get("fichier", ""),
            "segments": [], "envoyees": [], "avertissements": list(livre.avertissements) if livre else [],
            "caracteres": 0, "impose": False, "empreinte": "", "total": 0,
            "restantes": 0, "densite": "", "plan": False}


def selectionner(livre, reglages: dict, memoire: dict, budget: int,
                 relire: bool = False) -> dict:
    e = _dict_extrait(livre, reglages)
    if livre is None:
        e["avertissements"].append(f"fichier introuvable : {reglages.get('_introuvable')}")
        return e
    try:
        unites = livre.unites()
    except Exception as ex:
        e["avertissements"].append(f"lecture impossible : {ex}")
        return e
    e["empreinte"], e["total"] = livre.empreinte(), len(unites)
    if livre.scanne():
        e["avertissements"].append("PDF scanné (aucun texte) : pas encore exploitable (OCR à venir)")
        return e
    notes = [noter(t) for _, t in unites]
    e["densite"] = densite(notes)

    plage = reglages.get("pages") if livre.ext == ".pdf" else reglages.get("chapitres")
    if plage:
        # Choix imposé par David : envoyé tel quel, sans rotation.
        e["impose"] = True
        try:
            numeros = parse_plage(plage, len(unites))
        except ValueError as ex:
            e["avertissements"].append(str(ex))
            return e
        if livre.ext == ".epub":
            # « chapitres » : numéros de chapitre -> toutes leurs parties.
            numeros = [i for i, (ref, _) in enumerate(unites, 1)
                       if int(re.match(r"chap\. (\d+)", ref).group(1)) in set(numeros)]
    else:
        m = memoire.get(livre.rel, {})
        a_jour = m.get("empreinte") == e["empreinte"]
        deja = set(m.get("envoyees", [])) if a_jour and not relire else set()
        plan = m.get("plan") if a_jour else None
        if plan is not None:
            # Pages retenues par le repérage LLM (veille_livres_api.py),
            # lues dans l'ordre du livre ; la note n'est plus un filtre.
            e["plan"] = True
            candidats = [i for i in plan if 1 <= i <= len(unites)
                         and i not in deja and unites[i - 1][1]]
            numeros = candidats
        else:
            candidats = [i for i in range(1, len(unites) + 1)
                         if i not in deja and notes[i - 1] >= SEUIL_NOTE]
            numeros = sorted(candidats, key=lambda i: -notes[i - 1])
        e["restantes"] = len(candidats)
        if not candidats:
            if plan is not None and not plan:
                e["avertissements"].append("repérage : aucune page utile dans ce livre")
            elif deja:
                e["avertissements"].append("épuisé : toutes les pages utiles ont déjà "
                                           "été lues (--relire-livres pour recommencer)")
            else:
                e["avertissements"].append("aucune page assez riche en faits concrets")
            return e

    choisis, total = [], 0
    for i in numeros:
        texte = unites[i - 1][1]
        if not texte:
            continue
        if total + len(texte) > budget:
            if e["impose"] and not choisis:
                texte = texte[:budget].rsplit(" ", 1)[0] + " […]"
            else:
                if e["impose"]:
                    e["avertissements"].append(
                        f"pages imposées coupées au budget de {budget} caractères")
                break
        choisis.append((i, texte))
        total += len(texte)
    choisis.sort()                        # ordre du livre dans le prompt
    e["segments"] = [(unites[i - 1][0], texte) for i, texte in choisis]
    e["envoyees"] = [i for i, _ in choisis]
    e["caracteres"] = total
    if not e["impose"]:
        e["restantes"] -= len(choisis)
    return e


def extraire_tous(dossier: Path, livres_yaml: list, memoire_path: Path,
                  relire: bool = False, partage: bool = True, decouverts=None):
    """-> (extraits, listes_seulement). partage=True : budget total partagé
    entre les livres (un seul prompt) ; False : budget plein par livre (un
    appel API par livre, veille_livres_api.py)."""
    livres, listes = decouverts or decouvrir(dossier, livres_yaml)
    memoire = charger_memoire(memoire_path)
    nb = max(1, sum(1 for l, _ in livres if l is not None))
    budget = (min(MAX_CARACTERES_PAR_LIVRE, MAX_CARACTERES_TOTAL // nb)
              if partage else MAX_CARACTERES_PAR_LIVRE)
    extraits = []
    for livre, reglages in livres:
        b = int(reglages.get("max_caracteres") or budget)
        extraits.append(selectionner(livre, reglages, memoire, b, relire=relire))
    return extraits, listes


def lister_livres(dossier: Path, livres_yaml: list, memoire_path: Path) -> str:
    """Texte pour --lister-livres : pour chaque fichier, taille, densité de
    faits, avancement de la lecture et meilleures pages."""
    L = [f"Dossier des livres : {dossier}", ""]
    if not dossier.exists():
        L.append("(dossier absent : crée-le et déposes-y tes PDF/EPUB)")
        return "\n".join(L)
    livres, listes = decouvrir(dossier, livres_yaml)
    memoire = charger_memoire(memoire_path)
    if not livres:
        L.append("(aucun PDF/EPUB dans le dossier)")
    for livre, reglages in livres:
        if livre is None:
            L.append(f"■ {reglages.get('fichier')} : déclaré dans le YAML mais introuvable")
            L.append("")
            continue
        titre = livre.meta.get("titre", "?")
        auteur = f" — {livre.meta['auteur']}" if livre.meta.get("auteur") else ""
        L.append(f"■ {livre.rel}")
        L.append(f"   {titre}{auteur}")
        try:
            unites = livre.unites()
        except Exception as ex:
            L.append(f"   lecture impossible : {ex}")
            L.append("")
            continue
        unite = "pages" if livre.ext == ".pdf" else "blocs"
        if livre.scanne():
            L.append(f"   {len(unites)} {unite} — ⚠ PDF scanné, pas encore exploitable")
            L.append("")
            continue
        notes = [noter(t) for _, t in unites]
        utiles = [i for i, n in enumerate(notes, 1) if n >= SEUIL_NOTE]
        m = memoire.get(livre.rel, {})
        deja = set(m.get("envoyees", [])) if m.get("empreinte") == livre.empreinte() else set()
        plan = m.get("plan") if m.get("empreinte") == livre.empreinte() else None
        if plan is not None:
            L.append(f"   {len(unites)} {unite} — repérage LLM : {len(plan)} {unite} retenue(s), "
                     f"{len(deja & set(plan))} déjà lue(s)")
        else:
            L.append(f"   {len(unites)} {unite}, pas encore repéré — densité de faits : "
                     f"{densite(notes)} ({len(utiles)} {unite} utiles, "
                     f"{len(deja & set(utiles))} déjà lues)")
        if reglages.get("pages") or reglages.get("chapitres"):
            L.append(f"   choix imposé dans le YAML : {reglages.get('pages') or reglages.get('chapitres')}")
        if plan is not None:
            top = [i for i in plan if i not in deja][:5]
            titre_liste = "   prochaines pages du repérage :"
        else:
            top = sorted(sorted(utiles, key=lambda i: -notes[i - 1])[:5])
            titre_liste = "   meilleures (note « faits concrets ») :"
        if top:
            L.append(titre_liste)
            for i in top:
                debut = " ".join(unites[i - 1][1].split())[:90]
                L.append(f"     {unites[i - 1][0]} ({notes[i - 1]}) « {debut}… »")
        L.append("")
    for b in listes:
        L.append(f"■ (sans fichier) {b['titre']} : listé seulement, à joindre à la main")
    return "\n".join(L)

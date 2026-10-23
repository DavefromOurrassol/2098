#!/usr/bin/env python3
"""
et_si_exhaustif.py — Ourrassol 2098 (S27, passe exhaustive, 11 octobre 2026)
============================================================================

Complète la lecture IA du simulateur « et si ? » (simuler_et_si.py) : au lieu
de ne montrer à l'IA qu'une partie des entités (les plus influentes et les
directement concernées) avec des plafonds de propositions, la passe exhaustive
relit TOUTES les instances du scénario et tous les événements datés après
l'hypothèse, par lots, et demande pour chaque fiche : « cet élément change-t-il
quelque chose pour elle, et quoi ? ».

Réponses possibles, par fiche :
  - aucun changement ;
  - trajectoire à changer (instances) ;
  - relation nouvelle ou rompue (instances) ;
  - texte à revoir : le rôle ou la description deviendrait faux sans qu'un
    champ change (instances et événements).

v6 : chaque changement a un NIVEAU, selon un critère unique valable pour toute
hypothèse : « si on laisse la fiche telle quelle, un lecteur qui connaît
l'élément y trouve-t-il une affirmation fausse ? »
  - obligatoire : oui, la fiche devient fausse ou impossible ;
  - possible : conséquence plausible, la fiche reste vraie sans elle.
Les contrôles mécaniques ne suppriment plus une proposition douteuse : ils la
font descendre d'« obligatoire » à « possible », motif affiché. Seules les
réponses mal formées (entité inconnue, valeur invalide, contresens sur l'axe)
sont rejetées. Rien n'est perdu ; la liste obligatoire reste courte.

Les propositions passent les mêmes contrôles que la lecture IA du simulateur
(verifier_consequences), SANS plafond de nombre. Les événements antérieurs à
la date de l'hypothèse ne sont pas relus : le passé ne change pas.

Lecture seule : rien n'est écrit dans le vault, seulement le cache
generator/state/et_si_exhaustif.json.

USAGE
-----
    python3 generator/et_si_exhaustif.py --id invasion_bresil_2029 --scenario fortress_world --estimer
    python3 generator/et_si_exhaustif.py --id invasion_bresil_2029 --scenario fortress_world
    python3 generator/et_si_exhaustif.py --id invasion_bresil_2029 --scenario fortress_world --refaire
    python3 generator/et_si_exhaustif.py --id invasion_bresil_2029 --json
Sans --scenario : tous les scénarios de l'hypothèse.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE = SCRIPT_DIR / "state" / "et_si_exhaustif.json"
VERSION_PROMPT = "4"        # changer cette valeur fait relire toutes les fiches
# v9.5 (11 oct) : la contre-lecture classe le fait invoqué (matériel / tendance) ; le code
# rétrograde « choc amorti + tendance » ; elle voit le lieu ou la date de chaque fiche.
# v9.4 (11 oct) : contre-lecture v3 (le passé ne change pas ; un choc amorti ne contredit pas un
# état tardif, sauf faits matériels) avec la part résiduelle calculée ; verdicts en cache un par un.
# v9.4 (11 oct, rejeu) : un lien territoire hors carte est valable si la fiche est localisée
# dans un lieu nommé par l'hypothèse (description, contraintes) ; cas Genève.
# v9 (11 oct) : possibles regroupés par fiche ; les 20 plus importants choisis par un appel IA
# (en cache), les autres sur une ligne ; tri mécanique seulement en repli.
# v8 (11 oct, aucun appel) : possibles triés par score ; 20 détaillés, les autres sur une ligne.
# v7 (11 oct, cache des lots valable) : seule une disparition peut être une trajectoire obligatoire ;
# contre-lecture des obligatoires (question fermée : incompatible ou non ?), cache séparé.
# v6 (11 oct) : niveaux obligatoire / possible ; ne rien inventer sur l'élément (zones plus
# ou moins touchées, dates) ; les dates et l'existence des autres entités ne changent pas.
# v2 (11 oct) : lien causal direct obligatoire, conditionnel écarté, « texte » réservé
# aux phrases qui deviennent fausses, extrait introuvable écarté, axe des trajectoires.
LIENS = {"territoire", "relation", "variable"}
import re as _re
_HYPOTHETIQUE = _re.compile(r"\b(pourrai[ts]?|pourraient|pourront|potentiel\w*|eventuel\w*|"
                            r"susceptibles?|probablement|peut[- ]etre|risquer?(?:ait|aient)? de|"
                            r"risque de|semble(?:nt)?)\b")
_RENFORCE = _re.compile(r"\b(renforc\w*|consolid\w*|accro\w*|augment\w*|etend\w*|elargi\w*|propuls\w*)\b")
TRAJ_AFFAIBLISSEMENT = {"mature", "déclinant", "résiduel"}
# v3 (11 oct) : lot coupé relancé en deux moitiés ; lien « variable » seulement si l'effet
# atteint SEUIL_VARIABLE points ; un « texte » qui ne fait qu'élargir un rôle est écarté.
SEUIL_VARIABLE = 2.0
# v4 (11 oct, sans changer les consignes : le cache reste valable) : fiches sans réponse
# redemandées une fois ; un « texte » qui ne fait qu'atténuer un rôle est écarté, sauf si
# la raison dit que quelque chose devient faux.
# v5 (11 oct, cache toujours valable) : le prompt se termine par la liste des fiches du lot ;
# les réponses sur des fiches hors du lot (déjà jugées dans leur propre lot) sont comptées
# à part et ne gonflent plus les propositions écartées.
_ATTENUE = _re.compile(r"\b(moins|redui\w*|reduction|diminu\w*|affaibli\w*|attenu\w*|marginalis\w*|"
                       r"recentr\w*|evolu\w*|modifi\w*)\b")
_FAUX = _re.compile(r"(n'est plus|ne sont plus|ne peut plus|ne peuvent plus|n'existe plus|plus aucun|"
                    r"obsolete|caduc|caduque|faux|fausse|supprim\w*|disparu\w*|elimin\w*|perd\w* son|"
                    r"perd\w* le|perd\w* la|perd\w* ses|perte de)")
MAX_TOKENS_LOT = 8000
_AMPLIFIE = _re.compile(r"\b(renforc\w*|consolid\w*|accru\w*|accroi\w*|augment\w*|etend\w*|etendu\w*|"
                        r"elargi\w*|extension|desormais|davantage|propuls\w*|amplifi\w*)\b")
TAILLE_LOT = 15
# v9.6 (23 oct, aucun appel, rejouable au banc) : un « texte » obligatoire qui conteste seulement une
# date de la fiche (« trop tardive », « dès 2043, et non 2044 ») que l'élément ne fixe pas descend en
# possible. Pas si la justification invoque un fait matériel (destruction, « n'existe plus »).
_ANNEE = _re.compile(r"\b(1[89]\d\d|2[01]\d\d)\b")
_DATE_CONTESTEE = _re.compile(r"(trop tard\w*|bien avant|plus tot|date\w* (?:est |sont )?"
                              r"(?:fausse|incorrecte|erronee|impossible)|la date (?:de |du )?(?:1[89]|2[01])\d\d)")
_MATERIEL = _re.compile(r"\b(detrui\w*|destruction|n'existe plus|aneanti\w*|rase\w*)\b")


def annees_hypothese(hyp):
    """Années que l'élément fixe lui-même (nom, description, contraintes, date)."""
    texte = " ".join([str(hyp.get("nom") or ""), str(hyp.get("description") or "")]
                     + [str(c) for c in hyp.get("contraintes") or []])
    annees = {int(a) for a in _ANNEE.findall(texte)}
    if _annee(hyp.get("date")) is not None:
        annees.add(int(_annee(hyp.get("date"))))
    return annees


def _date_contestee(extrait, juge, annees_hyp):
    """`juge` déjà plié. Vrai si la justification conteste une année de l'extrait
    que l'élément ne fixe pas, sans invoquer de fait matériel."""
    propres = {int(a) for a in _ANNEE.findall(extrait)} - set(annees_hyp)
    if not propres or _MATERIEL.search(juge):
        return False
    for y in propres:
        if str(y) not in juge:
            continue
        if _DATE_CONTESTEE.search(juge) or _re.search(rf"\b(?:des|et non|non pas)\s+(?:en\s+)?{y}\b", juge):
            return True
    return False
# Coût indicatif (Mistral Large 3, $ par million de jetons) et jetons de sortie par fiche.
PRIX_ENTREE, PRIX_SORTIE = 0.50, 1.50
SORTIE_PAR_FICHE = 120
CHARS_PAR_JETON = 3.5


# ---------------------------------------------------------------------------
# Préparation des fiches
# ---------------------------------------------------------------------------

def _court(texte, n):
    texte = " ".join(str(texte or "").split())
    return texte if len(texte) <= n else texte[:n].rsplit(" ", 1)[0] + "…"


def _fiche_instance(i):
    zone = (i.get("localisation") or {}).get("zone") or "transnationale"
    allies = ", ".join(i.get("alliances") or []) or "—"
    rivaux = ", ".join(i.get("oppositions") or []) or "—"
    return (f"[instance] {i['slug']} | {i.get('name')} | trajectoire {i.get('trajectoire')} | zone {zone}\n"
            f"  rôle : {_court(i.get('role_dans_scenario'), 320)}\n"
            f"  alliés : {_court(allies, 200)} | rivaux : {_court(rivaux, 200)}")


def _fiche_evenement(e):
    return (f"[événement] {e['slug']} | {e.get('name')} | {e.get('date_label') or e.get('date')}\n"
            f"  description : {_court(e.get('description'), 320)}\n"
            f"  conséquences : {_court(e.get('consequences'), 200)}")


def _texte_complet(f):
    """Texte où l'extrait cité par l'IA doit se retrouver (contrôle anti-invention)."""
    if f["genre"] == "instance":
        i = f["data"]
        champs = [i.get("name"), i.get("role_dans_scenario"), i.get("responsabilites"),
                  i.get("description_journalistique"), i.get("tensions_narratives"),
                  i.get("signes_distinctifs"), (i.get("localisation") or {}).get("lieu")]
    else:
        e = f["data"]
        champs = [e.get("name"), e.get("description"), e.get("consequences"), e.get("realisation")]
    return " ".join(str(c or "") for c in champs)


def charger_fiches(hyp, sc):
    from loader import load_instances_for_scenario, load_event_instances_for_scenario
    instances = load_instances_for_scenario(sc)
    evenements = [e for e in load_event_instances_for_scenario(sc)
                  if _annee(e.get("date")) is not None and _annee(e.get("date")) >= hyp["date"]
                  and e.get("archetype") != hyp["id"]]
    fiches = [{"slug": i["slug"], "genre": "instance", "data": i, "texte": _fiche_instance(i)}
              for i in instances]
    fiches += [{"slug": e["slug"], "genre": "evenement", "data": e, "texte": _fiche_evenement(e)}
               for e in evenements]
    return fiches, instances


def _annee(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def lots(fiches, taille=TAILLE_LOT):
    return [fiches[k:k + taille] for k in range(0, len(fiches), taille)]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def territoires_touches(hyp, sc, lecture):
    pays = [op.get("pays") for op in (hyp.get("geographie") or {}).get(sc) or [] if op.get("pays")]
    if lecture and not lecture.get("erreur"):
        pays += [g.get("pays") for g in lecture.get("geographie") or [] if g.get("pays")]
    return list(dict.fromkeys(p for p in pays if p))


def variables_hypothese(hyp):
    """Variables que l'hypothèse touche elle-même (hors propagation par la matrice)."""
    return {i.get("variable") for i in hyp.get("impacts") or [] if i.get("variable")}


def contexte_commun(hyp, sc, effets, lecture, instances):
    import simuler_et_si as s
    from loader import load_scenario
    scen = load_scenario(sc)
    propres = variables_hypothese(hyp)
    lignes_effets = [f"- {e['variable']} : {e['effet']:+.1f} point(s)"
                     + (" (touchée par l'élément)" if e["variable"] in propres else " (par propagation, effet indirect)")
                     for e in (effets or [])[:8]] or ["- (aucun effet chiffré notable)"]
    contraintes = ""
    if hyp.get("contraintes"):
        contraintes = ("FAITS À RESPECTER :\n" + "\n".join(f"- {c}" for c in hyp["contraintes"]) + "\n")
    deja = []
    if lecture and not lecture.get("erreur"):
        if lecture.get("lecture"):
            deja.append(f"Lecture générale déjà retenue : {lecture['lecture']}")
        for t in lecture.get("trajectoires") or []:
            deja.append(f"- déjà retenu : {t['instance']} {t['avant']} → {t['apres']}")
        for r in lecture.get("relations") or []:
            deja.append(f"- déjà retenu : {r['type']} {r['action']} {r['a']} / {r['b']}")
    # v2 : territoires et entités directement touchés, pour juger le « lien ».
    pays = territoires_touches(hyp, sc, lecture)
    deja.append("Territoires touchés : " + (", ".join(pays) if pays
                else "aucun territoire précis (élément sans changement de carte)"))
    roster = "\n".join(f"- {i['slug']} | {i.get('name')}" for i in instances)
    return f"""Monde fictif Ourrassol 2098, scénario « {scen.get('name', sc)} » ({sc}).

LOGIQUE DU SCÉNARIO :
{_court(scen.get('summary'), 700)}
{_court(scen.get('system_logic'), 700)}

ÉLÉMENT PERTURBATEUR (pas encore dans le lore) :
{hyp['nom']} — apparition en {hyp['date']:g}.
{_court(hyp['description'], 700)}
{contraintes}Effets chiffrés simulés en fin de période (niveau 100 = crise) :
{chr(10).join(lignes_effets)}

{chr(10).join(deja) if deja else "(aucune lecture générale retenue)"}

TOUTES LES ENTITÉS DU SCÉNARIO (cibles possibles d'une relation) :
{roster}
"""


CONSIGNE = """TÂCHE : pour CHAQUE fiche ci-dessous, juge ce que l'élément perturbateur change pour elle
dans CE scénario, et donne à chaque changement un NIVEAU :
- "obligatoire" : sans ce changement, la fiche devient FAUSSE ou IMPOSSIBLE une fois l'élément ajouté
  au lore (une phrase contredite, une entité qui ne peut plus exister ou garder sa trajectoire, une
  alliance devenue impossible). "contredit" = le fait de l'élément qui la rend fausse.
- "possible" : conséquence plausible, mais la fiche reste vraie sans elle (une entité qui gagne ou
  perd du poids, un rôle qui s'élargit, une alliance qui devient probable).
Test unique : « si on laisse la fiche telle quelle, un lecteur qui connaît l'élément y trouve-t-il une
affirmation fausse ? » Oui → obligatoire. Non → possible, ou aucun changement.
Une fiche sans rapport avec l'élément : changements vides.

Chaque changement nomme son LIEN DIRECT avec l'élément :
- "territoire" : la fiche est localisée dans un territoire touché, ou y agit explicitement ;
- "relation" : la fiche est alliée ou rivale d'une entité directement touchée (nomme-la) ;
- "variable" : la fiche dépend directement d'une variable dont l'effet chiffré atteint au moins
  {seuil} points (nomme-la).

Règles de fond :
- N'invente aucun fait sur l'élément : utilise seulement sa description, les faits à respecter, les
  effets chiffrés et les territoires touchés. Si aucun territoire précis n'est touché, tu ne décides
  pas quelles zones le sont plus ou moins.
- Les dates et l'existence des AUTRES entités du lore ne changent pas. Un événement daté après
  l'élément n'est faux que si l'élément rend impossible ce qu'il raconte.
- Écris des faits, au présent ou au passé : jamais « pourrait », « potentiellement », « risque de ».

Changements possibles :
- "trajectoire" (instances seulement) : axe ORDONNÉ émergent → marginal → ascendant → dominant
  → mature → déclinant → résiduel → transformé → disparu → historique → mythifié. Une entité qui se
  RENFORCE avance vers ascendant ou dominant, jamais vers mature, déclinant ou résiduel (ce sont des
  affaiblissements). Une entité déjà dominante qui se renforce ne change pas. Ne propose qu'une valeur
  différente de l'actuelle, écrite exactement ainsi, accents compris. Une entité qui monte parce que
  le monde se durcit en général est au plus « possible ».
- "relation" (instances seulement) : alliance ou opposition, "nouvelle" ou "rompue", avec une autre
  entité de la liste complète ci-dessus (slug exact, finissant par _{sc}). Seulement si l'élément CRÉE
  ou ROMPT ce lien : une entité déjà hostile aux blocs ne devient pas « nouvellement opposée » à un bloc.
- "texte" (instances et événements) : une phrase de la fiche est à revoir. Obligatoire si elle
  devient FAUSSE ; un rôle qui s'élargit ou prend plus de poids reste vrai (possible au plus).
  N'invente pas de nouveaux faits sur la fiche.
  "extrait" = la phrase de la fiche, recopiée MOT POUR MOT ; "contredit" = le fait qui la rend fausse.
Une fiche peut avoir plusieurs changements, ou aucun.

Réponds UNIQUEMENT en JSON, une entrée par fiche lue, format exact :
{{"fiches": [
  {{"slug": "slug_de_la_fiche", "changements": []}},
  {{"slug": "...", "changements": [
     {{"type": "trajectoire", "niveau": "obligatoire | possible", "apres": "déclinant", "lien": "territoire",
       "lien_detail": "...", "contredit": "...", "raison": "une phrase"}},
     {{"type": "relation", "niveau": "obligatoire | possible", "cible": "slug_{sc}",
       "relation": "alliance | opposition", "action": "nouvelle | rompue", "lien": "relation",
       "lien_detail": "...", "contredit": "...", "raison": "une phrase"}},
     {{"type": "texte", "niveau": "obligatoire | possible", "extrait": "phrase recopiée", "contredit": "...",
       "lien": "territoire", "lien_detail": "...", "raison": "une phrase"}}
  ]}}
]}}

FICHES À LIRE :
"""


def prompt_lot(commun, lot, sc):
    return (commun + "\n" + CONSIGNE.format(sc=sc, seuil=f"{SEUIL_VARIABLE:g}") + "\n\n".join(f["texte"] for f in lot)
            + f"\n\nRéponds pour ces {len(lot)} fiche(s), et seulement pour elles (une entrée par fiche, "
            "changements vides si rien ne change) : " + ", ".join(f["slug"] for f in lot))


# ---------------------------------------------------------------------------
# Contrôle des réponses
# ---------------------------------------------------------------------------

def _plie(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).split())


NIVEAUX = ("obligatoire", "possible")
CLES_RES = ("obligatoire", "possible", "rejetees", "corrigees", "non_lues", "hors_lot")


def _vide():
    return {"trajectoires": [], "relations": [], "textes": []}


_MOTS_COMMUNS = {"les", "des", "une", "dans", "pour", "avec", "sans", "leur", "leurs", "cette", "apres",
                 "avant", "depuis", "aucune", "aucun", "seules", "seule", "elle", "elles", "ils", "mars",
                 "avril", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
                 "janvier", "fevrier", "mai", "etats", "unis", "rien", "entre", "environ", "quelques",
                 "vague", "villes", "ville", "pandemie", "conflit", "invasion", "destruction", "percee",
                 "raisonne", "l'energie"}
# Mots à majuscule seulement parce qu'ils ouvrent une phrase : écartés ; seuls restent des lieux.


def lieux_nommes(hyp):
    """v9.4 : lieux propres cités par l'hypothèse (mots à majuscule de son nom, de sa
    description et de ses contraintes), pliés. Sert au lien territoire hors carte."""
    texte = " ".join([str(hyp.get("nom") or ""), str(hyp.get("description") or "")]
                     + [str(c) for c in hyp.get("contraintes") or []])
    mots = _re.findall(r"\b[A-ZÀ-Ý][\wÀ-ÿ'-]{3,}", texte)
    return {_plie(m) for m in mots} - _MOTS_COMMUNS


def _fiche_dans_lieu(f, lieux):
    loc = (f["data"].get("localisation") or {}) if f["genre"] == "instance" else {}
    texte = _plie(" ".join(str(loc.get(k) or "") for k in ("lieu", "zone")).replace("_", " "))
    return any(_re.search(r"\b" + _re.escape(l) + r"\b", texte) for l in lieux)


def verifier_lot(brut, lot, by_inst, by_zone, effets=None, territoires=None, variables_hyp=None, lieux=None,
                 annees_hyp=None):
    """Contrôle d'un lot. v6 : un changement douteux descend d'« obligatoire » à « possible »
    (motif affiché) ; seules les réponses mal formées sont rejetées. Les trajectoires et
    relations passent ensuite verifier_consequences du simulateur, SANS plafond."""
    import simuler_et_si as s
    par_slug = {f["slug"]: f for f in lot}
    effet_var = {e["variable"]: abs(e.get("effet") or 0) for e in effets or []}
    variables_hyp = set(variables_hyp or ())
    brut_niv = {n: {"trajectoires": [], "relations": [], "textes": []} for n in NIVEAUX}
    rejetees, hors_lot, vues = [], [], set()
    for entree in (brut.get("fiches") or []) if isinstance(brut, dict) else []:
        if not isinstance(entree, dict):
            continue
        slug = entree.get("slug")
        f = par_slug.get(slug)
        if not f:
            hors_lot.append(str(slug))
            continue
        vues.add(slug)
        for c in entree.get("changements") or []:
            if not isinstance(c, dict):
                continue
            typ = str(c.get("type") or "").strip().lower()
            if typ not in ("trajectoire", "relation", "texte"):
                rejetees.append(f"{slug} : type de changement {c.get('type')!r} inconnu")
                continue
            if typ in ("trajectoire", "relation") and f["genre"] != "instance":
                rejetees.append(f"{slug} : {typ} proposé(e) pour un événement")
                continue
            niveau = "obligatoire" if _plie(c.get("niveau")).startswith("oblig") else "possible"
            raison = " ".join(str(c.get("raison") or "").split())
            lien = str(c.get("lien") or "").strip().lower()
            detail = " ".join(str(c.get("lien_detail") or "").split())
            contredit = " ".join(str(c.get("contredit") or "").split())
            motifs = []
            if lien not in LIENS or not detail:
                motifs.append("sans lien direct nommé")
            if _HYPOTHETIQUE.search(_plie(f"{raison} {detail} {contredit}")):
                motifs.append("au conditionnel")
            if lien == "territoire" and not territoires and not _fiche_dans_lieu(f, lieux or ()):
                # v9.4 : sauf si la fiche est localisée dans un lieu nommé par l'hypothèse.
                motifs.append("lien territoire alors qu'aucun territoire précis n'est touché")
            if lien == "variable":
                nommees = [v for v in effet_var if v in detail or v.replace("_", " ") in _plie(detail)]
                if not nommees or max(effet_var[v] for v in nommees) < SEUIL_VARIABLE:
                    motifs.append(f"lien variable sous {SEUIL_VARIABLE:g} points")
                elif variables_hyp and not any(v in variables_hyp for v in nommees):
                    motifs.append("variable touchée seulement par propagation")
            if niveau == "obligatoire" and not contredit:
                motifs.append("aucun fait contredit nommé")
            if detail:
                raison = f"{raison} [lien {lien} : {detail}]"
            if typ == "trajectoire":
                apres = s._valeur_canonique(c.get("apres"), s.TRAJECTOIRES) or str(c.get("apres") or "")
                avant = f["data"].get("trajectoire")
                if (apres in TRAJ_AFFAIBLISSEMENT and avant in s.TRAJECTOIRES[:4]
                        and _RENFORCE.search(_plie(raison))):
                    rejetees.append(f"trajectoire : {slug} {avant} → {apres} présenté comme un renforcement "
                                    f"(contresens sur l'axe)")
                    continue
            elif typ == "texte":
                extrait = " ".join(str(c.get("extrait") or "").split()).strip(" ….")
                if not extrait:
                    rejetees.append(f"{slug} : texte à revoir sans extrait")
                    continue
                juge = _plie(f"{c.get('raison') or ''} {contredit}")
                if _AMPLIFIE.search(juge):
                    motifs.append("élargit le rôle sans le contredire")
                elif _ATTENUE.search(juge) and not _FAUX.search(juge):
                    motifs.append("atténue le rôle sans le contredire")
                trouve = _plie(extrait)[:120] in _plie(_texte_complet(f))
                if not trouve:
                    motifs.append("extrait introuvable dans la fiche")
                if niveau == "obligatoire" and _date_contestee(extrait, juge, annees_hyp or ()):
                    motifs.append("date de la fiche contestée")   # v9.6
            if typ == "trajectoire" and niveau == "obligatoire" and apres != "disparu":
                # v7 : seule une disparition rend l'état actuel faux ; un changement de degré
                # (monter, décliner, mûrir) laisse la fiche vraie.
                motifs.append("changement de degré")
            if niveau == "obligatoire" and motifs:
                niveau = "possible"
                raison += f" _(rétrogradé : {', '.join(motifs)})_"
            elif [m for m in motifs if m != "au conditionnel"]:
                # v9.2 : un possible douteux est marqué aussi (il reste listé, hors priorité).
                # v9.3 : le conditionnel est normal pour un possible, il n'est plus signalé.
                raison += f" _(douteux : {', '.join(m for m in motifs if m != 'au conditionnel')})_"
            if contredit and typ != "texte":
                raison += f" — contredit : {contredit}"
            if typ == "trajectoire":
                brut_niv[niveau]["trajectoires"].append({"instance": slug, "apres": c.get("apres"), "raison": raison})
            elif typ == "relation":
                brut_niv[niveau]["relations"].append({"a": slug, "b": c.get("cible"), "type": c.get("relation"),
                                                      "action": c.get("action"), "raison": raison})
            else:
                brut_niv[niveau]["textes"].append({"slug": slug, "genre": f["genre"], "nom": f["data"].get("name"),
                                                   "extrait": extrait, "extrait_trouve": trouve,
                                                   "contredit": contredit, "raison": raison})
    manquantes = [f["slug"] for f in lot if f["slug"] not in vues]
    out = {"rejetees": rejetees, "corrigees": [], "non_lues": manquantes, "hors_lot": hors_lot}
    # Mêmes contrôles que la lecture IA, plafonds levés le temps de l'appel.
    sauve = dict(s.PLAFONDS)
    try:
        for k in s.PLAFONDS:
            s.PLAFONDS[k] = 10 ** 6
        for n in NIVEAUX:
            res = s.verifier_consequences({"trajectoires": brut_niv[n]["trajectoires"],
                                           "relations": brut_niv[n]["relations"]}, by_inst, by_zone)
            out[n] = {"trajectoires": res["trajectoires"], "relations": res["relations"],
                      "textes": brut_niv[n]["textes"]}
            out["rejetees"] += res["ecartees"]
            out["corrigees"] += res.get("corrigees") or []
    finally:
        s.PLAFONDS.clear()
        s.PLAFONDS.update(sauve)
    return out


def _fusion(a, b):
    """Additionne deux résultats de lot."""
    r = {}
    for k in CLES_RES:
        if k in NIVEAUX:
            r[k] = {t: a[k][t] + b[k][t] for t in ("trajectoires", "relations", "textes")}
        else:
            r[k] = a[k] + b[k]
    return r


def _sans_doublons(res, lecture):
    """Retire ce que la lecture IA a déjà proposé et les doublons ; un changement déjà
    obligatoire n'est pas répété en possible."""
    deja_t = {t["instance"] for t in (lecture or {}).get("trajectoires") or []}
    deja_r = {(frozenset((r["a"], r["b"])), r["type"]) for r in (lecture or {}).get("relations") or []}
    for n in NIVEAUX:
        traj, rel = [], []
        for t in res[n]["trajectoires"]:
            if t["instance"] in deja_t:
                continue
            deja_t.add(t["instance"])
            traj.append(t)
        for r in res[n]["relations"]:
            k = (frozenset((r["a"], r["b"])), r["type"])
            if k in deja_r:
                continue
            deja_r.add(k)
            rel.append(r)
        res[n]["trajectoires"], res[n]["relations"] = traj, rel
    return res


# ---------------------------------------------------------------------------
# Passe
# ---------------------------------------------------------------------------

def _empreinte(hyp, sc, effets, lot, commun):
    brut = json.dumps({"v": VERSION_PROMPT, "h": {k: hyp.get(k) for k in ("nom", "description", "date",
                                                                         "impacts", "contraintes", "mode")},
                       "sc": sc, "e": [(e["variable"], e["effet"]) for e in (effets or [])[:8]],
                       "c": hashlib.sha1(commun.encode("utf-8")).hexdigest(),
                       "f": [f["texte"] for f in lot]},
                      ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(brut.encode("utf-8")).hexdigest()[:16]


def _lire_cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _ecrire_cache(cache):
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def estimer(hyp, sc, effets, lecture=None, taille=TAILLE_LOT):
    fiches, instances = charger_fiches(hyp, sc)
    commun = contexte_commun(hyp, sc, effets, lecture, instances)
    cache = _lire_cache()
    a_lancer, chars = 0, 0
    for k, lot in enumerate(lots(fiches, taille)):
        cle = f"{hyp['id']}::{sc}::{k}"
        if (cache.get(cle) or {}).get("empreinte") == _empreinte(hyp, sc, effets, lot, commun):
            continue
        a_lancer += 1
        chars += len(prompt_lot(commun, lot, sc))
    jetons_e = chars / CHARS_PAR_JETON
    jetons_s = SORTIE_PAR_FICHE * len(fiches) * (a_lancer / max(1, len(lots(fiches, taille))))
    cout = (jetons_e * PRIX_ENTREE + jetons_s * PRIX_SORTIE) / 1e6
    return {"scenario": sc, "fiches": len(fiches),
            "instances": sum(1 for f in fiches if f["genre"] == "instance"),
            "evenements": sum(1 for f in fiches if f["genre"] == "evenement"),
            "lots": len(lots(fiches, taille)), "a_lancer": a_lancer,
            "jetons_entree": int(jetons_e), "cout_dollars": round(cout, 3)}


def passe_exhaustive(hyp, sc, effets, lecture=None, refaire=False, taille=TAILLE_LOT, contre=True,
                     classer=True):
    """Relit toutes les fiches du scénario. Retourne, par niveau (obligatoire / possible),
    trajectoires, relations et textes à revoir ; plus les rejets et les lots en échec.
    Rien n'est écrit dans le vault."""
    import simuler_et_si as s
    from llm_client import call_llm
    fiches, instances = charger_fiches(hyp, sc)
    by_inst = {i["slug"]: i for i in instances}
    try:
        repo, _ = s.charger_zone_repository()
        by_zone = {z.get("slug"): z for z in repo.load_all_zones(sc)}
    except Exception:
        by_zone = {}
    commun = contexte_commun(hyp, sc, effets, lecture, instances)
    territoires = territoires_touches(hyp, sc, lecture)
    lieux = lieux_nommes(hyp)
    annees_hyp = annees_hypothese(hyp)   # v9.6
    variables_hyp = variables_hypothese(hyp)
    cache = _lire_cache()
    total = {"obligatoire": _vide(), "possible": _vide(), "rejetees": [], "corrigees": [],
             "non_lues": [], "hors_lot": [], "echecs": [], "fiches": len(fiches),
             "slugs": [f["slug"] for f in fiches], "lots": 0, "depuis_cache": 0}

    def controle(brut, lot):
        return verifier_lot(brut, lot, by_inst, by_zone, effets, territoires, variables_hyp, lieux, annees_hyp)

    def lire(lot, cle, profondeur=0):
        """Un lot (cache, appel, contrôle). Un lot en échec est relancé en deux moitiés."""
        empreinte = _empreinte(hyp, sc, effets, lot, commun)
        entree = cache.get(cle) or {}
        deja_coupe = not refaire and entree.get("empreinte") == empreinte and entree.get("decoupe")
        if not refaire and entree.get("empreinte") == empreinte and isinstance(entree.get("brut"), dict):
            total["depuis_cache"] += 1
            return controle(entree["brut"], lot)
        try:
            if deja_coupe:
                raise RuntimeError("lot déjà découpé au passage précédent")
            texte = call_llm(system_prompt="Tu es l'architecte du lore d'un monde fictif. Tu lis chaque "
                             "fiche et tu sépares ce qui devient faux de ce qui est seulement plausible.",
                             user_prompt=prompt_lot(commun, lot, sc), max_tokens=MAX_TOKENS_LOT,
                             temperature=0.2, task_tier="structured_strict")
            brut = s._extraire_json(texte)
        except Exception as e:
            if len(lot) > 1 and profondeur < 3:
                moitie = len(lot) // 2
                if not deja_coupe:
                    cache[cle] = {"empreinte": empreinte, "decoupe": True,
                                  "date": datetime.now().isoformat(timespec="minutes")}
                    _ecrire_cache(cache)
                    print(f"  [passe] {cle} en échec ({type(e).__name__}) : relancé en deux moitiés", file=sys.stderr)
                r1 = lire(lot[:moitie], cle + "a", profondeur + 1)
                r2 = lire(lot[moitie:], cle + "b", profondeur + 1)
                if r1 is None or r2 is None:
                    return r1 or r2
                return _fusion(r1, r2)
            total["echecs"].append(f"{cle} ({lot[0]['slug']} …, {len(lot)} fiche(s)) : {type(e).__name__}: {e}")
            total["non_lues"] += [f["slug"] for f in lot]
            return None
        cache[cle] = {"empreinte": empreinte, "date": datetime.now().isoformat(timespec="minutes"), "brut": brut}
        _ecrire_cache(cache)
        return controle(brut, lot)

    for k, lot in enumerate(lots(fiches, taille)):
        total["lots"] += 1
        res = lire(lot, f"{hyp['id']}::{sc}::{k}")
        if res is None:
            continue
        # v4 : fiches restées sans réponse, redemandées une fois, seules.
        oubliees = [f for f in lot if f["slug"] in set(res["non_lues"])]
        if oubliees:
            print(f"  [passe] lot {k + 1} : {len(oubliees)} fiche(s) sans réponse, redemandée(s)", file=sys.stderr)
            res["non_lues"] = [sl for sl in res["non_lues"] if sl not in {f["slug"] for f in oubliees}]
            rattrapage = lire(oubliees, f"{hyp['id']}::{sc}::{k}r")
            if rattrapage is not None:
                res = _fusion(res, rattrapage)
        for cle_res in CLES_RES:
            if cle_res in NIVEAUX:
                for t in ("trajectoires", "relations", "textes"):
                    total[cle_res][t] += res[cle_res][t]
            else:
                total[cle_res] += res[cle_res]
    res = _sans_doublons(total, lecture)
    res["variables_hyp"] = sorted(variables_hyp)
    if contre:
        situation = {i["slug"]: (i.get("localisation") or {}).get("lieu") for i in instances}
        situation.update({f["slug"]: f["data"].get("date_label") or f["data"].get("date")
                          for f in fiches if f["genre"] == "evenement"})
        res = contre_lecture(res, hyp, sc, effets, cache, refaire, situation)
    if classer:
        res = classer_possibles(res, hyp, sc, effets, cache, refaire)
    return res


# ---------------------------------------------------------------------------
# v7 : contre-lecture des obligatoires
# ---------------------------------------------------------------------------

VERSION_CONTRE = "4"   # v7.1 : exemples neutres ; v9.4 : passé, amorti ; v9.5 : nature du fait, lieu
SEUIL_AMORTI = 0.25    # sous 25 % de la force initiale en fin de période : choc « largement amorti »
TAILLE_CONTRE = 25

CONSIGNE_CONTRE = """Tu vérifies des corrections proposées pour le lore d'un monde fictif. Pour CHAQUE proposition
ci-dessous, réponds à une seule question fermée : l'état actuel de la fiche (sa phrase, sa trajectoire,
sa relation) est-il LOGIQUEMENT INCOMPATIBLE avec l'élément perturbateur décrit ? Autrement dit : les
deux peuvent-ils être vrais en même temps dans le lore ?

Réponds "incompatible": false (la fiche reste vraie, la correction n'est pas obligatoire) quand :
- omission : la phrase ne mentionne pas l'élément, mais ne dit rien qui le contredise ;
- aggravation : l'élément accélère, aggrave, précipite ou renforce ce que dit la fiche ;
- nuance : la phrase reste vraie mais « pourrait être complétée ou nuancée » ;
- chronologie : un fait daté APRÈS l'élément est jugé impossible seulement parce que l'élément l'a
  précédé, ou une date de la fiche est contestée sans que l'élément la fixe ;
- invention : la correction s'appuie sur un fait que l'élément ne dit pas (zones plus touchées,
  victimes précises, dates) ;
- passé : la phrase décrit un fait daté AVANT l'élément ; l'élément ne change jamais le passé ;
- amorti : la phrase décrit un état tardif (souvent 2098) et l'élément est un choc largement amorti
  en fin de période (voir la ligne « Effet résiduel ») ; le monde a pu revenir à cet état. Seuls
  les FAITS MATÉRIELS de l'élément restent vrais pour toujours (destructions, morts, faits à
  respecter) : une phrase qu'ils contredisent reste incompatible, même si le choc est amorti ;
- autre : la fiche et l'élément peuvent être vrais ensemble pour une autre raison.
Réponds "incompatible": true seulement si laisser la fiche telle quelle crée une contradiction
réelle avec ce que dit l'élément (ou ses faits à respecter). Méthode : énonce ce qu'affirme la fiche,
puis ce qu'affirme l'élément ; s'ils peuvent être vrais ensemble, la réponse est false.

Exemples (monde inventé, sans rapport avec le lore) :
- Élément : « une épidémie tue 20 % de la population en 2040 ». Fiche : « le port de Velka est détruit
  par une guerre en 2060 ». Correction proposée : « l'épidémie a précédé la guerre, donc le port n'a pas
  pu survivre jusqu'en 2060 ». → false, chronologie : un port peut survivre à une épidémie.
- Même élément. Fiche : « la guilde soigne les villages abandonnés par l'État ». Correction : « la phrase
  ne dit pas que l'épidémie est la cause ». → false, omission.
- Même élément. Fiche : « l'archipel de Sorn n'a connu aucune épidémie depuis 2000 ». → true,
  contradiction : l'élément touche le monde entier en 2040.
- Même élément. Fiche : « le recensement de 2070 donne la même population qu'en 2030 ». → true,
  contradiction : un cinquième de la population est mort entre-temps.
- Élément : « une décennie de régimes autoritaires (2030-2040) ; effet résiduel en fin de période :
  10 % ». Fiche : « en 2098, une assemblée mondiale coordonne la gestion des océans ». → false,
  amorti : une coopération a pu se reconstruire après 2040.
- Même élément. Fiche : « la guerre des Détroits de 2025 a ruiné la flotte de Kesh ». → false, passé.
- Élément : « le barrage d'Ulm est détruit en 2050 ». Fiche : « en 2098, le barrage d'Ulm alimente la
  vallée ». → true, contradiction : une destruction matérielle reste vraie.

Pour CHAQUE proposition, classe aussi le fait invoqué (champ "fait") :
- "materiel" : un fait matériel ou un acte daté qui reste vrai pour toujours (destruction, morts,
  invasion ou attaque entre parties nommées, disparition d'un lieu, fait à respecter) ;
- "tendance" : un climat, une orientation politique, une politique publique, un rapport de force ou
  une évolution d'ensemble (fermeture des frontières, nationalisme, rejet du multilatéralisme…).

Réponds UNIQUEMENT en JSON, une entrée par proposition :
{"verdicts": [{"id": "o1", "incompatible": true, "fait": "materiel | tendance", "motif": "contradiction", "justification": "une phrase"},
              {"id": "o2", "incompatible": false, "motif": "omission | aggravation | nuance | chronologie | invention | autre",
               "justification": "une phrase"}]}
"""


def _part_residuelle(hyp, effets):
    """v9.4 : part de la force initiale qui reste en fin de période (calcul, pas l'IA)."""
    force = max((i.get("force") or 0 for i in hyp.get("impacts") or []), default=0)
    reste = max((abs(e.get("effet") or 0) for e in effets or []), default=0)
    if hyp.get("mode") == "rupture" or not force:
        return 1.0
    return reste / force


def _ligne_residuel(hyp, effets):
    force = max((i.get("force") or 0 for i in hyp.get("impacts") or []), default=0)
    if not force:
        return ""
    part = _part_residuelle(hyp, effets) if hyp.get("mode") != "rupture" else (
        max((abs(e.get("effet") or 0) for e in effets or []), default=0) / force)
    nature = ("choc largement amorti : les effets mesurés ont presque disparu" if part < SEUIL_AMORTI
              else "effet durable : il pèse encore sur la fin de période")
    rupture = " (mode rupture : l'équilibre du scénario est déplacé durablement)" if hyp.get("mode") == "rupture" else ""
    return f"\nEffet résiduel en fin de période : environ {part:.0%} de la force initiale — {nature}{rupture}."


def _fait(x):
    """v7.1 : seul le fait invoqué est montré, pas l'argumentaire du proposant."""
    raison = x.get("raison") or ""
    if " — contredit : " in raison:
        return raison.split(" — contredit : ", 1)[1]
    return raison.split(" [lien ", 1)[0]


def _items_obligatoires(res, situation=None):
    """v9.5 : chaque proposition dit où (ou quand) se situe la fiche."""
    situation = situation or {}

    def ou(slug):
        s = situation.get(slug)
        return f" [{s}]" if s else ""
    items = []
    bloc = res["obligatoire"]
    for t in bloc["trajectoires"]:
        items.append(("trajectoires", t, f"fiche {t['nom']}{ou(t['instance'])} : trajectoire actuelle « {t['avant']} », "
                      f"correction proposée → « {t['apres']} ». Fait invoqué : {_fait(t)}"))
    for r in bloc["relations"]:
        items.append(("relations", r, f"relation {r['a_nom']}{ou(r['a'])} ↔ {r['b_nom']}{ou(r['b'])} : "
                      f"{r['type']} {r['action']}. Fait invoqué : {_fait(r)}"))
    for t in bloc["textes"]:
        items.append(("textes", t, f"fiche {t['nom']} ({t['genre']}){ou(t['slug'])} : phrase « {t['extrait']} ». "
                      f"Fait invoqué : {t.get('contredit') or '—'}"))
    return items


def contre_lecture(res, hyp, sc, effets, cache, refaire=False, situation=None):
    """Revérifie chaque obligatoire par une question fermée ; ce qui n'est pas une
    contradiction réelle descend en « possible ». En cas d'échec, l'obligatoire reste."""
    import simuler_et_si as s
    from llm_client import call_llm
    items = _items_obligatoires(res, situation)
    amorti = _part_residuelle(hyp, effets) < SEUIL_AMORTI
    stats = {"verifies": 0, "confirmes": 0, "retrogrades": 0, "non_verifies": 0}
    res["contre_lecture"] = stats
    if not items:
        return res
    contraintes = "".join(f"\n- {c}" for c in hyp.get("contraintes") or [])
    effets_txt = "".join(f"\n- {e['variable']} : {e['effet']:+.1f}" for e in (effets or [])[:8])
    entete = (f"ÉLÉMENT PERTURBATEUR (scénario {sc}) : {hyp['nom']} — {hyp['date']:g}.\n"
              f"{_court(hyp['description'], 700)}"
              + (f"\nFaits à respecter :{contraintes}" if contraintes else "")
              + (f"\nEffets chiffrés :{effets_txt}" if effets_txt else "")
              + _ligne_residuel(hyp, effets) + "\n\n")
    # v9.4 : verdicts mis en cache proposition par proposition (clé = élément + texte de la
    # proposition) ; un paquet n'appelle l'IA que pour les propositions encore inconnues.
    # Les paquets complets des versions précédentes restent relus en priorité.
    def cle_item(txt):
        return f"{hyp['id']}::{sc}::contre1::" + hashlib.sha1(
            (VERSION_CONTRE + entete + txt).encode("utf-8")).hexdigest()[:16]

    verdicts = {}
    for k in range(0, len(items), TAILLE_CONTRE):
        paquet = items[k:k + TAILLE_CONTRE]
        lignes = "\n".join(f"[o{k + n + 1}] {txt}" for n, (_, _, txt) in enumerate(paquet))
        ancienne = f"{hyp['id']}::{sc}::contre::" + hashlib.sha1(
            (VERSION_CONTRE + entete + lignes).encode("utf-8")).hexdigest()[:16]
        brut = None if refaire else (cache.get(ancienne) or {}).get("brut")
        if isinstance(brut, dict):
            for v in brut.get("verdicts") or []:
                if isinstance(v, dict) and v.get("id"):
                    verdicts[str(v["id"])] = v
    a_demander = []
    for n, (_, _, txt) in enumerate(items):
        oid = f"o{n + 1}"
        if oid in verdicts:
            continue
        v = None if refaire else (cache.get(cle_item(txt)) or {}).get("verdict")
        if isinstance(v, dict):
            verdicts[oid] = v
        else:
            a_demander.append((oid, txt))
    for k in range(0, len(a_demander), TAILLE_CONTRE):
        paquet = a_demander[k:k + TAILLE_CONTRE]
        lignes = "\n".join(f"[{oid}] {txt}" for oid, txt in paquet)
        try:
            texte = call_llm(system_prompt="Tu es un vérificateur de cohérence strict et économe en corrections.",
                             user_prompt=entete + CONSIGNE_CONTRE + "\nPROPOSITIONS :\n" + lignes,
                             max_tokens=MAX_TOKENS_LOT, temperature=0.0, task_tier="structured_strict")
            brut = s._extraire_json(texte)
        except Exception as e:
            print(f"  [contre-lecture] échec ({type(e).__name__}: {e}) : obligatoires gardés tels quels",
                  file=sys.stderr)
            continue
        recus = {str(v["id"]): v for v in (brut.get("verdicts") or []) if isinstance(v, dict) and v.get("id")}
        for oid, txt in paquet:
            if oid in recus:
                verdicts[oid] = recus[oid]
                cache[cle_item(txt)] = {"date": datetime.now().isoformat(timespec="minutes"), "verdict": recus[oid]}
        _ecrire_cache(cache)
    garde = _vide()
    for n, (cle_bloc, x, _) in enumerate(items):
        v = verdicts.get(f"o{n + 1}")
        if v is None:
            stats["non_verifies"] += 1
            x["raison"] += " _(contre-lecture : sans réponse, gardé)_"
            garde[cle_bloc].append(x)
            continue
        stats["verifies"] += 1
        nature = _plie(v.get("fait") or "")
        tendance_amortie = amorti and nature.startswith("tendance")
        if (v.get("incompatible") is False or str(v.get("incompatible")).lower() == "false"
                or tendance_amortie):
            stats["retrogrades"] += 1
            motif = _plie(v.get("motif") or "autre").split()[0] if v.get("motif") else "autre"
            if tendance_amortie and not (v.get("incompatible") is False):
                # v9.5 : décision du code, pas de l'IA : choc amorti + fait de tendance.
                motif = "amorti"
            x["raison"] += (f" _(rétrogradé : contre-lecture {motif})_ — "
                            + " ".join(str(v.get("justification") or "").split()))
            res["possible"][cle_bloc].insert(0, x)
        else:
            stats["confirmes"] += 1
            garde[cle_bloc].append(x)
    res["obligatoire"] = garde
    return res


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------

def _slugs_touches(bloc):
    return ({t["instance"] for t in bloc["trajectoires"]} | {r["a"] for r in bloc["relations"]}
            | {t["slug"] for t in bloc["textes"]})


def _rendre_niveau(bloc):
    L = []
    if bloc["trajectoires"]:
        L.append("**Trajectoires**")
        L += [f"- {t['nom']} (`{t['instance']}`) : {t['avant']} → **{t['apres']}** — {t['raison']}"
              for t in bloc["trajectoires"]]
        L.append("")
    if bloc["relations"]:
        L.append("**Relations**")
        L += [f"- {r['type']} {r['action']} : {r['a_nom']} ↔ {r['b_nom']} — {r['raison']}" for r in bloc["relations"]]
        L.append("")
    if bloc["textes"]:
        L.append("**Textes**")
        for t in bloc["textes"]:
            contre = f" — contredit par : {t['contredit']}" if t.get("contredit") else ""
            marque = "" if t["extrait_trouve"] or "rétrogradé" in t["raison"] else " _(extrait introuvable dans la fiche)_"
            L.append(f"- {t['genre']} {t['nom']} (`{t['slug']}`) : « {t['extrait']} »{contre} — {t['raison']}{marque}")
        L.append("")
    return L or ["Aucun.", ""]


# v9 : possibles regroupés par fiche et classés par l'IA (un appel, en cache) ; le score
# mécanique ne sert plus que de repli si l'appel échoue, et d'ordre pour la liste courte.
PRIORITE_MAX = 20
VERSION_CLASSEMENT = "3"
# v9.1 : une proposition bâtie sur un fait inventé ou absent n'est pas candidate à la priorité
# (elle reste listée plus bas) ; le classeur voit si une vérification l'a jugée non nécessaire.
_DISQUALIFIE = ("contre-lecture invention", "contre-lecture chronologie", "contre-lecture omission",
                "lien territoire alors", "sans lien direct", "extrait introuvable",
                "date de la fiche contestée")


def _disqualifie(x):
    raison = x.get("raison") or ""
    return any(m in raison and ("rétrogradé" in raison or "douteux" in raison) for m in _DISQUALIFIE)


def _slug_de(genre, x):
    return x["instance"] if genre == "trajectoires" else (x["a"] if genre == "relations" else x["slug"])


def _nom_de(genre, x):
    return x.get("a_nom") if genre == "relations" else x.get("nom")


def grouper_possibles(bloc):
    """{slug: {"nom", "items": [(genre, x)]}} dans l'ordre d'apparition."""
    fiches = {}
    for g in ("trajectoires", "relations", "textes"):
        for x in bloc[g]:
            sl = _slug_de(g, x)
            fiches.setdefault(sl, {"nom": _nom_de(g, x) or sl, "items": []})["items"].append((g, x))
    return fiches


def _score_possible(genre, x, variables_hyp):
    """Repli mécanique (sans IA) : plus haut = à lire avant."""
    raison = x.get("raison") or ""
    s = 0
    poids_contre = {"aggravation": 1, "chronologie": 0, "autre": 0, "nuance": 0,
                    "omission": -2, "invention": -2}
    m = _re.search(r"rétrogradé : contre-lecture (\w+)", raison)
    refuse = bool(m)
    if m:
        s += poids_contre.get(m.group(1), 0)
    elif "rétrogradé : changement de degré" in raison:
        s += 1
    if "rétrogradé : lien territoire" in raison or "rétrogradé : sans lien" in raison:
        s -= 2
    m = _re.search(r"\[lien (\w+) : ([^\]]*)\]", raison)
    if m:
        if m.group(1) in ("relation", "territoire") and "rétrogradé : lien territoire" not in raison:
            s += 2
        elif m.group(1) == "variable" and any(v in m.group(2) for v in variables_hyp):
            s += 1
    if genre == "trajectoires" and x.get("apres") == "disparu" and not refuse:
        s += 1
    if _HYPOTHETIQUE.search(_plie(raison.split(" _(rétrogradé")[0])):
        s -= 1
    return s


def _resume_fiche(f):
    parts = []
    for g, x in f["items"]:
        if g == "trajectoires":
            parts.append(f"trajectoire {x['avant']} → {x['apres']}")
        elif g == "relations":
            parts.append(f"{x['type']} {x['action']} avec {x['b_nom']}")
        else:
            parts.append(f"texte « {_court(x['extrait'], 60)} »")
    return " ; ".join(parts)


CONSIGNE_CLASSEMENT = """Voici les conséquences POSSIBLES d'un élément perturbateur sur les fiches d'un monde fictif
(aucune n'est obligatoire). Choisis les {n} fiches dont la conséquence est la plus DIRECTE et la plus
FORTE : celles qu'un auteur devrait regarder en premier pour intégrer l'élément au lore. Préfère une
entité dont l'activité même est touchée par l'élément à une entité qui profite seulement d'un monde
plus chaotique en général. Une disparition n'est pas plus importante qu'une montée en soi ; un
changement qu'une vérification a jugé non nécessaire passe après les autres.

Réponds UNIQUEMENT en JSON, du plus important au moins important :
{{"classement": [{{"id": "f3", "pourquoi": "quelques mots"}}, ...]}}
"""


def classer_possibles(res, hyp, sc, effets, cache, refaire=False):
    """Un appel IA : les PRIORITE_MAX fiches possibles les plus importantes, dans l'ordre."""
    import simuler_et_si as s
    from llm_client import call_llm
    toutes = grouper_possibles(res["possible"])
    fiches = {}
    for sl, f in toutes.items():
        items = [(g, x) for g, x in f["items"] if not _disqualifie(x)]
        if items:
            fiches[sl] = {"nom": f["nom"], "items": items}
    res["classement"], res["classement_source"] = [], "score"
    if len(fiches) <= PRIORITE_MAX:
        res["classement"] = [{"slug": sl, "pourquoi": ""} for sl in fiches]
        res["classement_source"] = "tout"
        return res
    slugs = list(fiches)
    lignes = []
    for n, sl in enumerate(slugs):
        f = fiches[sl]
        raison = f["items"][0][1].get("raison") or ""
        raison = raison.split(" [lien ")[0].split(" _(rétrogradé")[0]
        verifie = any("rétrogradé : contre-lecture" in (x.get("raison") or "") for _, x in f["items"])
        lignes.append(f"[f{n + 1}] {f['nom']} : {_resume_fiche(f)} — {_court(raison, 160)}"
                      + (" (une vérification a jugé ce changement non nécessaire)" if verifie else ""))
    effets_txt = "".join(f"\n- {e['variable']} : {e['effet']:+.1f}" for e in (effets or [])[:8])
    prompt = (f"ÉLÉMENT PERTURBATEUR (scénario {sc}) : {hyp['nom']} — {hyp['date']:g}.\n"
              f"{_court(hyp['description'], 700)}" + (f"\nEffets chiffrés :{effets_txt}" if effets_txt else "")
              + "\n\n" + CONSIGNE_CLASSEMENT.format(n=PRIORITE_MAX) + "\nFICHES :\n" + "\n".join(lignes))
    cle = f"{hyp['id']}::{sc}::classement::" + hashlib.sha1(
        (VERSION_CLASSEMENT + prompt).encode("utf-8")).hexdigest()[:16]
    brut = None if refaire else (cache.get(cle) or {}).get("brut")
    if not isinstance(brut, dict):
        try:
            texte = call_llm(system_prompt="Tu es l'éditeur du lore d'un monde fictif ; tu hiérarchises.",
                             user_prompt=prompt, max_tokens=3000, temperature=0.0,
                             task_tier="structured_strict")
            brut = s._extraire_json(texte)
            cache[cle] = {"date": datetime.now().isoformat(timespec="minutes"), "brut": brut}
            _ecrire_cache(cache)
        except Exception as e:
            print(f"  [classement] échec ({type(e).__name__}: {e}) : tri mécanique", file=sys.stderr)
            return res
    vus = set()
    for c in (brut.get("classement") or []) if isinstance(brut, dict) else []:
        m = _re.fullmatch(r"f(\d+)", str((c or {}).get("id") or "").strip()) if isinstance(c, dict) else None
        if not m or not (1 <= int(m.group(1)) <= len(slugs)):
            continue
        sl = slugs[int(m.group(1)) - 1]
        if sl not in vus:
            vus.add(sl)
            res["classement"].append({"slug": sl, "pourquoi": " ".join(str(c.get("pourquoi") or "").split())})
        if len(res["classement"]) >= PRIORITE_MAX:
            break
    if res["classement"]:
        res["classement_source"] = "ia"
    return res


def _rendre_possibles(res):
    bloc, variables_hyp = res["possible"], res.get("variables_hyp") or []
    fiches = grouper_possibles(bloc)
    if not fiches:
        return ["Aucun.", ""]
    score = {sl: max(_score_possible(g, x, variables_hyp) for g, x in f["items"]) for sl, f in fiches.items()}
    classement = [c for c in res.get("classement") or [] if c["slug"] in fiches]
    source = res.get("classement_source")
    if not classement:
        classement = [{"slug": sl, "pourquoi": ""} for sl in sorted(fiches, key=lambda sl: -score[sl])[:PRIORITE_MAX]]
        source = "score"
    tete = {c["slug"] for c in classement}
    L = [f"**À lire en priorité ({len(classement)} fiches sur {len(fiches)})**"
         + {"ia": " — choisies et ordonnées par l'IA", "score": " — tri mécanique (classement IA indisponible)",
            "tout": ""}.get(source, ""), ""]
    for c in classement:
        f = fiches[c["slug"]]
        L.append(f"- **{f['nom']}** (`{c['slug']}`)" + (f" — _{c['pourquoi']}_" if c["pourquoi"] else ""))
        for g, x in f["items"]:
            ligne = _rendre_niveau({k: ([x] if k == g else []) for k in ("trajectoires", "relations", "textes")})[1]
            L.append("  " + ligne)
    L.append("")
    reste = sorted((sl for sl in fiches if sl not in tete), key=lambda sl: -score[sl])
    if reste:
        L.append(f"**Autres fiches avec des changements possibles ({len(reste)})**")
        L += [f"- {fiches[sl]['nom']} : {_resume_fiche(fiches[sl])}" for sl in reste]
        L.append("")
    return L


def rendre(res):
    L = ["### Passe exhaustive (IA, toutes les fiches — rien n'est écrit)", ""]
    if res.get("erreur"):
        return L + [f"_Passe impossible : {res['erreur']}_", ""]
    L.append(f"{res['fiches']} fiche(s) relue(s) en {res['lots']} lot(s)"
             + (f", dont {res['depuis_cache']} lot(s) repris du cache" if res.get("depuis_cache") else "") + ".")
    oblig, poss = _slugs_touches(res["obligatoire"]), _slugs_touches(res["possible"])
    seulement_poss = poss - oblig
    lues = res["fiches"] - len(set(res["non_lues"]))
    L.append(f"Verdicts : **{len(oblig)} fiche(s) à corriger**, {len(seulement_poss)} avec des changements "
             f"possibles seulement, {max(0, lues - len(oblig | poss))} inchangée(s).")
    L.append("")
    if res["echecs"]:
        L += [f"- ✗ {e}" for e in res["echecs"]] + [""]
    if res["non_lues"]:
        L += [f"_Fiches sans réponse de l'IA ({len(res['non_lues'])}) : "
              + ", ".join(res["non_lues"][:15]) + (" …" if len(res["non_lues"]) > 15 else "") + "_", ""]
    if res.get("hors_lot"):
        L += [f"_Réponses ignorées sur des fiches hors de leur lot ({len(res['hors_lot'])}) : "
              "ces fiches ont été jugées dans leur propre lot._", ""]
    cl = res.get("contre_lecture")
    if cl and cl["verifies"] + cl["non_verifies"]:
        L += [f"_Contre-lecture des obligatoires : {cl['verifies']} vérifié(s), {cl['confirmes']} confirmé(s), "
              f"{cl['retrogrades']} rétrogradé(s) en possible"
              + (f", {cl['non_verifies']} sans réponse (gardés)" if cl["non_verifies"] else "") + "._", ""]
    L += ["#### Obligatoire — la fiche devient fausse sans ce changement", ""]
    L += _rendre_niveau(res["obligatoire"])
    L += ["#### Possible — conséquence plausible, la fiche reste vraie sans elle", ""]
    retro = {}
    for bloc in res["possible"].values():
        for x in bloc:
            for m in _re.findall(r"rétrogradé : ([^)]*)\)", x.get("raison") or ""):
                for motif in m.split(", "):
                    retro[motif] = retro.get(motif, 0) + 1
    if retro:
        L += ["_Rétrogradés d'obligatoire à possible par les contrôles : "
              + ", ".join(f"{n} {m}" for m, n in sorted(retro.items(), key=lambda x: -x[1])) + "._", ""]
    L += _rendre_possibles(res)
    if res["corrigees"]:
        L += [f"_Corrections automatiques ({len(res['corrigees'])}) : " + " ; ".join(res["corrigees"][:8]) + "_", ""]
    if res["rejetees"]:
        L += [f"_Réponses rejetées car mal formées ({len(res['rejetees'])}) : " + " ; ".join(res["rejetees"][:8])
              + (" …" if len(res["rejetees"]) > 8 else "") + "_", ""]
    return L


# ---------------------------------------------------------------------------
# Ligne de commande (autonome)
# ---------------------------------------------------------------------------

def lecture_en_cache(hyp, sc, effets):
    """Lecture IA du simulateur si elle est en cache (jamais d'appel ici)."""
    import simuler_et_si as s
    try:
        cache = json.loads(s.CACHE_CONSEQUENCES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    entree = cache.get(f"{hyp['id']}::{sc}") or {}
    if entree.get("empreinte") != s._empreinte(hyp, sc, effets) or not isinstance(entree.get("brut"), dict):
        return None
    _, instances, zones = s._contexte_scenario(sc)
    return s.verifier_consequences(entree["brut"], {i["slug"]: i for i in instances},
                                   {z.get("slug"): z for z in zones})


def main():
    import simuler_et_si as s
    ap = argparse.ArgumentParser(description="Passe exhaustive du simulateur « et si ? » (lecture seule).")
    ap.add_argument("--id", required=True, help="id de l'hypothèse dans et_si/hypotheses.yaml")
    ap.add_argument("--scenario", default=None, help="limite à un scénario")
    ap.add_argument("--date", type=float, default=2098.0, help="date de mesure des effets (défaut 2098)")
    ap.add_argument("--estimer", action="store_true", help="nombre d'appels et coût, aucun appel")
    ap.add_argument("--refaire", action="store_true", help="ignore le cache")
    ap.add_argument("--taille-lot", type=int, default=TAILLE_LOT)
    ap.add_argument("--sans-contre-lecture", action="store_true", help="ne revérifie pas les obligatoires")
    ap.add_argument("--sans-classement", action="store_true", help="tri mécanique des possibles, sans IA")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    import dynamique as dyn
    from loader import VALID_VARS
    choix = [h for h in s.charger_hypotheses() if h.get("id") == args.id]
    if not choix:
        sys.exit(f"✗ Hypothèse {args.id!r} introuvable.")
    hyp, erreurs, _ = s.verifier_hypothese(choix[0], VALID_VARS, dyn)
    if erreurs:
        sys.exit("✗ Hypothèse invalide : " + " ; ".join(erreurs))
    if args.scenario and args.scenario not in hyp["scenarios"]:
        sys.exit(f"✗ Scénario {args.scenario!r} non couvert par l'hypothèse.")
    scenarios = [args.scenario] if args.scenario else hyp["scenarios"]
    resultats = s.simuler_hypothese(hyp, args.date, scenarios)

    sortie = {}
    for sc in scenarios:
        effets = (resultats.get(sc) or {}).get("effets") or []
        lecture = lecture_en_cache(hyp, sc, effets)
        if args.estimer:
            sortie[sc] = estimer(hyp, sc, effets, lecture, args.taille_lot)
            sortie[sc]["lecture_en_cache"] = lecture is not None
        else:
            try:
                sortie[sc] = passe_exhaustive(hyp, sc, effets, lecture, args.refaire, args.taille_lot,
                                             contre=not args.sans_contre_lecture,
                                             classer=not args.sans_classement)
            except Exception as e:
                sortie[sc] = {"erreur": f"{type(e).__name__}: {e}"}

    if args.json:
        print(json.dumps(sortie, ensure_ascii=False, indent=2, default=str))
        return
    for sc, r in sortie.items():
        print(f"## {sc}\n")
        if args.estimer:
            print(f"{r['fiches']} fiche(s) ({r['instances']} instances, {r['evenements']} événements "
                  f"après {hyp['date']:g}), {r['lots']} lot(s), {r['a_lancer']} à lancer "
                  f"(le reste en cache) ; ≈ {r['jetons_entree']} jetons d'entrée, ≈ {r['cout_dollars']} $.")
            print("Lecture IA du simulateur en cache : " + ("oui (reprise comme contexte)" if r["lecture_en_cache"]
                  else "non (lancer d'abord le simulateur avec --consequences-ia)") + "\n")
        else:
            print("\n".join(rendre(r)))


if __name__ == "__main__":
    main()

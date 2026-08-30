#!/usr/bin/env python3
"""
set_ton_personnel.py — Ourrassol 2098

Génère (ou fixe directement) le champ ton_personnel d'un·e journaliste
ou d'un·e orateur·rice, dans journaux.yaml (26 août 2026, suite du
chantier de nuance personnelle -- voir prompt_builder.py,
get_journal_profile()/build_system_prompt()).

Champ opt-in, unifié pour journalistes ET orateurs (David a préféré un
seul nom de champ plutôt que deux -- ton_personnel pour les uns,
style_rhetorique pour les autres, comme initialement prévu par erreur).
Absent par défaut sur toutes les entrées existantes -- ce script ne
touche jamais une personne sans le lui demander explicitement (mode
--nom) ou sans lui avoir dit de balayer une zone entière (--all-manquants).

Deux modes :
  --nom "Nom exact"       : une seule personne précise
  --all-manquants         : tout le monde dans la zone qui n'a pas
                             encore de ton_personnel (journalistes ET
                             orateurs confondus)

Le nom peut être un·e journaliste OU un·e orateur·rice -- cherché dans
les deux listes de la zone, peu importe. Le contexte donné au LLM
diffère légèrement selon le type (thématiques pour un·e journaliste,
communautés desservies/réputation pour un·e orateur·rice), mais le
champ écrit est toujours le même : ton_personnel.

--ton-personnel "..." : valeur donnée directement, aucun appel LLM
(mode --nom uniquement -- n'a pas de sens en --all-manquants, plusieurs
personnes ne peuvent pas partager la même nuance mot pour mot).

--overwrite : sans cette option, une personne qui a DÉJÀ un
ton_personnel est ignorée (jamais écrasée par erreur). Avec, la valeur
existante est remplacée.

Sauvegarde automatique horodatée avant toute écriture (même principe
que fix_doublons_journalistes.py, 26 août 2026) -- save_journaux()
n'a aucun filet natif.

Chaque échec individuel (panne API, réponse invalide) est non-bloquant
en mode --all-manquants -- les autres continuent.

Usage :
    python3 set_ton_personnel.py --scenario breakdown --ligne pro_pouvoir \\
        --zone-slug afrique_centrale_australe --nom "Mireille Mbuyi-Kabamba"

    python3 set_ton_personnel.py --scenario breakdown --ligne pro_pouvoir \\
        --zone-slug afrique_centrale_australe --nom "Mireille Mbuyi-Kabamba" \\
        --ton-personnel "Toujours un brin ironique, aime commencer par une question rhétorique."

    python3 set_ton_personnel.py --scenario breakdown --ligne pro_pouvoir \\
        --zone-slug afrique_centrale_australe --all-manquants

    python3 set_ton_personnel.py ... --dry-run   # appelle le LLM pour de vrai, n'écrit rien
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_journaux import load_journaux, save_journaux, JOURNAUX_PATH  # noqa: E402
from llm_client import call_llm, resolve_for_tier  # noqa: E402

TASK_TIER = "strict"

SYSTEM_PROMPT = (
    "Tu es l'assistant de worldbuilding du projet Ourrassol 2098 — "
    "simulateur de presse fictive en 2098. Tu inventes une nuance "
    "personnelle pour un·e membre d'une rédaction déjà établie. "
    "Réponds UNIQUEMENT avec un JSON valide. Pas de texte avant ou "
    "après. Pas de backticks."
)


def _trouver_entree(zone_data, nom):
    """Cherche `nom` dans journalistes puis orateurs de la zone.
    Retourne (liste_dict_ou_None, entree_dict_ou_None)."""
    for j in (zone_data.get("journalistes") or []):
        if j.get("nom") == nom:
            return zone_data.get("journalistes"), j
    for o in (zone_data.get("orateurs") or []):
        if o.get("nom") == nom:
            return zone_data.get("orateurs"), o
    return None, None


def _contexte_specifique(entree, est_orateur):
    if est_orateur:
        communautes = entree.get("communautes_desservies") or []
        reputation = entree.get("reputation_orale", "")
        return "Dessert : {}. Réputation orale : {}.".format(
            ", ".join(communautes) or "(non renseigné)",
            reputation or "(non renseignée)",
        )
    else:
        thematiques = entree.get("thematiques") or []
        return "Spécialisé·e en : {}.".format(", ".join(thematiques) or "(non renseigné)")


def _build_prompt(zone_nom, ton, langue_style, nom_cible, contexte_specifique, autres_nuances):
    return """Zone : {zone_nom}
Ton éditorial de cette édition (à respecter, ne pas réinventer) : {ton}
Registre linguistique de cette édition : {langue_style}

Tu inventes une NUANCE PERSONNELLE pour {nom_cible}, membre de cette
rédaction. {contexte_specifique}

Cette nuance doit rester EN COHÉRENCE avec le ton éditorial ci-dessus
(jamais le contredire) -- une manière personnelle d'incarner ce ton,
pas un ton différent. Pense : rythme d'écriture ou de parole, tics de
style, un trait de personnalité qui transparaît (impatience, ironie,
tendresse, méfiance...), une manière distinctive de construire ses
phrases ou son argumentation.

CONTRAINTES DE FORMAT (importantes) :
- DÉCRIS le style de manière ABSTRAITE -- rythme, structure de phrase,
  registre émotionnel, tic rhétorique récurrent. Ne cite JAMAIS
  d'exemple de phrase ou de formule concrète entre guillemets (ni « »,
  ni ", ni ') : un exemple verbatim ici serait recopié tel quel dans
  chaque article signé par cette personne, devenant vite répétitif au
  lieu de rester une inspiration de style.
- Reste vraiment concis : UNE SEULE phrase simple, 25 mots maximum.
  Pas de proposition sur proposition, pas d'énumération -- une image
  ou une observation, pas trois empilées.
- N'utilise JAMAIS de métaphore ou de comparaison puisée dans la
  violence, les armes, la guerre ou le combat (machette, soldat,
  ultimatum, offensive...) -- même utilisée au sens figuré, ce type
  d'image associée à une zone ou une culture perçue comme telle
  reconduit des clichés contemporains de conflit. Puise plutôt dans
  des domaines neutres : artisanat, musique, météo, gestes du
  quotidien, métiers ordinaires.
- N'ANCRE PAS cette nuance dans des stéréotypes culturels, ethniques,
  religieux ou régionaux TELS QU'ILS EXISTENT AUJOURD'HUI (2026) --
  nous sommes en 2098, un monde qui a eu 70 ans pour évoluer
  différemment du nôtre. Ne présume jamais qu'une origine culturelle
  perçue implique automatiquement un trait de caractère, une
  spiritualité ou un registre "typique" -- ce serait projeter des clichés
  contemporains sur un futur qui ne leur doit rien. Base la nuance sur
  la PERSONNALITÉ et les habitudes PROFESSIONNELLES de cette personne
  (rythme, tempérament, façon d'argumenter), pas sur une origine
  supposée. Si le ton éditorial de la zone (ci-dessus) intègre déjà
  des éléments culturels/religieux spécifiques, c'est un choix de
  worldbuilding déjà établi que tu peux suivre -- mais n'en rajoute
  jamais de toi-même au-delà de ce qui est déjà écrit dans ce ton.

Autres nuances déjà utilisées dans cette rédaction, à ne pas répéter
à l'identique : {autres_nuances}

Réponds avec un objet JSON unique :
{{
  "ton_personnel": "1 à 2 phrases décrivant cette nuance"
}}""".format(
        zone_nom=zone_nom,
        ton=ton or "(non renseigné)",
        langue_style=langue_style or "(aucun marqueur particulier)",
        nom_cible=nom_cible,
        contexte_specifique=contexte_specifique,
        autres_nuances=" / ".join(autres_nuances) or "(aucune autre pour l'instant)",
    )


def _extraire_repli(raw):
    """Repli si json.loads() échoue (même précaution que
    fix_doublons_journalistes.py, 26 août 2026)."""
    m = re.search(r'"ton_personnel"\s*:\s*"(.+?)"\s*[,}]', raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _generer_ton_personnel(zone_data, nom_cible, contexte_specifique, autres_nuances):
    """Jusqu'à deux appels LLM (retry si réponse vide/mal formée).
    Retourne (ton_ou_None, message)."""
    ton = zone_data.get("ton", "")
    langue_style = zone_data.get("langue_style", "")

    derniere_erreur = "raison inconnue"
    for tentative in range(2):
        prompt = _build_prompt(zone_data.get("nom", ""), ton, langue_style,
                                nom_cible, contexte_specifique, autres_nuances)
        try:
            raw = call_llm(
                system_prompt=SYSTEM_PROMPT, user_prompt=prompt,
                # max_tokens réduit de 200 à 90 (26 août 2026, retour de
                # David après un test réel à ~42 mots malgré la consigne
                # "25 mots maximum") -- un LLM respecte peu fiablement une
                # contrainte de longueur donnée en prose seule ; un vrai
                # plafond technique est un filet bien plus fiable que
                # l'instruction textuelle seule. Calibré large (~25-30
                # mots + l'enveloppe JSON) pour ne jamais tronquer une
                # réponse au milieu d'un mot.
                max_tokens=90, temperature=0.85, task_tier=TASK_TIER,
            ).strip()
        except Exception as e:
            derniere_erreur = "Échec appel LLM : {}".format(e)
            continue

        raw_nettoye = re.sub(r"^```(?:json)?\s*", "", raw)
        raw_nettoye = re.sub(r"\s*```$", "", raw_nettoye).strip()

        try:
            reponse = json.loads(raw_nettoye)
            valeur = (reponse.get("ton_personnel") or "").strip()
        except Exception:
            valeur = _extraire_repli(raw_nettoye) or ""

        if not valeur:
            derniere_erreur = "Réponse LLM vide ou mal formée"
            continue

        # Garde-fou (26 août 2026, retour de David) : la consigne
        # interdit les citations verbatim entre guillemets (risque de
        # répétition mot pour mot dans chaque article signé par cette
        # personne), mais le LLM peut l'ignorer -- un seul retry avec
        # rappel explicite avant d'accepter quand même (jamais de
        # blocage total pour un détail de forme).
        #
        # Bug trouvé en conditions réelles (26 août 2026) : la première
        # version ne vérifiait que « » et " -- une citation entre
        # guillemets simples ASCII ('lois divines') passait au travers
        # sans être détectée. Corrigé avec un motif qui exige une PAIRE
        # de guillemets simples entourant 3 caractères ou plus, pour ne
        # jamais confondre avec une apostrophe normale isolée
        # (contraction comme "l'urgence"/"j'ai", qui n'a jamais de
        # guillemet fermant correspondant à proximité).
        citation_detectee = (
            "«" in valeur or "»" in valeur or '"' in valeur
            or re.search(r"'[\w\s]{3,40}'", valeur)
        )
        if citation_detectee and tentative == 0:
            derniere_erreur = "citation entre guillemets détectée malgré la consigne, retry demandé"
            continue

        # Garde-fou longueur (26 août 2026, retour de David) : la
        # consigne "25 mots maximum" seule n'a pas suffi (~42 mots
        # observés en conditions réelles) -- max_tokens réduit ci-dessus
        # limite déjà le pire des cas, mais cette vérification explicite
        # ajoute un second filet et un retry si le premier essai dépasse
        # nettement la cible (marge de tolérance à 35 mots plutôt que 25
        # strict, pour ne pas retenter sur un dépassement mineur d'un ou
        # deux mots).
        nb_mots = len(valeur.split())
        if nb_mots > 35 and tentative == 0:
            derniere_erreur = "réponse trop longue ({} mots), retry demandé".format(nb_mots)
            continue

        return valeur, "OK"

    return None, "Deux tentatives épuisées -- {}".format(derniere_erreur)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--ligne", required=True, choices=["pro_pouvoir", "opposition"])
    parser.add_argument("--zone-slug", required=True)
    parser.add_argument("--nom", default=None,
                         help="Nom exact d'une personne précise (journaliste ou orateur·rice)")
    parser.add_argument("--all-manquants", action="store_true",
                         help="Génère pour tout le monde dans la zone sans ton_personnel")
    parser.add_argument("--ton-personnel", default=None,
                         help="Valeur donnée directement (mode --nom uniquement) -- "
                              "aucun appel LLM")
    parser.add_argument("--overwrite", action="store_true",
                         help="Remplace une valeur déjà existante (sinon ignorée)")
    parser.add_argument("--dry-run", action="store_true",
                         help="⚠️ Appelle quand même le LLM pour de vrai -- seule "
                              "l'écriture sur disque est court-circuitée.")
    args = parser.parse_args()

    if bool(args.nom) == bool(args.all_manquants):
        print("  ✗ Fournis exactement un des deux : --nom OU --all-manquants.")
        sys.exit(1)
    if args.ton_personnel and args.all_manquants:
        print("  ✗ --ton-personnel n'a de sens qu'avec --nom (une valeur "
              "directe ne peut pas s'appliquer à plusieurs personnes).")
        sys.exit(1)

    journaux = load_journaux()
    try:
        zone_data = journaux[args.scenario][args.ligne]["zones"][args.zone_slug]
    except KeyError:
        print("  ✗ Zone introuvable : {}/{}/{}".format(
            args.scenario, args.ligne, args.zone_slug))
        sys.exit(1)

    # Cibles à traiter : soit une seule personne, soit tout le monde
    # sans ton_personnel dans la zone (journalistes + orateurs).
    if args.nom:
        liste, entree = _trouver_entree(zone_data, args.nom)
        if entree is None:
            print("  ✗ '{}' introuvable dans cette zone (ni journaliste, "
                  "ni orateur·rice).".format(args.nom))
            sys.exit(1)
        cibles = [(liste, entree)]
    else:
        cibles = []
        for j in (zone_data.get("journalistes") or []):
            if args.overwrite or not j.get("ton_personnel"):
                cibles.append((zone_data.get("journalistes"), j))
        for o in (zone_data.get("orateurs") or []):
            if args.overwrite or not o.get("ton_personnel"):
                cibles.append((zone_data.get("orateurs"), o))
        if not cibles:
            print("  Tout le monde dans cette zone a déjà un ton_personnel "
                  "(utilise --overwrite pour régénérer quand même).")
            return

    print("{} personne(s) à traiter...".format(len(cibles)))
    print()

    reussis = []
    echecs = []
    autres_nuances_zone = [
        e.get("ton_personnel") for _, e in
        [(zone_data.get("journalistes"), j) for j in (zone_data.get("journalistes") or [])] +
        [(zone_data.get("orateurs"), o) for o in (zone_data.get("orateurs") or [])]
        if e.get("ton_personnel")
    ]

    for i, (liste, entree) in enumerate(cibles, 1):
        nom = entree.get("nom", "?")
        est_orateur = liste is zone_data.get("orateurs")
        print("[{}/{}] {} ({})".format(
            i, len(cibles), nom, "orateur·rice" if est_orateur else "journaliste"))

        if args.nom and args.ton_personnel:
            valeur, msg = args.ton_personnel, "OK (fourni directement)"
        else:
            contexte = _contexte_specifique(entree, est_orateur)
            try:
                valeur, msg = _generer_ton_personnel(
                    zone_data, nom, contexte, autres_nuances_zone
                )
            except Exception as e:
                valeur, msg = None, "Exception inattendue : {}".format(e)

        if not valeur:
            print("  ✗ {}".format(msg))
            echecs.append((nom, msg))
            continue

        entree["ton_personnel"] = valeur
        autres_nuances_zone.append(valeur)
        print("  ✓ {}".format(valeur))
        reussis.append((nom, valeur))

    print()
    print("=" * 70)
    print("RÉSUMÉ -- {} réussi(s), {} échec(s)".format(len(reussis), len(echecs)))
    print("=" * 70)
    if echecs:
        print("Échecs (à traiter manuellement ou relancer plus tard) :")
        for nom, msg in echecs:
            print("  {} -- {}".format(nom, msg))

    if args.dry_run:
        print()
        print("[dry-run] Rien écrit sur disque.")
        return

    if not reussis:
        print()
        print("Aucun ton_personnel écrit -- journaux.yaml non modifié.")
        return

    backup_path = JOURNAUX_PATH + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(JOURNAUX_PATH, backup_path)
    print()
    print("  ✓ Sauvegarde créée : {}".format(backup_path))

    save_journaux(journaux, dry_run=False)
    print("  ✓ journaux.yaml sauvegardé ({} ton_personnel écrit(s)).".format(len(reussis)))


if __name__ == "__main__":
    main()

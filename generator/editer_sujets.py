#!/usr/bin/env python3
"""
editer_sujets.py — Ourrassol 2098
===================================

Compagnon DESTRUCTIF de audit_sujets.py -- chantier "Suite narrative des
événements", point B, partie édition (5 septembre 2026).

Scindé volontairement du script d'audit en lecture seule : ces
opérations modifient ou suppriment des fichiers déjà publiés, donc
gardes-fous systématiques :
  - Rien n'est écrit/déplacé sans --apply (comme les autres scripts du
    projet -- detect_evenements_cites_retroactif.py, etc.).
  - --dry-run force le mode rapport même si --apply est présent.
  - Une SUPPRESSION ne supprime jamais définitivement : l'article est
    déplacé vers _corbeille/{scenario}/ (horodaté), jamais rm direct --
    décision actée avec David (5 septembre 2026), réversible à la main.
  - Une MODIFICATION DE DATE sauvegarde d'abord une copie intégrale de
    l'article AVANT modification, dans _backups/{scenario}/ (horodaté)
    -- réversible aussi, même si le champ modifié est ciblé. Le nom de
    fichier est aussi mis à jour (fragment de date sans accent, ex.
    "23aout2098"), pour rester cohérent avec le contenu.
  - Toute action (suppression ou modification) est journalisée en une
    ligne JSON dans _corbeille/journal_actions.jsonl (horodatage,
    fichier, action, ancien/nouvel état) -- trace d'audit, jamais purgée
    par ce script.

USAGE
-----
    # Supprimer un article (déplacement vers la corbeille, pas de rm) --
    # rapport seul par défaut, --apply pour exécuter réellement
    python3 editer_sujets.py --scenario new_sustainability \
        --supprimer-article 20260822_183332_....md --apply

    # Modifier la date_evenement d'un article (réordonnancement
    # chronologique) -- même garde-fou --apply
    python3 editer_sujets.py --scenario new_sustainability \
        --modifier-date 20260822_183332_....md \
        --nouvelle-date "23 août 2098" --apply

    # Sortie JSON (même convention que audit_sujets.py --json et
    # audit_sujets_edition.py --json) -- pour intégration GUI
    # (app.py appelle ce script en sous-processus avec --json)
    python3 editer_sujets.py --scenario ... --modifier-date ... \
        --nouvelle-date "..." --json
"""

import argparse
import json
import os
import re
import shutil
import unicodedata
from datetime import datetime

from edition_utils import parser_date_fictive, MOIS_FR

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORBEILLE_DIR = os.path.join(VAULT_ROOT, "_corbeille")
BACKUPS_DIR = os.path.join(VAULT_ROOT, "_backups")
JOURNAL_PATH = os.path.join(CORBEILLE_DIR, "journal_actions.jsonl")

# Pattern du fragment de date dans un nom de fichier généré, ex.
# "..._article_3janvier2098.md" ou "..._article_23aout2098.md" -- notez
# l'absence d'accent dans le nom de fichier (aout, pas août ; fevrier,
# pas février) contrairement à la valeur du frontmatter (date_evenement:
# 23 août 2098) qui, elle, garde les accents.
_RE_FRAGMENT_DATE_FICHIER = re.compile(
    r"^(.*_article_)(\d{1,2})([a-zA-Z]+)(\d{4})(\.md)$"
)


def _sans_accent(texte):
    """'août' -> 'aout', 'février' -> 'fevrier' -- même convention que
    les noms de fichiers déjà générés par le pipeline (voir generate.py/
    api.py, construction du nom de fichier depuis MOIS_FR)."""
    nfkd = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _nouveau_nom_fichier(ancien_nom, jour, mois, annee):
    """Reconstruit le nom de fichier avec le nouveau fragment de date,
    en conservant tel quel le préfixe (horodatage de génération,
    scénario, thématique) et le suffixe ('.md'). Retourne (nouveau_nom,
    None) ou (None, message_erreur) si le nom ne suit pas le format
    attendu -- dans ce cas, la modification de date_evenement est faite
    mais le fichier n'est PAS renommé (mieux vaut un nom de fichier
    incohérent, visible et signalé, qu'un renommage hasardeux)."""
    m = _RE_FRAGMENT_DATE_FICHIER.match(ancien_nom)
    if not m:
        return None, ("nom de fichier ne suit pas le format attendu "
                       "('..._article_JJmoisAAAA.md') -- fichier non renommé, "
                       "à vérifier/renommer à la main si besoin.")
    prefixe, _jour_ancien, _mois_ancien, _annee_ancienne, suffixe = m.groups()
    mois_sans_accent = _sans_accent(MOIS_FR[mois]).lower()
    nouveau_nom = "{}{}{}{}{}".format(prefixe, jour, mois_sans_accent, annee, suffixe)
    return nouveau_nom, None


def find_articles_dir(scenario):
    return os.path.join(VAULT_ROOT, "articles", scenario)


def _journaliser(action, details):
    """Ajoute une ligne au journal d'actions -- jamais purgé, jamais
    écrasé, uniquement ajouté (append). Ce journal est la seule trace
    fiable de ce que ce script a fait, indépendamment de si le fichier
    original a ensuite été retrouvé/restauré à la main ou non."""
    os.makedirs(CORBEILLE_DIR, exist_ok=True)
    entry = {
        "horodatage": datetime.now().isoformat(timespec="seconds"),
        "action": action,
    }
    entry.update(details)
    with open(JOURNAL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _valider_nom_fichier(scenario, fichier):
    """Résout et valide le chemin d'un article -- refuse tout chemin
    hors de articles/{scenario}/ (pas de ../.. ni de chemin absolu vers
    autre chose), pour qu'un nom de fichier mal formé ne puisse jamais
    toucher un fichier hors de son périmètre."""
    if os.path.dirname(fichier) or fichier in (".", ".."):
        return None, "Le nom de fichier ne doit pas contenir de chemin (juste le .md)."
    dossier = find_articles_dir(scenario)
    filepath = os.path.join(dossier, fichier)
    if not os.path.isfile(filepath):
        return None, "Fichier introuvable : {}".format(filepath)
    return filepath, None


# ---------------------------------------------------------------------------
# Suppression (déplacement vers corbeille)
# ---------------------------------------------------------------------------

def supprimer_article(scenario, fichier, apply, dry_run):
    """Retourne un dict structuré {"ok": bool, "error": str|None, ...} --
    utilisé aussi bien par l'affichage console (main()) que par la sortie
    --json (intégration GUI)."""
    filepath, err = _valider_nom_fichier(scenario, fichier)
    if err:
        return {"ok": False, "error": err}

    ecrire = apply and not dry_run
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(CORBEILLE_DIR, scenario)
    dest_path = os.path.join(dest_dir, "{}__{}".format(horodatage, fichier))

    resultat = {
        "ok": True,
        "action": "suppression_article",
        "applique": ecrire,
        "scenario": scenario,
        "fichier_original": fichier,
        "chemin_corbeille": dest_path,
    }

    if not ecrire:
        return resultat

    os.makedirs(dest_dir, exist_ok=True)
    shutil.move(filepath, dest_path)
    _journaliser("suppression_article", {
        "scenario": scenario,
        "fichier_original": fichier,
        "chemin_corbeille": dest_path,
    })
    resultat["journal"] = JOURNAL_PATH
    return resultat


# ---------------------------------------------------------------------------
# Modification de date_evenement (réordonnancement chronologique)
# ---------------------------------------------------------------------------

def modifier_date(scenario, fichier, nouvelle_date_str, apply, dry_run,
                   sync_date_publication=True):
    """Retourne un dict structuré {"ok": bool, "error": str|None, ...}."""
    filepath, err = _valider_nom_fichier(scenario, fichier)
    if err:
        return {"ok": False, "error": err}

    parsed = parser_date_fictive(nouvelle_date_str)
    if not parsed:
        return {"ok": False, "error": (
            "Date invalide ou format non reconnu : {!r} (attendu ex. "
            "'23 août 2098').".format(nouvelle_date_str)
        )}
    jour, mois, annee = parsed
    nouvelle_date_normalisee = "{} {} {}".format(jour, MOIS_FR[mois], annee)

    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    m_date = re.search(r"^date_evenement:\s*(.+)$", raw, re.MULTILINE)
    if not m_date:
        return {"ok": False, "error": (
            "Champ date_evenement introuvable dans le frontmatter -- "
            "abandon (rien de sûr à remplacer).")}
    ancienne_date = m_date.group(1).strip().strip('"').strip("'")

    m_pub = re.search(r"^date_publication:\s*(.+)$", raw, re.MULTILINE)
    ancienne_pub = m_pub.group(1).strip().strip('"').strip("'") if m_pub else None
    pub_etait_synchro = (ancienne_pub == ancienne_date)
    pub_sera_synchronisee = bool(pub_etait_synchro and sync_date_publication)

    nouveau_nom, err_nom = _nouveau_nom_fichier(fichier, jour, mois, annee)
    ecrire = apply and not dry_run

    resultat = {
        "ok": True,
        "action": "modification_date",
        "applique": ecrire,
        "scenario": scenario,
        "fichier_avant": fichier,
        "fichier_apres_prevu": nouveau_nom or fichier,
        "renommage_impossible": err_nom,
        "date_evenement_avant": ancienne_date,
        "date_evenement_apres": nouvelle_date_normalisee,
        "date_publication_avant": ancienne_pub,
        "date_publication_sera_synchronisee": pub_sera_synchronisee,
    }

    if not ecrire:
        return resultat

    # Sauvegarde intégrale AVANT modification, même si l'édition qui
    # suit est ciblée sur une seule ligne -- réversible à la main en
    # recopiant ce fichier par-dessus l'original si besoin.
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUPS_DIR, scenario)
    backup_path = os.path.join(backup_dir, "{}__avant_modif_date__{}".format(
        horodatage, fichier))
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy2(filepath, backup_path)

    nouveau_contenu = re.sub(
        r"^date_evenement:\s*.+$",
        "date_evenement: {}".format(nouvelle_date_normalisee),
        raw, count=1, flags=re.MULTILINE
    )
    if pub_sera_synchronisee:
        nouveau_contenu = re.sub(
            r"^date_publication:\s*.+$",
            "date_publication: {}".format(nouvelle_date_normalisee),
            nouveau_contenu, count=1, flags=re.MULTILINE
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(nouveau_contenu)

    chemin_final = filepath
    renommage_annule_collision = False
    if nouveau_nom and nouveau_nom != fichier:
        nouveau_chemin = os.path.join(os.path.dirname(filepath), nouveau_nom)
        if os.path.exists(nouveau_chemin):
            renommage_annule_collision = True
        else:
            os.rename(filepath, nouveau_chemin)
            chemin_final = nouveau_chemin

    _journaliser("modification_date", {
        "scenario": scenario,
        "fichier_avant": fichier,
        "fichier_apres": os.path.basename(chemin_final),
        "date_evenement_avant": ancienne_date,
        "date_evenement_apres": nouvelle_date_normalisee,
        "date_publication_synchronisee": pub_sera_synchronisee,
        "sauvegarde": backup_path,
    })

    resultat["fichier_apres"] = os.path.basename(chemin_final)
    resultat["renommage_annule_collision"] = renommage_annule_collision
    resultat["sauvegarde"] = backup_path
    resultat["journal"] = JOURNAL_PATH
    return resultat


# ---------------------------------------------------------------------------
# Affichage console (mode humain, --json désactivé)
# ---------------------------------------------------------------------------

def _afficher_suppression(r):
    if not r["ok"]:
        print("[erreur] {}".format(r["error"]))
        return
    print("[{}] Suppression (-> corbeille) : {}".format(
        "APPLIQUÉ" if r["applique"] else "rapport seul", r["fichier_original"]))
    print("  Destination corbeille : {}".format(r["chemin_corbeille"]))
    if not r["applique"]:
        print("  (relancer avec --apply, sans --dry-run, pour exécuter réellement)")
        return
    print("  OK -- déplacé, journalisé dans {}".format(r["journal"]))


def _afficher_modification_date(r):
    if not r["ok"]:
        print("[erreur] {}".format(r["error"]))
        return
    print("[{}] Modification de date : {}".format(
        "APPLIQUÉ" if r["applique"] else "rapport seul", r["fichier_avant"]))
    print("  date_evenement : {!r} -> {!r}".format(
        r["date_evenement_avant"], r["date_evenement_apres"]))
    if r["date_publication_avant"] is not None:
        if r["date_publication_sera_synchronisee"]:
            print("  date_publication : {!r} -> {!r} (synchronisée, était identique "
                  "à date_evenement)".format(r["date_publication_avant"], r["date_evenement_apres"]))
        else:
            print("  date_publication : {!r} -- laissée telle quelle (différait déjà "
                  "de date_evenement, ou synchronisation désactivée)".format(
                      r["date_publication_avant"]))
    print("  Fichier : {} -> {}".format(
        r["fichier_avant"],
        r["fichier_apres_prevu"] if not r.get("renommage_impossible")
        else "(inchangé -- {})".format(r["renommage_impossible"])))

    if not r["applique"]:
        print("  (relancer avec --apply, sans --dry-run, pour exécuter réellement)")
        return

    if r.get("renommage_annule_collision"):
        print("  [ATTENTION] Un fichier nommé {} existe déjà -- renommage annulé, "
              "le contenu est modifié mais le fichier garde son nom actuel. À "
              "renommer à la main si besoin.".format(r["fichier_apres_prevu"]))
    elif r["fichier_apres"] != r["fichier_avant"]:
        print("  Fichier renommé : {} -> {}".format(r["fichier_avant"], r["fichier_apres"]))
    print("  OK -- écrit, sauvegarde dans {}, journalisé dans {}".format(
        r["sauvegarde"], r["journal"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--supprimer-article", metavar="FICHIER", default=None,
                         help="Nom du fichier (dans articles/{scenario}/) à déplacer "
                              "vers la corbeille.")
    parser.add_argument("--modifier-date", metavar="FICHIER", default=None,
                         help="Nom du fichier (dans articles/{scenario}/) dont on "
                              "modifie date_evenement.")
    parser.add_argument("--nouvelle-date", default=None,
                         help="Nouvelle date (ex. '23 août 2098') -- requis avec --modifier-date.")
    parser.add_argument("--no-sync-date-publication", action="store_true",
                         help="Ne pas synchroniser date_publication même si elle était "
                              "identique à date_evenement avant modification.")
    parser.add_argument("--apply", action="store_true",
                         help="Exécute réellement l'action. Sans ce flag : rapport seul.")
    parser.add_argument("--dry-run", action="store_true",
                         help="Force le mode rapport même si --apply est présent.")
    parser.add_argument("--json", action="store_true",
                         help="Sortie JSON sur une seule ligne finale (même convention "
                              "que audit_sujets.py --json), pour intégration GUI.")
    args = parser.parse_args()

    if bool(args.supprimer_article) == bool(args.modifier_date):
        msg = "Fournir exactement une action : --supprimer-article OU --modifier-date."
        if args.json:
            print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
        else:
            print("[erreur] {}".format(msg))
        raise SystemExit(1)

    if args.supprimer_article:
        resultat = supprimer_article(args.scenario, args.supprimer_article,
                                      args.apply, args.dry_run)
        afficher = _afficher_suppression
    else:
        if not args.nouvelle_date:
            msg = "--nouvelle-date est requis avec --modifier-date."
            if args.json:
                print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
            else:
                print("[erreur] {}".format(msg))
            raise SystemExit(1)
        resultat = modifier_date(args.scenario, args.modifier_date, args.nouvelle_date,
                                  args.apply, args.dry_run,
                                  sync_date_publication=not args.no_sync_date_publication)
        afficher = _afficher_modification_date

    if args.json:
        print(json.dumps(resultat, ensure_ascii=False))
    else:
        afficher(resultat)


if __name__ == "__main__":
    main()

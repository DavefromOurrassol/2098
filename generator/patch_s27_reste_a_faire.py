#!/usr/bin/env python3
"""
patch_s27_reste_a_faire.py — Ourrassol 2098 (S27, phase 4, 17 octobre 2026)
==========================================================================

Modifie generator/appliquer_et_si.py :
  1. Check-list « reste à faire » : documentation/need_action/et_si_<id>_reste_a_faire.md,
     seulement ce qui reste à la main après application (phrases en entier avec
     le fait qui les contredit, nouvelles entités en YAML, brouillon de règle de
     lore, articles à relire calculés depuis le vault, opérations ⚠ laissées de
     côté, commandes de fin). Écrite avec --apply, ou seule avec --reste-a-faire
     (aucune modification du vault). Aucun appel IA.
  2. Affichage : « déjà appliqué / présente / absente » marqué « · », plus « ⚠ ».
  3. Journal .applique.json : n'est plus écrasé par une relance qui n'applique rien.

Sauvegarde : generator/appliquer_et_si.py.bak_reste. Refuse un second passage.

USAGE (depuis la racine du vault)
    python3 generator/patch_s27_reste_a_faire.py
"""

import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "appliquer_et_si.py"
MARQUEUR = "def ecrire_reste_a_faire("

REMPLACEMENTS = [
    # 1. Nouvelles fonctions, avant lancer()
    (
        "def lancer(cmd):\n",
        r'''# ---------------------------------------------------------------------------
# Check-list « reste à faire » (17 oct 2026)
# ---------------------------------------------------------------------------

NEED_ACTION = VAULT / "documentation" / "need_action"


def _articles_concernes(sc, entites, zones):
    """Articles du scénario qui citent une entité touchée ou dont la zone principale a changé."""
    trouves = []
    racine = VAULT / "articles"
    if not racine.exists():
        return trouves
    courts = {e: e[: -len(sc) - 1] if e.endswith("_" + sc) else e for e in entites}
    for p in sorted(racine.rglob("*.md")):
        if p.name.startswith("_"):
            continue
        try:
            d = decoupe(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        fm = lire_fm(d[1]) if d else None
        if not fm or fm.get("scenario") != sc:
            continue
        cites = {str(x) for x in (fm.get("entites_citees") or []) if x}
        motifs = [f"cite `{e}`" for e in entites if e in cites or courts[e] in cites]
        if fm.get("zone_principale") in zones:
            motifs.append(f"zone `{fm['zone_principale']}`")
        if motifs:
            titre = fm.get("titre") or fm.get("title") or p.stem
            date = fm.get("date_evenement") or fm.get("date_publication") or ""
            trouves.append((p.relative_to(VAULT), str(titre).strip(), date, motifs))
    return trouves


def ecrire_reste_a_faire(data, ops, rapport_ok=True):
    """Écrit documentation/need_action/et_si_<id>_reste_a_faire.md. Retourne le chemin."""
    hid, annee = data["id"], int(data["annee"]) if data.get("annee") is not None else None
    L = [f"# Reste à faire à la main — {hid}", "",
         f"*Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')} par appliquer_et_si.py, à partir de la "
         f"simulation du {data.get('date_simulation')} ({data.get('version')}). Les opérations mécaniques "
         "(zones, trajectoires, relations) sont déjà appliquées : ne figure ici que ce qui reste à la main.*", ""]
    n = 0

    def case(texte):
        nonlocal n
        n += 1
        L.append(f"- [ ] {n}. {texte}")

    faites = lambda o: o.get("retenue") or o.get("alerte") == "déjà appliqué"
    for sc in data["scenarios"]:
        ps = data["par_scenario"].get(sc) or {}
        lec, pas = ps.get("lecture") or {}, ps.get("passe") or {}
        mes_ops = [o for o in ops if o["sc"] == sc]
        L += [f"## {sc}", ""]

        # Opérations laissées de côté (⚠)
        cote = [o for o in mes_ops if not o.get("retenue") and o.get("alerte")
                and not str(o["alerte"]).startswith("déjà")]
        if cote:
            L += ["### Décisions laissées de côté (⚠)", ""]
            for o in cote:
                case(f"{o['texte']} — ⚠ {o['alerte']}. Garder tel quel, ou "
                     f"`python3 generator/appliquer_et_si.py --id {hid} --inclure {o['n']} --apply`.")
            L.append("")

        # Phrases à corriger
        textes = pas.get("textes") or []
        if textes:
            L += ["### Phrases à corriger", ""]
            for t in textes:
                dossier = "instances" if t.get("genre", "instance") == "instance" else "event_instances"
                case(f"`{dossier}/{t['slug']}.md` ({t.get('nom') or t['slug']})")
                L.append(f"  - Phrase : « {t.get('extrait')} »")
                if t.get("contredit"):
                    L.append(f"  - Contredite par : {t['contredit']}")
                if not t.get("extrait_trouve", True):
                    L.append("  - ⚠ extrait introuvable mot pour mot dans la fiche : chercher la phrase voisine.")
            L.append("")

        # Nouvelles entités
        nouv = lec.get("nouvelles_entites") or []
        if nouv:
            L += ["### Nouvelles entités proposées (facultatif)", ""]
            case(f"{len(nouv)} entité(s) : choisir `category`, garder ou retirer chaque entrée, coller dans "
                 "`entites_custom/queue.yaml`, puis `python3 generator/create_entities_and_instances.py --mode custom`.")
            L += ["", "```yaml"]
            for e in nouv:
                L += [f"- nom: {e.get('nom')}", "  category: <à choisir>", f"  role: {e.get('role')}",
                      "  etat: émergent", f"  scenario_ref: {sc}", "  scenario_hint:", f"  - {sc}"]
                if e.get("zone"):
                    L.append(f"  zone_hint: {e['zone']}")
                L.append(f"  source: et_si_{hid}")
            L += ["```", ""]

        # Règle de lore (brouillon)
        disparues = [o for o in mes_ops if o["genre"] == "trajectoire" and o.get("apres") == "disparu" and faites(o)]
        if disparues or data.get("contraintes"):
            L += ["### Règle de lore (brouillon)", ""]
            case(f"Relire puis ajouter à `documentation/lore_regles.yaml`, section `{sc}` "
                 "(vérifier le format sur une règle existante, par exemple `bruxelles_pas_un_centre`).")
            L += ["", "```yaml", f"# section {sc} > regles"]
            for o in disparues:
                nom = re.sub(r"\s*\(`.*$", "", o["texte"])
                L += [f"- id: {o['instance'][: -len(sc) - 1] if o['instance'].endswith('_' + sc) else o['instance']}_disparu_{annee}",
                      f"  termes: [\"{nom}\"]", "  gravite: a_relire",
                      f"  message: \"{nom} disparaît en {annee} ({data.get('nom') or hid}) : "
                      f"toute mention au présent après {annee} est fausse.\""]
            for c in data.get("contraintes") or []:
                L.append(f"# contrainte à transformer si besoin : {c}")
            L += ["```", ""]

        # Articles
        ents = [o["instance"] for o in mes_ops if o["genre"] == "trajectoire" and faites(o)]
        zones = {o["zone"] for o in mes_ops if o["genre"] == "zone" and faites(o)}
        arts = _articles_concernes(sc, ents, zones)
        L += ["### Articles à relire", ""]
        if arts:
            for chemin, titre, date, motifs in arts:
                case(f"`{chemin}` — *{titre}*" + (f", {date}" if date else "") + f" ({', '.join(motifs)})")
        else:
            L.append("Aucun article du vault ne cite une entité touchée ni n'a pour zone une zone changée.")
        L.append("")

        # Fin
        L += ["### Pour finir", ""]
        case(f"Relecture du lore : `python3 generator/audit_lore.py --scenario {sc}` (puis étapes 2 et 3 de "
             "Relations & lore si besoin)")
        case(f"Résumé du scénario (payant, un appel) : `python3 generator/generate_resume_scenarios.py --scenario {sc}`")
        L.append("")

    L += ["## Site", ""]
    case("Si des articles ont été corrigés : `python3 generator/chapos_revues.py`, puis `bash generator/publier_site.sh`")
    L += ["", "## Non repris ici", "",
          f"Les « possibles » de la passe exhaustive, la carte et les fiches trouvées par mots-clés restent "
          f"dans le rapport du simulateur : `documentation/need_action/et_si_{hid}.md`"
          + ("" if rapport_ok else " (introuvable : resimuler pour le régénérer)") + "."]
    NEED_ACTION.mkdir(parents=True, exist_ok=True)
    sortie = NEED_ACTION / f"et_si_{hid}_reste_a_faire.md"
    sortie.write_text("\n".join(L) + "\n", encoding="utf-8")
    return sortie


def lancer(cmd):
''',
    ),
    # 2. Option --reste-a-faire
    (
        '    ap.add_argument("--apply", action="store_true")\n',
        '    ap.add_argument("--apply", action="store_true")\n'
        '    ap.add_argument("--reste-a-faire", action="store_true",\n'
        '                    help="écrit seulement la check-list des tâches à la main (vault inchangé)")\n',
    ),
    # 3. Affichage « déjà … »
    (
        '        if o["alerte"]:\n'
        '            ligne += f"\\n         ⚠ {o[\'alerte\']}"',
        '        if o["alerte"] and str(o["alerte"]).startswith("déjà"):\n'
        '            ligne += f"\\n         · {o[\'alerte\']}"\n'
        '        elif o["alerte"]:\n'
        '            ligne += f"\\n         ⚠ {o[\'alerte\']}"',
    ),
    # 4. --reste-a-faire seul (après l'aperçu)
    (
        '    if not a.apply:\n'
        '        print("Relancer avec --apply pour écrire (sauvegarde .bak_appliquer), --sauter / --inclure pour trier.")\n'
        '        return\n',
        '    rapport_ok = (VAULT / "documentation" / "need_action" / f"et_si_{a.id}.md").exists()\n'
        '    if not a.apply:\n'
        '        if a.reste_a_faire:\n'
        '            p = ecrire_reste_a_faire(data, ops, rapport_ok)\n'
        '            print(f"\\n✓ check-list : {p.relative_to(VAULT)} (vault inchangé)")\n'
        '            return\n'
        '        print("Relancer avec --apply pour écrire (sauvegarde .bak_appliquer), --sauter / --inclure pour trier ;")\n'
        '        print("--reste-a-faire pour écrire seulement la check-list des tâches à la main.")\n'
        '        return\n',
    ),
    # 5. Journal non écrasé par une relance vide + check-list après --apply
    (
        '    lancer(["generator/validate.py"])\n'
        '    journal = APP_DIR / f"{a.id}.applique.json"\n',
        '    lancer(["generator/validate.py"])\n'
        '    p = ecrire_reste_a_faire(data, ops, rapport_ok)\n'
        '    print(f"✓ check-list : {p.relative_to(VAULT)}")\n'
        '    journal = APP_DIR / f"{a.id}.applique.json"\n'
        '    if n == 0 and journal.exists():\n'
        '        print(f"· rien de nouveau appliqué : journal {journal.relative_to(VAULT)} inchangé")\n'
        '        return\n',
    ),
]


def main():
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable")
    texte = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit("✗ patch déjà appliqué (ecrire_reste_a_faire présent) : rien fait.")
    for ancre, _ in REMPLACEMENTS:
        if texte.count(ancre) != 1:
            sys.exit(f"✗ ancre trouvée {texte.count(ancre)} fois au lieu d'une : rien fait.\n---\n{ancre[:200]}")
    for ancre, nouveau in REMPLACEMENTS:
        texte = texte.replace(ancre, nouveau)
    compile(texte, str(CIBLE), "exec")
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_reste"))
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"✓ {CIBLE.name} modifié ({len(REMPLACEMENTS)} remplacements), sauvegarde .bak_reste")


if __name__ == "__main__":
    main()

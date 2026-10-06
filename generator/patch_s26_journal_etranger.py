"""
patch_s26_journal_etranger.py — S26 (6 octobre 2026)
----------------------------------------------------
Mode Forcer : un journal d'une AUTRE zone peut couvrir l'élément forcé.

generate.py
  - nouvel argument --forcer-zone-journal <zone_slug> (ou forcer_zone_journal
    dans config.yaml) ;
  - scénarios limités à ceux où cette zone a une rédaction pour la ligne
    éditoriale choisie ;
  - par scénario : zone_slug = zone du journal (journal, signature,
    zone_principale suivent), zone_evenement = zone de l'élément forcé.

prompt_builder.py
  - build_journalistic_brief() : si zone_evenement != zone_slug, consigne
    « couverture d'un fait étranger » à la place de « ancré dans la zone » ;
  - build_geographie_context() : la zone de l'événement est aussi détaillée.

Usage (depuis generator/) :
    python3 patch_s26_journal_etranger.py          # aperçu, rien écrit
    python3 patch_s26_journal_etranger.py --apply  # écrit (.bak_s26)
Refuse un second passage (marqueur « S26 » déjà présent).
"""

import os
import shutil
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
MARQUEUR = "S26 (6 octobre 2026)"

# ─────────────────────────── generate.py ───────────────────────────

GEN_ARG_ANCRE = '    parser.add_argument("--forcer-zone", nargs="+", default=None)\n'
GEN_ARG_NOUVEAU = GEN_ARG_ANCRE + (
    '    # S26 (6 octobre 2026) : journal d\'une AUTRE zone que celle de l\'élément\n'
    '    # forcé -- vide (défaut) = comportement inchangé.\n'
    '    parser.add_argument("--forcer-zone-journal", default=None)\n'
)

GEN_FILTRE_ANCRE = "    resultats = []\n    for scenario_slug in scenarios_a_traiter:\n"
GEN_FILTRE_NOUVEAU = (
    "    # S26 (6 octobre 2026) : couverture par le journal d'une autre zone.\n"
    "    # Seuls les scénarios où cette zone a une rédaction (ligne choisie)\n"
    "    # sont gardés -- une zone n'existe en général que dans un scénario.\n"
    "    zone_journal = cli_args.forcer_zone_journal or config.get(\"forcer_zone_journal\") or None\n"
    "    if zone_journal:\n"
    "        from prompt_builder import _load_journaux\n"
    "        _jx = _load_journaux()\n"
    "        _ligne = config.get(\"ligne_editoriale\") or \"pro_pouvoir\"\n"
    "        avec_journal = [\n"
    "            sc for sc in scenarios_a_traiter\n"
    "            if zone_journal in ((_jx.get(sc, {}).get(_ligne, {}) or {}).get(\"zones\") or {})\n"
    "        ]\n"
    "        if not avec_journal:\n"
    "            print(\"\\n[erreur] La zone {!r} n'a pas de rédaction {} dans les scénarios \"\n"
    "                  \"retenus pour cet élément ({}).\".format(\n"
    "                      zone_journal, _ligne, \", \".join(scenarios_a_traiter)))\n"
    "            sys.exit(1)\n"
    "        ecartes = [sc for sc in scenarios_a_traiter if sc not in avec_journal]\n"
    "        if ecartes:\n"
    "            print(\"[generate] S26 — scénario(s) écarté(s), pas de rédaction {} : {}\".format(\n"
    "                zone_journal, \", \".join(ecartes)))\n"
    "        scenarios_a_traiter = avec_journal\n"
    "\n"
) + GEN_FILTRE_ANCRE

GEN_BOUCLE_ANCRE = (
    "        if zones_ici:\n"
    "            config_scenario[\"zone_slug\"] = zones_ici[0]\n"
    "            print(\"[generate] Zone d'ancrage pour {} : {}\".format(scenario_slug, zones_ici[0]))\n"
)
GEN_BOUCLE_NOUVEAU = GEN_BOUCLE_ANCRE + (
    "        # S26 (6 octobre 2026) : le journal de zone_journal écrit ; la zone\n"
    "        # de l'élément devient zone_evenement (consigne « fait étranger »).\n"
    "        if zone_journal:\n"
    "            config_scenario[\"zone_evenement\"] = zones_ici[0] if zones_ici else None\n"
    "            config_scenario[\"zone_slug\"] = zone_journal\n"
    "            print(\"[generate] S26 — journal de la zone {} ; fait couvert : {}\".format(\n"
    "                zone_journal, config_scenario[\"zone_evenement\"] or \"(zone de l'élément inconnue)\"))\n"
)

# ─────────────────────────── prompt_builder.py ───────────────────────────

PB_BRIEF_ANCRE = "    zone_slug_article = config.get(\"zone_slug\") or (snapshot or {}).get(\"zone_slug\")\n    if zone_slug_article:\n"
PB_BRIEF_NOUVEAU = (
    "    # S26 (6 octobre 2026) : journal d'une autre zone que le fait couvert\n"
    "    # (mode Forcer, --forcer-zone-journal). Remplace la consigne d'ancrage.\n"
    "    zone_evenement = config.get(\"zone_evenement\")\n"
    "    zone_journal_cfg = config.get(\"zone_slug\")\n"
    "    couverture_etrangere = bool(zone_evenement and zone_journal_cfg\n"
    "                                and zone_evenement != zone_journal_cfg)\n"
    "    if couverture_etrangere:\n"
    "        _sc = config.get(\"scenario\") or (snapshot or {}).get(\"scenario_slug\")\n"
    "        _noms = {z[\"slug\"]: z.get(\"nom\", z[\"slug\"])\n"
    "                 for z in _load_geographie(_sc) if z.get(\"slug\")}\n"
    "        _ev = _noms.get(zone_evenement, zone_evenement.replace(\"_\", \" \").title())\n"
    "        _jn = _noms.get(zone_journal_cfg, zone_journal_cfg.replace(\"_\", \" \").title())\n"
    "        lines.append(\n"
    "            \"- **Couverture d'un fait étranger** : le fait principal de cet article \"\n"
    "            \"se déroule dans la zone **{ev}**, mais tu écris pour un journal de la \"\n"
    "            \"zone **{jn}**, pour ses lecteurs. La date et le lieu de publication \"\n"
    "            \"sous le titre sont ceux de ta rédaction (zone {jn}). Tu ne prétends \"\n"
    "            \"jamais être sur place : tu t'appuies sur des sources à distance \"\n"
    "            \"(dépêches, correspondant·e, témoignages relayés, communiqués) et tu \"\n"
    "            \"peux le dire. Raconte le fait avec précision, puis regarde-le depuis \"\n"
    "            \"ta zone : ce qu'il change ou pourrait changer pour tes lecteurs \"\n"
    "            \"(économie, alliances, sécurité, ressources, communautés liées), \"\n"
    "            \"comment ta zone et ses acteurs réagissent. Les lieux, la culture et \"\n"
    "            \"la langue de la zone {ev} restent les siens : ne les transpose pas \"\n"
    "            \"chez toi, et ne transpose pas les tiens chez elle.\".format(ev=_ev, jn=_jn)\n"
    "        )\n"
    "    zone_slug_article = config.get(\"zone_slug\") or (snapshot or {}).get(\"zone_slug\")\n"
    "    if zone_slug_article and not couverture_etrangere:\n"
)

PB_GEO_ANCRE = "    # Tri : zones pertinentes d'abord (niveau croissant), autres ensuite\n"
PB_GEO_NOUVEAU = (
    "    # S26 (6 octobre 2026) : en couverture d'un fait étranger, la zone du\n"
    "    # fait est aussi détaillée (description, tensions, alliés).\n"
    "    zone_evenement = (config or {}).get(\"zone_evenement\")\n"
    "    if zone_evenement and zone_evenement in slug_to_zone:\n"
    "        zones_pertinentes.update(collect_zone_chain(zone_evenement, zone_evenement))\n"
    "\n"
) + PB_GEO_ANCRE

FICHIERS = {
    "generate.py": [
        ("argument --forcer-zone-journal", GEN_ARG_ANCRE, GEN_ARG_NOUVEAU),
        ("filtre des scénarios", GEN_FILTRE_ANCRE, GEN_FILTRE_NOUVEAU),
        ("zones par scénario", GEN_BOUCLE_ANCRE, GEN_BOUCLE_NOUVEAU),
    ],
    "prompt_builder.py": [
        ("consigne fait étranger", PB_BRIEF_ANCRE, PB_BRIEF_NOUVEAU),
        ("géographie zone de l'événement", PB_GEO_ANCRE, PB_GEO_NOUVEAU),
    ],
}


def main():
    apply = "--apply" in sys.argv
    nouveaux = {}
    ok = True
    for nom, remplacements in FICHIERS.items():
        chemin = os.path.join(ICI, nom)
        if not os.path.exists(chemin):
            print("✗ {} introuvable ({})".format(nom, chemin))
            ok = False
            continue
        texte = open(chemin, encoding="utf-8").read()
        if MARQUEUR in texte:
            print("✗ {} : déjà patché (marqueur « {} » présent) — rien à faire.".format(nom, MARQUEUR))
            ok = False
            continue
        for libelle, ancre, nouveau in remplacements:
            n = texte.count(ancre)
            if n != 1:
                print("✗ {} : ancre « {} » trouvée {} fois (attendu 1).".format(nom, libelle, n))
                ok = False
                continue
            texte = texte.replace(ancre, nouveau)
            print("✓ {} : {}".format(nom, libelle))
        nouveaux[nom] = texte

    if not ok:
        print("\nRien écrit.")
        sys.exit(1)

    # Contrôle de syntaxe avant écriture
    for nom, texte in nouveaux.items():
        try:
            compile(texte, nom, "exec")
        except SyntaxError as e:
            print("✗ {} : erreur de syntaxe après patch ({}). Rien écrit.".format(nom, e))
            sys.exit(1)

    if not apply:
        print("\nAperçu seulement — relancer avec --apply pour écrire.")
        return

    for nom, texte in nouveaux.items():
        chemin = os.path.join(ICI, nom)
        shutil.copy2(chemin, chemin + ".bak_s26")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(texte)
        print("✓ {} écrit (sauvegarde {}.bak_s26)".format(nom, nom))


if __name__ == "__main__":
    main()

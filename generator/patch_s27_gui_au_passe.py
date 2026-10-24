#!/usr/bin/env python3
"""
patch_s27_gui_au_passe.py — 24 octobre 2026 (S27, point 9, automatisation).

Les fiches des entités qui disparaissent passent au passé dans le parcours :
  - étape ④ « Appliquer » : pour chaque entité qui vient de disparaître, l'aperçu
    fiche_au_passe.py se lance tout seul (un appel IA par entité) ;
  - étape ⑤, rubrique « Fiches des entités disparues (au passé) » : état, boutons
    « Ouvrir l'avant/après ↗ » (Obsidian, retouchable), « Écrire dans la fiche »,
    « Refaire l'aperçu (IA) », « Ouvrir la fiche ↗ » ;
  - check-list : renvoie à cette rubrique (au lieu d'une commande de terminal).

Cibles (tout ou rien, sauvegardes .bak_s27_gui_au_passe) :
  generator/et_si_main.py      état « disparues », action --au-passe SLUG [--apply]
  generator/appliquer_et_si.py aperçu automatique après l'application ; check-list
  gui/app.py                   route /api/et_si/main/au_passe/<apercu|ecrire>
  gui/static/app.js            rubrique de l'étape ⑤
Prérequis : generator/fiche_au_passe.py posé. Que patch_s27_checklist_au_passe.py ait
été appliqué ou non, la check-list est mise à la nouvelle formulation.
Refuse un second passage. Redémarrer Flask ensuite.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_gui_au_passe.py
"""

import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
VAULT = GEN.parent
MARQUEUR = "PATCH_S27_GUI_AU_PASSE"

# ---------------------------------------------------------------- et_si_main.py
FONCTIONS_MAIN = '''# PATCH_S27_GUI_AU_PASSE (24 oct 2026) : fiches des entités disparues, à mettre au passé.
def fiches_disparues(data, suivi):
    """Entités que la phase 4 a fait disparaître (trajectoire « disparu » appliquée)."""
    ops, _ = ap.construire_plan(data)
    faites = suivi.get("au_passe") or {}
    out = []
    for o in ops:
        if o["genre"] != "trajectoire" or o.get("apres") != "disparu" or o.get("alerte") != "déjà appliqué":
            continue
        slug = o["instance"]
        rap = VAULT / "documentation" / "need_action" / f"fiche_au_passe_{slug}.md"
        out.append({"slug": slug, "sc": o["sc"], "nom": re.sub(r"\\s*\\(`.*$", "", o["texte"]),
                    "etat": "ecrite" if slug in faites else ("apercu" if rap.exists() else "a_faire"),
                    "rapport": str(rap.relative_to(VAULT)) if rap.exists() else None,
                    "date": faites.get(slug)})
    return out


def au_passe(hid, data, slug, apply):
    if slug not in {f["slug"] for f in fiches_disparues(data, lire_suivi(hid))}:
        sys.exit(f"✗ {slug} : pas une entité disparue de cette hypothèse (trajectoire appliquée)")
    cmd = [sys.executable, str(GEN / "fiche_au_passe.py"), "--slug", slug]
    cmd += ["--apply"] if apply else ["--contexte", f"{data.get('nom') or hid} ({_annee(data)})"]
    try:
        r = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True, timeout=280, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        print("✗ délai dépassé (280 s)")
        return 1
    print("\\n".join(s for s in (r.stdout.strip(), r.stderr.strip()) if s))
    if apply and r.returncode == 0:
        suivi = lire_suivi(hid)
        suivi.setdefault("au_passe", {})[slug] = maintenant()
        ecrire_suivi(hid, suivi)
    return r.returncode


def lancer(action, sc, data):'''

MAIN = [
    ("def lancer(action, sc, data):", FONCTIONS_MAIN),
    (
        "    return out\n\n\ndef main():",
        "    try:   # PATCH_S27_GUI_AU_PASSE\n"
        "        out[\"disparues\"] = fiches_disparues(data, suivi)\n"
        "    except Exception as e:\n"
        "        out[\"disparues\"] = []\n"
        "        out[\"erreurs\"].append(f\"fiches disparues : {type(e).__name__}: {e}\")\n"
        "    return out\n\n\ndef main():",
    ),
    (
        '    a.add_argument("--scenario")\n',
        '    a.add_argument("--au-passe", metavar="SLUG",   # PATCH_S27_GUI_AU_PASSE\n'
        '                   help="fiche d\'une entité disparue au passé : aperçu (un appel IA), --apply pour écrire")\n'
        '    a.add_argument("--scenario")\n',
    ),
    (
        "    if x.lancer:\n",
        "    if x.au_passe:   # PATCH_S27_GUI_AU_PASSE\n"
        "        return au_passe(x.id, data, x.au_passe, x.apply)\n"
        "    if x.lancer:\n",
    ),
]

# ----------------------------------------------------------- appliquer_et_si.py
CASE_ANCIENNE = (
    "                case(f\"`instances/{o['instance']}.md` est-elle encore écrite au présent ? \"\n"
    "                     f\"`python3 generator/fiche_au_passe.py --slug {o['instance']}` (aperçu, un appel IA), relire \"\n"
    "                     f\"`documentation/need_action/fiche_au_passe_{o['instance']}.md`, puis la même commande avec \"\n"
    "                     \"`--apply`.\")\n")
CASE_NOUVELLE = (
    "                case(f\"`instances/{o['instance']}.md` au passé : étape ⑤, rubrique « Fiches des entités \"\n"
    "                     f\"disparues » (aperçu fait à l'application : `documentation/need_action/fiche_au_passe_\"\n"
    "                     f\"{o['instance']}.md`) ; relire, retoucher si besoin, puis « Écrire dans la fiche ».\")\n")
LORE_ANCRE = ("        # Règle de lore (brouillon)\n"
              "        disparues = [o for o in mes_ops if o[\"genre\"] == \"trajectoire\" and o.get(\"apres\") == \"disparu\" and faites(o)]\n")
BLOC_CHECKLIST = LORE_ANCRE + (
    "        if disparues:   # PATCH_S27_AU_PASSE : la phase 4 change la trajectoire, pas le texte\n"
    "            L += [\"### Fiches des entités disparues (au passé)\", \"\"]\n"
    "            for o in disparues:\n" + CASE_NOUVELLE +
    "            L.append(\"\")\n")
AUTO = [(
    '    lancer(["generator/validate.py"])\n',
    '    lancer(["generator/validate.py"])\n'
    '    # PATCH_S27_GUI_AU_PASSE : aperçu « au passé » des fiches qui viennent de disparaître (un appel IA\n'
    '    # chacune) ; relecture et écriture à l\'étape ⑤.\n'
    '    for o in retenues:\n'
    '        if o["genre"] == "trajectoire" and o.get("apres") == "disparu" and fiche(o["instance"]).exists():\n'
    '            lancer(["generator/fiche_au_passe.py", "--slug", o["instance"], "--contexte",\n'
    '                    f"{data.get(\'nom\') or a.id} ({data.get(\'annee\')})"])\n',
)]

# ------------------------------------------------------------------- gui/app.py
APP_PY = [
    (
        '                 "journal": 300}   # PATCH_S27_JOURNAUX\n',
        '                 "journal": 300,   # PATCH_S27_JOURNAUX\n'
        '                 "au_passe": 300}   # PATCH_S27_GUI_AU_PASSE\n',
    ),
    (
        '    elif quoi == "articles" and action == "verifier":',
        '    elif (quoi == "au_passe" and action in ("apercu", "ecrire")   # PATCH_S27_GUI_AU_PASSE\n'
        '          and re.match(r"^[a-z0-9_]+$", str(data.get("slug") or ""))):\n'
        '        cmd += ["--au-passe", str(data["slug"])] + (["--apply"] if action == "ecrire" else [])\n'
        '    elif quoi == "articles" and action == "verifier":',
    ),
]

# ------------------------------------------------------------- gui/static/app.js
RUBRIQUE = r"""    // PATCH_S27_GUI_AU_PASSE : fiches des entités disparues, mises au passé (fiche_au_passe.py).
    const disp = etat.disparues || [];
    if (disp.length) {
      zoneMain.appendChild(sousTitre('Fiches des entités disparues (au passé)'));
      const ETATS_AP = { a_faire: ['· aperçu pas encore fait', '#888'],
                         apercu: ['⚠ avant / après prêt : à relire, puis « Écrire dans la fiche »', '#b9770e'],
                         ecrite: ['✓ écrite dans la fiche', '#1e8449'] };
      disp.forEach(f => {
        const bloc = mk('div');
        Object.assign(bloc.style, { margin: '6px 0', paddingLeft: '8px', borderLeft: '2px solid #ddd' });
        const titre = mk('div', 'option-label', `${f.nom} (${f.slug}) — ${f.sc}`);
        Object.assign(titre.style, { textTransform: 'none', letterSpacing: 'normal', fontSize: '12px',
                                     color: 'var(--text)' });
        bloc.appendChild(titre);
        const [txt, col] = ETATS_AP[f.etat] || ['?', '#888'];
        const st = mk('div', 'option-desc', txt + (f.date ? ` (${f.date})` : ''));
        st.style.color = col;
        bloc.appendChild(st);
        const l = mk('div');
        if (f.rapport) {
          const bO = bouton('Ouvrir l\'avant / après ↗');
          bO.addEventListener('click', () => _panneauOuvrirDansObsidian(f.rapport));
          l.appendChild(bO);
        }
        if (f.rapport && f.etat !== 'ecrite') {
          const bE = bouton('Écrire dans la fiche', 'yaml-btn yaml-btn-save');
          bE.addEventListener('click', () => {
            if (!confirm('Écrire dans la fiche les textes « Après » de l\'avant / après (retouches comprises) ?'
                         + '\n(Sauvegarde .bak_au_passe.)')) return;
            appeler('main/au_passe', 'ecrire', { slug: f.slug });
          });
          l.appendChild(bE);
          tous.push(bE);
        }
        const bP = bouton(f.etat === 'a_faire' ? 'Mettre au passé (IA)' : 'Refaire l\'aperçu (IA)');
        bP.addEventListener('click', () => {
          if (!confirm('Un appel IA : nouvel avant / après (les retouches faites dans l\'ancien sont perdues) ; '
                       + 'la fiche n\'est pas modifiée. Continuer ?')) return;
          appeler('main/au_passe', 'apercu', { slug: f.slug });
        });
        l.appendChild(bP);
        tous.push(bP);
        const bF = bouton('Ouvrir la fiche ↗');
        bF.addEventListener('click', () => _panneauOuvrirDansObsidian(`instances/${f.slug}.md`));
        l.appendChild(bF);
        bloc.appendChild(l);
        zoneMain.appendChild(bloc);
      });
    }

"""
APP_JS = [
    (
        "                    ['Règle', '📜'], ['Pour finir', '🏁']];   // PATCH_S27_CARTE_MAIN\n",
        "                    ['Règle', '📜'], ['Pour finir', '🏁'], ['Fiches', '⏳']];   // PATCH_S27_CARTE_MAIN / GUI_AU_PASSE\n",
    ),
    (
        "    // PATCH_S27_ARTICLES : articles à relire -- repérage par l'IA, jamais d'écriture dans un article.\n",
        RUBRIQUE + "    // PATCH_S27_ARTICLES : articles à relire -- repérage par l'IA, jamais d'écriture dans un article.\n",
    ),
]


def appliquer_remplacements(texte, rempl, nom):
    for i, (ancien, nouveau) in enumerate(rempl, 1):
        n = texte.count(ancien)
        if n != 1:
            raise ValueError(f"{nom} : remplacement {i}, {n} occurrence(s) au lieu d'une")
        texte = texte.replace(ancien, nouveau)
    return texte


def main() -> int:
    if not (GEN / "fiche_au_passe.py").exists():
        print("✗ Poser d'abord generator/fiche_au_passe.py — rien fait.")
        return 1
    cibles = {
        GEN / "et_si_main.py": MAIN,
        GEN / "appliquer_et_si.py": None,
        VAULT / "gui" / "app.py": APP_PY,
        VAULT / "gui" / "static" / "app.js": APP_JS,
    }
    prets = []
    try:
        for cible, rempl in cibles.items():
            if not cible.exists():
                raise ValueError(f"{cible} introuvable")
            texte = cible.read_text(encoding="utf-8")
            if MARQUEUR in texte:
                raise ValueError(f"{cible.name} : déjà patché")
            if rempl is None:   # appliquer_et_si.py : check-list (deux cas) + aperçu automatique
                if CASE_ANCIENNE in texte:
                    texte = appliquer_remplacements(texte, [(CASE_ANCIENNE, CASE_NOUVELLE)], cible.name)
                else:
                    texte = appliquer_remplacements(texte, [(LORE_ANCRE, BLOC_CHECKLIST)], cible.name)
                rempl = AUTO
            texte = appliquer_remplacements(texte, rempl, cible.name)
            if cible.suffix == ".py":
                compile(texte, str(cible), "exec")
            prets.append((cible, texte))
    except (ValueError, SyntaxError) as e:
        print(f"✗ {e} — rien écrit.")
        return 1
    for cible, texte in prets:
        shutil.copy2(cible, cible.with_name(cible.name + ".bak_s27_gui_au_passe"))
        cible.write_text(texte, encoding="utf-8")
        print(f"✓ {cible.relative_to(VAULT)} patché ; sauvegarde .bak_s27_gui_au_passe")
    print("  Redémarrer Flask, puis recharger la page.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

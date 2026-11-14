#!/usr/bin/env python3
"""
patch_u3ap_menu_groupes.py — Ourrassol 2098 (14 novembre 2026)

Regroupement du menu (gui/static/app.js, fonction buildNav) selon le Doc
« GUI Ourrassol : ajouter au monde » — SANS rien supprimer ni modifier
scripts_config.json (les ids, formulaires et routes sont inchangés) :

  ① Ajouter au monde : « Simulateur « et si ? » » (porte unique) ;
     sous-groupe REPLIÉ « Outils directs (ancien, avancé) » : Créer des entités,
     Injecter des événements, Injecter des signaux faibles (gardés tels quels).
  ② Sources : Veille signaux faibles (onglet, retiré de la liste du haut) + les 6 outils
     « monde réel ».
  ③ Articles, Presse & journaux, Relations & lore, Géographie (×2), Validation :
     inchangés.
  ④ Entretien (REPLIÉ par défaut, en bas) : compléter les fiches minimales,
     relations avec l'IA, instances manquantes, alliances fantômes, entités en
     échec, annuler, tracer, dates de naissance, présence garantie, présence
     d'une instance, + onglet « Audit par sujet ».

Garde-fous :
  - tout script futur des trois sections absorbées (entites_creation,
    entites_nettoyage, monde_reel) non listé ci-dessus est ajouté à « Entretien »
    (aucun outil ne peut disparaître du menu) ;
  - un groupe replié s'ouvre tout seul quand on y navigue (setActiveNav) ;
  - l'état ouvert/fermé est mémorisé par navigateur (localStorage, try/catch).

Retour arrière : restaurer app.js.bak_u3ap (ou git revert).
Après application : Cmd+Maj+R.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3ap_menu_groupes.py            # aperçu
    python3 generator/patch_u3ap_menu_groupes.py --apply    # écrit
Sauvegarde .bak_u3ap ; refuse un second passage ; contrôle de syntaxe (comme U3an :
une erreur déjà présente dans l'original, ex. « ||= » avec un node ancien, ne bloque pas).
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3ap"
APP_JS = Path("gui/static/app.js")

A_SECTIONS = """  { key: 'entites_creation',   label: 'Entités & événements — création' },
"""
A_SECTIONS_2 = """  { key: 'entites_nettoyage',  label: 'Entités & événements — nettoyage' },
"""
A_SECTIONS_3 = """  { key: 'monde_reel',         label: 'Référence — monde réel' },
"""

HELPERS = r"""// ── U3ap (14 novembre 2026) : menu en groupes (Ajouter au monde / Sources / Entretien) ──
// Les entrées scripts_config.json ne changent pas : seul leur rangement dans le menu.
const NAV_ABSORBEES_U3AP = ['entites_creation', 'entites_nettoyage', 'monde_reel'];
const NAV_DIRECTS_U3AP = ['create_entities', 'inject_events', 'inject_signals'];
const NAV_SOURCES_U3AP = ['export_prompt_veille', 'import_veille_etat_monde', 'export_prompt_signaux',
  'veille_livres_api', 'veille_rss_api', 'import_signaux_faibles'];
const NAV_ENTRETIEN_U3AP = ['enrich_minimal', 'fix_alliances_oppositions', 'generate_instances',
  'extract_phantom_slugs', 'requeue_needs_review', 'undo_custom', 'trace_injection',
  'fix_annee_debut_placeholder', 'set_priorite_forcee', 'set_selection_instance'];

function _navMemoireU3ap(cle, defaut) {
  try {
    const v = localStorage.getItem('ourrassol_nav_' + cle);
    return v === null ? defaut : v === '1';
  } catch (e) { return defaut; }
}

function _navMemoriserU3ap(cle, ouvert) {
  try { localStorage.setItem('ourrassol_nav_' + cle, ouvert ? '1' : '0'); } catch (e) { /* stockage indisponible */ }
}

function _navScriptsU3ap(ids) {
  // éléments de menu des scripts demandés (ceux absents de scripts_config.json sont ignorés)
  const els = [];
  ids.forEach(id => {
    const s = State.scripts.find(x => x.id === id);
    if (s) els.push(makeNavItem(s.id, s.icon, s.label, s.badge || null, 'script', false, s.gui_verified));
  });
  return els;
}

function _navGroupeReplieU3ap(nav, cle, titre, elements, ouvertDefaut) {
  const entete = document.createElement('div');
  entete.className = 'nav-section-label';
  entete.style.cursor = 'pointer';
  entete.style.userSelect = 'none';
  const corps = document.createElement('div');
  corps.dataset.navGroupe = cle;
  elements.forEach(e => corps.appendChild(e));
  const maj = (ouvert) => {
    entete.textContent = (ouvert ? '▾ ' : '▸ ') + titre;
    corps.style.display = ouvert ? '' : 'none';
    corps.dataset.ouvert = ouvert ? '1' : '0';
  };
  corps._majU3ap = maj;
  maj(_navMemoireU3ap(cle, ouvertDefaut));
  entete.addEventListener('click', () => {
    const ouvert = corps.dataset.ouvert !== '1';
    maj(ouvert);
    _navMemoriserU3ap(cle, ouvert);
  });
  nav.appendChild(entete);
  nav.appendChild(corps);
}

function construireGroupesNavU3ap(nav, quand) {
  if (quand === 'avant') {
    nav.appendChild(makeSectionLabel('Ajouter au monde'));
    _navScriptsU3ap(['simuler_et_si']).forEach(e => nav.appendChild(e));
    _navGroupeReplieU3ap(nav, 'directs', 'Outils directs (ancien, avancé)', _navScriptsU3ap(NAV_DIRECTS_U3AP), false);
    nav.appendChild(makeDivider());
    nav.appendChild(makeSectionLabel('Sources'));
    nav.appendChild(makeNavItem('veille_signaux', '🔭', 'Veille signaux faibles', null, 'tab'));
    _navScriptsU3ap(NAV_SOURCES_U3AP).forEach(e => nav.appendChild(e));
    nav.appendChild(makeDivider());
    return;
  }
  // Entretien : la liste fixe + tout script des sections absorbées qui n'a pas de place ailleurs
  const places = new Set(['simuler_et_si', ...NAV_DIRECTS_U3AP, ...NAV_SOURCES_U3AP, ...NAV_ENTRETIEN_U3AP]);
  const ids = [...NAV_ENTRETIEN_U3AP];
  State.scripts.forEach(s => {
    if (NAV_ABSORBEES_U3AP.includes(s.section) && !places.has(s.id)) ids.push(s.id);
  });
  const elements = _navScriptsU3ap(ids);
  elements.push(makeNavItem('sujets', '🧭', 'Audit par sujet', null, 'tab'));
  _navGroupeReplieU3ap(nav, 'entretien', 'Entretien', elements, false);
  nav.appendChild(makeDivider());
}

"""

A_DEF = "function buildNav() {\n"
A_AVANT = "  // Sections scripts\n  SECTIONS.forEach(section => {\n"
N_AVANT = "  construireGroupesNavU3ap(nav, 'avant');   // U3ap : Ajouter au monde, Sources\n" + A_AVANT
A_APRES = "  // Revue + Config\n  nav.appendChild(makeNavItem('review'"
N_APRES = "  construireGroupesNavU3ap(nav, 'apres');   // U3ap : Entretien (replié)\n" + A_APRES

A_ACTIF = """function setActiveNav(id) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === id);
  });
}
"""
N_ACTIF = """function setActiveNav(id) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === id);
  });
  // U3ap : un groupe replié s'ouvre quand on y navigue (sans mémoriser ce choix)
  const actif = document.querySelector('.nav-item.active');
  const corps = actif && actif.closest ? actif.closest('[data-nav-groupe]') : null;
  if (corps && corps.dataset.ouvert !== '1' && corps._majU3ap) corps._majU3ap(true);
}
"""

A_VEILLE_HAUT = "  nav.appendChild(makeNavItem('veille_signaux', '🔭', 'Veille signaux faibles', null, 'tab'));\n"

REMPL = [
    ("onglet Veille retiré du haut (il passe dans « Sources »)", A_VEILLE_HAUT, ""),
    ("section « création » retirée de SECTIONS", A_SECTIONS, ""),
    ("section « nettoyage » retirée de SECTIONS", A_SECTIONS_2, ""),
    ("section « monde réel » retirée de SECTIONS", A_SECTIONS_3, ""),
    ("fonctions des groupes", A_DEF, HELPERS + A_DEF),
    ("groupes avant les sections", A_AVANT, N_AVANT),
    ("groupe Entretien après les sections", A_APRES, N_APRES),
    ("ouverture automatique d'un groupe replié", A_ACTIF, N_ACTIF),
]


def _node_check(chemin):
    try:
        r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None, "node absent"
    return r.returncode == 0, r.stderr.strip()


def _premiere_erreur(msg):
    lignes = [l for l in msg.splitlines() if l.strip()]
    return " | ".join(l.strip() for l in lignes[:4] if "SyntaxError" in l or l.strip().startswith("("))[:300]


def verifier_js(chemin, original):
    """Une erreur DÉJÀ présente dans l'original (node ancien, « ||= ») ne bloque pas."""
    ok, msg = _node_check(chemin)
    if ok:
        return True, "node --check OK"
    if ok is False:
        with tempfile.TemporaryDirectory() as tmp:   # node refuse une extension autre que .js
            copie = Path(tmp) / "original.js"
            copie.write_text(Path(original).read_text(encoding="utf-8"), encoding="utf-8")
            ok0, msg0 = _node_check(copie)
        if ok0 is False and _premiere_erreur(msg) == _premiere_erreur(msg0):
            return True, f"erreur déjà présente dans l'original ({_premiere_erreur(msg0)[:80]}) : aucune erreur nouvelle"
        return False, msg[:400]
    t = chemin.read_text(encoding="utf-8")
    ok2 = t.count("{") == t.count("}") and t.count("(") == t.count(")")
    return ok2, "accolades/parenthèses équilibrées (node absent)" if ok2 else "déséquilibre accolades/parenthèses"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--js", default=str(APP_JS))
    a = ap.parse_args()
    chemin = Path(a.js)
    if not chemin.exists():
        print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
        return 2
    texte = chemin.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1
    nouveau = texte
    for libelle, ancre, rempl in REMPL:
        n = nouveau.count(ancre)
        if n != 1:
            print(f"✗ Ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
            return 1
        nouveau = nouveau.replace(ancre, rempl, 1)
        print(f"  ✓ {libelle}")
    if not a.apply:
        print(f"\nAperçu seulement : {len(texte.splitlines())} -> {len(nouveau.splitlines())} lignes. "
              "Relancer avec --apply pour écrire.")
        return 0
    bak = chemin.with_name(chemin.name + ".bak_u3ap")
    shutil.copy2(chemin, bak)
    chemin.write_text(nouveau, encoding="utf-8")
    ok, msg = verifier_js(chemin, bak)
    if not ok:
        shutil.copy2(bak, chemin)
        print(f"✗ Contrôle de syntaxe échoué, fichier restauré : {msg}")
        return 1
    print(f"  app.js : {msg}")
    print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})\n\nÀ faire : Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

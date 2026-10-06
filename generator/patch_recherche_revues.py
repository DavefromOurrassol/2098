#!/usr/bin/env python3
"""
patch_recherche_revues.py — Ourrassol 2098 (chantier 5, 5 octobre 2026)

Ajoute la recherche au site des revues (export_revues.py) :
  - une loupe « Rechercher » dans l'en-tête de chaque revue et du kiosque ;
  - <revue>/recherche.html + recherche.json : recherche dans les articles de la revue ;
  - recherche.html + recherche.json à la racine : recherche dans les 12 revues.
Recherche dans le navigateur (aucun serveur), texte complet compris, sans tenir
compte des accents ni de la casse ; tous les mots tapés doivent être présents.

Usage (depuis la racine du vault) :
    python3 generator/patch_recherche_revues.py           # aperçu, n'écrit rien
    python3 generator/patch_recherche_revues.py --apply   # écrit (.bak_recherche)
"""
import argparse
import shutil
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "export_revues.py"
MARQUEUR = "def page_recherche("

BLOC = """# ═══════════════════════════════════════════════════════════════════════════
# RECHERCHE (5 octobre 2026) — index JSON + page recherche.html, sans serveur
# ═══════════════════════════════════════════════════════════════════════════

CSS_RECHERCHE = \"\"\"
.loupe{display:inline-flex;align-items:center;gap:6px;font-family:'Archivo',sans-serif;font-size:13px;color:var(--muted)}
.loupe svg{width:15px;height:15px}
.champ{display:flex;gap:10px;margin-top:18px}
.champ input{flex:1;min-width:0;font-family:'Archivo',sans-serif;font-size:18px;padding:12px 14px;border:1px solid var(--ink);border-radius:0;background:var(--paper);color:var(--ink)}
.champ input:focus{outline:2px solid var(--accent);outline-offset:1px}
.compte{font-family:'Archivo',sans-serif;font-size:13px;color:var(--muted);margin-top:14px}
mark{background:#FFF1A8;color:inherit;padding:0 1px}
\"\"\"

SVG_LOUPE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
             '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>')


def loupe(prefix):
    return f'<a class="loupe" href="{prefix}recherche.html">{SVG_LOUPE}Rechercher</a>'


def texte_brut(md):
    \"\"\"Markdown -> texte simple pour l'index (wikilinks, gras, italiques retirés).\"\"\"
    s = re.sub(r"\\[\\[([^\\]|]+)\\|([^\\]]+)\\]\\]", r"\\2", md or "")
    s = re.sub(r"\\[\\[[^\\]]+\\]\\]", "", s)
    s = re.sub(r"^#+\\s*|^>\\s*|^[-*]\\s+", "", s, flags=re.M)
    s = re.sub(r"[*_]{1,2}", "", s)
    return re.sub(r"\\s+", " ", s).strip()


def entree_index(a, prefix_url, revue_nom=""):
    return {
        "u": prefix_url + f"articles/{a['page']}.html",
        "t": a["titre"], "c": texte_brut(a.get("chapo_aff") or ""),
        "z": a["zone_journal_nom"], "th": a["theme"], "j": a["journal"],
        "s": a["signature"], "r": revue_nom,
        "d": a["date"].isoformat() if a["date"] else "", "df": date_fr(a["date"]),
        "k": [str(t) for t in (a["fm"].get("tags") or [])],
        "x": texte_brut("\\n".join(a["blocs"])),
    }


JS_RECHERCHE = r\"\"\"
(function () {
  const champ = document.getElementById('q'), liste = document.getElementById('res'), compte = document.getElementById('compte');
  const plie = s => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const esc = s => (s || '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  let index = [];
  function surligne(txt, mots) {
    let out = esc(txt);
    for (const m of mots) {
      if (m.length < 2) continue;
      const p = plie(out); let r = '', i = 0, j;
      while ((j = p.indexOf(m, i)) !== -1) { r += out.slice(i, j) + '<mark>' + out.slice(j, j + m.length) + '</mark>'; i = j + m.length; }
      out = r + out.slice(i);
    }
    return out;
  }
  function extrait(x, mots) {
    const p = plie(x); let pos = -1;
    for (const m of mots) { pos = p.indexOf(m); if (pos !== -1) break; }
    if (pos === -1) return '';
    const d = Math.max(0, pos - 90), f = Math.min(x.length, pos + 160);
    return (d ? '… ' : '') + x.slice(d, f) + (f < x.length ? ' …' : '');
  }
  function chercher() {
    const q = champ.value.trim(), mots = plie(q).split(/\\s+/).filter(Boolean);
    history.replaceState(null, '', q ? '?q=' + encodeURIComponent(q) : location.pathname);
    if (!mots.length) { liste.innerHTML = ''; compte.textContent = index.length + ' articles. Tapez un mot (lieu, journal, personne, thème…).'; return; }
    const res = [];
    for (const a of index) {
      const t = plie(a.t), c = plie(a.c), meta = plie([a.z, a.th, a.j, a.s, a.r, (a.k || []).join(' ')].join(' ')), x = plie(a.x);
      let score = 0, tous = true;
      for (const m of mots) {
        const s = (t.includes(m) ? 8 : 0) + (c.includes(m) ? 4 : 0) + (meta.includes(m) ? 3 : 0) + (x.includes(m) ? 1 : 0);
        if (!s) { tous = false; break; }
        score += s;
      }
      if (tous) res.push([score, a]);
    }
    res.sort((p, q2) => q2[0] - p[0] || (q2[1].d > p[1].d ? 1 : -1));
    compte.textContent = res.length + ' résultat' + (res.length > 1 ? 's' : '') + ' pour « ' + q + ' »';
    liste.innerHTML = res.slice(0, 60).map(([, a]) => {
      const kick = [a.r, a.z, a.th].filter(Boolean).map(esc).join(' · ');
      const ex = extrait(a.x, mots);
      return '<div class="item"><div class="kick-s">' + kick + '</div>' +
        '<a class="t" href="' + a.u + '">' + surligne(a.t, mots) + '</a>' +
        (a.c ? '<p>' + surligne(a.c, mots) + '</p>' : '') +
        (ex ? '<p class="src">' + surligne(ex, mots) + '</p>' : '') +
        '<div class="src">' + esc(a.j) + ' · ' + esc(a.df) + '</div></div>';
    }).join('');
  }
  fetch('recherche.json').then(r => r.json()).then(d => {
    index = d;
    champ.value = new URLSearchParams(location.search).get('q') || '';
    chercher();
  }).catch(() => { compte.textContent = 'Index de recherche introuvable.'; });
  let minuterie;
  champ.addEventListener('input', () => { clearTimeout(minuterie); minuterie = setTimeout(chercher, 120); });
})();
\"\"\"


def page_recherche(entete, pied_html, titre_page, css_rel, accent, sous_titre):
    corps = [entete, '<main class="wrap">',
             f'<section><div class="kicker">Recherche</div>'
             f'<h1 style="margin:8px 0 0;font-size:40px">{e(sous_titre)}</h1>'
             f'<form class="champ" onsubmit="return false" role="search">'
             f'<input id="q" type="search" placeholder="Un lieu, un journal, une personne, un thème…" '
             f'autocomplete="off" aria-label="Rechercher"></form>'
             f'<div class="compte" id="compte">Chargement…</div></section>',
             '<section class="liste" id="res"></section>', '</main>', pied_html,
             f'<script>{JS_RECHERCHE}</script>']
    return page(titre_page, "\\n".join(corps), css_rel, accent)


"""

REMPLACEMENTS = [
    ("fonctions de recherche",
     "def publiables(articles, parution):\n",
     BLOC + "def publiables(articles, parution):\n"),
    ("feuille de style",
     'open(os.path.join(out_root, "style.css"), "w", encoding="utf-8").write(CSS)',
     'open(os.path.join(out_root, "style.css"), "w", encoding="utf-8").write(CSS + CSS_RECHERCHE)'),
    ("loupe en-tête des pages",
     "f'{e(entete_num)}</span></div></header>')",
     "f'{e(entete_num)}</span>{loupe(prefix)}</div></header>')"),
    ("loupe bandeau de la Une",
     """{e(str(rv.get("ville_siege", "")))}</span></div></div>',""",
     """{e(str(rv.get("ville_siege", "")))}</span>{loupe("")}</div></div>',"""),
    ("index et page de recherche de la revue",
     "    # ── Sources ──\n",
     """    # ── Recherche (5 octobre 2026) ──
    import json as _json
    open(os.path.join(out_dir, "recherche.json"), "w", encoding="utf-8").write(
        _json.dumps([entree_index(a, "") for a in arts], ensure_ascii=False, separators=(",", ":")))
    open(os.path.join(out_dir, "recherche.html"), "w", encoding="utf-8").write(
        page_recherche(mast_mini(""), pied(rv), f"Recherche — {rv['nom']}", "../style.css", accent,
                       f"Rechercher dans {rv['nom']}"))
    rv["_index"] = [entree_index(a, slugify(rv["nom"]) + "/", rv["nom"]) for a in arts]

    # ── Sources ──
"""),
    ("loupe du kiosque",
     """'<div class="devise">Le kiosque · six mondes, douze revues</div></header>'""",
     """'<div class="devise">Le kiosque · six mondes, douze revues</div>'
             '<div style="margin-top:14px">' + loupe("") + '</div></header>'"""),
    ("recherche globale",
     "    # ── Kiosque (hors fiction) ──\n",
     """    # ── Recherche globale dans les 12 revues (5 octobre 2026) ──
    import json as _json
    tout = [x for (_s, _l, rvk, _d, _n) in kiosque for x in rvk.get("_index", [])]
    open(os.path.join(out_root, "recherche.json"), "w", encoding="utf-8").write(
        _json.dumps(tout, ensure_ascii=False, separators=(",", ":")))
    tete = ('<header class="mast-mini"><div class="wrap"><a class="titre" href="index.html">Ourrassol 2098</a>'
            '<span class="sans" style="font-size:13px;color:var(--muted)">Le kiosque · douze revues</span></div></header>')
    open(os.path.join(out_root, "recherche.html"), "w", encoding="utf-8").write(
        page_recherche(tete, '<footer><div class="wrap"><span>Ourrassol 2098 · œuvre de fiction</span></div></footer>',
                       "Recherche — Ourrassol 2098", "style.css", "#2335A8", "Rechercher dans les douze revues"))
    print(f"  Recherche : {len(tout)} articles indexés (kiosque + une page par revue)")

    # ── Kiosque (hors fiction) ──
"""),
]


def patcher(src):
    if MARQUEUR in src:
        raise SystemExit("Recherche déjà ajoutée -- rien à faire.")
    for nom, ancre, _ in REMPLACEMENTS:
        if src.count(ancre) != 1:
            raise SystemExit(f"Ancre « {nom} » trouvée {src.count(ancre)} fois (attendu 1) -- patch non appliqué.")
    for _, ancre, nouveau in REMPLACEMENTS:
        src = src.replace(ancre, nouveau, 1)
    compile(src, str(CIBLE), "exec")
    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--cible", default=str(CIBLE), help=argparse.SUPPRESS)
    args = ap.parse_args()
    cible = Path(args.cible)
    nouveau = patcher(cible.read_text(encoding="utf-8"))
    if not args.apply:
        print(f"Aperçu OK : {cible.name} serait patché ({len(REMPLACEMENTS)} modifications). Relancer avec --apply.")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_recherche"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"Recherche ajoutée à {cible} (sauvegarde : {cible.name}.bak_recherche).")


if __name__ == "__main__":
    main()

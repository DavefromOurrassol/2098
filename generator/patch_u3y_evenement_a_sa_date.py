#!/usr/bin/env python3
"""
patch_u3y_evenement_a_sa_date.py — Ourrassol 2098 (U3y, 11 novembre 2026)
=========================================================================
Suite de U3s / U3t / U3w. Test réel des accords de 2039 : l'article est écrit au présent de 2098 ;
avec la consigne « tirées du passage » (U3t), l'IA a recopié tout le paragraphe dans la fiche de
2039 (dispensaire de 2042, unités mobiles d'« aujourd'hui »…) et inventé « automne 2039 ».

Quand un passage d'article est fourni, ce patch :
  1. CONSIGNE : l'événement choisi date de <année> ; description et réalisation racontent
     UNIQUEMENT cet événement tel qu'il se produit à sa date, sans recopier le passage, sans fait
     postérieur ni « aujourd'hui » ; date_label = l'année seule si le passage ne donne ni mois ni
     saison. La consigne de la description (U3t) ne dit plus « tirées du passage » mais
     « sur l'événement choisi seul, à sa date ».
  2. AVERTISSEMENT mécanique (non bloquant, dans les « Alertes de l'injection ») :
     « ⚠ [scénario] <champ> cite des années postérieures à l'événement (2039) : 2042 » et
     « ⚠ [scénario] <champ> parle d'« aujourd'hui » pour un événement de 2039 ».
     Champs contrôlés : réalisation et description (les conséquences peuvent regarder l'avenir).
Sans passage d'article, rien ne change.

Modifie generator/inject_custom_events.py (4 modifications). Exige U3s, U3t et U3w. Sauvegarde .bak_u3y.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3y_evenement_a_sa_date.py            # dry-run
  python3 generator/patch_u3y_evenement_a_sa_date.py --apply    # applique
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "inject_custom_events.py"
TAG = "u3y"

# 1. fonctions d'aide
A1 = "def _citations_absentes_u3t(instance_data, scenario):\n"
N1 = '''def _annee_evenement_u3y(idea, instance_data=None):
    """U3y : année de l'événement (date imposée, sinon date de la fiche), ou None."""
    for v in (idea.get("date_imposee"), (instance_data or {}).get("date")):
        try:
            a = int(float(v))
        except (TypeError, ValueError):
            continue
        if 2025 <= a <= 2098:
            return a
    return None


def _anachronismes_u3y(instance_data, idea, scenario):
    """U3y : années postérieures à l'événement, ou « aujourd'hui », dans la réalisation ou la
    description d'un événement tiré d'un article. Liste de messages (vide sinon)."""
    if not _DERNIER_ARTICLE_U3S.get(scenario):
        return []
    an = _annee_evenement_u3y(idea, instance_data)
    if not an:
        return []
    out = []
    for k in ("realisation", "description_complete"):
        t = str(instance_data.get(k) or "")
        apres = sorted({int(a) for a in re.findall(r"(?<!\\d)(20\\d\\d)(?!\\d)", t) if an < int(a) <= 2098})
        if apres:
            out.append(f"{k} cite des années postérieures à l'événement ({an}) : "
                       + ", ".join(str(a) for a in apres))
        if an < 2097 and re.search(r"aujourd.hui", t, re.IGNORECASE):
            out.append(f"{k} parle d'« aujourd'hui » pour un événement de {an}")
    return out


''' + A1

# 2. consigne de description (U3t) : plus « tirées du passage »
A2 = ('        desc_consigne_txt = ("description journalistique de l\'événement — 3-4 lignes sobres, tirées du passage "\n'
      '                             "de l\'article : ni scène, ni dialogue, ni détail absent du passage")\n')
N2 = ('        desc_consigne_txt = ("description journalistique de l\'événement — 3-4 lignes sobres sur l\'événement "\n'
      '                             "choisi seul, à sa date : ni scène, ni dialogue, ni détail absent du passage, "\n'
      '                             "sans recopier le passage")   # U3y\n')

# 3. consigne « à sa date »
A3 = "                         \"chiffre qui n'est pas dans le passage.\\n\")   # U3w\n"
N3 = A3 + '''        an_ev_u3y = _annee_evenement_u3y(idea)
        if an_ev_u3y:   # U3y
            contexte_txt += (f"L'événement choisi date de {an_ev_u3y}, alors que le passage peut décrire une époque "
                             f"plus tardive. La description et la réalisation racontent UNIQUEMENT cet événement, tel "
                             f"qu'il se produit en {an_ev_u3y} : ne recopie pas le passage, n'y mets aucun fait "
                             f"postérieur à {an_ev_u3y} ni « aujourd'hui ». date_label : l'année seule si le passage "
                             f"ne donne ni mois ni saison.\\n")
'''

# 4. avertissement
A4 = ('            for champ, nom_sc in _noms_scenario_u3w(instance_data):   # U3w\n'
      '                print(f"  ⚠ [{scenario}] le nom du scénario « {nom_sc} » apparaît dans {champ} : à retoucher")\n')
N4 = A4 + ('            for msg in _anachronismes_u3y(instance_data, idea, scenario):   # U3y\n'
           '                print(f"  ⚠ [{scenario}] {msg}")\n')

REMPLACEMENTS = [("aide", A1, N1), ("consigne description", A2, N2), ("consigne date", A3, N3),
                 ("avertissement", A4, N4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")
    if "_anachronismes_u3y" in src:
        print("= déjà appliqué, rien à faire")
        return
    if "_noms_scenario_u3w" not in src:
        sys.exit("✗ U3s / U3t / U3w ne sont pas appliqués")
    for nom, ancre, _ in REMPLACEMENTS:
        n = src.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (attendu 1) : fichier modifié ?")
    nouveau = src
    for _, ancre, rempl in REMPLACEMENTS:
        nouveau = nouveau.replace(ancre, rempl)
    print(f"{CIBLE.name} : {len(REMPLACEMENTS)} modifications prévues "
          f"(+{len(nouveau.splitlines()) - len(src.splitlines())} lignes)")
    if not args.apply:
        print("dry-run : rien écrit. Relancer avec --apply.")
        return
    bak = CIBLE.with_name(CIBLE.name + f".bak_{TAG}")
    shutil.copy2(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"✓ appliqué ; sauvegarde {bak.name} ; py_compile OK")


if __name__ == "__main__":
    main()

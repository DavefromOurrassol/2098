#!/usr/bin/env python3
"""
patch_s22_evenements_freres.py — Ourrassol 2098 (9 octobre 2026)

Corrige inject_custom_signals.py : en mode REPRISE, Mistral ressert les
evenement_cle déjà écrits pour les autres variables du même signal, et les
relances ne convergent pas (essai 3 identique à l'essai 1, cas réel
reseau_mobile_decentralise_urgence / geopolitique_conflits).

Deux causes :
1. `sibling_events` n'était rempli qu'en mémoire, pendant la boucle : en
   reprise (nouveau lancement), il était VIDE -> aucun événement interdit
   n'était montré au LLM. Et il ne gardait qu'UN événement par scénario
   (le dernier), alors qu'un signal a souvent 2-3 variables.
2. Chaque relance ne listait que les problèmes de l'essai précédent : les
   événements refusés aux essais d'avant étaient oubliés.

Correctif :
- `_evenements_du_signal()` : relit dans le registre tous les evenement_cle
  déjà écrits pour CE signal (toutes variables) ; `sibling_events` devient
  {scénario: [événements]}, initialisé depuis le registre.
- Les evenement_cle refusés pour doublon sont cumulés sur toutes les
  relances et listés explicitement comme INTERDITS.

Usage (depuis la racine du vault) :
    python3 generator/patch_s22_evenements_freres.py --dry-run
    python3 generator/patch_s22_evenements_freres.py
Sauvegarde : generator/inject_custom_signals.py.bak_s22_freres
Refuse un second passage.
"""
import argparse
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "inject_custom_signals.py"
MARQUEUR = "# S22-FRERES (9 octobre 2026)"

REMPLACEMENTS = [
    # 1. Helper : événements déjà écrits pour ce signal dans le registre
    (
        "def get_all_evenements(registre_text):",
        MARQUEUR + ''' -- événements déjà écrits pour CE signal
def _evenements_du_signal(registre_text, signal_slug):
    """Retourne {scénario: [evenement_cle]} des lignes du registre dont la
    source est `signal_slug` (toutes variables confondues). Sert à interdire
    au LLM de les réutiliser, y compris en reprise (nouveau lancement), où
    la mémoire de la boucle est vide."""
    result = {}
    parts = re.split(
        r"\\n## (" + "|".join(SCENARIOS) + r")\\n", registre_text
    )
    for i in range(1, len(parts), 2):
        scen = parts[i]
        for cols in parse_registre_table(parts[i + 1]):
            if len(cols) >= 6 and cols[2].strip() == signal_slug:
                ev = cols[5].strip()
                if ev and ev not in result.setdefault(scen, []):
                    result[scen].append(ev)
    return result


def _ajouter_evenement(dico, scen, ev):
    """Ajoute `ev` à dico[scen] (liste) sans doublon."""
    if ev and ev not in dico.setdefault(scen, []):
        dico[scen].append(ev)


def _evenements_refuses(issues):
    """Extrait {scénario: [evenement_cle]} des problèmes 'déjà présent dans
    le registre' renvoyés par validate_signal_block()."""
    import ast
    refuses = {}
    for issue in issues or []:
        m = re.match(r"^\\[(\\w+)\\] evenement_cle déjà présent dans le registre : (.+)$", issue)
        if not m:
            continue
        try:
            ev = ast.literal_eval(m.group(2))
        except (ValueError, SyntaxError):
            ev = m.group(2).strip("'\\"")
        _ajouter_evenement(refuses, m.group(1), ev)
    return refuses


def get_all_evenements(registre_text):''',
    ),
    # 2. Signature de step2_develop : nouveau paramètre `interdits`
    (
        "                   zone_hint=None, annee_apparition=None):\n    content = read_variable_file(variable_slug)",
        "                   zone_hint=None, annee_apparition=None, interdits=None):\n    content = read_variable_file(variable_slug)",
    ),
    # 3. Bloc des événements frères : listes par scénario + événements refusés cumulés
    (
        '''    sibling_block = ""
    if sibling_events:
        sibling_lines = "\\n".join(
            f"  - [{scen}] {ev}" for scen, ev in sibling_events.items()
        )''',
        '''    sibling_block = ""
    if sibling_events:
        ''' + MARQUEUR + ''' : plusieurs événements par scénario
        sibling_lines = "\\n".join(
            f"  - [{scen}] {ev}"
            for scen, evs in sibling_events.items()
            for ev in (evs if isinstance(evs, list) else [evs])
        )''',
    ),
    (
        '''concrète — plutôt qu'une reformulation du même événement.
"""
''',
        '''concrète — plutôt qu'une reformulation du même événement.
"""
    ''' + MARQUEUR + ''' : événements refusés aux essais précédents, cumulés
    if interdits:
        lignes_interdits = "\\n".join(
            f"  - [{scen}] {ev}" for scen, evs in interdits.items() for ev in evs
        )
        sibling_block += f"""
--- ⛔ ÉVÉNEMENTS DÉJÀ REFUSÉS AUX ESSAIS PRÉCÉDENTS (doublons du registre) ---
Ces `evenement_cle` ont DÉJÀ été rejetés pour cette variable. Ne les
réutilise sous AUCUNE forme, et ne les remplace pas par un autre événement
pris dans l'extrait du registre ci-dessus : invente un fait NEUF, propre à
la variable {variable_slug} (autre lieu, autre acteur, autre nature de fait).
{lignes_interdits}
"""
''',
    ),
    # 4. process_idea : initialisation depuis le registre
    (
        "    sibling_events = {}  # {scenario: evenement_cle} déjà validés pour CE signal dans ce run",
        "    " + MARQUEUR + " : {scenario: [evenement_cle]} déjà écrits pour CE signal,\n"
        "    # relus dans le registre (couvre la reprise), puis complétés dans la boucle.\n"
        "    sibling_events = _evenements_du_signal(registre_text, signal_slug)",
    ),
    # 5. Cumul des événements refusés sur toutes les relances
    (
        '''            previous, issues = None, None
            develop = step2_develop(''',
        '''            previous, issues = None, None
            interdits = {}  ''' + MARQUEUR + ''' : refusés, cumulés sur les relances
            develop = step2_develop(''',
    ),
    (
        '''                if attempt < MAX_FIX_ATTEMPTS:
                    develop = step2_develop(
                        client, idea_text, source, variable_slug, signal_slug, categorie,
                        registre_text, previous=yaml_text, issues=issues,
                        sibling_events=sibling_events, zone_hint=zone_hint,
                        annee_apparition=annee_apparition,
                    )''',
        '''                for scen, evs in _evenements_refuses(issues).items():
                    for ev in evs:
                        _ajouter_evenement(interdits, scen, ev)
                if attempt < MAX_FIX_ATTEMPTS:
                    develop = step2_develop(
                        client, idea_text, source, variable_slug, signal_slug, categorie,
                        registre_text, previous=yaml_text, issues=issues,
                        sibling_events=sibling_events, zone_hint=zone_hint,
                        annee_apparition=annee_apparition, interdits=interdits,
                    )''',
    ),
    # 6. Mémoire de la boucle : ajout au lieu d'écrasement
    (
        '''                sibling_events[scen] = data["evenement_cle"]''',
        '''                _ajouter_evenement(sibling_events, scen, data["evenement_cle"])''',
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fichier", default=str(CIBLE))
    args = ap.parse_args()
    cible = Path(args.fichier)
    texte = cible.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit(f"Déjà appliqué ({MARQUEUR} présent dans {cible.name}). Rien à faire.")
    for i, (avant, apres) in enumerate(REMPLACEMENTS, 1):
        n = texte.count(avant)
        if n != 1:
            sys.exit(f"Ancre {i} trouvée {n} fois (attendu 1) : patch abandonné, rien écrit.")
        texte = texte.replace(avant, apres)
    compile(texte, str(cible), "exec")
    if args.dry_run:
        print(f"OK (simulation) : {len(REMPLACEMENTS)} remplacements possibles, rien écrit.")
        return
    bak = cible.with_name(cible.name + ".bak_s22_freres")
    bak.write_text(cible.read_text(encoding="utf-8"), encoding="utf-8")
    cible.write_text(texte, encoding="utf-8")
    print(f"OK : {len(REMPLACEMENTS)} remplacements, sauvegarde {bak.name}.")


if __name__ == "__main__":
    main()

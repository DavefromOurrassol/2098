"""
patrons_spatiaux.py

Formalise le patron spatial de chaque scénario (P24, étape A).

Contrairement à une version figée en dur, les CITATIONS (state_logic,
state_logic_complementaire) sont chargées dynamiquement depuis le vault à
l'import de ce module, via extract_state_logic.py. Si tu modifies un
state_logic dans variables/organisation_territoires.md (ou geopolitique_
conflits.md / frontieres_du_systeme.md), ce module le reflète automatiquement
au prochain import -- aucune resynchronisation manuelle nécessaire pour cette
partie.

En revanche, la partie ANALYSE (_ANALYSE ci-dessous : patron_a_respecter,
a_eviter, sources_vault) reste écrite à la main. Ce n'est pas une citation
mais une interprétation -- si tu changes la logique d'un scénario en
profondeur dans le vault, cette partie doit être revalidée manuellement.
_build_patrons() lève une erreur explicite si un scénario listé dans
_ANALYSE disparaît du vault, pour éviter une dérive silencieuse de ce côté.

Objectif : servir de source de vérité unique, citable dans :
  - tout prompt de génération de zone (générateur top-down, P24 étape C)
  - tout garde-fou de cohérence de zone (P22, second signal "patron spatial")

Configuration du chemin vault : variable d'environnement
OURRASSOL_VAULT_ROOT si définie, sinon déduite de l'emplacement de ce
fichier en supposant generator/patrons_spatiaux.py avec variables/ au même
niveau que generator/ à la racine du vault. Redéfinir OURRASSOL_VAULT_ROOT
si cette hypothèse ne tient pas sur ta machine.
"""

import os
from pathlib import Path
from typing import TypedDict

from extract_state_logic import extract_state_logic

VARIABLE_PRINCIPALE = "organisation_territoires"
VARIABLES_COMPLEMENTAIRES = ["geopolitique_conflits", "frontieres_du_systeme"]


def _vault_root() -> Path:
    env = os.environ.get("OURRASSOL_VAULT_ROOT")
    if env:
        return Path(env)
    # Hypothèse par défaut : ce fichier vit dans generator/, variables/ est
    # au même niveau que generator/ à la racine du vault.
    return Path(__file__).resolve().parent.parent


def _variables_dir() -> Path:
    return _vault_root() / "variables"


class PatronSpatial(TypedDict):
    state_logic: str                              # Citée en direct du vault (dynamique)
    state_logic_complementaire: dict[str, str]     # Idem, {nom_variable: state_logic}
    patron_a_respecter: list[str]   # Analyse écrite à la main : ce qu'une zone DOIT incarner
    a_eviter: list[str]             # Analyse écrite à la main : anti-patterns
    sources_vault: list[str]        # Fiches vault à citer dans un prompt de génération/vérification


# Partie analyse uniquement -- pas de citation ici. Les state_logic sont
# injectés par _build_patrons() depuis le vault à l'import.
_ANALYSE: dict[str, dict] = {

    "reference": {
        "patron_a_respecter": [
            "Zones organisées autour de hubs urbains dominants.",
            "Périphéries en déclin, contraste centre/périphérie marqué.",
            "Pas de rupture radicale : c'est le scénario le plus conservateur des 6.",
        ],
        "a_eviter": [
            "Innovation institutionnelle ou sociale trop marquée "
            "(appartient plutôt à policy_reform ou new_sustainability).",
            "Zone orbitale/spatiale ambitieuse : l'expansion spatiale reste "
            "limitée et robotique dans ce scénario.",
        ],
        "sources_vault": [
            "variables/organisation_territoires.md -> states.reference",
            "variables/geopolitique_conflits.md -> states.reference",
            "variables/frontieres_du_systeme.md -> states.reference",
        ],
    },

    "policy_reform": {
        "patron_a_respecter": [
            "Institutions de régulation régionales/internationales actives.",
            "Montée de villes secondaires plutôt que mégapoles uniques.",
            "Coopération réelle mais non totale entre blocs rivaux.",
            "Zone orbitale/spatiale : gouvernance internationale coordonnée, "
            "coûts mutualisés — pas d'appropriation unilatérale.",
        ],
        "a_eviter": [
            "Institution supranationale hégémonique et incontestée.",
            "Logique de mégapole unique dominante (patron reference).",
        ],
        "sources_vault": [
            "variables/organisation_territoires.md -> states.policy_reform",
            "variables/geopolitique_conflits.md -> states.policy_reform",
            "variables/frontieres_du_systeme.md -> states.policy_reform",
        ],
    },

    "breakdown": {
        "patron_a_respecter": [
            "Fragmentation en blocs rivaux (cf. Bloc IV / Bloc IX déjà dans le vault).",
            "Zones no-go entre blocs.",
            "Absence d'institution supranationale stable.",
            "Zone orbitale/spatiale éventuelle : conflit ou saturation, jamais "
            "coopération stable.",
        ],
        "a_eviter": [
            "Toute zone portant une logique de gouvernance centralisée forte.",
        ],
        "sources_vault": [
            "variables/organisation_territoires.md -> states.breakdown",
            "variables/geopolitique_conflits.md -> states.breakdown",
            "variables/frontieres_du_systeme.md -> states.breakdown",
        ],
    },

    "fortress_world": {
        "patron_a_respecter": [
            "Enclave protégée, n'importe où dans le monde y compris en zone "
            "historiquement pauvre (cf. Bloc Johannesburg déjà dans le vault) "
            "— pas seulement un clivage Nord/Sud.",
            "Alternative : zone explicitement 'hors-forteresse' dégradée.",
            "Zone orbitale/spatiale éventuelle : militarisée, outil de "
            "surveillance d'un bloc, jamais un espace civil partagé.",
        ],
        "a_eviter": [
            "Zone 'neutre' ou intermédiaire qui n'incarne ni l'enclave "
            "protégée ni le hors-forteresse dégradé.",
        ],
        "sources_vault": [
            "variables/organisation_territoires.md -> states.fortress_world",
            "variables/geopolitique_conflits.md -> states.fortress_world",
            "variables/frontieres_du_systeme.md -> states.fortress_world",
        ],
    },

    "eco_communalism": {
        "patron_a_respecter": [
            "Petites communautés autonomes.",
            "Désurbanisation volontaire.",
            "Pas de grande institution centralisée.",
            "Zone orbitale/spatiale éventuelle : strictement scientifique, "
            "jamais économique/extractive.",
        ],
        "a_eviter": [
            "Zone de grande taille et centralisée : c'est le scénario le plus "
            "éloigné d'une logique de 'mégazone'.",
        ],
        "sources_vault": [
            "variables/organisation_territoires.md -> states.eco_communalism",
            "variables/geopolitique_conflits.md -> states.eco_communalism",
            "variables/frontieres_du_systeme.md -> states.eco_communalism",
        ],
    },

    "new_sustainability": {
        "patron_a_respecter": [
            "Institutions supranationales actives (cf. AGRB-ONU, AIER déjà "
            "dans le vault).",
            "Réseau distribué de hubs plutôt qu'un centre unique.",
            "Friction ou adaptation locale spécifique face à l'institution "
            "mère : une institution universelle ne s'implante jamais "
            "identiquement partout (d'Iribarne, Futuribles 2004).",
            "Zone orbitale/spatiale : pleinement intégrée à l'économie "
            "globale, coordonnée — c'est le seul scénario où une zone "
            "orbitale industrialisée et mature est cohérente.",
        ],
        "a_eviter": [
            "Simple copie conforme de l'institution mère sans réinterprétation "
            "locale.",
        ],
        "sources_vault": [
            "variables/organisation_territoires.md -> states.new_sustainability",
            "variables/geopolitique_conflits.md -> states.new_sustainability",
            "variables/frontieres_du_systeme.md -> states.new_sustainability",
        ],
    },
}


def _build_patrons() -> dict[str, PatronSpatial]:
    """
    Assemble PATRONS_SPATIAUX en combinant l'analyse statique (_ANALYSE)
    avec les citations lues en direct dans le vault.

    Lève RuntimeError avec un message actionnable si le vault n'est pas
    accessible, ou si un scénario de _ANALYSE a disparu du vault (dérive
    entre l'analyse écrite à la main et l'état réel du vault -- à
    réconcilier manuellement, jamais résolu automatiquement).
    """
    var_dir = _variables_dir()

    def _lire(nom_variable: str) -> dict[str, str]:
        try:
            return extract_state_logic(var_dir / f"{nom_variable}.md")
        except (ValueError, OSError) as e:
            raise RuntimeError(
                f"Impossible de lire {nom_variable}.md dans {var_dir}. "
                f"Vérifie OURRASSOL_VAULT_ROOT (actuellement résolu à : "
                f"{_vault_root()}). Erreur d'origine : {e}"
            ) from e

    logique_principale = _lire(VARIABLE_PRINCIPALE)
    logiques_complementaires = {
        nom: _lire(nom) for nom in VARIABLES_COMPLEMENTAIRES
    }

    patrons: dict[str, PatronSpatial] = {}
    for scenario, analyse in _ANALYSE.items():
        if scenario not in logique_principale:
            raise RuntimeError(
                f"Scénario '{scenario}' présent dans _ANALYSE (patrons_spatiaux.py) "
                f"mais absent de {VARIABLE_PRINCIPALE}.md dans le vault. "
                f"L'analyse écrite à la main et le vault ont divergé -- "
                f"à réconcilier manuellement, pas de résolution automatique."
            )
        patrons[scenario] = {
            "state_logic": logique_principale[scenario],
            "state_logic_complementaire": {
                nom: logiques_complementaires[nom][scenario]
                for nom in VARIABLES_COMPLEMENTAIRES
                if scenario in logiques_complementaires[nom]
            },
            "patron_a_respecter": analyse["patron_a_respecter"],
            "a_eviter": analyse["a_eviter"],
            "sources_vault": analyse["sources_vault"],
        }
    return patrons


PATRONS_SPATIAUX: dict[str, PatronSpatial] = _build_patrons()


def get_patron(scenario: str) -> PatronSpatial:
    """Retourne le patron spatial d'un scénario. Lève KeyError si inconnu."""
    try:
        return PATRONS_SPATIAUX[scenario]
    except KeyError:
        raise KeyError(
            f"Scénario inconnu : '{scenario}'. "
            f"Attendu un de : {sorted(PATRONS_SPATIAUX)}"
        )


def patron_spatial_prompt_block(scenario: str) -> str:
    """
    Génère un bloc de texte prêt à injecter dans un prompt LLM (génération ou
    vérification de zone), citant le patron spatial du scénario.

    Utilisation prévue :
      - P24 étape C (générateur top-down) : injection directe dans le prompt
        de création de zone.
      - P22 (garde-fou étendu) : comparaison qualitative description/type de
        zone vs ce bloc, en avertissement uniquement (jamais en blocage dur).
    """
    p = get_patron(scenario)
    lignes = [
        f"Patron spatial du scénario '{scenario}' :",
        f"  Logique territoriale : {p['state_logic']}",
    ]
    for nom_variable, logique in p["state_logic_complementaire"].items():
        lignes.append(f"  Logique {nom_variable} : {logique}")
    lignes.append("  À respecter :")
    lignes += [f"    - {r}" for r in p["patron_a_respecter"]]
    lignes.append("  À éviter :")
    lignes += [f"    - {r}" for r in p["a_eviter"]]
    return "\n".join(lignes)


if __name__ == "__main__":
    # Sanity check rapide : un bloc par scénario, aucune exception attendue.
    for slug in PATRONS_SPATIAUX:
        print(patron_spatial_prompt_block(slug))
        print()

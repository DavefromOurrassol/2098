"""
llm_client.py
-------------
Abstraction LLM pour Ourrassol 2098.
Supporte Claude (Anthropic), Mistral et OpenAI via une interface unifiée.

Deux modes de sélection du modèle :

1. OVERRIDE MANUEL (variables d'environnement) — priorité absolue,
   utile pour un test ponctuel en CLI, quel que soit le tier demandé
   par l'appelant :
       export LLM_PROVIDER=claude
       export LLM_MODEL=claude-sonnet-5

2. ROUTING PAR TIER (recommandé, utilisé par la majorité des scripts) —
   chaque appelant passe task_tier=... à call_llm(), et le modèle est
   résolu automatiquement depuis TASK_TIER_DEFAULTS ci-dessous. Si aucune
   variable d'environnement n'est positionnée, c'est ce mode qui s'applique.
   Si task_tier est omis ET qu'aucune variable d'env n'est positionnée,
   on retombe sur le tier "volume" (comportement le plus proche de l'ancien
   défaut mistral-small).

Usage dans les scripts :
    from llm_client import call_llm, LLM_PROVIDER, LLM_MODEL
    call_llm(system_prompt, user_prompt, task_tier="strict")
"""

import os
import time

# ─────────────────────────────────────────
# CONFIGURATION — OVERRIDE MANUEL (env vars)
# ─────────────────────────────────────────
#
# None si la variable n'a pas été positionnée par l'utilisateur — permet de
# distinguer "l'utilisateur veut forcer ce fournisseur/modèle" de "aucune
# préférence exprimée, laisser le routing par tier décider".

_ENV_PROVIDER = os.environ.get("LLM_PROVIDER")
_ENV_MODEL    = os.environ.get("LLM_MODEL")

# Modèles par défaut par fournisseur (utilisés si LLM_PROVIDER est forcé
# manuellement mais pas LLM_MODEL)
_DEFAULT_MODELS = {
    "claude":  "claude-sonnet-5",
    "mistral": "mistral-small-latest",
    "openai":  "gpt-5.5",
}

# Conservés pour compatibilité ascendante : scripts import LLM_PROVIDER/
# LLM_MODEL pour affichage diagnostique. Reflètent l'override manuel s'il
# existe, sinon un défaut générique (mistral/small) — mais dès qu'un script
# passe task_tier à call_llm(), c'est TASK_TIER_DEFAULTS qui fait foi pour
# l'appel réel, pas ces deux variables. Pour un log fidèle au tier réellement
# utilisé, préférer resolve_for_tier(task_tier) (voir plus bas).
LLM_PROVIDER = (_ENV_PROVIDER or "mistral").lower()
LLM_MODEL = _ENV_MODEL or _DEFAULT_MODELS.get(LLM_PROVIDER, _DEFAULT_MODELS["mistral"])


# ─────────────────────────────────────────
# CONFIGURATION — ROUTING PAR TIER
# ─────────────────────────────────────────
#
# strict            : identité/fidélité imposée (nom, personnage, voix) sur
#                      une sortie longue et créative — le point faible connu
#                      de mistral-small (bugs #18/#20 journaliste).
# structured_strict : sortie JSON/structurée canonique, référencée ensuite
#                      dans tout le vault (entités, instances, géographie).
# creative_souple    : rédaction/enrichissement libre, sans contrainte
#                      d'identité tierce à respecter.
# volume             : extraction, classification, résolution courte depuis
#                      du texte déjà existant — gros volume, faible enjeu
#                      par erreur individuelle.
#
# NOTE (11 juillet 2026) : "strict" est actuellement sur Mistral Large, pas
# Claude — phase de test. Repasser sur claude-sonnet-5 au moment du passage
# en production (une seule ligne à changer ci-dessous).
TASK_TIER_DEFAULTS = {
    "strict":            {"provider": "mistral", "model": "mistral-large-latest"},
    "structured_strict": {"provider": "mistral", "model": "mistral-large-latest"},
    "creative_souple":   {"provider": "mistral", "model": "mistral-large-latest"},
    "volume":            {"provider": "mistral", "model": "mistral-small-latest"},
}
_DEFAULT_TIER = "volume"


def resolve_for_tier(task_tier: str = None) -> tuple:
    """
    Résout (provider, model) réellement utilisés pour un appel donné.

    Priorité :
      1. Override manuel via LLM_PROVIDER / LLM_MODEL (si l'une des deux
         variables d'environnement est positionnée par l'utilisateur).
      2. Tier demandé (task_tier), résolu depuis TASK_TIER_DEFAULTS.
      3. Tier par défaut ("volume") si task_tier est None/inconnu.

    À utiliser côté appelant pour logger fidèlement ce qui sera réellement
    appelé, plutôt que d'importer LLM_MODEL statiquement (qui ne reflète
    pas le tier si un override n'est pas actif).
    """
    if _ENV_PROVIDER or _ENV_MODEL:
        return LLM_PROVIDER, LLM_MODEL

    tier = TASK_TIER_DEFAULTS.get(task_tier, TASK_TIER_DEFAULTS[_DEFAULT_TIER])
    return tier["provider"], tier["model"]


# Rate limiting (ajouté le 4 juillet) — PUREMENT RÉACTIF, aucune pause
# préventive : le code tourne à pleine vitesse tant que le fournisseur ne
# répond pas 429. Ne ralentit donc que si le palier réel du compte (Free,
# Scale, Tier X) est effectivement dépassé — s'adapte automatiquement à
# n'importe quel palier sans changer une ligne de code.
MAX_RETRIES_RATE_LIMIT = 4
BACKOFF_RATE_LIMIT = 15  # secondes, multiplié par le numéro de tentative


# ─────────────────────────────────────────
# INTERFACE PUBLIQUE
# ─────────────────────────────────────────

def call_llm(system_prompt: str, user_prompt: str,
             max_tokens: int = 2000, temperature: float = 0.7,
             task_tier: str = None) -> str:
    """
    Appelle le LLM configuré et retourne le texte brut de la réponse.
    Interface identique quel que soit le fournisseur.

    Sur une erreur 429 (rate limit), retente automatiquement avec un délai
    croissant (15s, 30s, 45s, 60s) jusqu'à MAX_RETRIES_RATE_LIMIT tentatives,
    avant de laisser remonter l'erreur. Aucun délai n'est appliqué en dehors
    de ce cas — un compte avec un palier large (ex. Scale) ne sera jamais
    ralenti artificiellement.

    Args:
        system_prompt : instruction système
        user_prompt   : message utilisateur
        max_tokens    : limite de tokens en sortie
        temperature   : créativité (0.0 = déterministe, 1.0 = max)
        task_tier     : "strict" | "structured_strict" | "creative_souple" |
                        "volume" — résout le provider/modèle via
                        TASK_TIER_DEFAULTS, sauf si LLM_PROVIDER/LLM_MODEL
                        est positionné manuellement (override total).
                        Si omis, comportement équivalent au tier "volume".

    Returns:
        str — texte de la réponse du modèle

    Raises:
        ImportError      : SDK non installé
        EnvironmentError : clé API manquante
        RuntimeError     : erreur de l'API distante (y compris 429 après
                           épuisement des tentatives)
    """
    provider, model = resolve_for_tier(task_tier)

    backends = {
        "mistral": _call_mistral,
        "openai":  _call_openai,
    }
    backend = backends.get(provider, _call_claude)

    for attempt in range(1, MAX_RETRIES_RATE_LIMIT + 1):
        try:
            return backend(system_prompt, user_prompt, max_tokens, temperature, model)
        except RuntimeError as e:
            is_rate_limit = "429" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES_RATE_LIMIT:
                wait = BACKOFF_RATE_LIMIT * attempt
                print(f"  [llm_client] Rate limit (429) — attente {wait}s "
                      f"avant nouvel essai ({attempt}/{MAX_RETRIES_RATE_LIMIT})...")
                time.sleep(wait)
                continue
            raise


# ─────────────────────────────────────────
# BACKEND CLAUDE (Anthropic)
# ─────────────────────────────────────────

def _call_claude(system_prompt: str, user_prompt: str,
                 max_tokens: int, temperature: float, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "Le SDK Anthropic n'est pas installé.\n"
            "  pip install anthropic --break-system-packages"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
    except Exception as e:
        raise RuntimeError(f"[llm_client] Erreur API Claude : {e}")

    tokens_in  = message.usage.input_tokens
    tokens_out = message.usage.output_tokens
    print(f"[llm] Claude ({model}) — entrée : {tokens_in} | sortie : {tokens_out}")

    return message.content[0].text


# ─────────────────────────────────────────
# BACKEND MISTRAL
# ─────────────────────────────────────────

def _call_mistral(system_prompt: str, user_prompt: str,
                  max_tokens: int, temperature: float, model: str) -> str:
    try:
        from mistralai import Mistral
    except ImportError:
        raise ImportError(
            "Le SDK Mistral n'est pas installé.\n"
            "  pip install mistralai --break-system-packages"
        )

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "[llm_client] Variable MISTRAL_API_KEY non définie.\n"
            "  export MISTRAL_API_KEY='votre-clé'"
        )

    client = Mistral(api_key=api_key)

    try:
        response = client.chat.complete(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ]
        )
    except Exception as e:
        raise RuntimeError(f"[llm_client] Erreur API Mistral : {e}")

    usage = response.usage
    print(f"[llm] Mistral ({model}) — entrée : {usage.prompt_tokens} | sortie : {usage.completion_tokens}")

    return response.choices[0].message.content


# ─────────────────────────────────────────
# BACKEND OPENAI
# ─────────────────────────────────────────

def _call_openai(system_prompt: str, user_prompt: str,
                  max_tokens: int, temperature: float, model: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "Le SDK OpenAI n'est pas installé.\n"
            "  pip install openai --break-system-packages"
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "[llm_client] Variable OPENAI_API_KEY non définie.\n"
            "  export OPENAI_API_KEY='votre-clé'"
        )

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            max_completion_tokens=max_tokens,  # GPT-5.x rejette "max_tokens" (erreur 400 confirmée le 5 juillet)
            # "temperature" volontairement omis : GPT-5.x n'accepte que sa valeur
            # par défaut (1) et rejette toute autre valeur explicite avec une
            # erreur 400 (confirmée le 5 juillet sur generate_journaux.py,
            # temperature=0.7). Ne pas passer le paramètre laisse l'API
            # appliquer son défaut — cohérent avec generate.py qui, par
            # coïncidence, passe déjà température=1.0 et n'a jamais été affecté.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ]
        )
    except Exception as e:
        raise RuntimeError(f"[llm_client] Erreur API OpenAI : {e}")

    usage = response.usage
    print(f"[llm] OpenAI ({model}) — entrée : {usage.prompt_tokens} | sortie : {usage.completion_tokens}")

    return response.choices[0].message.content


# ─────────────────────────────────────────
# TEST RAPIDE
# ─────────────────────────────────────────

if __name__ == "__main__":
    print(f"=== Test llm_client.py ===")
    for tier in ("strict", "structured_strict", "creative_souple", "volume"):
        p, m = resolve_for_tier(tier)
        print(f"  tier={tier:<18} → {p} / {m}")
    print()

    reponse = call_llm(
        system_prompt="Tu es un assistant de test. Réponds en une phrase courte.",
        user_prompt="Quel est le nom de la capitale de la France ?",
        max_tokens=50,
        temperature=0.0,
        task_tier="volume",
    )
    print(f"Réponse : {reponse}")

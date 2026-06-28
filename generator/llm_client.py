"""
llm_client.py
-------------
Abstraction LLM pour Ourrassol 2098.
Supporte Claude (Anthropic) et Mistral via une interface unifiée.

Fournisseur actif : variable d'environnement LLM_PROVIDER
    export LLM_PROVIDER=claude     # défaut
    export LLM_PROVIDER=mistral

Modèle actif : variable d'environnement LLM_MODEL (optionnel)
    export LLM_MODEL=mistral-large-latest   # override le modèle par défaut

Usage dans les scripts :
    from llm_client import call_llm, LLM_PROVIDER, LLM_MODEL
"""

import os

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "mistral").lower()

# Modèles par défaut par fournisseur
_DEFAULT_MODELS = {
    "claude":  "claude-sonnet-4-6",
    "mistral": "mistral-small",
}

LLM_MODEL = os.environ.get(
    "LLM_MODEL",
    _DEFAULT_MODELS.get(LLM_PROVIDER, _DEFAULT_MODELS["claude"])
)


# ─────────────────────────────────────────
# INTERFACE PUBLIQUE
# ─────────────────────────────────────────

def call_llm(system_prompt: str, user_prompt: str,
             max_tokens: int = 2000, temperature: float = 0.7) -> str:
    """
    Appelle le LLM configuré et retourne le texte brut de la réponse.
    Interface identique quel que soit le fournisseur.

    Args:
        system_prompt : instruction système
        user_prompt   : message utilisateur
        max_tokens    : limite de tokens en sortie
        temperature   : créativité (0.0 = déterministe, 1.0 = max)

    Returns:
        str — texte de la réponse du modèle

    Raises:
        ImportError      : SDK non installé
        EnvironmentError : clé API manquante
        RuntimeError     : erreur de l'API distante
    """
    if LLM_PROVIDER == "mistral":
        return _call_mistral(system_prompt, user_prompt, max_tokens, temperature)
    else:
        return _call_claude(system_prompt, user_prompt, max_tokens, temperature)


# ─────────────────────────────────────────
# BACKEND CLAUDE (Anthropic)
# ─────────────────────────────────────────

def _call_claude(system_prompt: str, user_prompt: str,
                 max_tokens: int, temperature: float) -> str:
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
            model=LLM_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
    except Exception as e:
        raise RuntimeError(f"[llm_client] Erreur API Claude : {e}")

    tokens_in  = message.usage.input_tokens
    tokens_out = message.usage.output_tokens
    print(f"[llm] Claude ({LLM_MODEL}) — entrée : {tokens_in} | sortie : {tokens_out}")

    return message.content[0].text


# ─────────────────────────────────────────
# BACKEND MISTRAL
# ─────────────────────────────────────────

def _call_mistral(system_prompt: str, user_prompt: str,
                  max_tokens: int, temperature: float) -> str:
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
            model=LLM_MODEL,
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
    print(f"[llm] Mistral ({LLM_MODEL}) — entrée : {usage.prompt_tokens} | sortie : {usage.completion_tokens}")

    return response.choices[0].message.content


# ─────────────────────────────────────────
# TEST RAPIDE
# ─────────────────────────────────────────

if __name__ == "__main__":
    print(f"=== Test llm_client.py ===")
    print(f"Fournisseur : {LLM_PROVIDER}")
    print(f"Modèle      : {LLM_MODEL}")
    print()

    reponse = call_llm(
        system_prompt="Tu es un assistant de test. Réponds en une phrase courte.",
        user_prompt="Quel est le nom de la capitale de la France ?",
        max_tokens=50,
        temperature=0.0
    )
    print(f"Réponse : {reponse}")

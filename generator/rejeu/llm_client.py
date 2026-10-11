APPELS = []
def call_llm(system_prompt, user_prompt, **k):
    APPELS.append(user_prompt[:80])
    raise RuntimeError("rejeu : appel IA non autorisé (absent du cache)")

# Banc de rejeu de la passe exhaustive (S27)

But : tester un réglage de `et_si_exhaustif.py` (contrôles, niveaux, tri, rendu) sur de vrais cas,
sans appeler l'IA et sans relire de rapport.

1. Lancer les passes réelles des cas voulus (une fois), puis `python3 generator/export_et_si.py`.
2. `python3 generator/rejeu/rejouer.py` : rejoue tous les couples de l'export.
3. `python3 generator/rejeu/evaluer.py` : score contre `reference.json`.

`reference.json` : verdicts attendus, validés par David le 11 octobre 2026.
Clés : `obligatoire`, `pas_obligatoire`, `pas_disparu`, `vu` (au moins possible) ;
`priorite` / `pas_priorite` sont indicatives (classement IA variable).

Limite : un changement de CONSIGNE (VERSION_PROMPT, VERSION_CONTRE, VERSION_CLASSEMENT) ne peut
pas être rejoué : il faut relancer les passes réelles, puis réexporter.

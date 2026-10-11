"""
dynamique.py — Ourrassol 2098
------------------------------
Moteur de simulation dynamique du réseau des 12 variables (chantier
"propagation dynamique", option c, 27 septembre 2026).

PRINCIPE
--------
Le level de chaque fiche variable (states[scénario].level) est l'état de
RÉFÉRENCE du scénario (histoire comprise). Le moteur ne simule que
l'ÉCART x_i(t) à cette référence, provoqué par les injections custom
(entités, événements, signaux), de ANNEE_DEPART jusqu'à la date de
l'article :

    x_i'' + 2 ζ_i ω_i x_i' + ω_i² x_i = ω_i² · [ u_i(t) + K · Σ_j c_ji · x_j(t − τ_ji) ]

  - second ordre amorti par variable :
      ζ_i (amortissement) ← simulation.volatility   (volatile = peu amorti, oscille)
      ω_i (vitesse propre) ← simulation.resilience  (résiliente = revient vite)
  - u_i(t) : forçage des chocs injectés (niveau en points), chaque choc
    monte linéairement jusqu'à pleine force en `duree` années, puis
    s'estompe avec une demi-vie (le monde absorbe les chocs) : celle de
    son niveau `persistance` (ephemere/normale/durable/permanente) s'il
    en a un, sinon celle de son type (DEMI_VIE_PAR_TYPE), sinon DEMI_VIE ;
  - couplage matriciel : c_ji = weight × polarity × temporal_weight ×
    multiplicateur(systemic_criticality de la source), retard
    τ_ji = lag × ANNEES_PAR_CYCLE ; K = K_COUPLAGE, gain global qui
    garantit la stabilité des boucles (voir rayon_spectral()) ;
  - un choc avec via_matrice = false agit sur une composante "locale"
    de l'écart, qui suit la même dynamique mais n'alimente PAS le
    couplage (superposition linéaire, exacte) ;
  - sortie : level = référence + marge · tanh(x / marge), avec
    marge = min(PLAFOND, distance à la borne 0/100) — écart plafonné en
    douceur, jamais de blocage dur à 0 ou 100 (voir niveau_sature()).

Système linéaire, déterministe, indépendant de l'ordre des injections.
Convention d'échelle : level 100 = crise maximale, delta_level >= 0,
polarite +1 = aggrave (voir echelles.py).

Ce module est PUR (aucune lecture de fichier) : les données viennent de
l'appelant (banc_calibration.py, puis snapshot.py à l'intégration).
"""

import math

# ─────────────────────────────────────────
# PARAMÈTRES (réglables — calibration)
# ─────────────────────────────────────────

ANNEE_DEPART = 2025.0      # début de la simulation
PAS = 1.0 / 12.0           # pas d'intégration : 1 mois
ANNEES_PAR_CYCLE = 5.0     # 1 cycle de `lag` de la matrice = 5 ans
DEMI_VIE = 20.0            # demi-vie d'un choc après sa pleine force (années)
PLAFOND = 15.0             # écart max (doux) au niveau de référence (points)
K_COUPLAGE = 0.05          # gain global de couplage matriciel (calibré le 27/09 : ρ≈0.42, ×1.7)
GAIN_CHOCS = 0.25          # fraction de delta_level réellement injectée : le monde
                           # absorbe l'essentiel d'un choc isolé (calibré le 27/09 :
                           # sans ce gain, la seule somme des chocs directs atteignait
                           # +60 à +80 points sur gouvernance/territoires)

# ── Persistance des chocs (27 septembre 2026) ──
# Demi-vie par TYPE de choc. None = DEMI_VIE ci-dessus, résolu au moment du
# calcul (pas à l'import) : `banc_calibration.py --demi-vie` continue donc
# de régler d'un coup tous les types laissés à None.
DEMI_VIE_PAR_TYPE = {
    "entite":    None,
    "evenement": None,
    "signal":    None,
}

# Niveau de persistance choisi PAR CHOC (champ `persistance` des fiches),
# prioritaire sur la demi-vie de son type. Valeur = demi-vie en années ;
# None = demi-vie par défaut du type ; math.inf = aucune décroissance
# (le choc reste à pleine force après sa rampe).
PERSISTANCE = {
    "ephemere":   10.0,
    "normale":    None,
    "durable":    40.0,
    "permanente": math.inf,
}
PERSISTANCE_DEFAUT = "normale"

# ── Persistance des INSTANCES d'entités, déduite de leur trajectoire
# (27 septembre 2026) : l'effet d'une entité dure tant qu'elle existe.
#   - trajectoire active                -> PERSISTANCE_INSTANCE_ACTIVE
#   - trajectoire terminée + annee_fin  -> pleine force jusqu'à annee_fin,
#                                          puis décroissance normale
#   - terminée sans annee_fin           -> normale (comportement d'avant)
# Un champ `persistance` explicite (bloc injection de l'instance, ou d'un
# impact) reste prioritaire. False = retour au comportement d'avant pour
# toutes les instances (demi-vie du type, décroissance dès la fin de rampe).
PERSISTANCE_INSTANCES_PAR_TRAJECTOIRE = True
PERSISTANCE_INSTANCE_ACTIVE = "permanente"   # repli possible : "durable"
TRAJECTOIRES_ACTIVES = {"emergent", "marginal", "ascendant", "dominant", "mature",
                        "declinant", "residuel", "transforme"}
TRAJECTOIRES_TERMINEES = {"disparu", "historique", "mythifie"}

# resilience (1-5) -> période propre T (années) ; ω = 2π / T
PERIODE_PAR_RESILIENCE = {1: 40.0, 2: 30.0, 3: 20.0, 4: 15.0, 5: 10.0}
PERIODE_DEFAUT = 20.0

# volatility -> ζ (1.0 = amortissement critique, pas de dépassement)
ZETA_PAR_VOLATILITY = {"low": 1.0, "medium": 0.7, "high": 0.45, "very_high": 0.3}
ZETA_DEFAUT = 0.7

# systemic_criticality (1-5) -> multiplicateur côté SOURCE (même table que P22)
CRITICITE = {1: 0.7, 2: 0.85, 3: 1.0, 4: 1.3, 5: 1.6}
CRITICITE_DEFAUT = 1.0


# ─────────────────────────────────────────
# Paramètres par variable
# ─────────────────────────────────────────

def parametres_variable(sim):
    """sim = bloc `simulation` d'une fiche variable (dict, éventuellement vide)."""
    sim = sim or {}
    try:
        periode = PERIODE_PAR_RESILIENCE.get(int(sim.get("resilience")), PERIODE_DEFAUT)
    except (TypeError, ValueError):
        periode = PERIODE_DEFAUT
    zeta = ZETA_PAR_VOLATILITY.get(str(sim.get("volatility", "")), ZETA_DEFAUT)
    try:
        crit = CRITICITE.get(int(sim.get("systemic_criticality")), CRITICITE_DEFAUT)
    except (TypeError, ValueError):
        crit = CRITICITE_DEFAUT
    return {"omega": 2 * math.pi / periode, "zeta": zeta, "crit": crit}


def couplages(variables, edges, params):
    """Liste (source, cible, coefficient, retard_en_pas) pour les liens entre
    variables connues. Aucun seuil de poids : tous les liens participent,
    pondérés par leur weight × temporal_weight."""
    out = []
    for e in edges:
        s, t = e["source"], e["target"]
        if s not in variables or t not in variables or s == t:
            continue
        c = (float(e.get("weight", 0)) * int(e.get("polarity", 1))
             * float(e.get("temporal_weight", 1.0)) * params[s]["crit"])
        retard = int(round(float(e.get("lag", 0)) * ANNEES_PAR_CYCLE / PAS))
        out.append((s, t, c, retard))
    return out


def rayon_spectral(variables, liens, k=None):
    """Rayon spectral de K·C (gain statique des boucles). < 1 = stable en
    régime permanent : un choc constant produit un écart borné. Calcul par
    itération de puissance sur |K·C| (majorant sûr, pas besoin de numpy)."""
    k = K_COUPLAGE if k is None else k
    idx = {v: n for n, v in enumerate(variables)}
    n = len(variables)
    m = [[0.0] * n for _ in range(n)]
    for s, t, c, _ in liens:
        m[idx[t]][idx[s]] += abs(k * c)
    vec = [1.0] * n
    lam = 0.0
    for _ in range(200):
        nv = [sum(m[i][j] * vec[j] for j in range(n)) for i in range(n)]
        norme = max(nv)
        if norme <= 0:
            return 0.0
        lam = norme / (max(vec) or 1.0)
        vec = [x / norme for x in nv]
    return lam


def k_effectif(variables, liens, params, marge_max=0.9):
    """Garde-fou de stabilité (théorème du petit gain) : le produit
    (gain de résonance maximal d'une variable) × ρ(|K·C|) doit rester < 1
    quels que soient les retards. S'il dépasse marge_max, K est réduit
    automatiquement. Retourne (k, indicateur, reduit)."""
    pic = 1.0
    for v in variables:
        z = params[v]["zeta"]
        if z < 0.7071:
            pic = max(pic, 1.0 / (2 * z * math.sqrt(1 - z * z)))
    indicateur = pic * rayon_spectral(variables, liens, K_COUPLAGE)
    if indicateur <= marge_max:
        return K_COUPLAGE, indicateur, False
    k = K_COUPLAGE * marge_max / indicateur
    return k, pic * rayon_spectral(variables, liens, k), True


# ─────────────────────────────────────────
# Forçages
# ─────────────────────────────────────────

def normaliser_persistance(valeur):
    """Ramène un champ `persistance` saisi à la main à une clé de PERSISTANCE
    (casse et accents ignorés : "Éphémère" -> "ephemere", "permanent" ->
    "permanente"). Retourne None si la valeur est absente, PERSISTANCE_DEFAUT
    n'étant PAS substitué ici pour que l'appelant puisse distinguer
    "absent" de "inconnu" ; retourne la chaîne brute si elle est inconnue."""
    if valeur is None or str(valeur).strip() == "":
        return None
    import unicodedata
    brut = unicodedata.normalize("NFKD", str(valeur).strip().lower())
    brut = "".join(c for c in brut if not unicodedata.combining(c))
    if brut == "permanent":
        brut = "permanente"
    return brut


def persistance_instance(inst, inj, imp):
    """(persistance, fin) d'un choc d'instance -- voir PERSISTANCE_INSTANCES_
    PAR_TRAJECTOIRE. `fin` = année jusqu'à laquelle le choc reste à pleine
    force avant de décroître (None = pas de palier)."""
    explicite = imp.get("persistance") or inj.get("persistance")
    if explicite or not PERSISTANCE_INSTANCES_PAR_TRAJECTOIRE:
        return explicite, None
    traj = normaliser_persistance(inst.get("trajectoire"))  # même nettoyage casse/accents
    if traj in TRAJECTOIRES_ACTIVES:
        return PERSISTANCE_INSTANCE_ACTIVE, None
    if traj in TRAJECTOIRES_TERMINEES:
        try:
            return None, float(inst.get("annee_fin"))
        except (TypeError, ValueError):
            return None, None
    return None, None


def demi_vie_choc(choc):
    """Demi-vie effective d'un choc : son niveau `persistance` s'il en a un
    (et qu'il est reconnu), sinon la demi-vie de son type, sinon DEMI_VIE.
    Une valeur de persistance inconnue retombe sur "normale" (le loader et
    les scripts d'injection la signalent en amont)."""
    niveau = normaliser_persistance(choc.get("persistance")) or PERSISTANCE_DEFAUT
    dv = PERSISTANCE.get(niveau)
    if dv is None:
        dv = DEMI_VIE_PAR_TYPE.get(choc.get("type"))
    return DEMI_VIE if dv is None else float(dv)


def forcage(choc, t):
    """Valeur (points de level) d'un choc à la date t : rampe linéaire sur
    `duree` années, puis décroissance exponentielle de demi-vie
    demi_vie_choc(choc) -- aucune décroissance si elle est infinie.
    Avec choc["fin"] (instance terminée, 27 septembre 2026) : palier à
    pleine force jusqu'à `fin`, décroissance seulement ensuite ; si `fin`
    tombe pendant la rampe, la montée s'arrête là et décroît aussitôt."""
    t0, duree, amp = choc["t0"], max(float(choc["duree"]), PAS), choc["amplitude"] * GAIN_CHOCS
    if t < t0:
        return 0.0
    fin = choc.get("fin")
    fin_montee = t0 + duree
    if fin is not None and fin < fin_montee:
        fin_montee = max(fin, t0)
    if t < fin_montee:
        return amp * (t - t0) / duree
    pic = amp * (fin_montee - t0) / duree
    debut_decroissance = max(fin_montee, fin) if fin is not None else fin_montee
    if t < debut_decroissance:
        return pic
    dv = demi_vie_choc(choc)
    if math.isinf(dv):
        return pic
    return pic * 0.5 ** ((t - debut_decroissance) / dv)


def niveau_sature(ref, x):
    """Référence + écart plafonné en douceur. La marge disponible est
    min(PLAFOND, distance à la borne 0 ou 100) : une variable déjà à 95
    ne peut monter que vers 100 (asymptotiquement), jamais s'y bloquer
    d'un coup ni la dépasser."""
    marge = min(PLAFOND, (100.0 - ref) if x >= 0 else ref)
    if marge <= 1e-6:
        return ref
    return ref + marge * math.tanh(x / marge)


# ─────────────────────────────────────────
# Intégration
# ─────────────────────────────────────────

def simuler(variables, niveaux_ref, params, liens, chocs, date_fin, echantillonner=None, k=None):
    """
    variables    : liste de slugs
    niveaux_ref  : {slug: level de référence du scénario}
    params       : {slug: parametres_variable(...)}
    liens        : couplages(...)
    chocs        : [{"nom", "variable", "t0", "duree", "amplitude", "via_matrice"}]
    date_fin     : date de l'article (float, ex. 2098.08)
    echantillonner : None, ou pas (années) pour renvoyer une trajectoire

    Retourne {"niveaux": {slug: level final}, "ecarts": {slug: x final},
              "trajectoire": [(t, {slug: level})]  (si echantillonner)}
    """
    k_coup = K_COUPLAGE if k is None else k
    n_pas = max(0, int(math.ceil((date_fin - ANNEE_DEPART) / PAS)))
    x_net = {v: 0.0 for v in variables}
    v_net = {v: 0.0 for v in variables}
    x_loc = {v: 0.0 for v in variables}
    v_loc = {v: 0.0 for v in variables}
    hist = {v: [] for v in variables}          # x_net passés, pour les retards
    entrants = {v: [] for v in variables}
    for s, t, c, r in liens:
        entrants[t].append((s, c, r))
    chocs_net = [c for c in chocs if c.get("via_matrice") and c["variable"] in x_net]
    chocs_loc = [c for c in chocs if not c.get("via_matrice") and c["variable"] in x_net]

    def niveau(v):
        return niveau_sature(niveaux_ref[v], x_net[v] + x_loc[v])

    trajectoire = []
    ecarts_traj = []
    prochain_echantillon = ANNEE_DEPART
    for k in range(n_pas):
        t = ANNEE_DEPART + k * PAS
        if echantillonner and t >= prochain_echantillon - 1e-9:
            trajectoire.append((round(t, 3), {v: niveau(v) for v in variables}))
            ecarts_traj.append((round(t, 3), {v: x_net[v] + x_loc[v] for v in variables}))
            prochain_echantillon += echantillonner
        for v in variables:
            hist[v].append(x_net[v])
        u_net = {v: 0.0 for v in variables}
        u_loc = {v: 0.0 for v in variables}
        for c in chocs_net:
            u_net[c["variable"]] += forcage(c, t)
        for c in chocs_loc:
            u_loc[c["variable"]] += forcage(c, t)
        for v in variables:
            coup = 0.0
            for s, cf, r in entrants[v]:
                i = k - r
                if i >= 0:
                    coup += cf * hist[s][i]
            w, z = params[v]["omega"], params[v]["zeta"]
            # Euler semi-implicite (stable pour ω·PAS << 1)
            a = w * w * (u_net[v] + k_coup * coup - x_net[v]) - 2 * z * w * v_net[v]
            v_net[v] += PAS * a
            a = w * w * (u_loc[v] - x_loc[v]) - 2 * z * w * v_loc[v]
            v_loc[v] += PAS * a
        for v in variables:
            x_net[v] += PAS * v_net[v]
            x_loc[v] += PAS * v_loc[v]

    t_fin = ANNEE_DEPART + n_pas * PAS
    if echantillonner:
        trajectoire.append((round(t_fin, 3), {v: niveau(v) for v in variables}))
    return {
        "niveaux": {v: round(niveau(v), 1) for v in variables},
        "ecarts": {v: round(x_net[v] + x_loc[v], 2) for v in variables},
        "trajectoire": trajectoire,
        "ecarts_traj": ecarts_traj,
    }


# ─────────────────────────────────────────
# Collecte des chocs depuis les structures du loader
# ─────────────────────────────────────────

def chocs_depuis_donnees(scenario, instances, events, signals):
    """Convertit les données chargées par loader.py en liste de chocs.
    Mêmes champs et même convention de signe que les anciennes fonctions
    apply_custom_* de snapshot.py (abs(delta_level) × polarite)."""
    chocs = []

    def amp(delta, pol):
        try:
            return abs(float(delta or 0)) * (1 if int(pol or 1) >= 0 else -1)
        except (TypeError, ValueError):
            return 0.0

    for inst in instances or []:
        inj = inst.get("injection") or {}
        if inj.get("type") != "custom" or not inj.get("annee_injection"):
            continue
        via = bool((inj.get("propagation") or {}).get("via_matrice", False))
        for imp in inj.get("impact_sur_variables") or []:
            persistance, fin = persistance_instance(inst, inj, imp)
            chocs.append({"nom": inst.get("name", inst.get("slug", "?")), "type": "entite",
                          "variable": imp.get("variable", ""), "t0": float(inj["annee_injection"]),
                          "duree": float(imp.get("duree") or 15), "via_matrice": via,
                          "persistance": persistance, "fin": fin,
                          "amplitude": amp(imp.get("delta_level"), imp.get("polarite", 1))})

    for ev in events or []:
        for imp in ev.get("impacts") or []:
            chocs.append({"nom": ev.get("name", "?"), "type": "evenement",
                          "variable": imp.get("variable", ""), "t0": float(ev.get("date", 2050)),
                          "duree": float(imp.get("duree") or 15), "via_matrice": bool(ev.get("via_matrice", False)),
                          "persistance": imp.get("persistance") or ev.get("persistance"),
                          "amplitude": amp(imp.get("delta_level"), imp.get("polarite", 1))})

    for sig in signals or []:
        d = (sig.get("scenarios") or {}).get(scenario)
        if not d:
            continue
        chocs.append({"nom": "[signal] " + str(sig.get("source_fiche", "signal")).replace(".md", ""),
                      "type": "signal", "variable": sig.get("variable", ""),
                      "t0": float(d.get("annee_injection", 2050)), "duree": float(d.get("duree") or 15),
                      "via_matrice": bool(sig.get("propagation_via_matrice", False)),
                      "persistance": d.get("persistance") or sig.get("persistance"),
                      "amplitude": amp(d.get("delta_level"), d.get("polarite", 1))})

    return [c for c in chocs if c["amplitude"]]

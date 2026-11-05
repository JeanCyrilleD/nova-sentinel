"""Adds risk amplifiers to out/dashboard.html: El Nino banner, current amplifier status per country, tested results."""
import json, html, contextlib, io, pandas as pd
res = json.load(open("out/amplifier_eval.json"))
with contextlib.redirect_stdout(io.StringIO()):
    from amplifier_eval import NB, p, W, active_drought, conflict_spike, oni, recent_event, surge, quiet
NAMES = dict(pd.read_csv("data/who_week_all.csv").groupby("iso_3_code")["adm0_viz_n"].first())
EAST = {"KEN", "SOM", "ETH", "UGA", "TZA", "SSD", "SDN", "RWA", "BDI"}
last = W.max(); win = W[W > last - pd.Timedelta(days=28)]
o_m, o_v = oni.index[-1], oni.iloc[-1]
rows = []
for c, nbs in NB.items():
    if c not in p:
        continue
    nbs = [n for n in nbs if n in p]
    s = {"voisin": [NAMES.get(n, n) for n in nbs if surge[n].loc[win].any()],
         "sécheresse": bool(active_drought(c).loc[last]), "conflits": bool(conflict_spike(c).loc[last]),
         "El Niño": c in EAST and o_v >= 0.5, "inondation": bool(recent_event(c, ["FL"], ["Green", "Orange", "Red"]).loc[last])}
    n_sig = int(bool(s["voisin"])) + s["sécheresse"] + s["conflits"] + s["El Niño"]
    active = (not quiet[c].loc[win].any()) and p[c].loc[win].sum() > 0
    level = "ÉPIDÉMIE EN COURS" if active else ("ALERTE" if n_sig >= 2 or len(s["voisin"]) >= 2 else ("VIGILANCE" if n_sig == 1 else "—"))
    rows.append((level, NAMES.get(c, c), s, n_sig))
order = {"ALERTE": 0, "VIGILANCE": 1, "ÉPIDÉMIE EN COURS": 2, "—": 3}
col = {"ALERTE": "#ef4444", "VIGILANCE": "#f59e0b", "ÉPIDÉMIE EN COURS": "#64748b", "—": "#334155"}
tr = ""
for level, nm, s, n in sorted(rows, key=lambda r: (order[r[0]], r[1])):
    tags = []
    if s["voisin"]: tags.append("voisin en hausse : " + ", ".join(s["voisin"]))
    if s["sécheresse"]: tags.append("sécheresse active (GDACS)")
    if s["conflits"]: tags.append("pic de conflits (HDX)")
    if s["El Niño"]: tags.append(f"El Niño fort (ONI {o_v:+.1f})")
    if s["inondation"]: tags.append("inondation récente (contexte)")
    tr += f'<tr><td style="color:{col[level]};font-weight:700">{level}</td><td>{html.escape(nm)}</td><td>{html.escape(" · ".join(tags) or "aucun signal")}</td></tr>'
keep = ["VIGILANCE seule (1 voisin)", "ALERTE (2 voisins)", "sécheresse active seul", "pic de conflits (z>=1) seul",
        "El Niño, Afrique de l'Est seulement", "inondation (GDACS, 8 sem.) seul", "inondation grave (orange/rouge) seul",
        "El Niño (ONI>=0.5) seul", "Score >= 1 signal", "Score >= 2 signaux (voisin, sécheresse, conflits, El Niño Est)"]
verdict = lambda r: ("gardé" if (r["ppv"] or 0) >= 0.3 or r["rule"].startswith("Score") or r["rule"].startswith("VIGILANCE seule") else "contexte seulement")
mt = "".join(f"<tr><td>{html.escape(r['rule'])}</td><td>{int(r['sensitivity']*100)} %</td><td>{r['alert_episodes']}</td><td>{'' if r['ppv'] is None else str(int(r['ppv']*100)) + ' %'}</td><td>{r['median_lead_days'] or '–'} j</td><td>{verdict(r)}</td></tr>"
             for k in keep for r in res if r["rule"] == k)
sec = f"""<h2>Climat, catastrophes et crises : amplificateurs de risque</h2>
<div class="card" style="border-left:5px solid #ef4444"><b>El Niño fort en cours</b> : indice ONI {o_v:+.2f} ({o_m:%B %Y}). Historiquement associé à des pluies extrêmes et des épidémies de choléra en Afrique de l'Est (Kenya, Somalie, Éthiopie, Ouganda, Tanzanie) pendant les petites pluies d'octobre à décembre, et à la sécheresse en Afrique australe. <b>Action :</b> vérifier les plans de contingence choléra et les stocks dans ces pays dès maintenant.</div>
<div class="card scroll"><table><tr><th>Niveau</th><th>Pays</th><th>Signaux actifs</th></tr>{tr}</table>
<small>VIGILANCE = 1 signal (voisin en hausse, sécheresse active, pic de conflits, El Niño en Afrique de l'Est). ALERTE = 2 signaux ou plus, ou 2 voisins en hausse.</small></div>
<div class="card"><b>Chaque facteur a été testé sur les 39 débuts d'épidémie (2023–2026)</b><table><tr><th>Signal</th><th>Débuts détectés</th><th>Épisodes</th><th>Alertes justes (hasard : 20 %)</th><th>Avance médiane</th><th>Décision</th></tr>{mt}</table>
<small>Leçons : la sécheresse active est le meilleur amplificateur (2 fois plus fiable que le hasard) ; El Niño ne compte qu'en Afrique de l'Est ; les inondations GDACS, toutes gravités confondues, ne font pas mieux que le hasard au niveau national et restent du contexte ; les inondations graves et cyclones ont été trop rares sur la période pour être évalués.</small></div>"""
page = open("out/dashboard.html").read()
page = page
act = ("<div class='card'><b>Action proportionnée</b> · <b style='color:#ef4444'>ALERTE</b> : surveillance renforcée des diarrhées aqueuses aiguës (zones frontalières, camps, zones sinistrées), stocks de SRO, tests rapides et kits WASH, plan de vaccination réactive prêt. "
       "<b style='color:#f59e0b'>VIGILANCE</b> : rappel de la définition de cas aux formations sanitaires et vérification des stocks. "
       "<b>Qui agit :</b> direction de la surveillance épidémiologique du ministère de la Santé, avec le cluster WASH. Une personne habilitée décide.</div>")
top = sec.split("<div class=\"card\"><b>Chaque facteur")[0].replace("<h2>Climat, catastrophes et crises : amplificateurs de risque</h2>", "<h2>Alertes de la semaine (26 pays d'Afrique suivis)</h2>") + act
tested = "<h2>Climat, catastrophes et crises : chaque facteur testé</h2><div class=\"card\"><b>Chaque facteur" + sec.split("<div class=\"card\"><b>Chaque facteur")[1]
a = page.index("<h2>Alertes de la semaine"); b = page.index("<h2>Fiabilité")
page = page[:a] + top + page[b:]
page = page.replace("<h2>Historique", tested + "<h2>Historique", 1)
open("out/dashboard.html", "w").write(page)
print(sorted(((r[0], r[1]) for r in rows if r[0] in ("ALERTE", "VIGILANCE")), key=lambda x: order[x[0]]))

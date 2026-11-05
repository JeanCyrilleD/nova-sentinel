"""Nova Sentinel dashboard v2: current tiered alerts (watch = 1 neighbour surging, warning = >=2), explanation, action, backtest metrics."""
import json, html, datetime as dt, contextlib, io, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    from backtest_crossborder_africa import NB, p, surge, quiet
ev = json.load(open("out/fusion_eval.json")); bt = json.load(open("out/backtest_crossborder_africa.json"))
NAMES = dict(pd.read_csv("data/who_week_all.csv").groupby("iso_3_code")["adm0_viz_n"].first())
last = p.index.max(); win = p.index[p.index > last - pd.Timedelta(days=28)]
alerts = []
for c, nbs in NB.items():
    nbs = [n for n in nbs if n in p]
    if c not in p or not nbs: continue
    if not quiet[c].loc[win].any() and p[c].loc[win].sum() > 0:
        alerts.append((c, "active", [], int(p[c].loc[win].sum()))); continue
    hot = [n for n in nbs if surge[n].loc[win].any()]
    if hot: alerts.append((c, "warning" if len(hot) >= 2 else "watch", hot, 0))
lvl = {"warning": ("#ef4444", "ALERTE"), "watch": ("#f59e0b", "VIGILANCE"), "active": ("#64748b", "ÉPIDÉMIE EN COURS")}
order = {"warning": 0, "watch": 1, "active": 2}
cards = []
for c, l, hot, cases in sorted(alerts, key=lambda a: order[a[1]]):
    col, lab = lvl[l]; nm = NAMES.get(c, c)
    if l == "active":
        body = f"{cases} cas signalés sur 4 semaines : riposte en cours, pas d'alerte précoce à donner."
    else:
        why = ", ".join(f"{NAMES.get(n, n)} ({int(p[n].loc[win].sum())} cas / 4 sem.)" for n in hot)
        act = ("Activer la surveillance renforcée des diarrhées aqueuses aiguës aux points d'entrée et dans les zones frontalières, vérifier les stocks de SRO, tests rapides et kits WASH, préparer un plan de vaccination réactive."
               if l == "warning" else "Rappeler la définition de cas aux formations sanitaires frontalières et vérifier les stocks de SRO et de tests rapides.")
        body = (f"<b>Pourquoi :</b> poussée de choléra chez {why}. {nm} n'a déclaré aucun cas depuis au moins 8 semaines.<br>"
                f"<b>Action proportionnée :</b> {act}<br><b>Qui agit :</b> direction de la surveillance épidémiologique (ministère de la Santé), avec le cluster WASH.")
    cards.append(f'<div class="card" style="border-left:5px solid {col}"><b style="color:{col}">{lab}</b> · <b>{html.escape(nm)}</b><br>{body}</div>')
rows = "".join(f"<tr><td>{html.escape(e['signal'])}</td><td>{int(e['sensitivity']*100)} %</td><td>{e['alert_episodes']}</td><td>{int(e['ppv']*100)} %</td><td>{int(e['base_rate']*100)} %</td><td>{e['median_lead_days']} j</td></tr>" for e in ev)
hist = "".join(f"<tr><td>{html.escape(NAMES.get(o['country'], o['country']))}</td><td>{o['onset']}</td><td>{'✓ ' + str(o['lead_days']) + ' j avant' if o['alerted'] else '✗ manquée'}</td><td>{html.escape(', '.join(NAMES.get(x.strip(), x.strip()) for x in o['why'].split(',') if x.strip()))}</td></tr>" for o in sorted(bt["onsets"], key=lambda o: o["onset"], reverse=True))
s = bt["summary"]; now = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nova Sentinel</title>
<style>body{{margin:0;background:#06121f;color:#e2e8f0;font-family:Inter,system-ui,sans-serif;line-height:1.45}}main{{max-width:980px;margin:auto;padding:24px 16px}}
h1{{margin:0;font-size:28px}}h2{{font-size:18px;margin:26px 0 10px;color:#5eead4}}.sub{{color:#94a3b8;margin:4px 0 18px}}.card{{background:#0c1f33;border:1px solid #16324f;border-radius:12px;padding:14px 16px;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}td,th{{padding:7px 8px;border-bottom:1px solid #16324f;text-align:left;vertical-align:top}}th{{color:#94a3b8;font-weight:600}}
.kpi{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.kpi div{{background:#0c1f33;border:1px solid #16324f;border-radius:12px;padding:12px}}.kpi b{{font-size:24px;display:block;color:#f8fafc}}
small{{color:#94a3b8}}.scroll{{max-height:360px;overflow:auto}}</style></head><body><main>
<h1>🛡️ Nova Sentinel</h1><div class="sub">Alerte précoce explicable du choléra par signaux transfrontaliers · données OMS jusqu'à la semaine du {last.date()} · généré le {now}</div>
<h2>Alertes de la semaine (26 pays d'Afrique suivis)</h2>{''.join(cards) or '<div class="card">Aucune alerte cette semaine.</div>'}
<h2>Fiabilité mesurée sur {s['period']}</h2>
<div class="kpi"><div><b>{s['onsets']}</b>débuts d'épidémie testés</div><div><b>{int(ev[0]['sensitivity']*100)} %</b>précédés d'une vigilance</div><div><b>{ev[0]['median_lead_days']} j</b>d'avance médiane</div><div><b>{int(ev[2]['ppv']*100)} %</b>des ALERTES suivies d'une épidémie (vs {int(ev[2]['base_rate']*100)} % au hasard)</div></div>
<div class="card"><table><tr><th>Règle</th><th>Débuts détectés</th><th>Épisodes d'alerte</th><th>Alertes justes</th><th>Taux au hasard</th><th>Avance médiane</th></tr>{rows}</table>
<small>Lecture : un seul voisin en poussée = VIGILANCE (large, peu spécifique). Deux voisins ou plus = ALERTE (rare, deux fois plus fiable que le hasard). La pluie n'améliore pas la fiabilité : elle est affichée comme contexte, pas comme déclencheur.</small></div>
<h2>Historique des débuts d'épidémie</h2><div class="card scroll"><table><tr><th>Pays</th><th>Début</th><th>Vigilance ?</th><th>Signal</th></tr>{hist}</table></div>
<h2>Garde-fous</h2><div class="card"><small>Données publiques et agrégées au niveau national uniquement (OMS, Open-Meteo ERA5, HDX HAPI) : aucune donnée individuelle. Les alertes proposent une action, une personne habilitée décide. Limites : données nationales hebdomadaires (pas de détail infranational), sous-déclaration variable selon les pays, 4 ans d'historique seulement. Voir DOCS.md.</small></div>
</main></body></html>"""
open("out/dashboard.html", "w").write(page); print(len(alerts), "alerts:", [(a[0], a[1]) for a in alerts])

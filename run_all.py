"""Nova Sentinel: refresh data, run backtests, build out/dashboard.html"""
import subprocess, sys, json, pandas as pd, html, datetime as dt
steps = [["ingest/who_don.py"], ["ingest/who_cholera_weekly.py"], ["backtest_cholera_chad_2026.py"]]
log = []
for s in steps:
    r = subprocess.run([sys.executable] + s, capture_output=True, text=True, timeout=300)
    log.append((s[0], r.returncode == 0))
b26 = json.load(open("out/backtest_cholera_chad_2026.json"))
b25 = json.load(open("out/backtest_cholera_chad_2025.json")); rvf = json.load(open("out/backtest_rvf_2025.json"))
d = pd.read_csv("data/who_cholera_weekly.csv", parse_dates=["date_wk"])
p = d.pivot_table(index=d.date_wk.dt.to_period("W-SUN").dt.start_time, columns="iso_3_code", values="cases", aggfunc="sum").fillna(0)
p = p.loc["2026-03-01":"2026-10-15"]
W, H, L, T = 900, 320, 50, 20
cols = {"TCD": "#f59e0b", "SDN": "#2dd4bf", "NGA": "#818cf8", "CMR": "#f472b6", "CAF": "#94a3b8"}
def xy(i, v, vmax): return L + i * (W - L - 20) / (len(p) - 1), T + (H - T - 30) * (1 - v / vmax)
svg = []
for c, col in cols.items():
    if c not in p: continue
    s = p[c]; vmax = max(s.max(), 1)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(i, v, vmax) for i, v in enumerate(s)))
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{3 if c=="TCD" else 2}" opacity="{1 if c in ("TCD","SDN") else .55}"/>')
def vline(date, label, col):
    i = (p.index <= pd.Timestamp(date)).sum() - 1; x = xy(i, 0, 1)[0]
    return f'<line x1="{x}" x2="{x}" y1="{T}" y2="{H-30}" stroke="{col}" stroke-dasharray="5 4"/><text x="{x+4}" y="{T+14}" fill="{col}" font-size="12">{label}</text>'
svg.append(vline("2026-05-11", "Alerte : poussée Soudan", "#2dd4bf"))
svg.append(vline(b26["chad_onset_week"], "Premiers cas Tchad", "#f59e0b"))
months = [(i, ix.strftime("%b")) for i, ix in enumerate(p.index) if ix.day <= 7]
svg += [f'<text x="{xy(i,0,1)[0]:.0f}" y="{H-8}" fill="#94a3b8" font-size="12">{m}</text>' for i, m in months]
legend = " ".join(f'<span style="color:{c}">■ {k}</span>' for k, c in cols.items())
rows = [("Choléra Tchad 2026", "Épidémies chez les voisins", f"{b26['lead_time_days']} j (Nigeria) · 28 j (Soudan)", "Non estimable (1 seul événement)", "Prometteur"),
        ("Choléra Tchad 2025", "Pluie + conflits (Ouaddaï)", "Aucune alerte", f"{len(b25['seasons_with_alert_2015_2024'])} saisons / 10", "Échec"),
        ("Vallée du Rift MR/SN 2025", "Pluie seule (5 sites)", "Aucune alerte (pic z=" + str(rvf["peak_z_2025_JulSep"]) + ")", "Plusieurs années", "Échec")]
tr = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
now = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nova Sentinel</title>
<style>body{{margin:0;background:#06121f;color:#e2e8f0;font-family:Inter,system-ui,sans-serif}}main{{max-width:960px;margin:auto;padding:24px 16px}}
h1{{margin:0;font-size:28px}}.sub{{color:#5eead4;margin:4px 0 20px}}.card{{background:#0c1f33;border:1px solid #16324f;border-radius:14px;padding:18px;margin-bottom:16px}}
.alert{{border-left:5px solid #f59e0b}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{padding:8px;border-bottom:1px solid #16324f;text-align:left}}
th{{color:#94a3b8;font-weight:600}}svg{{width:100%;height:auto}}small{{color:#94a3b8}}</style></head><body><main>
<h1>🛡️ Nova Sentinel</h1><div class="sub">Alerte précoce explicable · santé des populations · mis à jour {now}</div>
<div class="card alert"><b>Exemple d'alerte (rejouée) — semaine du 11 mai 2026 · Tchad Est</b><br>
Signal : poussée de choléra au Soudan (cas sur 2 semaines ≥ 3× la moyenne des 6 semaines précédentes). Contexte : saison des pluies proche, camps de réfugiés soudanais à l'est du Tchad.<br>
<b>Action proportionnée suggérée :</b> renforcer la surveillance des diarrhées aiguës et pré-positionner SRO et kits WASH dans les camps de l'Ouaddaï · <b>Qui agit :</b> surveillance épidémiologique du ministère de la Santé, cluster WASH.<br>
<b>Résultat réel :</b> premiers cas au Tchad 4 semaines plus tard (semaine du {b26['chad_onset_week']}).</div>
<div class="card"><b>Cas hebdomadaires de choléra (OMS), mars–octobre 2026</b> — chaque courbe à sa propre échelle<br><small>{legend}</small>
<svg viewBox="0 0 {W} {H}">{''.join(svg)}</svg></div>
<div class="card"><b>Tests sur des épidémies passées</b><table><tr><th>Épidémie</th><th>Signal</th><th>Avance</th><th>Fausses alertes</th><th>Verdict</th></tr>{tr}</table>
<small>Leçon : la météo et les conflits seuls ne prédisent pas ; les épidémies voisines donnent l'avance. Prochaine étape : mesurer les fausses alertes sur 2023–2025 et combiner les signaux.</small></div>
<div class="card"><small>Sources : OMS (Disease Outbreak News ; tableau de bord mondial du choléra), Open-Meteo ERA5, HDX HAPI (données agrégées). Données publiques agrégées uniquement, aucune donnée individuelle. Pipeline : {", ".join(f"{s} {'✓' if ok else '✗'}" for s, ok in log)}.</small></div>
</main></body></html>"""
open("out/dashboard.html", "w").write(page); print("dashboard ok", log)

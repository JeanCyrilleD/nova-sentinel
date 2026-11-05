"""Step 2: combine cross-border surge + rainfall (country centroid, 28-day seasonal z, Open-Meteo ERA5) + base-rate comparison.
Displacement (HAPI refugees, annual) is used as context in explanations only: too coarse in time to drive weekly alerts."""
import pandas as pd, numpy as np, requests, json, os
from backtest_crossborder_africa import NB, p, surge, quiet
d = pd.read_csv("data/who_week_all.csv"); cent = d.groupby("iso_3_code")[["center_lat", "center_lon"]].first()
R = pd.concat([pd.read_csv(f"data/rain/{f}", index_col=0, parse_dates=True).iloc[:, 0].rename(f[:3]) for f in os.listdir("data/rain")], axis=1)
if False:
    R = {}
    for c in NB:
        if c not in cent.index: continue
        la, lo = cent.loc[c]
        j = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=120, params={"latitude": round(la, 2), "longitude": round(lo, 2),
            "start_date": "2003-01-01", "end_date": "2026-10-25", "daily": "precipitation_sum", "timezone": "UTC"}).json()["daily"]
        R[c] = pd.Series(j["precipitation_sum"], index=pd.to_datetime(j["time"]))
    R = pd.DataFrame(R); R.to_csv(cache)
r28 = R.rolling(28, min_periods=20).sum()
doy = r28.index.dayofyear
base = r28[r28.index.year < 2023]
wet = r28.ge(base.quantile(0.5), axis=1)  # wet-season flag: 28-day rain above the 2012-2022 median for that country
wet_w = wet.reindex(p.index, method="nearest")
def evaluate(alert_fn, name):
    onsets = hits = eps_n = fa = 0; quiet_weeks = followed = 0; leads = []
    for c, nbs in NB.items():
        nbs = [n for n in nbs if n in p]
        if c not in p or not nbs: continue
        on = list(p.index[(p[c] > 0) & quiet[c]]); al = list(p.index[alert_fn(c, nbs)])
        for o in on:
            prev = [a for a in al if 7 <= (o - a).days <= 70]; onsets += 1
            if prev: hits += 1; leads.append((o - min(prev)).days)
        eps = []
        for a in al:
            if not eps or (a - eps[-1][-1]).days > 28: eps.append([a])
            else: eps[-1].append(a)
        eps_n += len(eps); fa += sum(1 for e in eps if not any(0 <= (o - e[0]).days <= 70 for o in on))
        for t in p.index[quiet[c]]:
            quiet_weeks += 1; followed += any(0 <= (o - t).days <= 70 for o in on)
    return {"signal": name, "sensitivity": round(hits / onsets, 2), "alert_episodes": eps_n, "ppv": round((eps_n - fa) / eps_n, 2) if eps_n else None,
            "base_rate": round(followed / quiet_weeks, 2), "median_lead_days": int(np.median(leads)) if leads else None, "onsets": onsets, "hits": hits}
A = lambda c, nbs: surge[nbs].any(axis=1) & quiet[c]
B = lambda c, nbs: A(c, nbs) & (wet_w[c] if c in wet_w else True)
C = lambda c, nbs: (surge[nbs].sum(axis=1) >= 2) & quiet[c]
out = [evaluate(A, "voisin en poussée"), evaluate(B, "voisin en poussée + saison humide"), evaluate(C, "≥2 voisins en poussée")]
json.dump(out, open("out/fusion_eval.json", "w"), indent=1, ensure_ascii=False)
for o in out: print(o)

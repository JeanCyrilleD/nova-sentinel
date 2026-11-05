"""Cross-border cholera signal, evaluated on all WHO weekly series 2023-2026 (data/who_week_all.csv).
Onset in country C = first week with cases after >= 8 weeks with zero reported cases.
Alert for C at week t = a neighbour surges (2-week cases >= 50 and >= 3x its previous 6-week mean), and C itself has had 0 cases for 8 weeks.
Hit = onset preceded by an alert 1-10 weeks before. False alarm = alert episode not followed by an onset within 10 weeks."""
import pandas as pd, json
NB = {"TCD": ["SDN","CAF","CMR","NGA","NER","LBY"], "SDN": ["TCD","SSD","ETH","ERI","EGY","LBY","CAF"], "SSD": ["SDN","ETH","KEN","UGA","COD","CAF"],
 "CAF": ["TCD","SDN","SSD","COD","COG","CMR"], "CMR": ["NGA","TCD","CAF","COG","GAB","GNQ"], "NGA": ["BEN","NER","TCD","CMR"],
 "NER": ["NGA","BEN","BFA","MLI","DZA","LBY","TCD"], "BFA": ["MLI","NER","BEN","TGO","GHA","CIV"], "MLI": ["SEN","MRT","DZA","NER","BFA","CIV","GIN"],
 "ETH": ["ERI","DJI","SOM","KEN","SSD","SDN"], "SOM": ["ETH","KEN","DJI"], "KEN": ["ETH","SOM","TZA","UGA","SSD"], "UGA": ["KEN","TZA","RWA","COD","SSD"],
 "TZA": ["KEN","UGA","RWA","BDI","COD","ZMB","MWI","MOZ"], "COD": ["CAF","SSD","UGA","RWA","BDI","TZA","ZMB","AGO","COG"], "ZMB": ["COD","TZA","MWI","MOZ","ZWE","BWA","NAM","AGO"],
 "MWI": ["TZA","ZMB","MOZ"], "MOZ": ["TZA","MWI","ZMB","ZWE","ZAF","SWZ"], "ZWE": ["ZMB","MOZ","ZAF","BWA"], "AGO": ["COD","ZMB","NAM","COG"],
 "BDI": ["RWA","TZA","COD"], "RWA": ["UGA","TZA","BDI","COD"], "COG": ["CMR","CAF","COD","AGO","GAB"], "GHA": ["CIV","BFA","TGO"], "TGO": ["GHA","BFA","BEN"], "BEN": ["TGO","BFA","NER","NGA"]}
d = pd.read_csv("data/who_week_all.csv", parse_dates=["date_wk"])
p = d.pivot_table(index="date_wk", columns="iso_3_code", values="cases", aggfunc="sum").asfreq("7D").fillna(0)
last2 = p.rolling(2).sum(); prev6 = p.shift(2).rolling(6, min_periods=3).mean() * 2
surge = (last2 >= 50) & (last2 >= 3 * prev6.clip(lower=1))
quiet = p.rolling(8).sum().shift(1) == 0
res, hits, onsets_n, alerts_n, fa = [], 0, 0, 0, 0
for c, nbs in NB.items():
    if c not in p: continue
    nbs = [n for n in nbs if n in p]
    if not nbs: continue
    onset = (p[c] > 0) & quiet[c]
    alert = surge[nbs].any(axis=1) & quiet[c]
    on_dates = list(p.index[onset]); al_dates = list(p.index[alert])
    # alert episodes: merge alerts within 4 weeks
    eps = []
    for a in al_dates:
        if not eps or (a - eps[-1][-1]).days > 28: eps.append([a])
        else: eps[-1].append(a)
    for o in on_dates:
        prev = [a for a in al_dates if 7 <= (o - a).days <= 70]
        onsets_n += 1
        if prev: hits += 1
        res.append({"country": c, "onset": str(o.date()), "alerted": bool(prev),
                    "lead_days": (o - min(prev)).days if prev else None,
                    "why": ", ".join(sorted({n for n in nbs if surge.loc[[a for a in prev], n].any()})) if prev else ""})
    for e in eps:
        alerts_n += 1
        if not any(0 <= (o - e[0]).days <= 70 for o in on_dates): fa += 1
lead = [r["lead_days"] for r in res if r["lead_days"]]
summary = {"period": f"{p.index.min().date()} to {p.index.max().date()}", "countries": len(NB), "onsets": onsets_n, "onsets_alerted": hits,
           "sensitivity": round(hits / onsets_n, 2) if onsets_n else None, "alert_episodes": alerts_n, "false_alarm_episodes": fa,
           "ppv": round((alerts_n - fa) / alerts_n, 2) if alerts_n else None, "median_lead_days": int(pd.Series(lead).median()) if lead else None}
json.dump({"summary": summary, "onsets": res}, open("out/backtest_crossborder_africa.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(summary, indent=1)); print(pd.DataFrame(res).to_string())

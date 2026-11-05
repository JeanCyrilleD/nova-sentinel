"""Backtest: cholera Chad 2026 (WHO weekly series: first Chad cases week of 8 Jun 2026).
Cross-border signal: a neighbour 'surges' when its last-2-week cases >= 50 and >= 3x its previous 6-week mean.
Neighbours of Chad: SDN, CAF, CMR, NGA, NER (LBY not in WHO series)."""
import pandas as pd, json
d = pd.read_csv("data/who_cholera_weekly.csv", parse_dates=["date_wk"])
p = d.pivot_table(index=d.date_wk.dt.to_period("W-SUN").dt.start_time, columns="iso_3_code", values="cases", aggfunc="sum").fillna(0)
NB = [c for c in ["SDN", "CAF", "CMR", "NGA", "NER"] if c in p]
last2 = p[NB].rolling(2).sum(); prev6 = p[NB].shift(2).rolling(6, min_periods=3).mean() * 2
surge = (last2 >= 50) & (last2 >= 3 * prev6.clip(lower=1))
tcd_onset = p.index[p["TCD"] > 0][p.index[p["TCD"] > 0] >= "2026-03-01"].min()
first = {c: str(surge.index[surge[c]].min().date()) for c in NB if surge[c].any()}
pre = {c: v for c, v in first.items() if pd.Timestamp(v) < tcd_onset}
first_any = min(pre.values()) if pre else None
res = {"chad_onset_week": str(tcd_onset.date()), "neighbour_first_surge": first,
       "first_cross_border_alert": first_any,
       "lead_time_days": (tcd_onset - pd.Timestamp(first_any)).days if first_any else None,
       "explanation": "; ".join(f"{c} surge {v}" for c, v in sorted(pre.items(), key=lambda x: x[1])),
       "caveat": "single event (2026); WHO weekly series available from 2026 only in this feed; false-alarm rate not estimable yet"}
json.dump(res, open("out/backtest_cholera_chad_2026.json", "w"), indent=1); print(json.dumps(res, indent=1))

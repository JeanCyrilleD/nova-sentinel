"""Backtest: cholera, Ouaddai (Chad), first confirmed case 13 Jul 2025 (Dougui camp; ReliefWeb EP-2025-000149-TCD).
Signals: (1) environment: 14-day rainfall, Abeche, seasonal z vs 2005-2024 (Open-Meteo ERA5);
(2) security/displacement pressure: conflict events Ouaddai, monthly (HDX HAPI, aggregated), z vs prior 24 months."""
import requests, pandas as pd, numpy as np, json
from fusion import seasonal_z, fuse, explain, THR
r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=120, params={"latitude": 13.83, "longitude": 20.83,
    "start_date": "2005-01-01", "end_date": "2025-12-31", "daily": "precipitation_sum", "timezone": "UTC"}).json()["daily"]
rain = pd.Series(r["precipitation_sum"], index=pd.to_datetime(r["time"])).rolling(14, min_periods=10).sum().resample("W-SUN").last()
rz = seasonal_z(rain, range(2005, 2025))
c = pd.read_csv("data/hapi_conflict_TCD.csv", usecols=["admin1_name", "events", "reference_period_start"])
c = c[c.admin1_name.str.contains("OUADDA", na=False)]
cm = c.groupby(pd.to_datetime(c.reference_period_start).dt.tz_localize(None))["events"].sum().sort_index()
cz_m = (cm - cm.rolling(24, min_periods=12).mean().shift(1)) / cm.rolling(24, min_periods=12).std().shift(1)
cz = cz_m.reindex(rz.index, method="ffill")
Z, score, alert = fuse({"rain_14d": rz, "conflict_ouaddai": cz})
onset = pd.Timestamp("2025-07-13")
win = (score.index >= "2025-04-01") & (score.index <= onset)
first = alert[win & alert].index.min()
# false alarms: alerts in Apr-Sep of 2015-2024 (no large declared cholera outbreak in Ouaddai in those seasons, assumption to verify)
fa_years = sorted({d.year for d in alert[alert & (alert.index.year.isin(range(2015, 2025))) & alert.index.month.isin(range(4, 10))].index})
res = {"onset": str(onset.date()), "first_alert_2025": str(first.date()) if pd.notna(first) else None,
       "lead_time_days": (onset - first).days if pd.notna(first) else None,
       "explanation_at_first_alert": explain(Z, first) if pd.notna(first) else None,
       "rain_only_first_alert": str(rz[win & (rz >= 1.5)].index.min().date()) if (win & (rz >= 1.5)).any() else None,
       "seasons_with_alert_2015_2024": fa_years, "threshold": THR,
       "assumption": "2015-2024 seasons treated as non-outbreak for Ouaddai; to verify with WHO AFRO bulletins"}
json.dump(res, open("out/backtest_cholera_chad_2025.json", "w"), indent=1)
pd.DataFrame({"score": score, "alert": alert}).join(Z).to_csv("out/cholera_chad_weekly.csv")
print(json.dumps(res, indent=1, ensure_ascii=False))

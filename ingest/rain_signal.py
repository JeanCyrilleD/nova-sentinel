"""Environmental signal: 30-day rainfall anomaly (z-score vs 2001-2024 climatology), Open-Meteo ERA5 archive (no key).
Backtest target: Rift Valley fever, Mauritania/Senegal 2025 (WHO DON584: first human cases 20 Sep 2025, first animal cases Aug 2025)."""
import requests, pandas as pd, numpy as np, os, json
BASE = os.path.join(os.path.dirname(__file__), "..")
SITES = {"Aleg (Brakna, MR)": (17.05, -13.92), "Rosso (Trarza, MR)": (16.51, -15.80), "Saint-Louis (SN)": (16.03, -16.49),
         "Aioun (Hodh El Gharbi, MR)": (16.66, -9.61), "Kiffa (Assaba, MR)": (16.62, -11.40)}
frames = []
for name, (lat, lon) in SITES.items():
    r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=120, params={
        "latitude": lat, "longitude": lon, "start_date": "2001-01-01", "end_date": "2025-12-31",
        "daily": "precipitation_sum,temperature_2m_max", "timezone": "UTC"})
    r.raise_for_status(); d = r.json()["daily"]
    df = pd.DataFrame({"date": pd.to_datetime(d["time"]), "rain": d["precipitation_sum"], "tmax": d["temperature_2m_max"]})
    df["site"] = name; frames.append(df)
df = pd.concat(frames)
df.to_csv(os.path.join(BASE, "data", "rain_daily.csv"), index=False)
df = df.sort_values(["site", "date"])
df["rain30"] = df.groupby("site")["rain"].transform(lambda s: s.rolling(30, min_periods=25).sum())
df["doy"] = df["date"].dt.dayofyear; df["year"] = df["date"].dt.year
clim = df[df.year.between(2001, 2024)].groupby(["site", "doy"])["rain30"].agg(["mean", "std"]).reset_index()
df = df.merge(clim, on=["site", "doy"])
df["z"] = (df["rain30"] - df["mean"]) / df["std"].replace(0, np.nan)
# regional signal = median z across sites; alert = z >= 1.5 sustained 7 days, Jul-Oct season
reg = df.groupby("date")["z"].median().rename("z").reset_index()
reg["alert"] = reg["z"].rolling(7).min() >= 1.5
reg.to_csv(os.path.join(BASE, "out", "rain_regional_z.csv"), index=False)
first = {}
for y in range(2001, 2026):
    a = reg[(reg.date.dt.year == y) & reg.alert & reg.date.dt.month.between(6, 10)]
    first[y] = str(a.date.min().date()) if len(a) else None
onset = pd.Timestamp("2025-09-20")
f25 = first[2025]
res = {"first_alert_by_year": first,
       "2025_first_alert": f25, "human_onset_2025": "2025-09-20",
       "lead_time_days_2025": (onset - pd.Timestamp(f25)).days if f25 else None,
       "peak_z_2025_JulSep": round(float(reg[(reg.date >= "2025-07-01") & (reg.date <= "2025-09-20")].z.max()), 2)}
json.dump(res, open(os.path.join(BASE, "out", "backtest_rvf_2025.json"), "w"), indent=1)
print(json.dumps(res, indent=1))

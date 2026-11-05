"""Nova Sentinel fusion: weekly multi-signal score with explanation.
Each signal -> z-score vs its own history (same week-of-year for seasonal signals). Score = mean of available z (missing inputs tolerated,
reported). Alert = score >= THR for 2 consecutive weeks. Explanation = contribution of each signal."""
import pandas as pd, numpy as np
THR = 1.0
def seasonal_z(s, base_years):
    df = s.to_frame("v"); df["w"] = df.index.isocalendar().week.values; df["y"] = df.index.year
    b = df[df.y.isin(base_years)].groupby("w")["v"].agg(["mean", "std"])
    m = df["w"].map(b["mean"]); sd = df["w"].map(b["std"]).replace(0, np.nan)
    return (df["v"] - m) / sd
def plain_z(s, base_mask):
    b = s[base_mask]; return (s - b.mean()) / (b.std() or np.nan)
def fuse(signals: dict):
    Z = pd.DataFrame(signals)
    score = Z.mean(axis=1, skipna=True)
    alert = (score >= THR) & (score.shift(1) >= THR)
    return Z, score, alert
def explain(Z, when):
    row = Z.loc[when].dropna().sort_values(ascending=False)
    return ", ".join(f"{k} z={v:+.1f}" for k, v in row.items()) + (f" | missing: {', '.join(Z.columns[Z.loc[when].isna()])}" if Z.loc[when].isna().any() else "")

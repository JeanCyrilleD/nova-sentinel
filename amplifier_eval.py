"""Evaluate risk amplifiers (floods, cyclones, drought, conflict spikes, El Nino) alone and combined with the cross-border WATCH.
Same protocol as backtest_crossborder_africa.py: onset = first cases after >= 8 quiet weeks; hit = alert 1-10 weeks before;
false alarm = alert episode not followed by an onset within 10 weeks; base rate = share of quiet weeks followed by an onset."""
import pandas as pd, numpy as np, json, contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    from backtest_crossborder_africa import NB, p, surge, quiet
W = p.index
g = pd.read_csv("data/gdacs_events.csv").dropna(subset=["iso3"])
g["from"] = pd.to_datetime(g["from"]); g["to"] = pd.to_datetime(g["to"])
g = g.drop_duplicates(["iso3", "id"])


def recent_event(c, types, levels, weeks=8):
    ev = g[(g.iso3 == c) & g.type.isin(types) & g.level.isin(levels)]
    s = pd.Series(False, index=W)
    for _, e in ev.iterrows():
        s |= (W >= e["from"]) & (W <= e["from"] + pd.Timedelta(weeks=weeks))
    return s


def active_drought(c):
    ev = g[(g.iso3 == c) & (g.type == "DR")]
    s = pd.Series(False, index=W)
    for _, e in ev.iterrows():
        s |= (W >= e["from"]) & (W <= e["to"])
    return s


cf = pd.read_csv("data/conflict_national.csv").dropna(subset=["month"])
cf["month"] = pd.to_datetime(cf["month"])
cm = cf.groupby(["iso3", "month"])["events"].sum().unstack(0).sort_index()
cz = (cm - cm.rolling(12, min_periods=6).mean().shift(1)) / cm.rolling(12, min_periods=6).std().shift(1)


def conflict_spike(c):
    if c not in cz:
        return pd.Series(False, index=W)
    z = cz[c].shift(1)  # monthly data is published after the month ends: use previous month only
    return (z.reindex(W, method="ffill") >= 1.0).fillna(False)


oni = pd.read_csv("data/oni.csv", parse_dates=["month"]).set_index("month")["oni"]
oni_w = oni.shift(1).reindex(W, method="ffill")  # previous month's value, as available in real time
elnino = (oni_w >= 0.5).fillna(False)
strong_elnino = (oni_w >= 1.0).fillna(False)

AMP = {
    "inondation (GDACS, 8 sem.)": lambda c: recent_event(c, ["FL"], ["Green", "Orange", "Red"]),
    "inondation grave (orange/rouge)": lambda c: recent_event(c, ["FL"], ["Orange", "Red"]),
    "cyclone orange/rouge": lambda c: recent_event(c, ["TC"], ["Orange", "Red"]),
    "sécheresse active": active_drought,
    "pic de conflits (z>=1)": conflict_spike,
    "El Niño (ONI>=0.5)": lambda c: elnino,
    "El Niño fort (ONI>=1)": lambda c: strong_elnino,
}


def evaluate(fn):
    onsets = hits = eps_n = fa = qw = fol = 0; leads = []
    for c, nbs in NB.items():
        nbs = [n for n in nbs if n in p]
        if c not in p or not nbs:
            continue
        on = list(W[(p[c] > 0) & quiet[c]]); al = list(W[fn(c, nbs) & quiet[c]])
        for o in on:
            prev = [a for a in al if 7 <= (o - a).days <= 70]; onsets += 1
            if prev:
                hits += 1; leads.append((o - min(prev)).days)
        eps = []
        for a in al:
            if not eps or (a - eps[-1][-1]).days > 28:
                eps.append([a])
            else:
                eps[-1].append(a)
        eps_n += len(eps); fa += sum(1 for e in eps if not any(0 <= (o - e[0]).days <= 70 for o in on))
        for t in W[quiet[c]]:
            qw += 1; fol += any(0 <= (o - t).days <= 70 for o in on)
    return {"sensitivity": round(hits / onsets, 2), "hits": hits, "onsets": onsets, "alert_episodes": eps_n,
            "ppv": round((eps_n - fa) / eps_n, 2) if eps_n else None, "base_rate": round(fol / qw, 2),
            "median_lead_days": int(np.median(leads)) if leads else None}


watch = lambda c, nbs: surge[nbs].any(axis=1)
res = [{"rule": "VIGILANCE seule (1 voisin)", **evaluate(watch)},
       {"rule": "ALERTE (2 voisins)", **evaluate(lambda c, nbs: surge[nbs].sum(axis=1) >= 2)}]
for name, f in AMP.items():
    res.append({"rule": f"{name} seul", **evaluate(lambda c, nbs, f=f: f(c))})
    res.append({"rule": f"VIGILANCE + {name}", **evaluate(lambda c, nbs, f=f: watch(c, nbs) & f(c))})
any_amp = lambda c: recent_event(c, ["FL"], ["Orange", "Red"]) | recent_event(c, ["TC"], ["Orange", "Red"]) | conflict_spike(c) | strong_elnino
res.append({"rule": "VIGILANCE + un amplificateur grave (inondation/cyclone grave, pic de conflits, El Niño fort)", **evaluate(lambda c, nbs: watch(c, nbs) & any_amp(c))})
if __name__ == "__main__":
  json.dump(res, open("out/amplifier_eval.json", "w"), indent=1, ensure_ascii=False)
for r in ([] if __name__ != "__main__" else res):
    print(f"{r['rule'][:70]:70s} sens={r['sensitivity']:.2f} ({r['hits']}/{r['onsets']}) episodes={r['alert_episodes']:3d} ppv={r['ppv']} base={r['base_rate']} lead={r['median_lead_days']}")
print("ONI last:", oni.index[-1].date(), oni.iloc[-1])

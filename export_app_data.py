"""Export weekly per-country status for the interactive app -> out/app_data.json"""
import json, contextlib, io, pandas as pd
res = json.load(open("out/amplifier_eval.json"))
with contextlib.redirect_stdout(io.StringIO()):
    from amplifier_eval import NB, p, W, surge, quiet, active_drought, conflict_spike, elnino, oni, recent_event
EAST = {"KEN", "SOM", "ETH", "UGA", "TZA", "SSD", "SDN", "RWA", "BDI"}
names = dict(pd.read_csv("data/who_week_all.csv").groupby("iso_3_code")["adm0_viz_n"].first())
weeks = [w for w in W if w >= pd.Timestamp("2023-03-01")]
countries = sorted(set(NB) | {n for v in NB.values() for n in v} & set(p.columns))
dr = {c: active_drought(c) for c in NB}; cs = {c: conflict_spike(c) for c in NB}
fl = {c: recent_event(c, ["FL"], ["Green", "Orange", "Red"]) for c in NB}
onsets = {c: [str(t.date()) for t in W[(p[c] > 0) & quiet[c]]] for c in NB if c in p}
weekly = []
for w in weeks:
    win = W[(W > w - pd.Timedelta(days=28)) & (W <= w)]
    row = {}
    for c in countries:
        cases = int(p[c].loc[w]) if c in p else 0
        rec = {"n": cases}
        if c in NB and c in p:
            nbs = [n for n in NB[c] if n in p]
            hot = [n for n in nbs if surge[n].loc[win].any()]
            sig = {"nb": hot, "dr": bool(dr[c].loc[w]), "cf": bool(cs[c].loc[w]), "en": bool(c in EAST and elnino.loc[w]), "fl": bool(fl[c].loc[w])}
            k = int(bool(hot)) + sig["dr"] + sig["cf"] + sig["en"]
            active = (not quiet[c].loc[win].any()) and p[c].loc[win].sum() > 0
            rec["l"] = "active" if active else ("warning" if k >= 2 or len(hot) >= 2 else ("watch" if k == 1 else "none"))
            rec["s"] = sig
        row[c] = rec
    weekly.append({"w": str(w.date()), "oni": round(float(oni.shift(1).reindex([w], method="ffill").iloc[0]), 2), "c": row})
out = {"countries": {c: names.get(c, c) for c in countries}, "monitored": list(NB), "neighbours": NB, "onsets": onsets,
       "weeks": weekly, "metrics": res, "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
json.dump(out, open("out/app_data.json", "w"), separators=(",", ":"))
print(len(weekly), "weeks", len(countries), "countries", round(len(json.dumps(out)) / 1e6, 2), "MB; last levels:",
      {c: v.get("l") for c, v in weekly[-1]["c"].items() if v.get("l") not in (None, "none")})

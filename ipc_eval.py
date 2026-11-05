"""Food insecurity amplifier: share of population in IPC phase 3+ (current analysis, national), HDX HAPI.
Signal = latest published share (as of that week) >= 20 %. Evaluated with the same protocol as amplifier_eval.py."""
import requests, pandas as pd, json, os, contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    from amplifier_eval import NB, W, evaluate, watch, active_drought, conflict_spike, elnino
f = "data/ipc_national.csv"
if not os.path.exists(f):
    app = dict(l.strip().split("=", 1) for l in open(".env") if "=" in l)["HAPI_APP_IDENTIFIER"]
    rows = []
    for c in NB:
        r = requests.get("https://hapi.humdata.org/api/v2/food-security-nutrition-poverty/food-security", timeout=90, params={
            "location_code": c, "admin_level": 0, "ipc_type": "current", "output_format": "json", "limit": 5000,
            "app_identifier": app}).json()["data"]
        rows += [{"iso3": c, "phase": x["ipc_phase"], "frac": x["population_fraction_in_phase"],
                  "start": x["reference_period_start"][:10], "end": x["reference_period_end"][:10]} for x in r]
    pd.DataFrame(rows).to_csv(f, index=False)
ipc = pd.read_csv(f, parse_dates=["start", "end"])
p3 = ipc[ipc.phase.isin(["3+"])]
if p3.empty:
    p3 = ipc[ipc.phase.isin(["3", "4", "5"])].groupby(["iso3", "start", "end"], as_index=False)["frac"].sum()
EAST = {"KEN", "SOM", "ETH", "UGA", "TZA", "SSD", "SDN", "RWA", "BDI"}


def food_crisis(c, thr=0.2):
    d = p3[p3.iso3 == c].sort_values("end")
    s = pd.Series(float("nan"), index=W)
    for _, r in d.iterrows():
        s[W >= r["end"]] = r["frac"]  # usable only after the analysis period ends (publication lag ignored: optimistic)
    return (s >= thr).fillna(False)


fc = {c: food_crisis(c) for c in NB}
nino_e = lambda c: elnino if c in EAST else pd.Series(False, index=W)
dr = {c: active_drought(c) for c in NB}; cs = {c: conflict_spike(c) for c in NB}
score = lambda c, nbs, food=False: (watch(c, nbs).astype(int) + dr[c].astype(int) + cs[c].astype(int) + nino_e(c).astype(int)
                                    + (fc[c].astype(int) if food else 0))
res = [{"rule": "insécurité alimentaire IPC 3+ >= 20 % seule", **evaluate(lambda c, nbs: fc[c])},
       {"rule": "Score >= 1 avec IPC", **evaluate(lambda c, nbs: score(c, nbs, True) >= 1)},
       {"rule": "Score >= 2 avec IPC", **evaluate(lambda c, nbs: score(c, nbs, True) >= 2)},
       {"rule": "Score >= 2 sans IPC", **evaluate(lambda c, nbs: score(c, nbs) >= 2)}]
allr = json.load(open("out/amplifier_eval.json"))
allr = [r for r in allr if r["rule"] not in {x["rule"] for x in res}] + res
json.dump(allr, open("out/amplifier_eval.json", "w"), indent=1, ensure_ascii=False)
print("countries with IPC data:", p3.iso3.nunique())
for r in res:
    print(f"{r['rule']:45s} sens={r['sensitivity']:.2f} ({r['hits']}/{r['onsets']}) ep={r['alert_episodes']} ppv={r['ppv']} base={r['base_rate']} lead={r['median_lead_days']}")

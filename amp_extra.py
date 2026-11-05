import contextlib, io, json
with contextlib.redirect_stdout(io.StringIO()):
    from amplifier_eval import *
EAST = {"KEN","SOM","ETH","UGA","TZA","SSD","SDN","RWA","BDI"}
nino_region = lambda c: elnino if c in EAST else pd.Series(False, index=W)
dr = {}; cs = {}
def sig(c, nbs):
    for d, f in ((dr, active_drought), (cs, conflict_spike)):
        if c not in d: d[c] = f(c)
    return [watch(c, nbs).astype(int), dr[c].astype(int), cs[c].astype(int), nino_region(c).astype(int)]
extra = [{"rule": "El Niño, Afrique de l'Est seulement", **evaluate(lambda c, nbs: nino_region(c))},
         {"rule": "Score >= 2 signaux (voisin, sécheresse, conflits, El Niño Est)", **evaluate(lambda c, nbs: sum(sig(c, nbs)) >= 2)},
         {"rule": "Score >= 1 signal", **evaluate(lambda c, nbs: sum(sig(c, nbs)) >= 1)},
         {"rule": "VIGILANCE ou sécheresse", **evaluate(lambda c, nbs: watch(c, nbs) | dr.setdefault(c, active_drought(c)))}]
allr = json.load(open("out/amplifier_eval.json")) + extra
json.dump(allr, open("out/amplifier_eval.json", "w"), indent=1, ensure_ascii=False)
for r in extra: print(f"{r['rule'][:62]:62s} sens={r['sensitivity']:.2f} ({r['hits']}/{r['onsets']}) ep={r['alert_episodes']} ppv={r['ppv']} base={r['base_rate']} lead={r['median_lead_days']}")

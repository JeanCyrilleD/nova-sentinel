"""Risk amplifiers: GDACS floods/cyclones/droughts, NOAA ONI (El Nino), HDX HAPI conflict events (national, monthly).
Usage: python3 ingest/amplifiers.py [gdacs|oni|conflict]   (idempotent, cached in data/)"""
import requests, pandas as pd, os, sys, time, contextlib, io
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, BASE)
with contextlib.redirect_stdout(io.StringIO()):
    from backtest_crossborder_africa import NB
D = lambda f: os.path.join(BASE, "data", f)


def gdacs():
    rows, t0 = [], time.time()
    months = pd.date_range("2022-06-01", "2026-11-01", freq="MS")
    done = pd.read_csv(D("gdacs_events.csv")) if os.path.exists(D("gdacs_events.csv")) else pd.DataFrame(columns=["month"])
    have = set(done["month"].astype(str))
    for m in months:
        if str(m.date()) in have:
            continue
        if time.time() - t0 > 120:
            break
        e = (m + pd.offsets.MonthEnd(0)).date()
        page, got = 1, False
        while True:
            r = requests.get("https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH", timeout=60, params={
                "eventlist": "FL;TC;DR", "fromDate": str(m.date()), "toDate": str(e),
                "alertlevel": "Green;Orange;Red", "pageNumber": page})
            f = r.json().get("features", []) if r.status_code == 200 and r.text.strip() else []
            for x in f:
                pr = x["properties"]
                for ac in pr.get("affectedcountries") or [{"iso3": pr.get("iso3")}]:
                    rows.append({"month": str(m.date()), "iso3": ac.get("iso3"), "type": pr["eventtype"],
                                 "level": pr["alertlevel"], "from": pr["fromdate"][:10], "to": pr["todate"][:10],
                                 "id": pr["eventid"]})
                    got = True
            if len(f) < 100:
                break
            page += 1
        if not got:
            rows.append({"month": str(m.date()), "iso3": None})
    out = pd.concat([done, pd.DataFrame(rows)]) if rows else done
    out.to_csv(D("gdacs_events.csv"), index=False)
    print("gdacs months:", out["month"].nunique(), "/", len(months))


def oni():
    t = requests.get("https://psl.noaa.gov/data/correlation/oni.data", timeout=60).text.splitlines()
    rec = []
    for l in t[1:]:
        p = l.split()
        if len(p) == 13 and p[0].isdigit():
            for i, v in enumerate(p[1:], 1):
                if float(v) > -90:
                    rec.append({"month": f"{p[0]}-{i:02d}-01", "oni": float(v)})
    pd.DataFrame(rec).to_csv(D("oni.csv"), index=False)
    print("oni", rec[-1])


def conflict():
    app = dict(l.strip().split("=", 1) for l in open(os.path.join(BASE, ".env")) if "=" in l)["HAPI_APP_IDENTIFIER"]
    f = D("conflict_national.csv")
    done = pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=["iso3"])
    rows, t0 = [], time.time()
    for c in NB:
        if c in set(done["iso3"]):
            continue
        if time.time() - t0 > 120:
            break
        r = requests.get("https://hapi.humdata.org/api/v2/coordination-context/conflict-events", timeout=90, params={
            "location_code": c, "admin_level": 0, "start_date": "2021-01-01", "output_format": "json",
            "limit": 10000, "app_identifier": app}).json()["data"]
        rows += [{"iso3": c, "month": x["reference_period_start"][:10], "type": x["event_type"],
                  "events": x["events"], "fatalities": x["fatalities"]} for x in r]
        if not r:
            rows.append({"iso3": c})
    out = pd.concat([done, pd.DataFrame(rows)])
    out.to_csv(f, index=False)
    print("conflict countries:", out["iso3"].nunique(), "/", len(NB))


{"gdacs": gdacs, "oni": oni, "conflict": conflict}[sys.argv[1]]()

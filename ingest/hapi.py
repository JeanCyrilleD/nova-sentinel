"""HDX HAPI ingest (aggregated, admin-level only) -> data/hapi_<theme>_<ISO3>.csv. Needs HAPI_APP_IDENTIFIER in .env."""
import os, sys, requests, csv
BASE = os.path.join(os.path.dirname(__file__), "..")
APP = dict(l.strip().split("=", 1) for l in open(os.path.join(BASE, ".env")) if "=" in l)["HAPI_APP_IDENTIFIER"]
THEMES = {"idps": "affected-people/idps", "conflict": "coordination-context/conflict-events",
          "refugees": "affected-people/refugees-persons-of-concern"}
def pull(theme, iso3):
    rows, off = [], 0
    key = "asylum_location_code" if theme == "refugees" else "location_code"
    while True:
        r = requests.get(f"https://hapi.humdata.org/api/v2/{THEMES[theme]}", timeout=90, params={
            key: iso3, "output_format": "json", "limit": 1000, "offset": off, "app_identifier": APP})
        r.raise_for_status(); d = r.json()["data"]; rows += d
        if len(d) < 1000: break
        off += 1000
    if rows:
        with open(os.path.join(BASE, "data", f"hapi_{theme}_{iso3}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return len(rows)
if __name__ == "__main__":
    for iso in sys.argv[1:] or ["TCD", "MRT", "SEN"]:
        for t in THEMES: print(iso, t, pull(t, iso))

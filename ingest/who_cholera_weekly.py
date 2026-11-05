"""WHO global cholera dashboard, weekly cases by country (public ArcGIS feature service) -> data/who_cholera_weekly.csv"""
import requests, pandas as pd, os
URL = "https://services.arcgis.com/5T5nSi527N4F7luB/arcgis/rest/services/cholera_adm0_week_view/FeatureServer/0/query"
ISO = ["SDN", "TCD", "SSD", "CAF", "CMR", "NGA", "NER", "ETH", "SOM", "MLI", "BFA"]
rows, off = [], 0
while True:
    r = requests.get(URL, timeout=120, params={"where": "iso_3_code in (%s)" % ",".join(f"'{i}'" for i in ISO),
        "outFields": "iso_3_code,date_wk,cases,deaths", "orderByFields": "ObjectId", "resultOffset": off,
        "resultRecordCount": 2000, "f": "json"}).json()
    f = r.get("features", []); rows += [x["attributes"] for x in f]
    if not r.get("exceededTransferLimit") and len(f) < 2000: break
    off += len(f)
d = pd.DataFrame(rows); d["date_wk"] = pd.to_datetime(d["date_wk"], unit="ms")
d.sort_values(["iso_3_code", "date_wk"]).to_csv(os.path.join(os.path.dirname(__file__), "..", "data", "who_cholera_weekly.csv"), index=False)
print(d.groupby("iso_3_code").agg(first=("date_wk", "min"), last=("date_wk", "max"), weeks=("cases", "size"), cases=("cases", "sum")))

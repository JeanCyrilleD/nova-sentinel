"""WHO Disease Outbreak News -> data/who_don.csv (public API, no key)."""
import csv, requests, re, html, sys, os
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "who_don.csv")
url = "https://www.who.int/api/news/diseaseoutbreaknews"
rows, skip = [], 0
while True:
    r = requests.get(url, params={"$top": 100, "$skip": skip, "$orderby": "PublicationDate desc",
                                  "$select": "Title,PublicationDate,UrlName"}, timeout=60)
    r.raise_for_status(); v = r.json().get("value", [])
    if not v: break
    for it in v:
        rows.append({"date": it["PublicationDate"][:10], "title": html.unescape(it["Title"]),
                     "url": "https://www.who.int/emergencies/disease-outbreak-news/item/" + it["UrlName"]})
    skip += 100
    if skip > 2000: break
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["date", "title", "url"]); w.writeheader(); w.writerows(rows)
print(len(rows), "items; latest", rows[0]["date"] if rows else None)

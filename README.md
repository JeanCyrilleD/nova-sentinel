# Nova Sentinel

Explainable cholera early warning from cross-border, climate and crisis signals.
Future Health Digital Innovation Challenge · Population Health · Challenge 06 "Population and Workforce Health Early Warning".

- **Live console (no install, no login):** https://jeancyrilled.github.io/nova-sentinel/ — opens on this week's alerts; the same file is [`index.html`](index.html).
- **Demo video, live console (1 min 29 s):** [`video/nova_sentinel_demo_live.mp4`](video/nova_sentinel_demo_live.mp4) — a live alert with its evidence, the officer's decision, the per-country signal view and a back-test replay.
- **Technical documentation:** [`DOCS.md`](DOCS.md) (problem, architecture, validation, assumptions, limitations, responsible AI, path to pilot).
- **Narrated walkthrough (first version):** [`video/nova_sentinel_demo.mp4`](video/nova_sentinel_demo.mp4) (2 min 15 s, narrated).
- **Solution deck:** [`docs/NovaSentinel_solution_deck.pdf`](docs/NovaSentinel_solution_deck.pdf).

## What the console shows (updated 19 November 2026, after the review)
- **Which signals fired, country by country:** one row per monitored country for the selected week — neighbour surging, drought, conflict spike, El Niño (East Africa), flood as context — with the alert level, its confidence, the data status and whether an officer has reviewed it.
- **How confident each alert is:** High / Moderate / Low, taken from how often alerts built on the same signals were followed by an outbreak in the 2023–2026 back-test, compared with chance. Lowered one step when the country's own reporting is incomplete.
- **Why it fired, in plain words,** with the rule that fired and an evidence table: signal, place, weeks and case counts.
- **The officer decides:** accept, dismiss or comment on each alert; every decision is time-stamped in a decision log that can be exported as CSV. (In this public demo the log is kept in the visitor's browser; a ministry deployment writes it to its own alert register.)
- **Delayed or missing data is said, not hidden:** a banner gives the date of the latest data from each source and how old it is; weeks a country did not report to WHO appear as "n/r" (not reported), never as zero, and the brief warns when recent weeks are missing.

To rebuild the console after a data refresh: `PYTHONPATH=. python3 export_app_data.py && python3 app/build_app.py`.

## Run it
```bash
pip install pandas requests
echo "HAPI_APP_IDENTIFIER=<base64 of app_name:email>" > .env   # free HDX HAPI identifier
python3 ingest/who_cholera_weekly.py        # WHO weekly cholera cases (2026 feed)
# full 2023-2026 series: WHO global cholera dashboard CSV (cholera_adm0_week) -> data/who_week_all.csv
python3 backtest_crossborder_africa.py      # surge rule, 26 countries
python3 ingest/amplifiers.py oni && python3 ingest/amplifiers.py gdacs && python3 ingest/amplifiers.py conflict
PYTHONPATH=. python3 amplifier_eval.py && PYTHONPATH=. python3 amp_extra.py && PYTHONPATH=. python3 ipc_eval.py
PYTHONPATH=. python3 export_app_data.py     # -> out/app_data.json, injected into app/template.html
```

## Results (back-test, Jan 2023 – Oct 2026, 39 outbreak onsets, 26 countries)
| Rule | Onsets caught | Alerts followed by an outbreak (chance 20 %) | Median lead |
|---|---|---|---|
| WATCH · any one signal | 79 % | 23 % | 70 days |
| WARNING · 2+ neighbours surging | 10 % | 44 % | 28 days |
| Active drought | 38 % | 39 % | 63 days |
| El Niño · East Africa | 15 % | 45 % | 24 days |

Negative results are kept in `DOCS.md`. Data: WHO, GDACS, NOAA, HDX HAPI, Open-Meteo (public, aggregated, country level). No personal data.

License: Apache License 2.0. Copyright 2026 Ahadi Jean Cyrille Dahani.

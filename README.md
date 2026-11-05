# Nova Sentinel

Explainable cholera early warning from cross-border, climate and crisis signals.
Future Health Digital Innovation Challenge · Population Health · Challenge 06 "Population and Workforce Health Early Warning".

- **Interactive prototype:** [`index.html`](index.html) — download and open in any browser, no login (weekly map replay 2023–2026, explained alerts, proportionate actions, measured reliability).
- **Technical documentation:** [`DOCS.md`](DOCS.md) (problem, architecture, validation, assumptions, limitations, responsible AI, path to pilot).
- **Demo video:** [`video/nova_sentinel_demo.mp4`](video/nova_sentinel_demo.mp4) (2 min 15 s, narrated).
- **Solution deck:** [`docs/NovaSentinel_solution_deck.pdf`](docs/NovaSentinel_solution_deck.pdf).

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

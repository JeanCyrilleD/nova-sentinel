# Nova Sentinel — Technical documentation

Future Health Digital Innovation Challenge · Population Health · Challenge 06 "Population and Workforce Health Early Warning"

## 1. Problem
Cholera outbreaks in fragile, climate-exposed and conflict-affected countries are usually detected after local transmission is established. Preparedness actions that save lives (oral rehydration stocks, rapid tests, WASH kits, reactive vaccination planning, case-definition refreshers at border health facilities) need weeks of lead time. Signals that could give this lead time exist, but they sit in separate public datasets and are reviewed separately.

## 2. What Nova Sentinel does
Every week, Nova Sentinel:
1. ingests public, aggregated signals: WHO weekly cholera cases by country, WHO Disease Outbreak News, rainfall (Open-Meteo ERA5), displacement and conflict context (HDX HAPI);
2. detects **surges** in each country: cases over the last 2 weeks ≥ 50 and ≥ 3× the previous 6-week mean;
3. raises a tiered, explainable alert for each **quiet neighbour** (no cases for ≥ 8 weeks):
   - **WATCH**: one neighbour surging;
   - **WARNING**: two or more neighbours surging;
4. explains each alert (which neighbour, how many cases, which weeks) and proposes a **proportionate preventive action** and the **responsible role** (national epidemiological surveillance, WASH cluster);
5. leaves the decision to a human: the system prepares, an authorised person decides.

## 3. Architecture
```
ingest/who_cholera_weekly.py   WHO global cholera dashboard (public ArcGIS feature service)
ingest/who_don.py              WHO Disease Outbreak News API
ingest/rain_centroids.py       Open-Meteo ERA5 daily rainfall, country centroids, 2012–2026
ingest/hapi.py                 HDX HAPI (refugees, IDPs, conflict events; admin-level aggregates)
backtest_crossborder_africa.py surge + alert rules, back-test on 26 African countries
fusion_eval.py                 compares signal combinations against the base rate
dashboard.py                   weekly alerts, explanations, actions, reliability metrics -> out/dashboard.html
run_all.py                     end-to-end refresh
```
Python 3, pandas, requests. No model training: transparent rules, so every alert can be explained and audited. Runs on a laptop in under 3 minutes.

## 4. Validation (back-test, January 2023 – October 2026, 26 African countries)
An **onset** is the first week with reported cases after ≥ 8 weeks with none. A hit is an onset preceded by an alert 1–10 weeks earlier. A false alarm is an alert episode not followed by an onset within 10 weeks. The base rate is the share of quiet weeks followed by an onset within 10 weeks.

| Rule | Onsets detected | Alert episodes | Alerts followed by an onset (PPV) | Base rate | Median lead time |
|---|---|---|---|---|---|
| WATCH: ≥1 neighbour surging | 19 / 39 (49 %) | 75 | 25 % | 20 % | 56 days |
| WATCH + wet season | 15 / 39 (38 %) | 57 | 25 % | 20 % | 49 days |
| WARNING: ≥2 neighbours surging | 4 / 39 (10 %) | 9 | 44 % | 20 % | 28 days |

Case studies:
- **Chad 2026** (first cases week of 8 June): Sudan surge on 11 May, 4 weeks ahead; Nigeria surge from 30 March.
- **Chad 2025** (first confirmed case 13 July, Dougui camp): WATCH from a Nigeria surge 28 days before.

Negative results, kept on purpose:
- Rainfall alone did not anticipate Rift Valley fever in Mauritania/Senegal 2025 and fired in several outbreak-free years.
- Rainfall plus conflict events did not anticipate cholera in Ouaddaï (Chad) 2025 and fired in 5 of 10 outbreak-free seasons.
- Adding a wet-season filter to the cross-border rule lowers detection without improving precision. Rainfall is therefore shown as context, not used as a trigger.

## 5. Assumptions
- WHO weekly national counts are a usable proxy for transmission, despite reporting delays and under-reporting.
- Cross-border spread (trade, displacement, pastoral movement) is a leading driver of new outbreaks in quiet neighbours.
- A 1–10 week window is long enough to change preparedness and short enough to stay relevant.

## 6. Limitations
- National level only: no sub-national location, so alerts cannot yet say which district to prioritise.
- Only about 4 years of weekly history: 39 onsets, so metrics have wide uncertainty.
- The WATCH tier has low precision (25 % vs 20 % by chance): it is a prompt to check readiness, not a prediction. The WARNING tier is more precise (44 %) but rare.
- Reporting differences between countries (testing, delays, political sensitivity) affect both onsets and surges.
- Neighbour lists are hand-coded; sea, river and road connectivity are not yet weighted.

## 7. Responsible AI, safety and data governance
- Only public, aggregated data at country level; no personal or individual health data.
- Displacement and conflict data come from HDX HAPI aggregates; ACLED-derived data is used only through HAPI aggregates, in line with its licence.
- Small-cell suppression applies to any future sub-national view (no unit below 5 cases displayed).
- Every alert shows its evidence and its rule; no black-box score.
- Human in the loop: the system proposes, a mandated public-health officer decides. No automatic public communication.
- Explicit statement of uncertainty and false-alarm rates on the dashboard to limit alert fatigue.

## 8. Scalability and path to pilot
- Already runs on 26 countries with no country-specific tuning; adding a country is a data-source mapping.
- Next: sub-national data (WHO AFRO bulletins, ministry sitreps), weighting by mobility corridors and refugee flows, and an animal-health signal for zoonoses (Rift Valley fever).
- Pilot path: weekly bulletin for a regional surveillance team or a health cluster, compared with their current event-based surveillance over one rainy season.

## 9. Data sources
- WHO Global Cholera and AWD dashboard (weekly cases by country).
- WHO Disease Outbreak News API.
- Open-Meteo historical weather API (ERA5).
- HDX Humanitarian API (HAPI): refugees, IDPs, conflict events (aggregated).
- ReliefWeb (Chad 2025 cholera reference: first confirmed case 13 July 2025).

## 10. Risk amplifiers: climate, disasters and crises (added 5 Nov 2026)
Sources: GDACS (UN/EC Global Disaster Alert and Coordination System) floods, tropical cyclones and droughts; NOAA Oceanic Niño Index (ONI, previous month only, as available in real time); HDX HAPI national monthly conflict events (previous month only). Same back-test protocol as section 4.

| Signal | Onsets detected | Alert episodes | PPV (base 20 %) | Median lead | Decision |
|---|---|---|---|---|---|
| Active drought (GDACS) | 38 % | 28 | 39 % | 63 days | kept |
| Conflict spike (monthly z ≥ 1) | 21 % | 30 | 30 % | 52 days | kept |
| El Niño (ONI ≥ 0.5), East Africa only | 15 % | 11 | 45 % | 24 days | kept, regional |
| El Niño, all countries | 28 % | 30 | 33 % | 21 days | replaced by regional rule |
| Floods, any GDACS level, 8 weeks | 36 % | 50 | 20 % | 70 days | context only (no better than chance) |
| Severe floods / cyclones (orange/red) | 0 % | 5 / 0 | – | – | too rare in 2023–2026 to evaluate |
| Any 1 signal (WATCH) | 79 % | 82 | 23 % | 70 days | WATCH tier |
| 2+ signals (WARNING) | 26 % | 40 | 30 % | 35 days | WARNING tier, with "2+ neighbours surging" |

Final tiers: WATCH = one signal among neighbour surge, active drought, conflict spike, El Niño (East Africa); WARNING = two or more signals, or two or more neighbours surging. Floods are displayed as context.
Caveats: 39 onsets only, several signals were tested, so some apparent gains may be chance (multiple-comparison risk); national resolution blurs local floods; El Niño effects are region- and season-specific and the regional rule is a first approximation.
Current status (ONI Sept 2026 = +2.46, strong El Niño): seasonal warning for East Africa for the October–December short rains.
- Food insecurity (IPC phase 3+ ≥ 20 % of population, HDX HAPI, 23 countries): alone 36 % of onsets detected but PPV 22 % (chance level); adding it to the score raises detection (WATCH 85 %) but lowers precision (WARNING PPV 25 % vs 30 % without it). Decision: shown as vulnerability context, not used as a trigger.
- Sub-national resolution: no public weekly sub-national cholera series covers these 26 countries; WHO AFRO bulletins and ministry sitreps are PDFs. Planned for the pilot phase with a partner surveillance team.

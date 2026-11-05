import pandas as pd, requests, os, time, contextlib, io, sys
d = pd.read_csv('data/who_week_all.csv'); cent = d.groupby('iso_3_code')[['center_lat','center_lon']].first()
with contextlib.redirect_stdout(io.StringIO()):
    from backtest_crossborder_africa import NB
t0 = time.time()
for c in NB:
    f = f'data/rain/{c}.csv'
    if os.path.exists(f) or c not in cent.index: continue
    if time.time() - t0 > 140: break
    la, lo = cent.loc[c]
    j = requests.get('https://archive-api.open-meteo.com/v1/archive', timeout=60, params={'latitude': round(la,2), 'longitude': round(lo,2),
        'start_date': '2012-01-01', 'end_date': '2026-10-25', 'daily': 'precipitation_sum', 'timezone': 'UTC'}).json()
    if 'daily' not in j: print('ERR', c, j); break
    pd.Series(j['daily']['precipitation_sum'], index=pd.to_datetime(j['daily']['time']), name=c).to_csv(f)
print(len(os.listdir('data/rain')), 'of', len(NB))

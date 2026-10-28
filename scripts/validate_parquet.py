"""Compara una salida LOCAL de Spark con el oráculo original; no produce datos para EMR."""
import argparse
from pathlib import Path
import pandas as pd
from airline_data.oracle import load_truth, METRIC_COLUMNS, CURATED_COLUMNS
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--rows',type=int,required=True)
p.add_argument('--detail',required=True);p.add_argument('--metrics',required=True)
a=p.parse_args();truth=load_truth(a.seed,a.rows)
def read_tree(path):
    files=sorted(Path(path).rglob('*.parquet'))
    if not files:raise SystemExit(f'No hay Parquet en {path}')
    frames=[]
    for f in files:
        df=pd.read_parquet(f)
        for part in f.parts:
            if part.startswith('month='):df['month']=part.split('=',1)[1]
        frames.append(df)
    return pd.concat(frames,ignore_index=True)
got=read_tree(a.detail); expected=truth.detail.copy()
for col in ['reservation_id','flight_id']:
    got[col]=got[col].astype(str); expected[col]=expected[col].astype(str)
cols=CURATED_COLUMNS+['month']
got=got[cols].sort_values('reservation_id').reset_index(drop=True)
expected=expected[cols].sort_values('reservation_id').reset_index(drop=True)
pd.testing.assert_frame_equal(got,expected,check_dtype=False)
m=read_tree(a.metrics)[METRIC_COLUMNS].sort_values(['route','month']).reset_index(drop=True)
t=truth.metrics.sort_values(['route','month']).reset_index(drop=True)
# Discrepancia explícita: el enunciado dice CONFIRMED, oracle.py cuenta todas en bookings.
assert (m['bookings']==m['seats_sold']).all(), 'bookings no sigue el enunciado'
compare=[x for x in METRIC_COLUMNS if x!='bookings']
pd.testing.assert_frame_equal(m[compare],t[compare],check_dtype=False,rtol=1e-10,atol=1e-10)
print({'detail_rows':len(got),'months':got.month.nunique(),'metrics_rows':len(m),'comparacion':'OK salvo discrepancia documental bookings'})
print('bookings: salida=CONFIRMED; oracle=CONFIRMED+CANCELLED. Solicitar aclaración al docente.')

import argparse, json, re
from pathlib import Path
from string import Template
p=argparse.ArgumentParser()
p.add_argument('--settings', default='aws-settings.json')
p.add_argument('--out', default='catalog.sql')
a=p.parse_args()
s=json.loads(Path(a.settings).read_text())
assert re.fullmatch(r'[a-z][a-z0-9_]*',s['database']), 'Database inválida'
assert re.fullmatch(r'[a-z0-9][a-z0-9.-]+[a-z0-9]',s['bucket']), 'Bucket inválido'
assert re.fullmatch(r'[a-zA-Z0-9_/-]+',s['data_prefix']), 'Prefijo inválido'
base=Path(__file__).resolve().parents[1]
text=Template((base/'sql/catalog.sql.template').read_text()).substitute(DATABASE=s['database'],BUCKET=s['bucket'],DATA_PREFIX=s['data_prefix'])
Path(a.out).write_text(text,encoding='utf-8')
print(f'SQL escrito en {a.out}; no se ha enviado a AWS')

import math, sys
from pathlib import Path
import yaml
path=Path(sys.argv[1] if len(sys.argv)>1 else 'cost_projection.yaml')
d=yaml.safe_load(path.read_text())
assert d.get('assumptions') and 'PENDIENTE' not in d['assumptions'], 'Completar supuestos'
items=d.get('line_items',[])
assert items, 'No hay partidas'
for item in items:
    amount=item.get('monthly_usd')
    assert isinstance(amount,(float,int)) and not isinstance(amount,bool) and math.isfinite(amount) and amount>=0, f'Importe inválido: {item}'
total=sum(x['monthly_usd'] for x in items)
assert total<=50, f'Supera el límite del archivo entregado: {total:.2f} USD'
assert 'total' not in d, 'No escribir un campo total'
print(f'Suma: {total:.2f} USD. Solo validación formal; comparar con inventario, tarifas y evaluador.')

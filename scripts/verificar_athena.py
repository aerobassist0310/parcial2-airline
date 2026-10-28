"""Comprueba R4-R7 contra el oráculo usando Athena, Glue y el endpoint (versión previa al harness).

Ejecutar desde la raíz del repositorio con credenciales de AWS (en la EC2, el perfil de instancia):
    python -m scripts.verificar_athena --prefix full --rows 2000000
    python -m scripts.verificar_athena --prefix full --rows 2000000 --recrear-tablas

--recrear-tablas vuelve a crear las tablas de Glue apuntando a s3://BUCKET/PREFIX/ (DROP TABLE solo
borra la definición en el catálogo, nunca los Parquet de S3).
"""
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import boto3

from airline_data.oracle import CURATED_COLUMNS, METRIC_COLUMNS, load_truth

p = argparse.ArgumentParser()
p.add_argument("--bucket", default="p2-airline-salvatore-20261027")
p.add_argument("--prefix", default="full")
p.add_argument("--db", default="airline_analytics")
p.add_argument("--seed", type=int, default=12345)
p.add_argument("--rows", type=int, default=2000000)
p.add_argument("--api", default="http://127.0.0.1:8000")
p.add_argument("--recrear-tablas", action="store_true")
a = p.parse_args()

athena = boto3.client("athena", region_name="us-east-1")
glue = boto3.client("glue", region_name="us-east-1")
s3 = boto3.client("s3", region_name="us-east-1")


def q(sql, db=a.db):
    kw = dict(QueryString=sql, WorkGroup="primary",
              ResultConfiguration={"OutputLocation": f"s3://{a.bucket}/athena-results/"})
    if db:
        kw["QueryExecutionContext"] = {"Database": db}
    qid = athena.start_query_execution(**kw)["QueryExecutionId"]
    while True:
        qe = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        estado = qe["Status"]["State"]
        if estado in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)
    if estado != "SUCCEEDED":
        raise SystemExit(f"FALLO EN ATHENA:\n{sql}\n{qe['Status'].get('StateChangeReason')}")
    filas = athena.get_query_results(QueryExecutionId=qid)["ResultSet"]["Rows"]
    return [[c.get("VarCharValue") for c in f["Data"]] for f in filas], qe["Statistics"].get("DataScannedInBytes", 0)


def ok(condicion, mensaje):
    print(("OK     " if condicion else "FALLA  ") + mensaje)


base = f"s3://{a.bucket}/{a.prefix}"
if a.recrear_tablas:
    q(f"CREATE DATABASE IF NOT EXISTS {a.db}", db=None)
    q("DROP TABLE IF EXISTS reservations_curated")
    q("DROP TABLE IF EXISTS route_month_metrics")
    q(f"""CREATE EXTERNAL TABLE reservations_curated (
 reservation_id string, flight_id string, route string, fare_class string,
 price_cents bigint, status string)
PARTITIONED BY (month string)
STORED AS PARQUET
LOCATION '{base}/curated/reservations_curated/'
TBLPROPERTIES ('classification'='parquet')""")
    q("MSCK REPAIR TABLE reservations_curated")
    q(f"""CREATE EXTERNAL TABLE route_month_metrics (
 route string, month string, seats_capacity bigint, seats_sold bigint,
 occupancy double, revenue_cents bigint, bookings bigint, cancellations bigint)
STORED AS PARQUET
LOCATION '{base}/metrics/route_month_metrics/'
TBLPROPERTIES ('classification'='parquet')""")
    print("TABLAS CREADAS EN GLUE, APUNTANDO A", base, "\n")

truth = load_truth(a.seed, a.rows)
meses = list(truth.partition_counts)

n = int(q("SELECT count(*) FROM reservations_curated")[0][1][0])
ok(n == truth.row_count, f"R4 filas curadas: Athena {n} / oraculo {truth.row_count}")
for m in (meses[0], meses[len(meses) // 2], meses[-1]):
    v = int(float(q(f"SELECT coalesce(sum(price_cents),0) FROM reservations_curated "
                    f"WHERE month='{m}' AND status='CONFIRMED'")[0][1][0]))
    ok(v == truth.confirmed_revenue(m), f"R4 ingresos confirmados {m}: {v} / {truth.confirmed_revenue(m)}")

nparts = sum(len(pg["Partitions"]) for pg in glue.get_paginator("get_partitions").paginate(
    DatabaseName=a.db, TableName="reservations_curated"))
ok(nparts == 24, f"R5 particiones registradas: {nparts} / 24")
for tabla, cols, part in (("reservations_curated", CURATED_COLUMNS, ["month"]),
                          ("route_month_metrics", METRIC_COLUMNS, [])):
    t = glue.get_table(DatabaseName=a.db, Name=tabla)["Table"]
    nombres = [c["Name"] for c in t["StorageDescriptor"]["Columns"]]
    pk = [c["Name"] for c in t.get("PartitionKeys", [])]
    ok(nombres[:len(cols)] == cols and pk == part, f"R5 columnas de {tabla}")

top = q("SELECT route, CAST(sum(seats_sold) AS DOUBLE)/sum(seats_capacity) AS occ "
        "FROM route_month_metrics GROUP BY route ORDER BY occ DESC LIMIT 10")[0][1:]
exp = truth.top_routes(10)
rutas_ok = [r[0] for r in top] == list(exp["route"])
valores_ok = all(abs(float(r[1]) - e) <= 0.001 * abs(e) for r, e in zip(top, exp["occupancy"]))
ok(rutas_ok and valores_ok, "R6 top-10 rutas por ocupacion")

tam = [o["Size"] for pg in s3.get_paginator("list_objects_v2").paginate(
    Bucket=a.bucket, Prefix=f"{a.prefix}/curated/reservations_curated/")
    for o in pg.get("Contents", []) if o["Key"].endswith(".parquet")]
limite = 2 * sum(tam) / 24
m = meses[12]
filas, escaneado = q(f"SELECT count(*), sum(price_cents) FROM reservations_curated WHERE month='{m}'")
ok(int(filas[1][0]) == truth.partition_counts[m] and escaneado <= limite,
   f"R6 consulta de un mes ({m}): escaneo {escaneado} B, limite {limite:.0f} B")

api = a.api.rstrip("/") + "/analytics/occupancy?"
for _, fila in truth.metrics.sample(3, random_state=1).iterrows():
    url = api + urllib.parse.urlencode({"route": fila["route"], "month": fila["month"]})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            b = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("FALLA  ", fila["route"], fila["month"], "HTTP", e.code, e.read().decode()[:200])
        continue
    seg = time.perf_counter() - t0
    bien = (abs(b["occupancy"] - fila["occupancy"]) <= 0.001 * fila["occupancy"]
            and b["seats_sold"] == fila["seats_sold"] and b["seats_capacity"] == fila["seats_capacity"])
    ok(bien and seg <= 10, f"R7 {fila['route']} {fila['month']}: {b['occupancy']:.4f} "
       f"(oraculo {fila['occupancy']:.4f}) en {seg:.1f} s")

try:
    urllib.request.urlopen(api + "route=ZZZ-YYY&month=2023-01", timeout=15)
    ok(False, "R7 ruta inexistente deberia dar 404")
except urllib.error.HTTPError as e:
    ok(e.code == 404, f"R7 ruta inexistente: HTTP {e.code}")

import os
import re
import time
from threading import Lock

_client = None
_lock = Lock()

def identifier(name):
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", name):
        raise ValueError("Identificador SQL inválido")
    return name

def occupancy(route, month):
    global _client
    import boto3
    from botocore.config import Config
    if not re.fullmatch(r"[A-Z]{3}-[A-Z]{3}", route) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("Ruta o mes inválido")
    with _lock:
        if _client is None:
            _client = boto3.client("athena", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                config=Config(connect_timeout=2, read_timeout=3, retries={"total_max_attempts": 1}, max_pool_connections=20))
    client = _client
    table = identifier(os.getenv("ATHENA_METRICS_TABLE", "route_month_metrics"))
    database = identifier(os.environ["ATHENA_DATABASE"])
    timeout = float(os.getenv("ATHENA_TIMEOUT_SECONDS", "9"))
    deadline = time.monotonic() + timeout
    sql = (f"SELECT route, month, occupancy, seats_sold, seats_capacity FROM {table} "
           f"WHERE route='{route}' AND month='{month}' LIMIT 1")
    kwargs = dict(QueryString=sql, QueryExecutionContext={"Database": database},
                  WorkGroup=os.getenv("ATHENA_WORKGROUP", "primary"))
    if os.getenv("ATHENA_OUTPUT"):
        kwargs["ResultConfiguration"] = {"OutputLocation": os.environ["ATHENA_OUTPUT"]}
    qid = client.start_query_execution(**kwargs)["QueryExecutionId"]
    while True:
        if time.monotonic() > deadline:
            client.stop_query_execution(QueryExecutionId=qid)
            raise TimeoutError(f"Athena superó el plazo; consulta {qid}")
        qe = client.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = qe["Status"]["State"]
        if state == "SUCCEEDED":
            break
        if state in {"FAILED", "CANCELLED"}:
            raise RuntimeError(f"Athena {state}: {qe['Status'].get('StateChangeReason', '')}")
        time.sleep(0.2)
    rows = client.get_query_results(QueryExecutionId=qid, MaxResults=2)["ResultSet"]["Rows"]
    if len(rows) < 2:
        return None
    data = [x.get("VarCharValue") for x in rows[1]["Data"]]
    return {"route": data[0], "month": data[1], "occupancy": float(data[2]),
            "seats_sold": int(data[3]), "seats_capacity": int(data[4])}

"""Prueba rápida de R2: 50 reservas simultáneas contra un vuelo de 1 cupo y otro de 7.

    python -m scripts.prueba_concurrencia --api http://127.0.0.1:8000
"""
import argparse
import json
import threading
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

p = argparse.ArgumentParser()
p.add_argument("--api", default="http://127.0.0.1:8000")
base = p.parse_args().api.rstrip("/")


def post(ruta, cuerpo):
    req = urllib.request.Request(base + ruta, data=json.dumps(cuerpo).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


for cupos in (1, 7):
    fid = "R2-" + uuid.uuid4().hex[:8]
    post("/admin/flights", {"flight_id": fid, "route": "BOG-MDE", "flight_date": "2030-03-01",
                            "capacity": cupos, "price_cents": 10000})
    barrera = threading.Barrier(50)

    def reservar(i):
        barrera.wait()
        return post("/reservations", {"flight_id": fid, "passenger_name": f"P{i}", "fare_class": "ECONOMY"})

    with ThreadPoolExecutor(50) as ex:
        codigos = list(ex.map(reservar, range(50)))
    n201, n409 = codigos.count(201), codigos.count(409)
    otros = sorted(set(c for c in codigos if c not in (201, 409)))
    bien = n201 == cupos and n409 == 50 - cupos and not otros
    print(("OK     " if bien else "FALLA  ") + f"R2 con {cupos} cupo(s): {n201} con 201, {n409} con 409, otros {otros}")

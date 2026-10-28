"""Servidor académico sencillo; no es un servidor de producción de propósito general."""
import json
import logging
import os
import re
import uuid
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, unquote
from . import db, athena

WEB = Path(__file__).resolve().parents[1] / "frontend"
log = logging.getLogger("airline")

class BadRequest(Exception):
    pass

def clean_route(value):
    value = re.sub(r"\s+", "", str(value)).upper()
    if not re.fullmatch(r"[A-Z]{3}-[A-Z]{3}", value):
        raise BadRequest("Ruta esperada AAA-BBB")
    return value

def text(body, name, limit=200):
    value = body.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise BadRequest(f"Campo inválido: {name}")
    return value.strip()

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, fmt, *args):
        log.info(fmt, *args)

    def send(self, code, value, mime="application/json; charset=utf-8"):
        payload = json.dumps(value, ensure_ascii=False).encode() if mime.startswith("application/json") else value
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method):
        try:
            u = urlparse(self.path)
            query = parse_qs(u.query)
            if method == "GET" and u.path in {"/", "/manager"}:
                return self.send(200, (WEB / ("manager.html" if u.path == "/manager" else "index.html")).read_bytes(), "text/html; charset=utf-8")
            if method == "GET" and u.path in {"/app.js", "/style.css"}:
                mime = "text/javascript; charset=utf-8" if u.path.endswith(".js") else "text/css; charset=utf-8"
                return self.send(200, (WEB / u.path[1:]).read_bytes(), mime)
            if method == "GET" and u.path == "/health":
                return self.send(200, {"status": "ok"})
            if method == "GET" and u.path == "/flights/search":
                origin = query.get("origin", [""])[0].upper()
                destination = query.get("destination", [""])[0].upper()
                route = clean_route(origin + "-" + destination)
                day = date.fromisoformat(query.get("date", [""])[0]).isoformat()
                with db.connection() as c:
                    rows = db.execute(c, """SELECT flight_id, route, flight_date, seats_available, price_cents
                        FROM flights WHERE route=? AND flight_date=? AND seats_available>0 ORDER BY flight_id""", (route, day)).fetchall()
                return self.send(200, [dict(row) for row in rows])
            if method == "GET" and u.path.startswith("/reservations/"):
                rid = unquote(u.path[len("/reservations/"):])
                with db.connection() as c:
                    row = db.execute(c, """SELECT reservation_id, flight_id, status, passenger_name
                        FROM reservations WHERE reservation_id=?""", (rid,)).fetchone()
                return self.send(200 if row else 404, dict(row) if row else {"detail": "Reserva inexistente"})
            if method == "GET" and u.path == "/analytics/occupancy":
                route = clean_route(query.get("route", [""])[0])
                month = query.get("month", [""])[0]
                result = athena.occupancy(route, month)
                return self.send(200 if result else 404, result or {"detail": "Sin datos"})
            if method == "POST":
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 16384:
                    raise BadRequest("Tamaño JSON inválido")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise BadRequest("Se espera un objeto JSON")
                if u.path == "/admin/flights":
                    fid = text(body, "flight_id")
                    route = clean_route(body.get("route", ""))
                    day = date.fromisoformat(text(body, "flight_date")).isoformat()
                    capacity, price = body.get("capacity"), body.get("price_cents")
                    if type(capacity) is not int or capacity <= 0 or type(price) is not int or price <= 0:
                        raise BadRequest("Capacidad y precio deben ser enteros positivos")
                    try:
                        with db.connection() as c:
                            db.execute(c, "INSERT INTO flights VALUES (?,?,?,?,?,?)", (fid, route, day, capacity, capacity, price))
                    except Exception as e:
                        if db.integrity_error(e):
                            return self.send(409, {"detail": "El vuelo ya existe"})
                        raise
                    return self.send(201, {"flight_id": fid, "route": route, "flight_date": day, "capacity": capacity, "price_cents": price})
                if u.path == "/reservations":
                    fid = text(body, "flight_id")
                    name = text(body, "passenger_name")
                    fare = text(body, "fare_class").upper()
                    if fare not in {"ECONOMY", "BUSINESS"}:
                        raise BadRequest("Clase inválida")
                    rid = uuid.uuid4().hex
                    with db.connection() as c:
                        result = db.execute(c, """UPDATE flights SET seats_available=seats_available-1
                            WHERE flight_id=? AND seats_available>0""", (fid,))
                        if result.rowcount == 0:
                            exists = db.execute(c, "SELECT 1 FROM flights WHERE flight_id=?", (fid,)).fetchone()
                            code = 409 if exists else 404
                            response = {"detail": "Sin cupos" if exists else "Vuelo inexistente"}
                        else:
                            db.execute(c, "INSERT INTO reservations VALUES (?,?,?,?,?)", (rid, fid, "CONFIRMED", name, fare))
                            code, response = 201, {"reservation_id": rid, "flight_id": fid, "status": "CONFIRMED", "passenger_name": name}
                    return self.send(code, response)
            return self.send(404, {"detail": "Ruta inexistente"})
        except (ValueError, BadRequest, KeyError) as e:
            return self.send(422, {"detail": str(e)})
        except TimeoutError:
            return self.send(504, {"detail": "La consulta Athena tardó demasiado"})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            log.exception("Fallo de solicitud")
            return self.send(500, {"detail": "Error interno; revisar los registros"})

class Server(ThreadingHTTPServer):
    request_queue_size = 256
    daemon_threads = True

def main():
    logging.basicConfig(level=logging.INFO)
    db.start()
    Server((os.getenv("APP_HOST", "127.0.0.1"), int(os.getenv("APP_PORT", "8000"))), Handler).serve_forever()

if __name__ == "__main__":
    main()

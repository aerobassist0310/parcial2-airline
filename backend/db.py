"""SQLite permite probar localmente; PostgreSQL es el destino del laboratorio."""
import os
import sqlite3
from contextlib import contextmanager

MODE = os.getenv("DB_MODE", "sqlite")
POOL = None

def start():
    global POOL
    if MODE == "postgres":
        from psycopg_pool import ConnectionPool
        from psycopg.rows import dict_row
        POOL = ConnectionPool(os.environ["DATABASE_URL"], min_size=2,
                              max_size=int(os.getenv("DB_POOL_MAX", "20")),
                              timeout=15, kwargs={"row_factory": dict_row})
        POOL.wait(timeout=30)
    elif MODE != "sqlite":
        raise ValueError("DB_MODE debe ser sqlite o postgres")
    with connection() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS flights (
            flight_id TEXT PRIMARY KEY, route TEXT NOT NULL, flight_date TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK(capacity > 0),
            seats_available INTEGER NOT NULL CHECK(seats_available >= 0),
            price_cents BIGINT NOT NULL CHECK(price_cents > 0),
            CHECK(seats_available <= capacity))""")
        c.execute("CREATE INDEX IF NOT EXISTS flights_search ON flights(route, flight_date)")
        c.execute("""CREATE TABLE IF NOT EXISTS reservations (
            reservation_id TEXT PRIMARY KEY,
            flight_id TEXT NOT NULL REFERENCES flights(flight_id),
            status TEXT NOT NULL CHECK(status = 'CONFIRMED'),
            passenger_name TEXT NOT NULL, fare_class TEXT NOT NULL)""")

@contextmanager
def connection():
    if MODE == "postgres":
        with POOL.connection() as c:
            yield c
    else:
        c = sqlite3.connect(os.getenv("SQLITE_PATH", "airline-local.db"), timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        try:
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

def execute(c, sql, params=()):
    return c.execute(sql.replace("?", "%s") if MODE == "postgres" else sql, params)

def integrity_error(e):
    if MODE == "postgres":
        import psycopg
        return isinstance(e, psycopg.errors.UniqueViolation)
    return isinstance(e, sqlite3.IntegrityError)

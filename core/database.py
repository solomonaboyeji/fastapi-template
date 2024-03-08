import psycopg2

import psycopg2.pool
import atexit
from psycopg2.extensions import connection as PsycopgConnection
from core.config import DB_CONN_STRING, MAX_DB_POOL_SIZE, MIN_DB_POOL_SIZE

# Create a connection pool
DB_POOL = psycopg2.pool.SimpleConnectionPool(
    minconn=MIN_DB_POOL_SIZE,
    maxconn=MAX_DB_POOL_SIZE,
    dsn=DB_CONN_STRING,
)

# Ensure connections are closed when the application exits
atexit.register(DB_POOL.closeall)


def get_db() -> PsycopgConnection:
    db: PsycopgConnection = DB_POOL.getconn()
    return db

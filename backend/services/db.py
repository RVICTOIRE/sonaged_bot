import contextlib
import os
from urllib.parse import urlparse, unquote
import psycopg2
from config import config


def _connect_from_parts_or_url(database_url: str):
    # Prefer explicit parts to avoid URL decoding issues
    if os.getenv("DB_NAME"):
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
        )
        conn.set_client_encoding("UTF8")
        return conn

    # Support special characters in user/password via parsing + unquote
    parsed = urlparse(database_url)
    if parsed.scheme.startswith("postgres"):
        user = unquote(parsed.username) if parsed.username else None
        password = unquote(parsed.password) if parsed.password else None
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        dbname = parsed.path.lstrip("/")
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        # Ensure UTF-8 client encoding
        conn.set_client_encoding("UTF8")
        return conn
    # Fallback to raw dsn if not a URL
    conn = psycopg2.connect(database_url)
    conn.set_client_encoding("UTF8")
    return conn


@contextlib.contextmanager
def get_db():
    conn = _connect_from_parts_or_url(config.DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()




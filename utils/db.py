"""Postgres-backed daily treatment log (SQLAlchemy).

Reads DATABASE_URL from the environment (Railway injects it automatically).
If DATABASE_URL is unset, all functions report unavailable and the app falls
back to the local session-state log — so `streamlit run app.py` still works
with zero setup on a laptop.
"""
import os

import pandas as pd

COLUMNS = [
    ("date", "TEXT"), ("operator", "TEXT"), ("rig", "TEXT"), ("well", "TEXT"),
    ("county", "TEXT"), ("fluid_system", "TEXT"), ("volume_bbl", "REAL"),
    ("gpm", "REAL"), ("temp_f", "REAL"), ("ph", "REAL"), ("chlorides", "REAL"),
    ("calcium", "REAL"), ("hardness", "REAL"), ("pf", "REAL"), ("mf", "REAL"),
    ("pm", "REAL"), ("iron", "REAL"), ("do_ppm", "REAL"), ("h2s_ppm", "REAL"),
    ("coupon_mpy", "REAL"), ("corr_gal_day", "REAL"), ("scav_gal_day", "REAL"),
    ("h2s_status", "TEXT"), ("scav_beg", "REAL"), ("scav_rec", "REAL"),
    ("scav_used", "REAL"), ("scav_end", "REAL"), ("corr_beg", "REAL"),
    ("corr_rec", "REAL"), ("corr_used", "REAL"), ("corr_end", "REAL"),
    ("buster_beg", "REAL"), ("buster_rec", "REAL"), ("buster_used", "REAL"),
    ("buster_end", "REAL"), ("pump_notes", "TEXT"), ("h2s_notes", "TEXT"),
]
COLUMN_NAMES = [n for n, _ in COLUMNS]

_engine = None


def database_url():
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def available() -> bool:
    return bool(database_url())


def get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine
        _engine = create_engine(database_url(), pool_pre_ping=True)
    return _engine


def init_db() -> bool:
    """Create the daily_log table if missing. Returns False when no DB."""
    if not available():
        return False
    from sqlalchemy import MetaData, Table, Column, Integer, DateTime, func, TEXT, REAL
    types = {"TEXT": TEXT, "REAL": REAL}
    meta = MetaData()
    Table("daily_log", meta,
          Column("id", Integer, primary_key=True),
          *[Column(name, types[t]) for name, t in COLUMNS],
          Column("created_at", DateTime, server_default=func.now()))
    meta.create_all(get_engine(), checkfirst=True)
    return True


def add_entry(row: dict):
    from sqlalchemy import text
    cols = [c for c in COLUMN_NAMES if c in row]
    params = {c: row[c] for c in cols}
    sql = text(f"INSERT INTO daily_log ({', '.join(cols)}) "
               f"VALUES ({', '.join(':' + c for c in cols)})")
    with get_engine().begin() as conn:
        conn.execute(sql, params)


def fetch_log() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM daily_log ORDER BY id", get_engine())
    return df.drop(columns=["id", "created_at"], errors="ignore")


def clear_log():
    from sqlalchemy import text
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM daily_log"))

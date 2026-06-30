"""일봉 OHLCV SQLite 저장소.

장 마감 후 collect_ohlcv.py 가 전 종목 일봉을 수집해 저장하고,
장중에는 get_prev_day / get_recent 로 빠르게 조회한다.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "data" / "ohlcv.db"


def _conn(db_path: Path = _DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = _DB_PATH) -> None:
    with _conn(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                ticker        TEXT    NOT NULL,
                date          TEXT    NOT NULL,
                open          REAL,
                high          REAL,
                low           REAL,
                close         REAL,
                volume        INTEGER,
                trading_value REAL,
                PRIMARY KEY (ticker, date)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ohlcv_ticker_date ON ohlcv(ticker, date DESC)"
        )


def upsert_rows(rows: list[dict], db_path: Path = _DB_PATH) -> int:
    """OHLCV 행 일괄 upsert. rows 각 항목: {ticker, date, open, high, low, close, volume, trading_value}"""
    if not rows:
        return 0
    with _conn(db_path) as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO ohlcv
               (ticker, date, open, high, low, close, volume, trading_value)
               VALUES (:ticker, :date, :open, :high, :low, :close, :volume, :trading_value)""",
            rows,
        )
    return len(rows)


def get_recent(ticker: str, n_days: int = 60, db_path: Path = _DB_PATH) -> list[dict]:
    """최근 n_days 영업일치 OHLCV — 날짜 오름차순."""
    with _conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM ohlcv WHERE ticker=? AND date != '' ORDER BY date DESC LIMIT ?",
            (ticker, n_days),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_prev_day(ticker: str, today: str, db_path: Path = _DB_PATH) -> dict | None:
    """today(YYYYMMDD) 이전 가장 최근 영업일 OHLCV."""
    with _conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM ohlcv WHERE ticker=? AND date<? AND date != '' ORDER BY date DESC LIMIT 1",
            (ticker, today),
        ).fetchone()
    return dict(row) if row else None


def get_max_date(db_path: Path = _DB_PATH) -> str | None:
    """DB 전체에서 가장 최근 날짜(YYYYMMDD) 반환. 데이터 없으면 None."""
    try:
        with _conn(db_path) as conn:
            row = conn.execute(
                "SELECT MAX(date) FROM ohlcv WHERE date != ''"
            ).fetchone()
        return row[0] if row and row[0] else None
    except Exception:
        return None

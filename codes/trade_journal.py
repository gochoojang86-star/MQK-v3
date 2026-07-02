"""
Trade Journal - 거래 생애주기 관리 (SQLite)
LLM 미사용.

스키마:
  trades: 진입부터 청산까지 단일 레코드
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from config.settings import RISK

_DEFAULT_DB = Path(__file__).parent.parent / "data" / "trades.db"


class TradeJournal:
    def __init__(self, db_path: Path = _DEFAULT_DB) -> None:
        self._db = Path(db_path)
        self._db.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker          TEXT NOT NULL,
                    name            TEXT NOT NULL,
                    entry_date      TEXT NOT NULL,
                    entry_price     REAL NOT NULL,
                    quantity        INTEGER NOT NULL,
                    stop_loss_price REAL NOT NULL,
                    entry_reason    TEXT,
                    confidence      INTEGER,
                    order_no        TEXT,
                    exit_date       TEXT,
                    exit_price      REAL,
                    exit_reason     TEXT,
                    pnl             REAL,
                    pnl_pct         REAL,
                    result          TEXT,
                    strategy_type   TEXT DEFAULT 'TREND',
                    highest_price   REAL,
                    target1_hit     INTEGER DEFAULT 0,
                    trailing_active INTEGER DEFAULT 0,
                    created_at      TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            self._ensure_column(conn, "highest_price", "REAL")
            self._ensure_column(conn, "target1_hit", "INTEGER DEFAULT 0")
            self._ensure_column(conn, "trailing_active", "INTEGER DEFAULT 0")
            self._ensure_column(conn, "strategy_type", "TEXT DEFAULT 'TREND'")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_executions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id        INTEGER NOT NULL,
                    ticker          TEXT NOT NULL,
                    side            TEXT NOT NULL,
                    exec_date       TEXT NOT NULL,
                    price           REAL NOT NULL,
                    quantity        INTEGER NOT NULL,
                    reason          TEXT,
                    realized_pnl    REAL DEFAULT 0,
                    realized_pnl_pct REAL DEFAULT 0,
                    created_at      TEXT DEFAULT (datetime('now','localtime'))
                )
            """)

    def _ensure_column(self, conn, name: str, ddl: str) -> None:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(trades)").fetchall()
        }
        if name not in columns:
            conn.execute(f"ALTER TABLE trades ADD COLUMN {name} {ddl}")

    def open_trade(
        self,
        ticker: str,
        name: str,
        entry_date: str,
        entry_price: float,
        quantity: int,
        stop_loss_price: float,
        entry_reason: str,
        confidence: int,
        order_no: str = "",
        strategy_type: str = "TREND",
    ) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO trades
                   (ticker, name, entry_date, entry_price, quantity,
                    stop_loss_price, entry_reason, confidence, order_no,
                    highest_price, target1_hit, trailing_active, strategy_type)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    ticker,
                    name,
                    entry_date,
                    entry_price,
                    quantity,
                    stop_loss_price,
                    entry_reason,
                    confidence,
                    order_no,
                    entry_price,
                    0,
                    0,
                    strategy_type,
                ),
            )
            return cur.lastrowid

    def close_trade(
        self,
        ticker: str,
        exit_date: str,
        exit_price: float,
        exit_reason: str,
        quantity: int | None = None,
    ) -> None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, entry_price, quantity FROM trades "
                "WHERE ticker=? AND exit_date IS NULL ORDER BY id DESC LIMIT 1",
                (ticker,),
            ).fetchone()
            if not row:
                raise ValueError(f"{ticker}: 청산할 미결 포지션이 없습니다.")
            close_quantity = int(quantity or row["quantity"])
            if close_quantity <= 0:
                raise ValueError(f"{ticker}: 청산 수량은 1 이상이어야 합니다.")
            if close_quantity > int(row["quantity"]):
                raise ValueError(f"{ticker}: 청산 수량이 보유 수량을 초과합니다.")

            realized_pnl = (exit_price - row["entry_price"]) * close_quantity
            realized_pnl_pct = (
                (exit_price - row["entry_price"]) / row["entry_price"] * 100
            )
            self._record_execution(
                conn=conn,
                trade_id=row["id"],
                ticker=ticker,
                side="SELL",
                exec_date=exit_date,
                price=exit_price,
                quantity=close_quantity,
                reason=exit_reason,
                realized_pnl=realized_pnl,
                realized_pnl_pct=realized_pnl_pct,
            )

            if close_quantity < int(row["quantity"]):
                conn.execute(
                    """UPDATE trades SET quantity=?, target1_hit=1
                       WHERE id=?""",
                    (int(row["quantity"]) - close_quantity, row["id"]),
                )
                return

            realized_total = self._realized_total(conn, row["id"])
            realized_quantity = self._realized_quantity(conn, row["id"])
            realized_pnl_pct = (
                realized_total / (float(row["entry_price"]) * realized_quantity) * 100
                if realized_quantity
                else 0.0
            )
            result = "WIN" if realized_total > 0 else ("LOSS" if realized_total < 0 else "BREAKEVEN")
            conn.execute(
                """UPDATE trades SET exit_date=?, exit_price=?, exit_reason=?,
                   pnl=?, pnl_pct=?, result=? WHERE id=?""",
                (
                    exit_date,
                    exit_price,
                    exit_reason,
                    round(realized_total, 0),
                    round(realized_pnl_pct, 2),
                    result,
                    row["id"],
                ),
            )

    def _record_execution(
        self,
        conn,
        trade_id: int,
        ticker: str,
        side: str,
        exec_date: str,
        price: float,
        quantity: int,
        reason: str,
        realized_pnl: float = 0.0,
        realized_pnl_pct: float = 0.0,
    ) -> None:
        conn.execute(
            """INSERT INTO trade_executions
               (trade_id, ticker, side, exec_date, price, quantity, reason,
                realized_pnl, realized_pnl_pct)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                trade_id,
                ticker,
                side,
                exec_date,
                price,
                quantity,
                reason,
                round(realized_pnl, 0),
                round(realized_pnl_pct, 2),
            ),
        )

    def _realized_total(self, conn, trade_id: int) -> float:
        row = conn.execute(
            "SELECT COALESCE(SUM(realized_pnl), 0) AS total "
            "FROM trade_executions WHERE trade_id=?",
            (trade_id,),
        ).fetchone()
        return float(row["total"] or 0)

    def _realized_quantity(self, conn, trade_id: int) -> int:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) AS quantity "
            "FROM trade_executions WHERE trade_id=?",
            (trade_id,),
        ).fetchone()
        return int(row["quantity"] or 0)

    def get_trade_executions(self, ticker: str | None = None) -> list[dict]:
        with self._conn() as conn:
            if ticker:
                rows = conn.execute(
                    "SELECT * FROM trade_executions WHERE ticker=? ORDER BY id",
                    (ticker,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM trade_executions ORDER BY id"
                ).fetchall()
        return [dict(r) for r in rows]

    def update_position_management(
        self,
        ticker: str,
        stop_loss_price: float | None = None,
        highest_price: float | None = None,
        target1_hit: bool | None = None,
        trailing_active: bool | None = None,
    ) -> None:
        """보유 포지션의 보호 스탑/최고가/1차익절 상태를 갱신한다.

        손절가는 절대 낮추지 않는다.
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, stop_loss_price, highest_price FROM trades "
                "WHERE ticker=? AND exit_date IS NULL ORDER BY id DESC LIMIT 1",
                (ticker,),
            ).fetchone()
            if not row:
                return

            updates = []
            params = []
            if stop_loss_price is not None:
                protected_stop = max(float(row["stop_loss_price"]), float(stop_loss_price))
                updates.append("stop_loss_price=?")
                params.append(protected_stop)
            if highest_price is not None:
                previous_high = float(row["highest_price"] or 0)
                updates.append("highest_price=?")
                params.append(max(previous_high, float(highest_price)))
            if target1_hit is not None:
                updates.append("target1_hit=?")
                params.append(1 if target1_hit else 0)
            if trailing_active is not None:
                updates.append("trailing_active=?")
                params.append(1 if trailing_active else 0)
            if not updates:
                return
            params.append(row["id"])
            conn.execute(
                f"UPDATE trades SET {', '.join(updates)} WHERE id=?",
                params,
            )

    def reconcile_open_positions(self, broker_positions: list[dict]) -> list[str]:
        """브로커가 실제 보유 중인데 저널엔 없는 종목을 open_trade로 백필한다.

        2026-07-02 사고: 브로커(모의계좌)엔 실제 보유 중인 종목이 있었는데 저널에
        진입 기록이 없어 CLOSE phase의 SELL 처리와 코드 레벨 하드 스톱로스가 모두
        해당 종목을 인식하지 못했다 (둘 다 저널을 유일한 진실의 원천으로 사용).
        매수 주문이 저널 기록 없이 체결되는 경로(수동 매수, 저널 기록 전 프로세스
        종료 등)가 있는 한 이 드리프트는 재발할 수 있으므로, 반복 호출해 항상
        브로커 잔고 기준으로 누락분을 메꾼다.

        이미 저널에 있는 종목은 절대 덮어쓰지 않는다 — 수량/평단가 불일치 자체가
        더 깊은 버그의 신호일 수 있어 자동 정정하지 않고 그대로 둔다.
        """
        tracked = {pos["ticker"] for pos in self.get_open_positions()}
        backfilled: list[str] = []
        for pos in broker_positions:
            ticker = str(pos.get("ticker") or "").strip()
            quantity = int(pos.get("quantity") or 0)
            if not ticker or quantity <= 0 or ticker in tracked:
                continue
            avg_price = float(pos.get("avg_price") or 0)
            # stop_loss_price=0은 코드 레벨 하드 스톱로스 체크에서 무시되므로(0 이하 skip),
            # 백필된 포지션도 즉시 보호받도록 RiskConfig 최대 손절폭 기준 보수적 기본값을 채운다.
            # LLM/사용자가 더 타이트한 값으로 갱신하기 전까지의 임시 안전망일 뿐이다.
            default_stop = (
                round(avg_price * (1 - RISK.max_stop_loss_pct / 100), 0) if avg_price > 0 else 0.0
            )
            self.open_trade(
                ticker=ticker,
                name=str(pos.get("name") or ticker),
                entry_date=datetime.now().strftime("%Y-%m-%d"),
                entry_price=avg_price,
                quantity=quantity,
                stop_loss_price=default_stop,
                entry_reason="reconciled_from_broker_balance",
                confidence=0,
                order_no="RECONCILED",
                strategy_type="UNKNOWN",
            )
            backfilled.append(ticker)
        return backfilled

    def get_open_positions(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE exit_date IS NULL ORDER BY entry_date"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_closed_trades(self, days: int = 30) -> list[dict]:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE exit_date >= ? ORDER BY exit_date DESC",
                (since,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_daily_summary(self, date: str) -> dict:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE exit_date=?", (date,)
            ).fetchall()
        trades = [dict(r) for r in rows]
        wins = [t for t in trades if t.get("result") == "WIN"]
        losses = [t for t in trades if t.get("result") == "LOSS"]
        breakeven = [t for t in trades if t.get("result") == "BREAKEVEN"]
        return {
            "date": date,
            "total_trades": len(trades),
            "win_trades": len(wins),
            "loss_trades": len(losses),
            "breakeven_trades": len(breakeven),
            "total_pnl": sum(t.get("pnl", 0) for t in trades),
            "win_rate": (
                round(len(wins) / len(trades) * 100, 1) if trades else 0.0
            ),
        }

    def today_summary(self) -> dict:
        """현재 날짜 기준 거래 요약. TradingAgent 사전주입 컨텍스트용."""
        today = datetime.now().strftime("%Y-%m-%d")
        summary = self.get_daily_summary(today)
        closed_today = [
            t for t in self.get_closed_trades(days=1) if t.get("exit_date") == today
        ]
        return {
            "trade_count": summary["total_trades"],
            "realized_pnl_pct": round(
                sum(t.get("pnl_pct") or 0 for t in closed_today), 2
            ),
            "win": summary["win_trades"],
            "loss": summary["loss_trades"],
            "open_positions": len(self.get_open_positions()),
            "last_trade": self._last_trade_summary(today),
        }

    def _last_trade_summary(self, date: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT ticker, result, pnl_pct FROM trades "
                "WHERE exit_date=? ORDER BY id DESC LIMIT 1",
                (date,),
            ).fetchone()
        if row is None:
            return None
        r = dict(row)
        return {
            "ticker": r["ticker"],
            "result": r.get("result"),
            "pct": r.get("pnl_pct") or 0,
        }

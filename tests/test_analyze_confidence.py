import importlib.util
import sqlite3
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "analyze_confidence", Path(__file__).resolve().parent.parent / "scripts" / "analyze_confidence.py"
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


def _make_db(path: Path, rows):
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE trades (id INTEGER PRIMARY KEY, ticker TEXT, entry_date TEXT, exit_date TEXT, "
        "confidence INTEGER, pnl REAL, pnl_pct REAL, result TEXT, strategy_type TEXT)"
    )
    conn.executemany(
        "INSERT INTO trades (ticker, entry_date, exit_date, confidence, pnl, pnl_pct, result, strategy_type) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()


def test_load_excludes_open_reconciled_and_filters_strategy(tmp_path):
    db = tmp_path / "t.db"
    _make_db(db, [
        ("A", "2099-01-01", "2099-01-02", 80, 1000, 3.0, "WIN", "X"),
        ("B", "2099-01-01", None, 80, None, None, None, "X"),          # 미청산
        ("C", "2099-01-01", "2099-01-02", 0, 10, 1.0, "WIN", "X"),     # reconcile
        ("D", "2099-01-01", "2099-01-02", 75, -500, -2.0, "LOSS", "Y"),
    ])
    assert {t["ticker"] for t in ac.load_closed_trades(db)} == {"A", "D"}
    assert {t["ticker"] for t in ac.load_closed_trades(db, strategy="X")} == {"A"}


def test_summarize_and_threshold_table():
    trades = [
        {"confidence": 72, "pnl_pct": -2.0},
        {"confidence": 78, "pnl_pct": 1.0},
        {"confidence": 82, "pnl_pct": 4.0},
        {"confidence": 88, "pnl_pct": 2.0},
    ]
    s = ac.summarize(trades)
    assert s["n"] == 4 and s["win_rate"] == 75.0 and round(s["avg_ret"], 2) == 1.25
    assert round(s["profit_factor"], 2) == 3.5
    th = dict(ac.by_threshold(trades))
    assert th[80]["n"] == 2 and th[80]["win_rate"] == 100.0
    assert th[90]["n"] == 0


def test_render_handles_empty_and_flags_small_sample():
    assert "분석할 거래가 없습니다" in ac.render([], 20)
    text = ac.render([{"confidence": 80, "pnl_pct": 1.0}], 20)
    assert "표본 부족" in text and "한계" in text

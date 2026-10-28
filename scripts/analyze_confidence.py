#!/usr/bin/env python3
"""매매 일지(data/trades.db)로 confidence 구간별 성과를 분석한다.

목적: buy_confidence_threshold를 감이 아니라 실제 청산 결과로 정한다.
읽기 전용이며 DB를 수정하지 않는다.

사용:
  python scripts/analyze_confidence.py
  python scripts/analyze_confidence.py --db data/trades.db --days 90 --strategy VOLUME_SURGE_LEADER
"""
from __future__ import annotations

import argparse
import sqlite3
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "trades.db"
BUCKETS = [(0, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 101)]
THRESHOLDS = [60, 65, 70, 75, 80, 85, 90]
MIN_N_DEFAULT = 20


def load_closed_trades(
    db_path: Path,
    days: int | None = None,
    strategy: str | None = None,
) -> list[dict]:
    """청산 완료 + confidence 기록이 있는 거래만 읽는다.

    confidence=0/NULL은 브로커 잔고 보정(reconcile)으로 생성된 거래라 제외한다.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        sql = (
            "SELECT ticker, entry_date, exit_date, confidence, pnl, pnl_pct, result, strategy_type "
            "FROM trades WHERE exit_date IS NOT NULL AND pnl_pct IS NOT NULL "
            "AND confidence IS NOT NULL AND confidence > 0"
        )
        params: list = []
        if days:
            sql += " AND entry_date >= ?"
            params.append((datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"))
        if strategy:
            sql += " AND strategy_type = ?"
            params.append(strategy)
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def summarize(trades: list[dict]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0}
    rets = [float(t["pnl_pct"]) for t in trades]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r < 0]
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    return {
        "n": n,
        "win_rate": len(wins) / n * 100,
        "avg_ret": sum(rets) / n,
        "median_ret": statistics.median(rets),
        "avg_win": (gross_win / len(wins)) if wins else 0.0,
        "avg_loss": (sum(losses) / len(losses)) if losses else 0.0,
        "profit_factor": (gross_win / gross_loss) if gross_loss > 0 else float("inf") if gross_win > 0 else 0.0,
        "total_ret": sum(rets),
    }


def by_bucket(trades: list[dict]) -> list[tuple[str, dict]]:
    rows = []
    for lo, hi in BUCKETS:
        label = f"{lo}~{hi - 1}" if hi <= 100 else f"{lo}+"
        subset = [t for t in trades if lo <= int(t["confidence"]) < hi]
        rows.append((label, summarize(subset)))
    return rows


def by_threshold(trades: list[dict]) -> list[tuple[int, dict]]:
    return [(th, summarize([t for t in trades if int(t["confidence"]) >= th])) for th in THRESHOLDS]


def _fmt(s: dict, min_n: int) -> str:
    if s["n"] == 0:
        return "      -"
    pf = "inf" if s["profit_factor"] == float("inf") else f"{s['profit_factor']:.2f}"
    flag = "  (표본 부족)" if s["n"] < min_n else ""
    return (
        f"n={s['n']:>3}  승률={s['win_rate']:5.1f}%  평균={s['avg_ret']:+6.2f}%  "
        f"중앙값={s['median_ret']:+6.2f}%  평균이익={s['avg_win']:+5.2f}%  평균손실={s['avg_loss']:+6.2f}%  "
        f"PF={pf:>5}  누적={s['total_ret']:+7.2f}%{flag}"
    )


def render(trades: list[dict], min_n: int) -> str:
    out = []
    total = summarize(trades)
    out.append(f"분석 대상: 청산 완료 거래 {total['n']}건 (confidence 기록 있는 것만)")
    if total["n"] == 0:
        out.append("분석할 거래가 없습니다.")
        return "\n".join(out)
    out.append(f"전체: {_fmt(total, min_n)}")
    out.append("")
    out.append("[구간별 성과] — confidence가 높을수록 성과가 좋아지는지 확인")
    for label, s in by_bucket(trades):
        out.append(f"  {label:>6}: {_fmt(s, min_n)}")
    out.append("")
    out.append("[임계값별 성과] — 'confidence ≥ X만 진입했다면'의 결과")
    for th, s in by_threshold(trades):
        out.append(f"  ≥{th:>3}: {_fmt(s, min_n)}")
    out.append("")
    out.append("해석 가이드")
    out.append("  - 구간이 올라갈수록 승률·평균 수익이 함께 오르면 confidence가 유효한 신호입니다.")
    out.append("  - 구간 간 차이가 없거나 뒤집히면 confidence는 변별력이 없어, 임계값보다 다른 기준이 중요합니다.")
    out.append(f"  - n<{min_n}인 구간은 우연 가능성이 커서 임계값 결정 근거로 쓰지 마십시오.")
    out.append("  - 한계: 실제로 체결된 거래만 포함합니다. 임계값 미만이라 진입하지 않은 신호의 성과는 알 수 없습니다.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--days", type=int, default=None, help="최근 N일 진입 거래만")
    ap.add_argument("--strategy", default=None, help="strategy_type 필터")
    ap.add_argument("--min-n", type=int, default=MIN_N_DEFAULT, help="구간별 최소 표본 수 (기본 20)")
    args = ap.parse_args(argv)

    if not args.db.exists():
        print(f"DB 없음: {args.db}", file=sys.stderr)
        return 1
    print(render(load_closed_trades(args.db, args.days, args.strategy), args.min_n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

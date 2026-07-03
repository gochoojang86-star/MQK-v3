#!/usr/bin/env python3
"""장초반 선진입 워처 (PM2: mqk-v3-premarket-watcher, 09:00 기동 → 09:17 종료).

market_close가 next_day_premarket_context.json에 남긴 premarket_entry_candidates를
30초 간격으로 폴링해, 장초반 조건(시가 범위 + 초반 거래대금) 충족 시:
  1. watchlist 병합
  2. intraday LLM 즉시 트리거

09:17에 정규 scan이 시작되므로 그 전에 종료한다.
"""
from __future__ import annotations

import fcntl
import logging
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mqk_v3_premarket_watcher")

POLL_INTERVAL_SEC = 30
END_TIME = "09:17"
_LOCK_PATH = Path(__file__).parent / "data" / "mqk_v3.lock"
_TRIGGERED_PATH = Path(__file__).parent / "data" / "premarket_watcher_triggered.json"


def _try_lock():
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    f = open(_LOCK_PATH, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except OSError:
        f.close()
        return None


def _load_triggered() -> set:
    try:
        import json
        data = json.loads(_TRIGGERED_PATH.read_text(encoding="utf-8"))
        if data.get("date") == datetime.now().strftime("%Y%m%d"):
            return set(data.get("tickers", []))
    except Exception:
        pass
    return set()


def _save_triggered(tickers: set) -> None:
    import json
    _TRIGGERED_PATH.write_text(
        json.dumps({"date": datetime.now().strftime("%Y%m%d"), "tickers": list(tickers)}),
        encoding="utf-8",
    )


def _check_entry_condition(snapshot: dict, cond: dict) -> tuple[bool, str]:
    """시가 갭 범위 + 초반 거래대금 조건 확인."""
    change_pct = snapshot.get("change_pct") or 0.0
    trading_value = snapshot.get("trading_value") or 0.0

    min_chg = cond.get("min_open_change_pct", -999)
    max_chg = cond.get("max_open_change_pct", 999)
    min_tv = cond.get("min_5min_trading_value", 0)

    if not (min_chg <= change_pct <= max_chg):
        return False, f"갭 범위 미충족: {change_pct:.1f}% (조건 {min_chg}~{max_chg}%)"
    if trading_value < min_tv:
        return False, f"거래대금 미충족: {trading_value/1e8:.0f}억 (조건 {min_tv/1e8:.0f}억↑)"
    return True, f"조건 충족: 갭 {change_pct:.1f}%, 거래대금 {trading_value/1e8:.0f}억"


def main() -> None:
    from codes.market_calendar import check_trading_day, read_cached_trading_day

    cached = read_cached_trading_day()
    if cached is None:
        cached = check_trading_day()
    if not cached:
        logger.info("[premarket_watcher] 휴장일 — 종료")
        return

    from broker.kis_api import KISApi
    from orchestrator_v3 import MQKOrchestratorV3, load_next_day_premarket_context

    orch = MQKOrchestratorV3(kis_api=KISApi())
    ctx = load_next_day_premarket_context()
    candidates = ctx.get("premarket_entry_candidates") or []

    if not candidates:
        logger.info("[premarket_watcher] premarket_entry_candidates 없음 — 종료")
        return

    logger.info(f"[premarket_watcher] 후보 {len(candidates)}개 감시 시작: {[c['ticker'] for c in candidates]}")
    triggered = _load_triggered()

    while datetime.now().strftime("%H:%M") < END_TIME:
        now_hhmm = datetime.now().strftime("%H:%M")

        # 09:05 이전은 시가 확정 전 — 대기
        if now_hhmm < "09:05":
            time.sleep(POLL_INTERVAL_SEC)
            continue

        _poll_once(orch, candidates, triggered)
        time.sleep(POLL_INTERVAL_SEC)

    logger.info("[premarket_watcher] 09:17 scan 시작 — 워처 종료")


def _poll_once(orch, candidates: list[dict], triggered: set) -> None:
    """후보 전체를 한 번 순회하며 진입 조건을 확인하고, 충족 시 즉시 트리거한다."""
    from market_intelligence.stock import get_watchlist_intraday_snapshot
    from orchestrator_v3 import load_watchlist_entries, save_watchlist

    for cand in candidates:
        ticker = cand.get("ticker")
        if not ticker or ticker in triggered:
            continue

        cond = cand.get("entry_condition", {})
        try:
            snapshot_result = get_watchlist_intraday_snapshot(orch._mil, "PREMARKET", [ticker])
            items = (snapshot_result or {}).get("tickers") or []
            snap = next((s for s in items if s.get("ticker") == ticker), None)
            if not snap:
                continue

            ok, reason = _check_entry_condition(snap, cond)
            name = cand.get("name", ticker)
            logger.info(f"[premarket_watcher] {name}({ticker}): {reason}")

            if ok:
                lock = _try_lock()
                if lock is None:
                    logger.info(f"[premarket_watcher] {ticker} 락 경합 — 다음 폴에서 재시도")
                    continue
                try:
                    wl = load_watchlist_entries()
                    existing_tickers = {e["ticker"] for e in wl}
                    if ticker not in existing_tickers:
                        new_entry = {
                            "ticker": ticker,
                            "setup": cand.get("setup", "THEME_CATALYST"),
                            "theme": cand.get("theme", ""),
                            "role": cand.get("role", ""),
                            "reason": cand.get("reason", "premarket_watcher 조건 충족"),
                            "confidence": 70,
                        }
                        save_watchlist(wl + [new_entry])
                        logger.info(f"[premarket_watcher] {ticker} watchlist 추가 (setup={new_entry['setup']})")

                    triggered.add(ticker)
                    _save_triggered(triggered)

                    try:
                        orch._telegram.notify(
                            f"⚡ *장초반 선진입 조건 충족* {name} ({ticker})\n"
                            f"{reason}\n"
                            f"테마: {cand.get('theme', '')} / {cand.get('setup', '')}\n"
                            f"intraday 즉시 트리거"
                        )
                    except Exception as e:
                        logger.warning(f"[premarket_watcher] 알림 실패: {e}")

                    logger.info(f"[premarket_watcher] {ticker} → intraday 즉시 실행")
                    orch.run_intraday_v3()

                finally:
                    fcntl.flock(lock, fcntl.LOCK_UN)
                    lock.close()

        except Exception as e:
            logger.warning(f"[premarket_watcher] {ticker} 체크 오류: {e}")


if __name__ == "__main__":
    main()

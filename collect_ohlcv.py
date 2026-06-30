#!/usr/bin/env python3
"""장 마감 후 전 종목 일봉 수집 (PM2 19:00 평일).

- 최초 실행(DB 비어있거나 데이터가 5일 이상 오래됨): 60일치 전체 수집 (full)
- 이후 매일: 당일 + 전일(안전 버퍼) 2일치만 추가 수집 (incremental)

키움 ka10081 연속조회 → data/ohlcv.db upsert.
rate limit: KIWOOM_MIN_INTERVAL_SECONDS (기본 0.35s) 자동 준수.
"""
from __future__ import annotations

import csv
import logging
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("mqk_ohlcv")

BASE = Path(__file__).parent
UNIVERSE = BASE / "data" / "universe.csv"

FULL_LIMIT = 60        # 최초 수집: 60영업일
INCREMENTAL_LIMIT = 2  # 이후 매일: 2일 (당일 + 전일 안전버퍼)
STALE_DAYS = 5         # 이 일수 이상 오래된 데이터면 full 재수집

# 랜덤 타임슬립: API 호출 간 불규칙한 간격으로 rate limit 회피
_JITTER_MIN = 0.05   # 매 호출 후 추가 최솟값(초)
_JITTER_MAX = 0.25   # 매 호출 후 추가 최댓값(초)
_BURST_EVERY = 50    # N종목마다 긴 휴식
_BURST_MIN = 1.0     # 긴 휴식 최솟값(초)
_BURST_MAX = 2.5     # 긴 휴식 최댓값(초)


def _is_incremental() -> bool:
    """DB에 최근 데이터가 있으면 True (incremental), 없거나 오래됐으면 False (full)."""
    from broker.ohlcv_store import get_max_date
    max_date = get_max_date()
    if not max_date:
        return False
    cutoff = (datetime.now() - timedelta(days=STALE_DAYS)).strftime("%Y%m%d")
    return max_date >= cutoff


def _collect_ticker(api, ticker: str, today: str, limit: int) -> list[dict]:
    from broker.kiwoom_api import KiwoomRateLimitError
    try:
        rows = api.daily_candles_paged(ticker, base_dt=today, limit=limit)
        return [{"ticker": ticker, **r} for r in rows]
    except KiwoomRateLimitError as e:
        logger.warning(f"[{ticker}] rate limit, 30s 대기 후 재시도: {e}")
        time.sleep(30)
        rows = api.daily_candles_paged(ticker, base_dt=today, limit=limit)
        return [{"ticker": ticker, **r} for r in rows]


def main() -> int:
    from broker.kiwoom_api import KiwoomApi
    from broker.ohlcv_store import init_db, upsert_rows

    api = KiwoomApi()
    if not api.available:
        logger.error("Kiwoom API 자격증명 미설정 — KIWOOM_APP_KEY / KIWOOM_SECRET_KEY 확인")
        return 1

    init_db()

    incremental = _is_incremental()
    limit = INCREMENTAL_LIMIT if incremental else FULL_LIMIT
    mode = "incremental" if incremental else "full"

    tickers: list[str] = []
    with open(UNIVERSE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = (row.get("ticker") or "").strip()
            if t:
                tickers.append(t)

    today = datetime.now().strftime("%Y%m%d")
    total = len(tickers)
    logger.info(f"수집 시작 [{mode}]: {total}종목 / {limit}영업일 / base_dt={today}")

    ok = fail = 0
    batch: list[dict] = []

    for i, ticker in enumerate(tickers, 1):
        try:
            rows = _collect_ticker(api, ticker, today, limit)
            if rows:
                batch.extend(rows)
                ok += 1
            else:
                logger.warning(f"[{ticker}] 빈 응답")
                fail += 1
        except Exception as e:
            logger.warning(f"[{ticker}] 실패: {e}")
            fail += 1

        # 매 호출 후 짧은 랜덤 지터 (API 클라이언트의 min_interval 위에 추가)
        time.sleep(random.uniform(_JITTER_MIN, _JITTER_MAX))

        # N종목마다 긴 휴식 — 연속 호출 패턴 차단
        if i % _BURST_EVERY == 0:
            burst_sleep = random.uniform(_BURST_MIN, _BURST_MAX)
            logger.debug(f"burst sleep {burst_sleep:.2f}s ({i}/{total})")
            time.sleep(burst_sleep)

        if len(batch) >= 5000 or i % 200 == 0:
            if batch:
                upsert_rows(batch)
                batch = []
            logger.info(f"진행: {i}/{total} ({i/total*100:.1f}%) ok={ok} fail={fail}")

    if batch:
        upsert_rows(batch)

    logger.info(f"완료 [{mode}]: ok={ok}, fail={fail}, 총 {total}종목")
    return 0 if fail < total * 0.1 else 1


if __name__ == "__main__":
    sys.exit(main())

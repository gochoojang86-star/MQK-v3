"""종목분석 도구 6개: get_ohlcv, get_realtime_price, get_intraday_candles, get_flow, get_news_stock, get_watchlist_intraday_snapshot

get_snapshot은 제거되었다 — get_ohlcv의 output1이 현재가+호가+밸류에이션을 포함한다.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

from broker.kiwoom_api import _abs_float, _abs_int
from broker.telegram_news import get_recent_news, search_recent_news
from codes.news_fetcher import NaverNewsFetcher
from market_intelligence.base import MILContext, ToolFailure

_NAVER_LOW_SIGNAL_PATTERNS = (
    "주가,",
    "주가 ",
    "장중",
    "상승률 상위",
    "하락률 상위",
    "상한가",
    "하한가",
    "증시 풍향계",
    "강세... 왜?",
    "강세…왜?",
    "급등",
)


def _is_low_signal_naver_article(title: str, summary: str) -> bool:
    haystack = f"{title} {summary}".strip().lower()
    return any(pattern.lower() in haystack for pattern in _NAVER_LOW_SIGNAL_PATTERNS)


def _rank_naver_articles(items: list) -> list:
    def key(item) -> tuple[int, str]:
        title = str(getattr(item, "title", "") or "")
        summary = str(getattr(item, "description", "") or "")
        return (
            1 if _is_low_signal_naver_article(title, summary) else 0,
            title,
        )

    return sorted(items, key=key)


def get_ohlcv(ctx: MILContext, phase: str, ticker: str, period: int = 60) -> dict:
    """국내주식기간별시세. output1=현재가/호가/밸류에이션, output2=OHLCV+권리락코드."""

    def fetch():
        end = datetime.now()
        start = end - timedelta(days=max(period * 3, 30))
        raw = ctx.kis_api.raw_get(
            "FHKST03010100",
            "domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker,
                "FID_INPUT_DATE_1": start.strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            },
        )
        out1 = raw.get("output1", {})
        candles = [
            {
                "date": row.get("stck_bsop_date"),
                "open": _to_float(row.get("stck_oprc")),
                "high": _to_float(row.get("stck_hgpr")),
                "low": _to_float(row.get("stck_lwpr")),
                "close": _to_float(row.get("stck_clpr")),
                "volume": _to_float(row.get("acml_vol")),
                "trading_value": _to_float(row.get("acml_tr_pbmn")),
                "rights_event_code": row.get("flng_cls_code"),
            }
            for row in raw.get("output2", [])[:period]
        ]
        return {
            "ticker": ticker,
            "current_price": _to_float(out1.get("stck_prpr")),
            "ask_price": _to_float(out1.get("askp")),
            "bid_price": _to_float(out1.get("bidp")),
            "per": _to_float(out1.get("per")),
            "eps": _to_float(out1.get("eps")),
            "pbr": _to_float(out1.get("pbr")),
            "market_cap": _to_float(out1.get("hts_avls")),
            "upper_limit": _to_float(out1.get("stck_mxpr")),
            "lower_limit": _to_float(out1.get("stck_llam")),
            "candles": candles,
        }

    return ctx.cached_call("get_ohlcv", phase, {"ticker": ticker, "period": period}, fetch)


def get_realtime_price(ctx: MILContext, phase: str, tickers: list[str]) -> dict:
    """관심종목(멀티종목) 시세조회. 최대 30종목 배치. 모의투자 미지원 (mode=real 고정)."""

    if len(tickers) > 30:
        raise ToolFailure("get_realtime_price: 최대 30종목까지만 조회 가능")

    def fetch():
        try:
            params = {"FID_COND_MRKT_DIV_CODE_1": "J"}
            for i, ticker in enumerate(tickers, start=1):
                params[f"FID_INPUT_ISCD_{i}"] = ticker
                params[f"FID_COND_MRKT_DIV_CODE_{i}"] = "J"
            raw = ctx.kis_api.raw_get(
                "FHKST11300006",
                "domestic-stock/v1/quotations/intstock-multprice",
                params,
                mode="real",
            )
            prices = [
                {
                    "ticker": row.get("inter_shrn_iscd"),
                    "price": _to_float(row.get("inter2_prpr")),
                    "change_pct": _to_float(row.get("prdy_ctrt")),
                    "volume": _to_float(row.get("acml_vol")),
                    "source": "KIS",
                }
                for row in raw.get("output", [])
            ]
            return {"prices": prices, "source": "KIS"}
        except Exception as kis_exc:
            if not (ctx.kiwoom_api and ctx.kiwoom_api.available):
                raise kis_exc

            fallback_prices = []
            for ticker in tickers:
                intraday = _fetch_intraday_candles_raw(ctx, ticker)
                candles = intraday.get("candles", []) or []
                latest = candles[-1] if candles else {}
                fallback_prices.append(
                    {
                        "ticker": ticker,
                        "price": _to_float(latest.get("close")),
                        "change_pct": 0.0,
                        "volume": _to_float(latest.get("volume")),
                        "source": "KIWOOM_INTRADAY_REFERENCE",
                    }
                )

            return {
                "prices": fallback_prices,
                "source": "KIWOOM_INTRADAY_REFERENCE",
                "reference_only": True,
                "missing_fields": ["change_pct"],
            }

    return ctx.cached_call("get_realtime_price", phase, {"tickers": tickers}, fetch)


def _fetch_intraday_candles_raw(ctx: MILContext, ticker: str, full_day: bool = False) -> dict:
    import logging
    logger = logging.getLogger("mqk_v3")

    # 1. 키움 API 우선 — full_day=True면 연속조회로 장 전체, 아니면 단일 호출(~30봉)
    if ctx.kiwoom_api and ctx.kiwoom_api.available:
        try:
            if full_day:
                logger.debug(f"[_fetch_intraday_candles_raw] 키움 full_day: {ticker}")
                candles = ctx.kiwoom_api.intraday_candles_full_day(ticker)
                source = "KIWOOM_FULL"
            else:
                logger.debug(f"[_fetch_intraday_candles_raw] 키움 단일: {ticker}")
                raw = ctx.kiwoom_api.intraday_candles(ticker)
                candles_data = raw.get("stk_min_pole_chart_qry", [])
                today_str = datetime.now().strftime("%Y%m%d")
                # 키움 ka10080은 가격을 전일/직전 대비 등락 방향의 부호(+/-)를 붙여
                # 반환한다 — 문자열의 '-'는 음수가 아니라 "하락 표시"다. _to_float를
                # 그대로 쓰면 하락 분봉의 OHLC가 마이너스 가격으로 파싱된다
                # (2026-07-03 000660 09:19~09:20 분봉 실사고, intraday_candles_full_day는
                # 이미 _abs_float로 처리 중이었으나 이 단일조회 경로만 누락돼 있었음).
                candles = [
                    {
                        "time": (row.get("cntr_tm") or "")[8:12],
                        "open": _abs_float(row.get("open_pric")),
                        "high": _abs_float(row.get("high_pric")),
                        "low": _abs_float(row.get("low_pric")),
                        "close": _abs_float(row.get("cur_prc")),
                        "volume": _abs_int(row.get("trde_qty")),
                    }
                    for row in candles_data
                    if (row.get("cntr_tm") or "")[:8] == today_str
                ]
                source = "KIWOOM"
            if candles:
                candles.sort(key=lambda c: c["time"] or "")
                logger.info(f"[_fetch_intraday_candles_raw] 키움 성공({source}): {ticker}, {len(candles)}개 분봉")
                return {"ticker": ticker, "candles": candles, "source": source}
            logger.warning(f"[_fetch_intraday_candles_raw] 키움 빈 응답: {ticker}")
        except Exception as e:
            logger.warning(f"[_fetch_intraday_candles_raw] 키움 실패: {ticker}, {str(e)[:100]}")

    # 2. KIS 폴백 (최근 ~30봉)
    try:
        logger.debug(f"[_fetch_intraday_candles_raw] KIS 폴백: {ticker}")
        raw = ctx.kis_api.raw_get(
            "FHKST03010200",
            "domestic-stock/v1/quotations/inquire-time-itemchartprice",
            {
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker,
                "FID_INPUT_HOUR_1": datetime.now().strftime("%H%M%S"),
                "FID_PW_DATA_INCU_YN": "N",
            },
        )
        candles_data = raw.get("output2", [])
        if candles_data:
            candles = [
                {
                    "time": row.get("stck_cntg_hour"),
                    "open": _to_float(row.get("stck_oprc")),
                    "high": _to_float(row.get("stck_hgpr")),
                    "low": _to_float(row.get("stck_lwpr")),
                    "close": _to_float(row.get("stck_prpr")),
                    "volume": _to_float(row.get("cntg_vol")),
                }
                for row in candles_data
            ]
            candles.sort(key=lambda c: c["time"] or "")
            logger.info(f"[_fetch_intraday_candles_raw] KIS 폴백 성공: {ticker}, {len(candles)}개 분봉")
            return {"ticker": ticker, "candles": candles, "source": "KIS"}
        logger.warning(f"[_fetch_intraday_candles_raw] KIS 폴백 빈 응답: {ticker}")
    except Exception as e:
        logger.warning(f"[_fetch_intraday_candles_raw] KIS 폴백 실패: {ticker}, {str(e)[:100]}")

    logger.error(f"[_fetch_intraday_candles_raw] 모든 소스 실패: {ticker}")
    return {"ticker": ticker, "candles": [], "source": "NONE"}


def get_intraday_candles(ctx: MILContext, phase: str, ticker: str, force_refresh: bool = False) -> dict:
    """주식당일분봉조회 — force_refresh=True 시 키움 연속조회로 장 전체 분봉 반환."""

    def fetch():
        return _fetch_intraday_candles_raw(ctx, ticker, full_day=force_refresh)

    return ctx.cached_call(
        "get_intraday_candles",
        phase,
        {"ticker": ticker},
        fetch,
        force_refresh=force_refresh,
    )


def get_flow(ctx: MILContext, phase: str, ticker: str) -> dict:
    """종목별 투자자매매동향(일별) - 외국인/기관/개인/투신/사모/은행/보험/기금 순매수 수량.

    응답은 output2(일별 리스트, 최신일 우선). 당일 row는 장 종료 후 확정된다.
    """

    def fetch():
        # 당일 기준 조회는 장 종료 후에만 가능 (장중엔 rt_cd=2/빈 결과 — D1 확인).
        # 오늘부터 최대 4일 거슬러가며 데이터가 있는 기준일을 찾는다.
        raw = {}
        for days_back in range(5):
            base_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
            raw = ctx.kis_api.raw_get(
                "FHPTJ04160001",
                "domestic-stock/v1/quotations/investor-trade-by-stock-daily",
                {
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": ticker,
                    "FID_INPUT_DATE_1": base_date,
                    "FID_ORG_ADJ_PRC": "",
                    "FID_ETC_CLS_CODE": "1",
                },
            )
            if raw.get("output2"):
                break
        days = [
            {
                "date": row.get("stck_bsop_date"),
                "close": _to_float(row.get("stck_clpr")),
                "foreign_net_qty": _to_float(row.get("frgn_ntby_qty")),
                "institution_net_qty": _to_float(row.get("orgn_ntby_qty")),
                "individual_net_qty": _to_float(row.get("prsn_ntby_qty")),
                "trust_net_qty": _to_float(row.get("ivtr_ntby_qty")),
                "private_fund_net_qty": _to_float(row.get("pe_fund_ntby_vol")),
                "bank_net_qty": _to_float(row.get("bank_ntby_qty")),
                "insurance_net_qty": _to_float(row.get("insu_ntby_qty")),
                "pension_net_qty": _to_float(row.get("fund_ntby_qty")),
            }
            for row in raw.get("output2", [])
        ]
        return {"ticker": ticker, "days": days}

    return ctx.cached_call("get_flow", phase, {"ticker": ticker}, fetch)


def get_news_stock(ctx: MILContext, phase: str, ticker: str) -> dict:
    """ticker 필터 뉴스 2종 통합: 텔레그램 속보 + 네이버 뉴스 검색.

    텔레그램(최근 2시간)은 속보성, 네이버(종목명 검색)는 summary 중심의 촉매 맥락
    보강용이다. KIS 뉴스는 종목 직접성보다 랭킹/시황 잡음이 많아 제외한다.
    각 소스는 개별 격리 — 실패는 missing_fields에 기록하고 0건으로 해석하지 않는다.
    """

    def fetch():
        result: dict = {"ticker": ticker}
        missing: list[str] = []

        # 텔레그램 속보 (수집기 mqk-telegram-news가 sqlite에 적재)
        try:
            result["telegram_headlines"] = [
                {
                    "title": n.get("title"),
                    "summary": str(n.get("content") or "")[:240],
                    "sentiment": n.get("sentiment"),
                    "source": n.get("source"),
                    "date": n.get("date"),
                }
                for n in get_recent_news(ticker=ticker, hours=2)[:10]
            ]
        except Exception:
            result["telegram_headlines"] = []
            missing.append("telegram_headlines")

        # 네이버 뉴스 검색 (종목명 기준 — 촉매 맥락)
        try:
            stock_name = ""
            try:
                stock_name = (ctx.kis_api.get_snapshot(ticker) or {}).get("name", "")
            except Exception:
                pass
            if stock_name:
                items = _rank_naver_articles(NaverNewsFetcher().search(stock_name, display=8))
                result["naver_headlines"] = [
                    {"title": n.title, "summary": n.description[:120],
                     "date": n.pub_date, "url": n.url}
                    for n in items[:5]
                ]
                # generic headlines는 now 네이버 summary 중심 결과를 alias한다.
                result["headlines"] = result["naver_headlines"]
            else:
                result["headlines"] = []
                result["naver_headlines"] = []
                missing.append("naver_headlines")
        except Exception:
            result["headlines"] = []
            result["naver_headlines"] = []
            missing.append("naver_headlines")

        if missing:
            result["missing_fields"] = missing
        return result

    return ctx.cached_call("get_news_stock", phase, {"ticker": ticker}, fetch)


def search_telegram_news(ctx: MILContext, phase: str, query: str, hours: int = 72, limit: int = 20) -> dict:
    """텔레그램 속보를 자유 질의로 검색한다.

    정치테마/인맥/정책 테마처럼 종목명 자체보다 시장이 어떤 이슈와 엮어 인식하는지가
    중요한 경우에 사용한다.
    """

    def fetch():
        return {
            "query": query,
            "hours": int(hours),
            "results": [
                {
                    "ticker": row.get("ticker", ""),
                    "title": row.get("title", ""),
                    "content": row.get("content", ""),
                    "sentiment": row.get("sentiment", ""),
                    "score": row.get("score", 0.0),
                    "source": row.get("source", ""),
                    "url": row.get("url", ""),
                    "date": row.get("date", ""),
                }
                for row in search_recent_news(query=query, hours=hours, limit=limit)
            ],
        }

    return ctx.cached_call(
        "search_telegram_news",
        phase,
        {"query": query, "hours": int(hours), "limit": int(limit)},
        fetch,
    )


def get_watchlist_intraday_snapshot(ctx: MILContext, phase: str, tickers: list[str]) -> dict:
    """watchlist 장중 판단용 번들 스냅샷.

    가격/등락률/거래량은 멀티시세로 배치 조회하고, 최신 분봉/상태만 종목별로 보강한다.
    개별 종목 실패가 전체 번들을 깨지 않도록 missing_fields에 격리한다.
    """

    def fetch():
        normalized = _normalize_tickers(tickers)
        if not normalized:
            return {"tickers": []}

        batched_prices: dict[str, dict] = {}
        try:
            price_rows = get_realtime_price(ctx, phase, normalized).get("prices", [])
            batched_prices = {str(row.get("ticker") or "").strip(): row for row in price_rows}
        except Exception:
            batched_prices = {}

        from market_intelligence.risk_filter import get_stock_status

        rows: list[dict] = []
        for ticker in normalized:
            item: dict = {"ticker": ticker}
            missing_fields: list[str] = []

            price_row = batched_prices.get(ticker, {})
            item["price"] = _to_float(price_row.get("price"))
            item["change_pct"] = _to_float(price_row.get("change_pct"))
            item["volume"] = _to_float(price_row.get("volume"))
            if not price_row:
                missing_fields.append("realtime_price")

            try:
                snap = ctx.kis_api.get_snapshot(ticker) or {}
                item["name"] = snap.get("name") or ticker
                item["trading_value"] = _to_float(snap.get("trading_value") or snap.get("acml_tr_pbmn"))
                item["market_cap"] = _coerce_market_cap(snap)
                # 당일 시가/고가/저가 — LIMIT_UP_PULLBACK 눌림% 계산에 사용
                day_open = _to_float(snap.get("stck_oprc"))
                day_high = _to_float(snap.get("stck_hgpr"))
                day_low = _to_float(snap.get("stck_lwpr"))
                if day_open:
                    item["day_open"] = day_open
                if day_high:
                    item["day_high"] = day_high
                if day_low:
                    item["day_low"] = day_low
            except Exception:
                item["name"] = ticker
                item["trading_value"] = 0.0
                item["market_cap"] = 0.0
                missing_fields.append("snapshot")

            try:
                from broker.ohlcv_store import get_prev_day as _get_prev_day
                today_str = datetime.now().strftime("%Y%m%d")
                prev = _get_prev_day(ticker, today_str)
                if prev:
                    item["prev_close"] = prev["close"]
                    item["prev_high"] = prev["high"]
                    item["prev_low"] = prev["low"]
                    item["prev_open"] = prev["open"]
            except Exception:
                pass

            try:
                intraday = _fetch_intraday_candles_raw(ctx, ticker)
                candles = intraday.get("candles", [])
                item["candle_count"] = len(candles)
                item["latest_candle"] = candles[-1] if candles else None
                item["recent_candles"] = candles[-10:] if candles else []
                item["intraday_trend"] = _infer_intraday_trend(candles)
                if item.get("price", 0.0) <= 0 and item["latest_candle"]:
                    item["price"] = _to_float(item["latest_candle"].get("close"))
                    item["price_reference_source"] = "intraday_candle_reference"
            except Exception:
                item["candle_count"] = 0
                item["latest_candle"] = None
                item["recent_candles"] = []
                item["intraday_trend"] = "unknown"
                missing_fields.append("intraday_candles")

            try:
                ohlcv = get_ohlcv(ctx, phase, ticker, period=25)
                item["resistance"] = _compute_resistance_facts(
                    ohlcv.get("candles", []), item.get("price", 0.0)
                )
            except Exception:
                item["resistance"] = _compute_resistance_facts([], 0.0)
                missing_fields.append("resistance")

            try:
                status = get_stock_status(ctx, phase, ticker)
                item["status"] = {
                    "trading_halted": bool(status.get("trading_halted")),
                    "administrative_issue": bool(status.get("administrative_issue")),
                    "is_limit_up": bool(status.get("is_limit_up")),
                    "is_limit_down": bool(status.get("is_limit_down")),
                    "is_vi": bool(status.get("is_vi")),
                }
            except Exception:
                item["status"] = {}
                missing_fields.append("status")

            if missing_fields:
                item["missing_fields"] = missing_fields
            rows.append(item)

        thin_candle_tickers = [
            r["ticker"] for r in rows if r.get("candle_count", 0) < 10
        ]
        guidance: dict = {}
        if thin_candle_tickers:
            guidance = {
                "thin_candles": thin_candle_tickers,
                "hint": (
                    f"{thin_candle_tickers} 종목은 분봉이 10개 미만입니다. "
                    "눌림/반등 패턴 확인이 필요하면 "
                    "get_intraday_candles(ticker, force_refresh=true)를 "
                    "추가 호출한 뒤 판단하십시오."
                ),
            }

        result: dict = {"tickers": rows}
        if guidance:
            result["_guidance"] = guidance
        return result

    return ctx.cached_call(
        "get_watchlist_intraday_snapshot",
        phase,
        {"tickers": _normalize_tickers(tickers)},
        fetch,
    )


def get_fundamentals(ctx: MILContext, phase: str, ticker: str) -> dict:
    """SEPA 펀더멘털 스크리닝용 재무 데이터 4종 조합.

    재무비율/손익계산서/대차대조표/종목투자의견 각각 개별 try/except 처리하여
    한 API 실패가 다른 섹션에 영향을 주지 않는다 (결측은 missing_fields에 기록,
    0으로 해석하지 않는다).

    손익계산서/대차대조표 단위는 억원(100mln KRW) — 필드명에 _100mln 접미사로 명시.
    """

    def fetch():
        result = {"ticker": ticker}
        missing_fields: list[str] = []

        common_params = {
            "FID_DIV_CLS_CODE": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker,
        }

        try:
            raw = ctx.kis_api.raw_get(
                "FHKST66430300",
                "domestic-stock/v1/finance/financial-ratio",
                common_params,
            )
            result["financial_ratios"] = [
                {
                    "period": row.get("stac_yymm"),
                    "revenue_growth_rate_pct": _to_float(row.get("grs")),
                    "operating_profit_growth_rate_pct": _to_float(row.get("bsop_prfi_inrt")),
                    "net_income_growth_rate_pct": _to_float(row.get("ntin_inrt")),
                    "roe_pct": _to_float(row.get("roe_val")),
                    "eps": _to_float(row.get("eps")),
                    "bps": _to_float(row.get("bps")),
                    "debt_ratio_pct": _to_float(row.get("lblt_rate")),
                }
                for row in raw.get("output", [])[:4]
            ]
        except Exception:
            result["financial_ratios"] = []
            missing_fields.append("financial_ratios")

        try:
            raw = ctx.kis_api.raw_get(
                "FHKST66430200",
                "domestic-stock/v1/finance/income-statement",
                common_params,
            )
            result["income_statements"] = [
                {
                    "period": row.get("stac_yymm"),
                    "revenue_100mln": _to_float(row.get("sale_account")),
                    "operating_profit_100mln": _to_float(row.get("op_prfi")),
                    "net_income_100mln": _to_float(row.get("thtr_ntin")),
                }
                for row in raw.get("output", [])[:4]
            ]
        except Exception:
            result["income_statements"] = []
            missing_fields.append("income_statements")

        try:
            raw = ctx.kis_api.raw_get(
                "FHKST66430100",
                "domestic-stock/v1/finance/balance-sheet",
                common_params,
            )
            result["balance_sheets"] = [
                {
                    "period": row.get("stac_yymm"),
                    "total_assets_100mln": _to_float(row.get("total_aset")),
                    "total_liabilities_100mln": _to_float(row.get("total_lblt")),
                    "total_equity_100mln": _to_float(row.get("total_cptl")),
                }
                for row in raw.get("output", [])[:4]
            ]
        except Exception:
            result["balance_sheets"] = []
            missing_fields.append("balance_sheets")

        try:
            today = datetime.now()
            six_months_ago = today - timedelta(days=180)
            raw = ctx.kis_api.raw_get(
                "FHKST663300C0",
                "domestic-stock/v1/quotations/invest-opinion",
                {
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_COND_SCR_DIV_CODE": "16633",
                    "FID_INPUT_ISCD": ticker,
                    "FID_INPUT_DATE_1": "00" + six_months_ago.strftime("%Y%m%d"),
                    "FID_INPUT_DATE_2": "00" + today.strftime("%Y%m%d"),
                },
            )
            result["analyst_opinions"] = [
                {
                    "date": row.get("stck_bsop_date"),
                    "opinion": row.get("invt_opnn"),
                    "firm": row.get("mbcr_name"),
                    "target_price": _to_float(row.get("hts_goal_prc")),
                }
                for row in raw.get("output", [])[:10]
            ]
        except Exception:
            result["analyst_opinions"] = []
            missing_fields.append("analyst_opinions")

        if missing_fields:
            result["missing_fields"] = missing_fields

        return result

    return ctx.cached_call("get_fundamentals", phase, {"ticker": ticker}, fetch)


def get_intraday_institutional_flow(ctx: MILContext, phase: str, ticker: str) -> dict:
    """KIS HHPTJ04160200 종목별 외인·기관 장중 추정 가집계.

    bsop_hour_gb: 1=09시, 2=10시, 3=11시, 4=12~13시, 5=오후(최신).
    frgn_fake_ntby_qty = 외인 추정 순매수 수량 (양수=매수, 음수=매도).
    orgn_fake_ntby_qty = 기관 추정 순매수 수량.
    sum_fake_ntby_qty = 외인+기관 합계.
    모의투자 미지원 — mode=real 고정.
    """

    def fetch():
        raw = ctx.kis_api.raw_get(
            "HHPTJ04160200",
            "domestic-stock/v1/quotations/investor-trend-estimate",
            {"MKSC_SHRN_ISCD": ticker},
            mode="real",
        )
        rows = raw.get("output2", []) or []
        periods = [
            {
                "period": row.get("bsop_hour_gb"),
                "foreign_net_qty": _to_float(row.get("frgn_fake_ntby_qty")),
                "institution_net_qty": _to_float(row.get("orgn_fake_ntby_qty")),
                "total_net_qty": _to_float(row.get("sum_fake_ntby_qty")),
            }
            for row in rows
        ]
        # 최신 기간 (bsop_hour_gb=5)을 첫 번째로 노출
        periods.sort(key=lambda p: -(int(p["period"]) if str(p["period"]).isdigit() else 0))
        return {"ticker": ticker, "periods": periods}

    return ctx.cached_call("get_intraday_institutional_flow", phase, {"ticker": ticker}, fetch)


def get_orderbook(ctx: MILContext, phase: str, ticker: str) -> dict:
    """매수/매도 10호가 잔량 + 순매수잔량 비율.

    SOUL 핵심 판단 근거: "호가창의 체결 속도와 거래대금의 폭발력".
    bid_ask_ratio > 1.0 이면 매수잔량이 매도잔량보다 많음(매수 우세).
    net_bid_qty 양수이면 순매수 호가 잔량 우세.
    """

    def fetch():
        raw = ctx.kis_api.raw_get(
            "FHKST01010200",
            "domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker,
            },
        )
        out1 = raw.get("output1", {}) or {}

        ask = [
            {
                "price": _to_float(out1.get(f"askp{i}")),
                "qty": _to_float(out1.get(f"askp_rsqn{i}")),
                "qty_change": _to_float(out1.get(f"askp_rsqn_icdc{i}")),
            }
            for i in range(1, 11)
        ]
        bid = [
            {
                "price": _to_float(out1.get(f"bidp{i}")),
                "qty": _to_float(out1.get(f"bidp_rsqn{i}")),
                "qty_change": _to_float(out1.get(f"bidp_rsqn_icdc{i}")),
            }
            for i in range(1, 11)
        ]
        total_ask = _to_float(out1.get("total_askp_rsqn"))
        total_bid = _to_float(out1.get("total_bidp_rsqn"))
        net_bid = _to_float(out1.get("ntby_aspr_rsqn"))

        return {
            "ticker": ticker,
            "ask": ask,
            "bid": bid,
            "total_ask_qty": total_ask,
            "total_bid_qty": total_bid,
            "bid_ask_ratio": round(total_bid / total_ask, 3) if total_ask > 0 else None,
            "net_bid_qty": net_bid,
        }

    return ctx.cached_call("get_orderbook", phase, {"ticker": ticker}, fetch)


def _to_float(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


_ROUND_FIGURE_TIERS = [
    (10_000, 1_000),
    (100_000, 5_000),
    (1_000_000, 10_000),
]
_ROUND_FIGURE_DEFAULT_UNIT = 100_000


def _round_figure_unit(price: float) -> float:
    """가격대별 라운드 피겨 단위. 1만원 미만=1,000원, ~10만원=5,000원, ~100만원=10,000원, 그 이상=100,000원."""
    for threshold, unit in _ROUND_FIGURE_TIERS:
        if price < threshold:
            return unit
    return _ROUND_FIGURE_DEFAULT_UNIT


def _compute_resistance_facts(candles: list[dict], current_price: float) -> dict:
    """일봉 candle 리스트(get_ohlcv의 candles, 최근이 마지막)와 현재가로 저항선 fact를 계산한다.

    candles의 마지막 항목은 장중이면 당일(미마감) 봉이다. 20일 고점 계산에서는
    제외하고, 그 open을 당일 시가로 사용해 라운드피겨 돌파 여부를 판정한다.
    모든 계산은 여기서 끝낸다 — LLM은 이 결과값만 읽는다.
    """
    empty = {
        "resistance_20d_high": 0.0,
        "pct_from_resistance": 0.0,
        "round_figure_price": 0.0,
        "pct_from_round_figure": 0.0,
        "is_breakout_20d_high": False,
        "is_breakout_round_figure": False,
        "volume_vs_5d_avg_ratio": 0.0,
    }
    if current_price <= 0 or not candles:
        return empty

    today = candles[-1]
    prior_candles = candles[:-1]

    last_20 = prior_candles[-20:]
    resistance_20d_high = max((c.get("high", 0.0) for c in last_20), default=0.0)
    pct_from_resistance = (
        round((current_price - resistance_20d_high) / resistance_20d_high * 100, 2)
        if resistance_20d_high > 0 else 0.0
    )
    is_breakout_20d_high = resistance_20d_high > 0 and current_price > resistance_20d_high

    today_open = today.get("open", 0.0) or 0.0
    unit = _round_figure_unit(today_open if today_open > 0 else current_price)
    round_figure_price = math.ceil(today_open / unit) * unit if today_open > 0 else 0.0
    pct_from_round_figure = (
        round((current_price - round_figure_price) / round_figure_price * 100, 2)
        if round_figure_price > 0 else 0.0
    )
    # today_open이 라운드 피겨와 정확히 같으면(이미 그 레벨에서 시작) 이 세션 안에서는
    # "돌파"가 아니다 — 장 시작 전에 이미 그 레벨을 확보한 것으로 본다. 의도된 동작.
    is_breakout_round_figure = (
        round_figure_price > 0
        and today_open < round_figure_price
        and current_price >= round_figure_price
    )

    last_5 = prior_candles[-5:]
    avg_5d_trading_value = (
        sum(c.get("trading_value", 0.0) for c in last_5) / len(last_5)
        if last_5 else 0.0
    )
    today_trading_value = today.get("trading_value", 0.0) or 0.0
    volume_vs_5d_avg_ratio = (
        round(today_trading_value / avg_5d_trading_value, 2)
        if avg_5d_trading_value > 0 else 0.0
    )

    return {
        "resistance_20d_high": resistance_20d_high,
        "pct_from_resistance": pct_from_resistance,
        "round_figure_price": round_figure_price,
        "pct_from_round_figure": pct_from_round_figure,
        "is_breakout_20d_high": is_breakout_20d_high,
        "is_breakout_round_figure": is_breakout_round_figure,
        "volume_vs_5d_avg_ratio": volume_vs_5d_avg_ratio,
    }


def _normalize_tickers(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values[:30]:
        ticker = str(raw).strip()
        if len(ticker) != 6 or not ticker.isdigit():
            continue
        if ticker in seen:
            continue
        seen.add(ticker)
        normalized.append(ticker)
    return normalized


def _infer_intraday_trend(candles: list[dict]) -> str:
    if len(candles) < 2:
        return "unknown"
    first = _to_float(candles[0].get("close"))
    last = _to_float(candles[-1].get("close"))
    if first <= 0 or last <= 0:
        return "unknown"
    diff_pct = (last - first) / first * 100
    if diff_pct >= 0.7:
        return "up"
    if diff_pct <= -0.7:
        return "down"
    return "flat"


def _aggregate_intraday_value_bars(candles: list[dict], interval_minutes: int = 10) -> list[dict]:
    """정규화된 분봉을 interval_minutes 단위 거래대금 바로 합친다."""
    buckets: dict[str, dict] = {}
    for candle in candles:
        raw_time = str(candle.get("time") or "").strip()
        if len(raw_time) < 4 or not raw_time[:4].isdigit():
            continue
        hour = int(raw_time[:2])
        minute = int(raw_time[2:4])
        bucket_minute = (minute // interval_minutes) * interval_minutes
        bucket_key = f"{hour:02d}{bucket_minute:02d}"

        price = _to_float(candle.get("close")) or _to_float(candle.get("open"))
        volume = _to_float(candle.get("volume"))
        trading_value = price * volume if price > 0 and volume > 0 else 0.0

        bucket = buckets.setdefault(bucket_key, {"time": bucket_key, "trading_value": 0.0})
        bucket["trading_value"] += trading_value

    return [buckets[key] for key in sorted(buckets.keys())]


def _coerce_market_cap(row: dict) -> float:
    market_cap = _to_float(row.get("market_cap"))
    if market_cap > 0:
        return market_cap

    hts_avls = _to_float(row.get("hts_avls"))
    if hts_avls > 0:
        return hts_avls * 100_000_000

    return 0.0


def get_intraday_volume_trend(ctx: MILContext, phase: str, ticker: str) -> dict:
    """10분봉 기준 거래대금 트렌드 분석 — v4 세력 이탈 감지 핵심 도구.

    최근 5봉 평균 거래대금 vs 직전 5봉 평균을 비교한다.
    decline_pct <= -40% 이면 signal="VOLUME_DRY" (세력 이탈 신호).
    """

    def fetch():
        intraday = _fetch_intraday_candles_raw(ctx, ticker, full_day=True)
        candles = intraday.get("candles", []) or []
        value_bars = _aggregate_intraday_value_bars(candles, interval_minutes=10)

        if len(value_bars) < 10:
            return {
                "ticker": ticker,
                "trend": "STABLE",
                "recent_avg_krw": 0,
                "prev_avg_krw": 0,
                "decline_pct": 0.0,
                "signal": None,
                "source": intraday.get("source", "NONE"),
                "bar_count": len(value_bars),
            }

        vols = [float(bar["trading_value"]) for bar in value_bars[-10:]]
        prev_avg = sum(vols[:5]) / 5
        recent_avg = sum(vols[5:10]) / 5
        decline_pct = ((recent_avg - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0.0

        if decline_pct <= -40.0:
            trend = "DECLINING"
            signal = "VOLUME_DRY"
        elif decline_pct <= -10.0:
            trend = "DECLINING"
            signal = None
        elif decline_pct >= 20.0:
            trend = "INCREASING"
            signal = None
        else:
            trend = "STABLE"
            signal = None

        return {
            "ticker": ticker,
            "trend": trend,
            "recent_avg_krw": recent_avg,
            "prev_avg_krw": prev_avg,
            "decline_pct": round(decline_pct, 1),
            "signal": signal,
            "source": intraday.get("source", "NONE"),
            "bar_count": len(value_bars),
        }

    return ctx.cached_call("get_intraday_volume_trend", phase, {"ticker": ticker}, fetch)

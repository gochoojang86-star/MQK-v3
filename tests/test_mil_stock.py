"""market_intelligence/stock.py 테스트"""
from market_intelligence.base import MILContext
from market_intelligence.stock import (
    get_ohlcv,
    get_realtime_price,
    get_intraday_candles,
    get_flow,
    get_news_stock,
    search_telegram_news,
    get_fundamentals,
    get_watchlist_intraday_snapshot,
)


class StubKisApi:
    def __init__(self, raw_responses=None):
        self._raw_responses = raw_responses or {}
        self.raw_get_calls = []

    def raw_get(self, tr_id, path, params, mode=None):
        self.raw_get_calls.append((tr_id, path, params, mode))
        return self._raw_responses[tr_id]

    def get_snapshot(self, ticker):
        return {"name": f"종목{ticker}", "trading_value": "1000000000", "market_cap": "5000000000000"}


def make_ctx(**kwargs):
    return MILContext(kis_api=StubKisApi(**kwargs))


def test_get_ohlcv_returns_output1_valuation_and_output2_candles():
    ctx = make_ctx(
        raw_responses={
            "FHKST03010100": {
                "output1": {
                    "stck_prpr": "70000", "askp": "70100", "bidp": "69900",
                    "per": "12.5", "eps": "5600", "pbr": "1.2",
                    "hts_avls": "420000000000000",
                    "stck_mxpr": "91000", "stck_llam": "49000",
                },
                "output2": [
                    {"stck_bsop_date": "20260609", "stck_oprc": "69500", "stck_hgpr": "70200",
                     "stck_lwpr": "69300", "stck_clpr": "70000", "acml_vol": "1000000",
                     "acml_tr_pbmn": "70000000000", "flng_cls_code": "00"},
                ],
            },
        },
    )
    result = get_ohlcv(ctx, "SCAN", ticker="005930", period=60)
    assert result["current_price"] == 70000.0
    assert result["per"] == 12.5
    assert result["candles"][0]["close"] == 70000.0
    assert result["candles"][0]["rights_event_code"] == "00"


def test_get_realtime_price_batches_tickers():
    ctx = make_ctx(
        raw_responses={
            "FHKST11300006": {
                "output": [
                    {"inter_shrn_iscd": "005930", "inter2_prpr": "70000", "prdy_ctrt": "1.0", "acml_vol": "100"},
                    {"inter_shrn_iscd": "000660", "inter2_prpr": "180000", "prdy_ctrt": "5.0", "acml_vol": "200"},
                ],
            },
        },
    )
    result = get_realtime_price(ctx, "INTRADAY", tickers=["005930", "000660"])
    assert result["prices"][0]["ticker"] == "005930"
    assert result["prices"][1]["price"] == 180000.0


def test_get_realtime_price_rejects_more_than_30_tickers():
    import pytest
    from market_intelligence.base import ToolFailure

    ctx = make_ctx(raw_responses={})
    with pytest.raises(ToolFailure):
        get_realtime_price(ctx, "INTRADAY", tickers=[f"{i:06d}" for i in range(31)])


def test_get_intraday_candles_parses_minute_bars():
    ctx = make_ctx(
        raw_responses={
            "FHKST03010200": {
                "output2": [
                    {"stck_cntg_hour": "093000", "stck_oprc": "69800", "stck_hgpr": "70000",
                     "stck_lwpr": "69700", "stck_prpr": "69900", "cntg_vol": "5000"},
                ],
            },
        },
    )
    result = get_intraday_candles(ctx, "INTRADAY", ticker="005930")
    assert result["candles"][0]["close"] == 69900.0


class StubKiwoomApi:
    """intraday_candles(ka10080)가 부호 포함 가격 문자열을 돌려주는 상황을 흉내낸다."""

    available = True

    def __init__(self, rows):
        self._rows = rows

    def intraday_candles(self, ticker: str, tic_scope: str = "1") -> dict:
        return {"stk_min_pole_chart_qry": self._rows}


def test_get_intraday_candles_strips_kiwoom_direction_sign_from_price():
    """2026-07-03 실사고: 000660 09:19~09:20 분봉이 open/low/close에 '-' 부호가 붙어
    (예: '-2186000') LLM에게 마이너스 가격으로 전달됐다. 키움 ka10080은 전일/직전
    대비 등락 방향을 가격 문자열 부호로 표시하므로(예: intraday_candles_full_day가
    이미 _abs_float로 처리 중), 단일조회 경로도 절댓값으로 정규화해야 한다."""
    ctx = make_ctx()
    ctx.kiwoom_api = StubKiwoomApi(rows=[
        {"cntr_tm": f"{datetime_today()}091900", "open_pric": "2192000", "high_pric": "2195000",
         "low_pric": "-2179000", "cur_prc": "-2186000", "trde_qty": "35198"},
        {"cntr_tm": f"{datetime_today()}092000", "open_pric": "-2186000", "high_pric": "2193000",
         "low_pric": "-2183000", "cur_prc": "2192000", "trde_qty": "14111"},
    ])

    result = get_intraday_candles(ctx, "INTRADAY", ticker="000660")

    for candle in result["candles"]:
        assert candle["open"] > 0
        assert candle["high"] > 0
        assert candle["low"] > 0
        assert candle["close"] > 0
    assert result["candles"][0]["low"] == 2179000.0
    assert result["candles"][0]["close"] == 2186000.0
    assert result["candles"][1]["open"] == 2186000.0
    assert result["candles"][1]["low"] == 2183000.0


def datetime_today() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")


def test_get_intraday_candles_force_refresh_bypasses_cache():
    ctx = make_ctx(
        raw_responses={
            "FHKST03010200": {
                "output2": [
                    {"stck_cntg_hour": "093000", "stck_oprc": "69800", "stck_hgpr": "70000",
                     "stck_lwpr": "69700", "stck_prpr": "69900", "cntg_vol": "5000"},
                ],
            },
        },
    )

    get_intraday_candles(ctx, "INTRADAY", ticker="005930")
    get_intraday_candles(ctx, "INTRADAY", ticker="005930", force_refresh=True)

    assert len(ctx.kis_api.raw_get_calls) == 2


def test_get_flow_parses_investor_breakdown():
    ctx = make_ctx(
        raw_responses={
            "FHPTJ04160001": {
                "output2": [
                    {"stck_bsop_date": "20260609", "stck_clpr": "70000",
                     "frgn_ntby_qty": "-10000", "orgn_ntby_qty": "5000",
                     "prsn_ntby_qty": "5000", "ivtr_ntby_qty": "1000",
                     "pe_fund_ntby_vol": "500", "bank_ntby_qty": "100",
                     "insu_ntby_qty": "200", "fund_ntby_qty": "300"},
                ],
            },
        },
    )
    result = get_flow(ctx, "SCAN", ticker="005930")
    assert result["days"][0]["foreign_net_qty"] == -10000.0
    assert result["days"][0]["institution_net_qty"] == 5000.0


def _patch_news_sources(monkeypatch, telegram=None, naver=None):
    import market_intelligence.stock as mil_stock

    monkeypatch.setattr(mil_stock, "get_recent_news",
                         lambda ticker="", hours=2: telegram or [])

    class FakeNaver:
        def search(self, query, display=5):
            return naver or []

    monkeypatch.setattr(mil_stock, "NaverNewsFetcher", FakeNaver)


def test_get_news_stock_filters_by_ticker(monkeypatch):
    from codes.news_fetcher import NewsItem
    _patch_news_sources(
        monkeypatch,
        naver=[NewsItem(title="삼성전자 신규 수주", description="AI 칩 공급 계약",
                        url="https://n.news", pub_date="2026-06-09", source="naver")],
    )

    class SnapshotKis(StubKisApi):
        def get_snapshot(self, ticker):
            return {"name": "삼성전자"}

    from market_intelligence.cache import MILCache
    from market_intelligence.circuit_breaker import CircuitBreaker
    ctx = MILContext(
        kis_api=SnapshotKis(raw_responses={}),
        cache=MILCache(), circuit_breaker=CircuitBreaker(),
    )
    result = get_news_stock(ctx, "SCAN", ticker="005930")
    assert result["headlines"][0]["title"] == "삼성전자 신규 수주"


def test_get_ohlcv_caches_per_ticker_and_period():
    ctx = make_ctx(
        raw_responses={
            "FHKST03010100": {"output1": {}, "output2": []},
        },
    )
    get_ohlcv(ctx, "SCAN", ticker="005930", period=60)
    get_ohlcv(ctx, "SCAN", ticker="005930", period=60)
    assert len(ctx.kis_api.raw_get_calls) == 1


def _fundamentals_responses():
    return {
        "FHKST66430300": {
            "rt_cd": "0",
            "output": [
                {"stac_yymm": "202603", "grs": "69.1600", "bsop_prfi_inrt": "756.1000",
                 "ntin_inrt": "474.3200", "roe_val": "19.16", "eps": "6993.00",
                 "sps": "57655", "bps": "71907.00", "rsrv_rate": "50140.0200",
                 "lblt_rate": "30.1500"},
            ],
        },
        "FHKST66430200": {
            "rt_cd": "0",
            "output": [
                {"stac_yymm": "202603", "sale_account": "1338734.00",
                 "sale_cost": "519602.00", "sale_totl_prfi": "819132",
                 "bsop_prti": "572328.00", "op_prfi": "588284.00",
                 "thtr_ntin": "472253.00"},
            ],
        },
        "FHKST66430100": {
            "rt_cd": "0",
            "output": [
                {"stac_yymm": "202603", "cras": "3062201.00", "fxas": "3271195.00",
                 "total_aset": "6333396.00", "flow_lblt": "1206038.00",
                 "fix_lblt": "260999.00", "total_lblt": "1467036.00",
                 "total_cptl": "4866360.00"},
            ],
        },
        "FHKST663300C0": {
            "rt_cd": "0",
            "output": [
                {"stck_bsop_date": "20260610", "invt_opnn": "BUY",
                 "mbcr_name": "현대차", "hts_goal_prc": "440000",
                 "stck_prdy_clpr": "322000"},
            ],
        },
    }


def test_get_fundamentals_parses_all_four_sections():
    ctx = make_ctx(raw_responses=_fundamentals_responses())
    result = get_fundamentals(ctx, "SCAN", ticker="005930")

    assert result["ticker"] == "005930"

    fr = result["financial_ratios"][0]
    assert fr["period"] == "202603"
    assert fr["revenue_growth_rate_pct"] == 69.16
    assert fr["operating_profit_growth_rate_pct"] == 756.10
    assert fr["roe_pct"] == 19.16
    assert fr["eps"] == 6993.0
    assert fr["bps"] == 71907.0
    assert fr["debt_ratio_pct"] == 30.15

    inc = result["income_statements"][0]
    assert inc["period"] == "202603"
    assert inc["revenue_100mln"] == 1338734.0
    assert inc["operating_profit_100mln"] == 588284.0
    assert inc["net_income_100mln"] == 472253.0

    bs = result["balance_sheets"][0]
    assert bs["period"] == "202603"
    assert bs["total_assets_100mln"] == 6333396.0
    assert bs["total_liabilities_100mln"] == 1467036.0
    assert bs["total_equity_100mln"] == 4866360.0

    op = result["analyst_opinions"][0]
    assert op["date"] == "20260610"
    assert op["opinion"] == "BUY"
    assert op["firm"] == "현대차"
    assert op["target_price"] == 440000.0

    assert "missing_fields" not in result


def test_get_fundamentals_one_section_failure_records_missing_fields():
    responses = _fundamentals_responses()
    del responses["FHKST66430200"]  # income-statement 호출 시 KeyError 발생 -> 실패 처리

    ctx = make_ctx(raw_responses=responses)
    result = get_fundamentals(ctx, "SCAN", ticker="005930")

    assert result["income_statements"] == []
    assert "income_statements" in result["missing_fields"]
    assert result["financial_ratios"]
    assert result["balance_sheets"]
    assert result["analyst_opinions"]


def test_get_fundamentals_caches_per_ticker():
    ctx = make_ctx(raw_responses=_fundamentals_responses())
    get_fundamentals(ctx, "SCAN", ticker="005930")
    get_fundamentals(ctx, "SCAN", ticker="005930")
    assert len(ctx.kis_api.raw_get_calls) == 4

def test_get_news_stock_merges_telegram_and_naver(monkeypatch):
    from codes.news_fetcher import NewsItem
    _patch_news_sources(
        monkeypatch,
        telegram=[{"title": "삼성전자 대규모 수주", "content": "AI 칩 공급 계약 논의",
                    "sentiment": "positive", "score": 0.8, "source": "FastStockNews",
                    "date": "2026-06-12T10:00:00"}],
        naver=[NewsItem(title="삼성전자, 세계 최초 공정 발표", description="2나노 양산" * 30,
                         url="https://n.news", pub_date="Fri, 12 Jun 2026", source="naver")],
    )

    class SnapshotKis(StubKisApi):
        def get_snapshot(self, ticker):
            return {"name": "삼성전자"}

    from market_intelligence.cache import MILCache
    from market_intelligence.circuit_breaker import CircuitBreaker
    ctx = MILContext(
        kis_api=SnapshotKis(raw_responses={"FHKST01011800": {"output": []}}),
        cache=MILCache(), circuit_breaker=CircuitBreaker(),
    )
    result = get_news_stock(ctx, "SCAN", ticker="005930")

    assert result["telegram_headlines"][0]["summary"] == "AI 칩 공급 계약 논의"
    assert result["headlines"][0]["title"].startswith("삼성전자")
    assert result["telegram_headlines"][0]["title"] == "삼성전자 대규모 수주"
    assert result["naver_headlines"][0]["title"].startswith("삼성전자")
    assert len(result["naver_headlines"][0]["summary"]) <= 120
    assert "missing_fields" not in result


def test_get_news_stock_deprioritizes_low_signal_naver_articles(monkeypatch):
    from codes.news_fetcher import NewsItem
    _patch_news_sources(
        monkeypatch,
        naver=[
            NewsItem(
                title="마키나락스 주가, 7월 3일 장중 24,000원 12.68% 상승",
                description="장중 주가 설명 기사",
                url="https://a",
                pub_date="Fri, 03 Jul 2026",
                source="naver",
            ),
            NewsItem(
                title="'피지컬 AI 열풍' 스타트업에도 뭉칫돈",
                description="마키나락스는 제조·국방 특화 AI 기업으로 누적 투자와 사업 확장을 이어가고 있다.",
                url="https://b",
                pub_date="Fri, 03 Jul 2026",
                source="naver",
            ),
        ],
    )

    class SnapshotKis(StubKisApi):
        def get_snapshot(self, ticker):
            return {"name": "마키나락스"}

    from market_intelligence.cache import MILCache
    from market_intelligence.circuit_breaker import CircuitBreaker
    ctx = MILContext(
        kis_api=SnapshotKis(raw_responses={}),
        cache=MILCache(), circuit_breaker=CircuitBreaker(),
    )
    result = get_news_stock(ctx, "SCAN", ticker="477850")

    assert result["naver_headlines"][0]["title"].startswith("'피지컬 AI 열풍'")
    assert result["naver_headlines"][1]["title"].startswith("마키나락스 주가")

def test_get_news_stock_isolates_source_failures(monkeypatch):
    import market_intelligence.stock as mil_stock

    def boom(ticker="", hours=2):
        raise RuntimeError("sqlite down")

    monkeypatch.setattr(mil_stock, "get_recent_news", boom)

    class BoomNaver:
        def search(self, query, display=5):
            raise RuntimeError("network down")

    monkeypatch.setattr(mil_stock, "NaverNewsFetcher", BoomNaver)

    class SnapshotKis(StubKisApi):
        def get_snapshot(self, ticker):
            return {"name": "삼성전자"}

    from market_intelligence.cache import MILCache
    from market_intelligence.circuit_breaker import CircuitBreaker
    ctx = MILContext(
        kis_api=SnapshotKis(raw_responses={}),
        cache=MILCache(), circuit_breaker=CircuitBreaker(),
    )
    result = get_news_stock(ctx, "SCAN", ticker="005930")

    assert result["headlines"] == []
    assert result["telegram_headlines"] == []
    assert result["naver_headlines"] == []
    assert set(result["missing_fields"]) == {"telegram_headlines", "naver_headlines"}


def test_search_telegram_news_returns_query_results(monkeypatch):
    import market_intelligence.stock as mil_stock

    monkeypatch.setattr(
        mil_stock,
        "search_recent_news",
        lambda query, hours=72, limit=20: [
            {"ticker": "011080", "title": "형지I&C 이재명 테마주 부각", "content": "정책 기대", "sentiment": "positive",
             "score": 0.8, "source": "FastStockNews", "url": "https://example.com", "date": "2026-06-25T10:00:00"}
        ],
    )

    ctx = make_ctx(raw_responses={})
    result = search_telegram_news(ctx, "SCAN", query="형지I&C 이재명", hours=48, limit=5)

    assert result["query"] == "형지I&C 이재명"
    assert result["hours"] == 48
    assert result["results"][0]["ticker"] == "011080"
    assert "이재명" in result["results"][0]["title"]


def test_get_watchlist_intraday_snapshot_bundles_price_news_and_status(monkeypatch):
    import market_intelligence.stock as mil_stock
    import market_intelligence.risk_filter as mil_risk_filter

    monkeypatch.setattr(
        mil_stock,
        "get_recent_news",
        lambda ticker="", hours=2: [{"title": f"{ticker} 속보", "source": "FastStockNews", "date": "2026-06-15T09:30:00"}],
    )
    monkeypatch.setattr(
        mil_risk_filter,
        "get_stock_status",
        lambda ctx, phase, ticker: {"ticker": ticker, "is_limit_up": False, "is_limit_down": False, "is_vi": False,
                                    "trading_halted": False, "administrative_issue": False},
    )

    class FakeNaver:
        def search(self, query, display=5):
            return []

    monkeypatch.setattr(mil_stock, "NaverNewsFetcher", FakeNaver)

    ctx = make_ctx(
        raw_responses={
            "FHKST11300006": {
                "output": [
                    {"inter_shrn_iscd": "005930", "inter2_prpr": "70000", "prdy_ctrt": "1.0", "acml_vol": "100"},
                    {"inter_shrn_iscd": "000660", "inter2_prpr": "180000", "prdy_ctrt": "5.0", "acml_vol": "200"},
                ],
            },
            "FHKST03010200": {
                "output2": [
                    {"stck_cntg_hour": "093000", "stck_oprc": "69800", "stck_hgpr": "70000",
                     "stck_lwpr": "69700", "stck_prpr": "69900", "cntg_vol": "5000"},
                    {"stck_cntg_hour": "094000", "stck_oprc": "69900", "stck_hgpr": "70600",
                     "stck_lwpr": "69800", "stck_prpr": "70550", "cntg_vol": "4000"},
                ],
            },
            "FHKST01011800": {"output": []},
        },
    )

    result = get_watchlist_intraday_snapshot(ctx, "INTRADAY", ["005930", "000660", "00ABCD"])

    assert [row["ticker"] for row in result["tickers"]] == ["005930", "000660"]
    assert result["tickers"][0]["price"] == 70000.0
    assert result["tickers"][0]["intraday_trend"] == "up"
    assert "headline_count" not in result["tickers"][0]
    assert "latest_headlines" not in result["tickers"][0]


def test_get_watchlist_intraday_snapshot_uses_hts_avls_for_market_cap(monkeypatch):
    import market_intelligence.stock as mil_stock
    import market_intelligence.risk_filter as mil_risk_filter

    monkeypatch.setattr(mil_stock, "get_recent_news", lambda ticker="", hours=2: [])
    monkeypatch.setattr(
        mil_risk_filter,
        "get_stock_status",
        lambda ctx, phase, ticker: {"ticker": ticker, "is_limit_up": False, "is_limit_down": False, "is_vi": False,
                                    "trading_halted": False, "administrative_issue": False},
    )

    class FakeNaver:
        def search(self, query, display=5):
            return []

    monkeypatch.setattr(mil_stock, "NaverNewsFetcher", FakeNaver)

    class HtsAvlsKisApi(StubKisApi):
        def get_snapshot(self, ticker):
            return {"name": f"종목{ticker}", "trading_value": "1000000000", "hts_avls": "42000"}

    ctx = MILContext(
        kis_api=HtsAvlsKisApi(
            raw_responses={
                "FHKST11300006": {"output": [{"inter_shrn_iscd": "005930", "inter2_prpr": "70000", "prdy_ctrt": "1.0", "acml_vol": "100"}]},
                "FHKST03010200": {"output2": []},
                "FHKST01011800": {"output": []},
            }
        )
    )

    result = get_watchlist_intraday_snapshot(ctx, "INTRADAY", ["005930"])

    assert result["tickers"][0]["market_cap"] == 4_200_000_000_000.0


def _make_candle_raw(hour, open_, high, low, close, vol):
    return {
        "stck_cntg_hour": hour,
        "stck_oprc": str(open_),
        "stck_hgpr": str(high),
        "stck_lwpr": str(low),
        "stck_prpr": str(close),
        "cntg_vol": str(vol),
    }


def _snapshot_ctx(candle_rows, monkeypatch):
    import market_intelligence.stock as mil_stock
    import market_intelligence.risk_filter as mil_risk_filter

    monkeypatch.setattr(mil_stock, "get_recent_news", lambda ticker="", hours=2: [])
    monkeypatch.setattr(mil_stock, "NaverNewsFetcher", type("FN", (), {"search": lambda self, q, display=5: []})())
    monkeypatch.setattr(
        mil_risk_filter,
        "get_stock_status",
        lambda ctx, phase, ticker: {
            "trading_halted": False, "administrative_issue": False,
            "is_limit_up": False, "is_limit_down": False, "is_vi": False,
        },
    )
    return make_ctx(
        raw_responses={
            "FHKST11300006": {"output": [{"inter_shrn_iscd": "005930", "inter2_prpr": "70000", "prdy_ctrt": "1.0", "acml_vol": "100"}]},
            "FHKST03010200": {"output2": candle_rows},
            "FHKST01011800": {"output": []},
        }
    )


def test_snapshot_includes_candle_count_and_recent_candles(monkeypatch):
    candles = [
        _make_candle_raw("090000", 69000, 70000, 68900, 69900, 5000),
        _make_candle_raw("091000", 69900, 70500, 69800, 70400, 4000),
        _make_candle_raw("092000", 70400, 71000, 70300, 70800, 6000),
        _make_candle_raw("093000", 70800, 71200, 70600, 71100, 3000),
    ]
    ctx = _snapshot_ctx(candles, monkeypatch)
    result = get_watchlist_intraday_snapshot(ctx, "INTRADAY", ["005930"])

    row = result["tickers"][0]
    assert row["candle_count"] == 4
    assert len(row["recent_candles"]) == 4  # 10개 미만이면 전부 (4개 있으면 4개)
    assert row["recent_candles"][-1] == row["latest_candle"]  # 마지막 봉 일치
    assert "_guidance" in result  # 4개 < 10 → guidance 있음 (force_refresh 권고)


def test_snapshot_guidance_when_thin_candles(monkeypatch):
    candles = [
        _make_candle_raw("090000", 69000, 70000, 68900, 69900, 5000),
        _make_candle_raw("091000", 69900, 70500, 69800, 70400, 4000),
    ]
    ctx = _snapshot_ctx(candles, monkeypatch)
    result = get_watchlist_intraday_snapshot(ctx, "INTRADAY", ["005930"])

    row = result["tickers"][0]
    assert row["candle_count"] == 2
    assert len(row["recent_candles"]) == 2

    guidance = result["_guidance"]
    assert "005930" in guidance["thin_candles"]
    assert "force_refresh" in guidance["hint"]


def test_snapshot_guidance_when_no_candles(monkeypatch):
    ctx = _snapshot_ctx([], monkeypatch)
    result = get_watchlist_intraday_snapshot(ctx, "INTRADAY", ["005930"])

    assert result["tickers"][0]["candle_count"] == 0
    assert result["tickers"][0]["recent_candles"] == []
    assert "005930" in result["_guidance"]["thin_candles"]

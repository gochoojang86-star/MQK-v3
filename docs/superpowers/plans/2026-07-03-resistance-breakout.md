# RESISTANCE_BREAKOUT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new `RESISTANCE_BREAKOUT` setup type (20-day-high / round-figure breakout with volume confirmation) to SCAN and INTRADAY, so MQK v3 can also catch strength-continuation entries, not just dip-buys (REVERSAL) and volume surges.

**Architecture:** One pure calculation function (`_compute_resistance_facts`) computes resistance/round-figure facts from `get_ohlcv` daily candles. SCAN embeds these facts into the top-N `candidate_pool` entries (mirrors the existing `_prefetch_pool_news` prefetch pattern). INTRADAY embeds the same facts per-ticker into `get_watchlist_intraday_snapshot`. A new `exploration_policy.resistance_breakout_allowed` flag (reusing the existing `_is_risk_off_regime`/`is_crash` signals) is code-enforced in `_sanitize_intraday_result` so a crashing market cannot buy a "breakout" that is really just noise.

**Tech Stack:** Python 3.12, pytest, existing MQK v3 orchestrator/market_intelligence modules. No new dependencies, no new external tools.

## Global Constraints

- Every calculation (20-day high, round-figure level, volume ratio) is computed in code — the LLM never does this arithmetic itself (spec §2.1).
- Round-figure units by price tier: <10,000원 → 1,000원; 10,000~100,000원 → 5,000원; 100,000~1,000,000원 → 10,000원; ≥1,000,000원 → 100,000원 (spec §1).
- 20-day high excludes the current (still-forming, if intraday) daily candle (spec §2.1).
- Volume confirmation threshold: today's trading value ≥ 2x the trailing 5-day average (spec §1, matches existing REVERSAL setup's panic-sell volume check).
- SCAN prefetch is capped at the top 15 pool candidates (spec §2.2) — same cost-bounding pattern as `_prefetch_pool_news` (top 12).
- `RESISTANCE_BREAKOUT` only applies to `role=본류 대장주` (spec §1).
- Banned during RED/RISK_OFF regime or live `is_crash=true`, enforced in code, not just prompt (spec §3.2).
- No new MIL tool — reuse `get_ohlcv` everywhere (spec §6).
- No new `sell_type` — fake-breakout exits reuse existing `PRICE_SIGNAL` (spec §1, §6).

---

### Task 1: `_compute_resistance_facts` pure function

**Files:**
- Modify: `market_intelligence/stock.py`
- Test: `tests/test_mil_stock.py`

**Interfaces:**
- Produces: `_round_figure_unit(price: float) -> float` and `_compute_resistance_facts(candles: list[dict], current_price: float) -> dict` with keys `resistance_20d_high`, `pct_from_resistance`, `round_figure_price`, `pct_from_round_figure`, `is_breakout_20d_high`, `is_breakout_round_figure`, `volume_vs_5d_avg_ratio`. Both are module-level functions in `market_intelligence/stock.py`, consumed by Task 2 (same file) and Task 3 (`orchestrator_v3.py`, imported as `from market_intelligence.stock import _compute_resistance_facts`).
- Candle dict shape consumed (matches `get_ohlcv`'s `candles` list, most recent last): `{"date": str, "open": float, "high": float, "low": float, "close": float, "volume": float, "trading_value": float, "rights_event_code": str}`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_mil_stock.py` (append near the top, after the imports — add `_compute_resistance_facts` and `_round_figure_unit` to the existing import block from `market_intelligence.stock`):

```python
def test_round_figure_unit_scales_by_price_tier():
    from market_intelligence.stock import _round_figure_unit

    assert _round_figure_unit(5_000) == 1_000
    assert _round_figure_unit(9_999) == 1_000
    assert _round_figure_unit(10_000) == 5_000       # boundary: "1만원 미만"만 1,000원대
    assert _round_figure_unit(50_000) == 5_000
    assert _round_figure_unit(100_000) == 10_000      # boundary
    assert _round_figure_unit(500_000) == 10_000
    assert _round_figure_unit(1_000_000) == 100_000   # boundary
    assert _round_figure_unit(2_500_000) == 100_000


def _candle(open_, high, low, close, trading_value=1_000_000_000.0):
    return {"open": open_, "high": high, "low": low, "close": close,
            "volume": 1000, "trading_value": trading_value}


def test_compute_resistance_facts_detects_20d_high_breakout():
    from market_intelligence.stock import _compute_resistance_facts

    prior = [_candle(90_000, 95_000, 89_000, 94_000) for _ in range(19)]
    prior.append(_candle(94_000, 100_000, 93_000, 99_000))  # 20th prior day, highest high
    today = _candle(99_000, 101_000, 98_500, 100_500)
    candles = prior + [today]

    facts = _compute_resistance_facts(candles, current_price=101_000.0)

    assert facts["resistance_20d_high"] == 100_000.0
    assert facts["is_breakout_20d_high"] is True
    assert facts["pct_from_resistance"] == 1.0


def test_compute_resistance_facts_no_breakout_when_below_resistance():
    from market_intelligence.stock import _compute_resistance_facts

    prior = [_candle(90_000, 95_000, 89_000, 94_000) for _ in range(20)]
    today = _candle(94_000, 94_500, 93_000, 94_200)
    candles = prior + [today]

    facts = _compute_resistance_facts(candles, current_price=94_200.0)

    assert facts["resistance_20d_high"] == 95_000.0
    assert facts["is_breakout_20d_high"] is False


def test_compute_resistance_facts_detects_round_figure_breakout():
    from market_intelligence.stock import _compute_resistance_facts

    prior = [_candle(28_000, 29_000, 27_500, 28_500) for _ in range(20)]
    today = _candle(29_500, 31_000, 29_200, 30_800)  # 시가 29,500 < 라운드(30,000) <= 현재가
    candles = prior + [today]

    facts = _compute_resistance_facts(candles, current_price=30_800.0)

    assert facts["round_figure_price"] == 30_000.0
    assert facts["is_breakout_round_figure"] is True


def test_compute_resistance_facts_no_round_figure_breakout_when_open_already_above():
    from market_intelligence.stock import _compute_resistance_facts

    prior = [_candle(28_000, 29_000, 27_500, 28_500) for _ in range(20)]
    today = _candle(30_500, 31_000, 30_200, 30_800)  # 시가부터 이미 30,000 위 — "돌파"가 아님

    facts = _compute_resistance_facts(prior + [today], current_price=30_800.0)

    assert facts["is_breakout_round_figure"] is False


def test_compute_resistance_facts_volume_ratio_uses_prior_5_day_average():
    from market_intelligence.stock import _compute_resistance_facts

    prior = [_candle(90_000, 95_000, 89_000, 94_000, trading_value=1_000_000_000.0) for _ in range(20)]
    today = _candle(94_000, 96_000, 93_500, 95_500, trading_value=3_000_000_000.0)

    facts = _compute_resistance_facts(prior + [today], current_price=95_500.0)

    assert facts["volume_vs_5d_avg_ratio"] == 3.0


def test_compute_resistance_facts_handles_empty_candles():
    from market_intelligence.stock import _compute_resistance_facts

    facts = _compute_resistance_facts([], current_price=0.0)

    assert facts["resistance_20d_high"] == 0.0
    assert facts["is_breakout_20d_high"] is False
    assert facts["is_breakout_round_figure"] is False
    assert facts["volume_vs_5d_avg_ratio"] == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_mil_stock.py -k "round_figure_unit or compute_resistance_facts" -v`
Expected: FAIL with `ImportError: cannot import name '_round_figure_unit'` (or `_compute_resistance_facts`) from `market_intelligence.stock`.

- [ ] **Step 3: Write the implementation**

In `market_intelligence/stock.py`, add near the top of the file, right after the `_to_float` helper (search for `def _to_float`) — do NOT put it before `_to_float` since it isn't used, this is just for a logical grouping near other small numeric helpers:

```python
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
```

Add `import math` to the top of `market_intelligence/stock.py` if not already present (check the existing `from __future__ import annotations` / `from datetime import ...` import block — add `import math` as its own line before the `from datetime import` line).

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_mil_stock.py -k "round_figure_unit or compute_resistance_facts" -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add market_intelligence/stock.py tests/test_mil_stock.py
git commit -m "feat: add resistance/round-figure breakout fact calculation

Pure function _compute_resistance_facts computes 20-day-high breakout,
round-figure breakout, and 5-day volume ratio from get_ohlcv candles.
All arithmetic is code-computed — no LLM estimation of these values.
Part of RESISTANCE_BREAKOUT setup (docs/superpowers/specs/2026-07-03-resistance-breakout-design.md)."
```

---

### Task 2: Wire resistance facts into `get_watchlist_intraday_snapshot` (INTRADAY)

**Files:**
- Modify: `market_intelligence/stock.py:342` (`get_watchlist_intraday_snapshot`)
- Test: `tests/test_mil_stock.py`

**Interfaces:**
- Consumes: `_compute_resistance_facts(candles, current_price)` from Task 1 (same file, no import needed).
- Produces: each ticker dict returned by `get_watchlist_intraday_snapshot` gains a `"resistance"` key holding the dict from `_compute_resistance_facts`. INTRADAY prompt (Task 7) reads `resistance.is_breakout_20d_high` / `resistance.is_breakout_round_figure` / `resistance.volume_vs_5d_avg_ratio` per watchlist ticker.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_mil_stock.py`, near `test_get_watchlist_intraday_snapshot_bundles_price_news_and_status`:

```python
def test_get_watchlist_intraday_snapshot_includes_resistance_facts(monkeypatch):
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

    ctx = make_ctx(
        raw_responses={
            "FHKST11300006": {
                "output": [{"inter_shrn_iscd": "000660", "inter2_prpr": "101000", "prdy_ctrt": "5.0", "acml_vol": "200"}],
            },
            "FHKST03010200": {"output2": []},
            "FHKST01011800": {"output": []},
            "FHKST03010100": {
                "output1": {"stck_prpr": "101000"},
                "output2": (
                    [{"stck_bsop_date": f"2026060{i}", "stck_oprc": "90000", "stck_hgpr": "95000",
                      "stck_lwpr": "89000", "stck_clpr": "94000", "acml_vol": "100000",
                      "acml_tr_pbmn": "1000000000"} for i in range(1, 10)]
                    + [{"stck_bsop_date": "20260620", "stck_oprc": "94000", "stck_hgpr": "100000",
                        "stck_lwpr": "93000", "stck_clpr": "99000", "acml_vol": "100000",
                        "acml_tr_pbmn": "1000000000"}]
                    + [{"stck_bsop_date": "20260703", "stck_oprc": "99000", "stck_hgpr": "101500",
                        "stck_lwpr": "98500", "stck_clpr": "101000", "acml_vol": "100000",
                        "acml_tr_pbmn": "1000000000"}]  # 당일(미마감) 봉 — 마지막
                ),
            },
        },
    )

    result = get_watchlist_intraday_snapshot(ctx, "INTRADAY", tickers=["000660"])

    resistance = result["tickers"][0]["resistance"]
    assert resistance["resistance_20d_high"] == 100_000.0
    assert resistance["is_breakout_20d_high"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_mil_stock.py -k test_get_watchlist_intraday_snapshot_includes_resistance_facts -v`
Expected: FAIL with `KeyError: 'resistance'`.

- [ ] **Step 3: Write the implementation**

In `market_intelligence/stock.py`, inside `get_watchlist_intraday_snapshot`'s `fetch()` function, inside the `for ticker in normalized:` loop, add a new try/except block right after the existing `intraday`/`recent_candles` try/except block (search for `missing_fields.append("intraday_candles")` — insert after that block's `except` closes, before the `get_stock_status` try/except block):

```python
            try:
                ohlcv = get_ohlcv(ctx, phase, ticker, period=25)
                item["resistance"] = _compute_resistance_facts(
                    ohlcv.get("candles", []), item.get("price", 0.0)
                )
            except Exception:
                item["resistance"] = _compute_resistance_facts([], 0.0)
                missing_fields.append("resistance")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_mil_stock.py -v`
Expected: all tests in the file pass (including the new one, and the two pre-existing `test_get_watchlist_intraday_snapshot_*` tests still pass since they don't assert on `FHKST03010100` being absent — verify no regression by reading their output if anything fails).

- [ ] **Step 5: Commit**

```bash
git add market_intelligence/stock.py tests/test_mil_stock.py
git commit -m "feat: include resistance facts in get_watchlist_intraday_snapshot

INTRADAY now sees resistance_20d_high/round_figure/volume_vs_5d_avg_ratio
per watchlist ticker, reusing get_ohlcv (already cached, no new API cost
on repeated 10-minute ticks within the same day)."
```

---

### Task 3: `_prefetch_pool_resistance` + wire into SCAN

**Files:**
- Modify: `orchestrator_v3.py` (new method near `_prefetch_pool_news`, call site in `run_scan_v3`)
- Test: `tests/test_orchestrator_v3.py`

**Interfaces:**
- Consumes: `_compute_resistance_facts` from Task 1 — add `from market_intelligence.stock import _compute_resistance_facts` to `orchestrator_v3.py`'s import block (near the existing `from market_intelligence import stock as mil_stock` line).
- Produces: `MQKOrchestratorV3._prefetch_pool_resistance(self, pool: list[dict], top_n: int | None = None) -> None` — mutates `pool` in place, setting `item["facts"]["resistance"]` for the top `top_n` (default 15) items.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_orchestrator_v3.py`:

```python
def test_prefetch_pool_resistance_bounds_to_top_15(monkeypatch, tmp_path):
    import market_intelligence.stock as mil_stock

    calls = []

    def fake_get_ohlcv(ctx, phase, ticker, period=60):
        calls.append(ticker)
        return {
            "current_price": 100_000.0,
            "candles": [{"open": 90_000, "high": 95_000, "low": 89_000, "close": 94_000,
                         "trading_value": 1_000_000_000.0} for _ in range(20)]
                       + [{"open": 94_000, "high": 101_000, "low": 93_500, "close": 100_500,
                           "trading_value": 1_000_000_000.0}],
        }

    monkeypatch.setattr(mil_stock, "get_ohlcv", fake_get_ohlcv)

    orch = make_orchestrator(tmp_path)
    pool = [{"ticker": f"{i:06d}", "facts": {}} for i in range(20)]

    orch._prefetch_pool_resistance(pool)

    assert len(calls) == 15
    assert "resistance" in pool[0]["facts"]
    assert pool[0]["facts"]["resistance"]["is_breakout_20d_high"] is True
    assert "resistance" not in pool[15]["facts"]


def test_prefetch_pool_resistance_skips_ticker_on_fetch_failure(monkeypatch, tmp_path):
    import market_intelligence.stock as mil_stock

    monkeypatch.setattr(mil_stock, "get_ohlcv", lambda ctx, phase, ticker, period=60: (_ for _ in ()).throw(RuntimeError("api down")))

    orch = make_orchestrator(tmp_path)
    pool = [{"ticker": "005930", "facts": {}}]

    orch._prefetch_pool_resistance(pool)  # 예외 전파 없이 조용히 스킵돼야 함

    assert "resistance" not in pool[0]["facts"]


def test_run_scan_v3_calls_prefetch_pool_resistance(monkeypatch, tmp_path):
    orch = make_orchestrator(tmp_path)
    calls = []
    orch._prefetch_pool_resistance = lambda pool, top_n=None: calls.append("resistance")
    orch._prefetch_pool_news = lambda pool, top_n=None: calls.append("news")
    orch._build_scan_candidate_pool = lambda regime=None: []
    orch._build_scan_market_story_brief = lambda: {}
    orch._build_context = lambda *a, **k: {"candidate_pool": []}
    orch._trading_agent = FakeTradingAgent({
        "next_action": "final", "action": "WAIT", "watchlist": [], "candidates": [], "reason": "",
    })
    orch._record_tool_request = lambda *a, **k: None
    orch._alert_on_tool_failures = lambda *a, **k: None
    orch._save_json = lambda *a, **k: None
    orch._apply_scan_diversity_guard = lambda result, context: result
    orch._watchlist_entries_from_scan_result = lambda result: []

    monkeypatch.setattr("orchestrator_v3._LAST_REGIME_PATH", tmp_path / "last_regime.json")
    monkeypatch.setattr("orchestrator_v3._DRIFT_STATE_PATH", tmp_path / "drift_state.json")
    monkeypatch.setattr("orchestrator_v3._WATCHLIST_PATH", tmp_path / "watchlist.json")

    orch.run_scan_v3()

    assert calls == ["news", "resistance"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_orchestrator_v3.py -k "prefetch_pool_resistance or run_scan_v3_calls_prefetch" -v`
Expected: FAIL — `AttributeError: 'MQKOrchestratorV3' object has no attribute '_prefetch_pool_resistance'` for the first two; the third fails the same way once its monkeypatch assignment on a nonexistent-but-assignable attribute succeeds but `run_scan_v3` never calls it (assert `calls == ["news", "resistance"]` fails with `calls == ["news"]`).

- [ ] **Step 3: Write the implementation**

In `orchestrator_v3.py`, add the import (near the top, alongside `from market_intelligence import stock as mil_stock`):

```python
from market_intelligence.stock import _compute_resistance_facts
```

Add the new method directly after `_prefetch_pool_news` (search for `# ── 컨텍스트/스냅샷 빌더` which marks the line right after `_prefetch_pool_news` ends):

```python
    def _prefetch_pool_resistance(self, pool: list[dict], top_n: int | None = None) -> None:
        """pool 상위 우선순위 구간 종목의 저항선/라운드피겨 fact를 코드가 미리 계산해 embed한다.

        get_ohlcv 실패는 해당 종목만 스킵 (전체 SCAN 중단 없음). _prefetch_pool_news와
        동일한 비용 상한 패턴 — 상위 top_n개만 조회.
        """
        phase = TradingPhase.SCAN.value
        if top_n is None:
            top_n = min(len(pool), 15)
        for item in pool[:top_n]:
            ticker = item.get("ticker", "")
            if not ticker:
                continue
            try:
                ohlcv = mil_stock.get_ohlcv(self._mil, phase, ticker, period=25)
                item["facts"]["resistance"] = _compute_resistance_facts(
                    ohlcv.get("candles", []), ohlcv.get("current_price", 0.0)
                )
            except Exception as e:
                logger.debug(f"[SCAN POOL RESISTANCE] {ticker} 저항선 계산 실패 (스킵): {e}")
```

In `run_scan_v3()`, right after the existing `self._prefetch_pool_news(context["candidate_pool"])` line, add:

```python
        self._prefetch_pool_resistance(context["candidate_pool"])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_orchestrator_v3.py -k "prefetch_pool_resistance or run_scan_v3_calls_prefetch" -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add orchestrator_v3.py tests/test_orchestrator_v3.py
git commit -m "feat: prefetch resistance facts for top-15 SCAN candidates

_prefetch_pool_resistance mirrors _prefetch_pool_news's bounded-cost
pattern. Wired into run_scan_v3 right after the news prefetch."
```

---

### Task 4: `exploration_policy.resistance_breakout_allowed`

**Files:**
- Modify: `orchestrator_v3.py:1537` (`_build_context`, inside the `exploration_policy` dict)
- Test: `tests/test_orchestrator_v3.py`

**Interfaces:**
- Consumes: existing `_is_risk_off_regime(regime)` and `is_crash` (already a parameter of `_build_context` as of the 2026-07-03 `leader_reentry_confidence_floor` fix — no signature change needed).
- Produces: `exploration_policy["resistance_breakout_allowed"]: bool`, consumed by Task 5 (`_sanitize_intraday_result`) and by the INTRADAY prompt (Task 7).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_orchestrator_v3.py`, right after `test_run_intraday_v3_disables_leader_reentry_floor_when_live_is_crash_even_if_regime_stale`:

```python
def test_run_intraday_v3_disables_resistance_breakout_during_risk_off_regime(monkeypatch, tmp_path):
    import market_intelligence.portfolio as mil_portfolio
    import market_intelligence.market as mil_market

    monkeypatch.setattr(mil_portfolio, "get_open_positions",
                         lambda ctx, phase: {"positions": [], "position_count": 0})
    monkeypatch.setattr(mil_portfolio, "get_daily_pnl",
                         lambda ctx, phase: {"realized_pnl_pct": 0.0, "realized_pnl_krw": 0, "total_eval_amt": 10_000_000})
    monkeypatch.setattr(mil_market, "get_market_context",
                         lambda ctx, phase: {"kospi_change_pct": -7.0, "kosdaq_change_pct": -6.0, "foreign_net_buy_krw": 0})
    monkeypatch.setattr(mil_market, "get_intraday_index_candles", lambda ctx, phase: {"candles": []})
    monkeypatch.setattr(mil_market, "get_sector_breadth", lambda ctx, phase: {"market_breadth": {}})

    orch = make_orchestrator(tmp_path)
    orch._drift_detector = FakeDriftDetector({
        "drift_judgment": "STABLE", "reason": "no_trigger_fired", "metrics": {}, "triggered": [],
        "new_status": None, "risk_guidance_delta": {},
        "drift_state": {"date": "2026-06-09", "last_trigger_time": {}, "today_caution_count": 0, "daily_lite_llm_calls": 0},
    })
    orch._trading_agent = FakeTradingAgent({"action": "NO_TRADE", "proposals": [], "reason": "폭락장 관망"})

    regime = {
        "status": "RED", "regime": "RISK_OFF", "confidence": 90,
        "risk_guidance": {"max_positions": 4, "buy_confidence_threshold": 75,
                           "risk_per_trade_pct": 0.35, "min_trading_value_krw": 1_000_000_000},
        "drift_triggers": [], "cooldown_minutes": 60, "max_daily_triggers": 3,
        "timestamp": "2026-06-09T08:45:00",
    }
    (tmp_path / "last_regime.json").write_text(json.dumps(regime), encoding="utf-8")
    (tmp_path / "watchlist.json").write_text(json.dumps({"watchlist": ["005930"]}), encoding="utf-8")

    monkeypatch.setattr("orchestrator_v3._LAST_REGIME_PATH", tmp_path / "last_regime.json")
    monkeypatch.setattr("orchestrator_v3._DRIFT_STATE_PATH", tmp_path / "drift_state.json")
    monkeypatch.setattr("orchestrator_v3._WATCHLIST_PATH", tmp_path / "watchlist.json")

    orch.run_intraday_v3()

    assert orch._trading_agent.calls[0][1]["exploration_policy"]["resistance_breakout_allowed"] is False
```

Also modify the existing `test_run_intraday_v3_stable_executes_no_trade` test (search for `assert orch._trading_agent.calls[0][1]["exploration_policy"]["leader_reentry_confidence_floor"] == 70.0`) — add a line right after it:

```python
    assert orch._trading_agent.calls[0][1]["exploration_policy"]["resistance_breakout_allowed"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_orchestrator_v3.py -k "resistance_breakout_allowed or stable_executes_no_trade" -v`
Expected: FAIL — `KeyError: 'resistance_breakout_allowed'` for both.

- [ ] **Step 3: Write the implementation**

In `orchestrator_v3.py`, inside `_build_context`'s `exploration_policy` dict (right after the `leader_reentry_confidence_floor` entry, before the closing `}`), add:

```python
                    "resistance_breakout_allowed": not (_is_risk_off_regime(regime) or is_crash),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_orchestrator_v3.py -k "resistance_breakout_allowed or stable_executes_no_trade" -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add orchestrator_v3.py tests/test_orchestrator_v3.py
git commit -m "feat: add exploration_policy.resistance_breakout_allowed

Reuses the RED/RISK_OFF + live is_crash gate already proven for
leader_reentry_confidence_floor. RESISTANCE_BREAKOUT entries are
suppressed the same way during a crash."
```

---

### Task 5: Code-level enforcement in `_sanitize_intraday_result`

**Files:**
- Modify: `orchestrator_v3.py:1706` (`_sanitize_intraday_result`), call site at `orchestrator_v3.py:802`, `_INTRADAY_PROPOSAL_REASON_CODES` set and `_infer_intraday_proposal_reason_code`'s `setup_map`
- Test: `tests/test_orchestrator_v3.py`

**Interfaces:**
- Consumes: `resistance_breakout_allowed: bool` (new optional parameter, default `True` for backward compatibility with the 4 existing call sites in tests that don't pass it).
- Produces: `_sanitize_intraday_result(result, resistance_breakout_allowed=True) -> dict` — strips any `side=="BUY"` proposal with `setup=="RESISTANCE_BREAKOUT"` when `resistance_breakout_allowed` is `False`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_orchestrator_v3.py`:

```python
def test_sanitize_intraday_result_strips_resistance_breakout_buy_when_not_allowed(tmp_path):
    orch = make_orchestrator(tmp_path)
    result = {
        "action": "BUY",
        "proposals": [
            {"ticker": "005930", "side": "BUY", "setup": "RESISTANCE_BREAKOUT", "confidence": 80,
             "stop_loss_price": 290000, "reason": "라운드피겨 돌파"},
        ],
        "reason": "돌파 진입",
    }

    sanitized = orch._sanitize_intraday_result(result, resistance_breakout_allowed=False)

    assert sanitized["proposals"] == []


def test_sanitize_intraday_result_keeps_resistance_breakout_buy_when_allowed(tmp_path):
    orch = make_orchestrator(tmp_path)
    result = {
        "action": "BUY",
        "proposals": [
            {"ticker": "005930", "side": "BUY", "setup": "RESISTANCE_BREAKOUT", "confidence": 80,
             "stop_loss_price": 290000, "reason": "라운드피겨 돌파"},
        ],
        "reason": "돌파 진입",
    }

    sanitized = orch._sanitize_intraday_result(result, resistance_breakout_allowed=True)

    assert len(sanitized["proposals"]) == 1
    assert sanitized["proposals"][0]["standardized_reason_code"] == "RESISTANCE_BREAKOUT_ENTRY"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_orchestrator_v3.py -k "sanitize_intraday_result_strips_resistance or sanitize_intraday_result_keeps_resistance" -v`
Expected: FAIL — `TypeError: _sanitize_intraday_result() got an unexpected keyword argument 'resistance_breakout_allowed'`.

- [ ] **Step 3: Write the implementation**

In `orchestrator_v3.py`, add `"RESISTANCE_BREAKOUT_ENTRY"` to the `_INTRADAY_PROPOSAL_REASON_CODES` set (search for `_INTRADAY_PROPOSAL_REASON_CODES = {`, add the line inside the set alongside the other `*_ENTRY` values):

```python
    "RESISTANCE_BREAKOUT_ENTRY",
```

In `_infer_intraday_proposal_reason_code`'s `setup_map` dict, add:

```python
        "RESISTANCE_BREAKOUT": "RESISTANCE_BREAKOUT_ENTRY",
```

Change the `_sanitize_intraday_result` signature and add the filter (inside the `for proposal in raw_proposals:` loop, right after the `if side not in {"BUY", "SELL"}: continue` line):

```python
    def _sanitize_intraday_result(self, result: dict, resistance_breakout_allowed: bool = True) -> dict:
```

```python
            if (
                not resistance_breakout_allowed
                and side == "BUY"
                and _normalize_setup_name(proposal.get("setup")) == "RESISTANCE_BREAKOUT"
            ):
                logger.warning(
                    f"[V3 INTRADAY] resistance_breakout_allowed=False인데 RESISTANCE_BREAKOUT BUY "
                    f"proposal 포함({proposal.get('ticker')}) — 안전상 제거"
                )
                continue
```

Update the call site in `run_intraday_v3` (search for `result = self._sanitize_intraday_result(result)`):

```python
        result = self._sanitize_intraday_result(
            result,
            resistance_breakout_allowed=context["exploration_policy"]["resistance_breakout_allowed"],
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_orchestrator_v3.py -v`
Expected: all tests in the file pass (full-file run, since this touches a widely-used method — confirm no regression in the other 3 pre-existing `_sanitize_intraday_result` call sites in the test file, which don't pass the new kwarg and rely on the `True` default).

- [ ] **Step 5: Commit**

```bash
git add orchestrator_v3.py tests/test_orchestrator_v3.py
git commit -m "fix: enforce resistance_breakout_allowed in code, not just prompt

_sanitize_intraday_result now strips RESISTANCE_BREAKOUT BUY proposals
when exploration_policy.resistance_breakout_allowed=False, mirroring the
existing HOLD-with-proposals safety strip. Prompt-only compliance was
the root cause of the 2026-07-02 leader_reentry_confidence_floor
incident — this setup gets the code-level gate from day one."
```

---

### Task 6: SCAN prompt (`scan.md`) — RESISTANCE_BREAKOUT setup

**Files:**
- Modify: `prompts/agents/trading_agent/scan.md`
- Test: `tests/test_trading_agent.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_trading_agent.py` (follow the existing `test_scan_prompt_mentions_candidate_pool_as_primary_input` pattern — same file reads `Path("prompts/agents/trading_agent/scan.md").read_text(encoding="utf-8")`):

```python
def test_scan_prompt_describes_resistance_breakout_setup():
    text = Path("prompts/agents/trading_agent/scan.md").read_text(encoding="utf-8")
    assert "RESISTANCE_BREAKOUT" in text
    assert "facts.resistance" in text
    assert "risk_off_mode일 때 이 셋업으로 신규 등재 금지" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_trading_agent.py -k test_scan_prompt_describes_resistance_breakout_setup -v`
Expected: FAIL — `AssertionError`.

- [ ] **Step 3: Update the prompt**

In `prompts/agents/trading_agent/scan.md`, change the `## Role` intro (the numbered list of 3 setup types) to 4:

```
4. **RESISTANCE_BREAKOUT**: 본류 대장주가 최근 20일 고점 또는 라운드 피겨(가격대별 자동 단위)를 상향 돌파 + 거래대금 5일 평균 대비 2배 이상
```

(Insert as a new line 8, right after the existing REVERSAL line — i.e. after `3. **REVERSAL**: 폭락일(지수 -3%↓) + 본류 대장주 당일 낙폭 -5%↑ + 패닉셀 거래대금 폭증 → 저점 반등 후보`.)

Add a new section right after `## REVERSAL 판별 기준` (before `## final 전 체크리스트`):

```markdown
## RESISTANCE_BREAKOUT 판별 기준
- **대상**: `role=본류 대장주`만. 후발주 돌파는 대상 아님.
- pool 상위 종목에는 `facts.resistance`가 코드로 미리 계산되어 있다 — 직접 계산하지 말고 이 값을 읽어라:
  - `is_breakout_20d_high`: 최근 20일 고점 상향 돌파 여부
  - `is_breakout_round_figure`: 당일 시가 아래에 있던 라운드 피겨(`round_figure_price`)를 상향 돌파했는지
  - `volume_vs_5d_avg_ratio`: 오늘 거래대금 ÷ 최근 5일 평균
- **조건 1 (필수)**: `is_breakout_20d_high` 또는 `is_breakout_round_figure` 중 하나 이상 `true`
- **조건 2 (필수)**: `volume_vs_5d_avg_ratio ≥ 2.0`
- **confidence 가산**: 둘 다 `true`(20일 고점 + 라운드 피겨 동시 돌파)면 `theme_evidence`에 "동시 돌파" 명시하고 confidence를 더 줄 수 있다.
- **risk_off_mode일 때 이 셋업으로 신규 등재 금지** — 폭락장의 개별 종목 돌파는 가짜 돌파일 확률이 높다.
- `facts.resistance`가 없는 종목(top 15 밖이라 프리페치 안 됨)은 이 셋업으로 등재하지 말 것 — 직접 계산해서 추정하지 마라.
```

Update the JSON output example's setup enum string (search for `"setup": "VOLUME_SURGE_LEADER|THEME_CATALYST|REVERSAL",`):

```json
      "setup": "VOLUME_SURGE_LEADER|THEME_CATALYST|REVERSAL|RESISTANCE_BREAKOUT",
```

Add to the `## Forbidden` list (append as a new bullet at the end):

```
- **RESISTANCE_BREAKOUT**: `facts.resistance.is_breakout_20d_high`도 `is_breakout_round_figure`도 `false`인데 등재 금지
- **RESISTANCE_BREAKOUT**: `volume_vs_5d_avg_ratio < 2.0`인데 등재 금지
- **RESISTANCE_BREAKOUT**: risk_off_mode에서 신규 등재 금지
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_trading_agent.py -k test_scan_prompt_describes_resistance_breakout_setup -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add prompts/agents/trading_agent/scan.md tests/test_trading_agent.py
git commit -m "feat: add RESISTANCE_BREAKOUT setup to SCAN prompt

4th setup type alongside VOLUME_SURGE_LEADER/THEME_CATALYST/REVERSAL.
Reads code-precomputed facts.resistance rather than asking the LLM to
estimate breakout levels itself."
```

---

### Task 7: INTRADAY prompt (`intraday.md`) — entry/exit criteria

**Files:**
- Modify: `prompts/agents/trading_agent/intraday.md`
- Test: `tests/test_trading_agent.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_trading_agent.py`:

```python
def test_intraday_prompt_describes_resistance_breakout_entry_and_exit():
    text = Path("prompts/agents/trading_agent/intraday.md").read_text(encoding="utf-8")
    assert "RESISTANCE_BREAKOUT" in text
    assert "resistance_breakout_allowed" in text
    assert "RESISTANCE_BREAKOUT_ENTRY" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_trading_agent.py -k test_intraday_prompt_describes_resistance_breakout_entry_and_exit -v`
Expected: FAIL — `AssertionError`.

- [ ] **Step 3: Update the prompt**

In `prompts/agents/trading_agent/intraday.md`, add a new row to the "진입 근거" table (right after the REVERSAL rows, inside the existing `| setup | 핵심 확인 사항 |` table):

```
| RESISTANCE_BREAKOUT | `resistance.is_breakout_20d_high` 또는 `resistance.is_breakout_round_figure`가 `true` / `resistance.volume_vs_5d_avg_ratio ≥ 2.0` / 돌파 봉이 재이탈 없이 유지 / `exploration_policy.resistance_breakout_allowed=true`일 때만 |
```

Add a clarifying line right after the existing table (after the `role=후발주` / `하락 중 거래대금 폭증` paragraph, before `## 청산 근거`):

```
`exploration_policy.resistance_breakout_allowed=false`이면 RESISTANCE_BREAKOUT으로는 어떤 BUY proposal도 내지 마라 — 코드가 강제로 제거하니 시도해도 소용없다.
```

Update the "청산 근거" table's `PRICE_SIGNAL` row to also cover the fake-breakout case (change the existing row from `| PRICE_SIGNAL | day_low 하향돌파 + 해당봉 거래대금 ≥ 직전 10봉 평균 2배 | 즉시 |` to):

```
| PRICE_SIGNAL | `day_low` 하향돌파 + 해당봉 거래대금 ≥ 직전 10봉 평균 2배 **또는** RESISTANCE_BREAKOUT 포지션이 돌파했던 저항선(`resistance_20d_high`/`round_figure_price`) 아래로 분봉 종가 재이탈 | 즉시 |
```

Update the `standardized_reason_code` enum line (search for `"standardized_reason_code": "BUY_SIGNAL_CONFIRMED|SELL_SIGNAL_CONFIRMED|...`) — no change needed there (that's the top-level code list, unrelated to setup-specific proposal codes). Update the BUY proposal standardized_reason_code list instead (search for `` `REVERSAL_ENTRY` / `THEME_CATALYST_ENTRY` / `VOLUME_SURGE_ENTRY` / `LIMIT_UP_PULLBACK_ENTRY` / `RELATIVE_STRENGTH_ENTRY` / `TREND_ENTRY` / `BUY_CANDIDATE` ``):

```
`REVERSAL_ENTRY` / `THEME_CATALYST_ENTRY` / `VOLUME_SURGE_ENTRY` / `LIMIT_UP_PULLBACK_ENTRY` / `RESISTANCE_BREAKOUT_ENTRY` / `RELATIVE_STRENGTH_ENTRY` / `TREND_ENTRY` / `BUY_CANDIDATE`
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_trading_agent.py -k test_intraday_prompt_describes_resistance_breakout_entry_and_exit -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add prompts/agents/trading_agent/intraday.md tests/test_trading_agent.py
git commit -m "feat: add RESISTANCE_BREAKOUT entry/exit criteria to INTRADAY prompt

Entry gated on exploration_policy.resistance_breakout_allowed (code
also enforces this — see _sanitize_intraday_result). Fake-breakout exit
reuses the existing PRICE_SIGNAL sell_type."
```

---

### Task 8: Full regression pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all tests pass (no failures, no errors). If any pre-existing test broke, it's almost certainly one of:
- A test asserting the exact `exploration_policy` dict shape without the new `resistance_breakout_allowed` key (fix: add the key to that test's expected dict).
- A test asserting the exact set of `## Forbidden` bullets or table rows via string equality rather than `in` (fix: use `in`/substring assertions, don't fully replace).

- [ ] **Step 2: Manually sanity-check the two new prompt sections render sensibly**

Run: `.venv/bin/python -c "
from llm.soul import inject_agent
print(inject_agent('trading_agent/scan')[-3000:])
"`

Confirm the RESISTANCE_BREAKOUT section appears intact (no broken markdown, no truncation) in the assembled soul+scan.md prompt.

- [ ] **Step 3: No commit needed for this task** — Task 8 is verification-only. If Step 1 required fixes, commit those fixes individually with their own descriptive messages (not bundled into a generic "fix tests" commit).

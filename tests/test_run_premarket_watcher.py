"""장초반 선진입 워처(run_premarket_watcher.py) 테스트"""


def test_module_imports_without_error():
    import run_premarket_watcher  # noqa: F401


def test_check_entry_condition_passes_within_gap_and_trading_value():
    from run_premarket_watcher import _check_entry_condition

    ok, reason = _check_entry_condition(
        {"change_pct": 3.0, "trading_value": 80_000_000_000},
        {"min_open_change_pct": -2.0, "max_open_change_pct": 8.0, "min_5min_trading_value": 50_000_000_000},
    )

    assert ok is True
    assert "조건 충족" in reason


def test_check_entry_condition_fails_when_gap_out_of_range():
    from run_premarket_watcher import _check_entry_condition

    ok, reason = _check_entry_condition(
        {"change_pct": 12.0, "trading_value": 80_000_000_000},
        {"min_open_change_pct": -2.0, "max_open_change_pct": 8.0, "min_5min_trading_value": 50_000_000_000},
    )

    assert ok is False
    assert "갭 범위 미충족" in reason


def test_check_entry_condition_fails_when_trading_value_too_low():
    from run_premarket_watcher import _check_entry_condition

    ok, reason = _check_entry_condition(
        {"change_pct": 3.0, "trading_value": 10_000_000_000},
        {"min_open_change_pct": -2.0, "max_open_change_pct": 8.0, "min_5min_trading_value": 50_000_000_000},
    )

    assert ok is False
    assert "거래대금 미충족" in reason


def test_poll_once_uses_watchlist_intraday_snapshot_not_missing_mil_method(monkeypatch, tmp_path):
    """이전 버그: orch._mil.get_intraday_snapshot()는 MILContext에 존재하지 않는 메서드라
    호출 시 AttributeError로 조용히 매턴 스킵됐다(09:00~09:17 내내 아무 것도 안 감시).
    올바른 진입점(market_intelligence.stock.get_watchlist_intraday_snapshot)을 쓰는지 확인."""
    from run_premarket_watcher import _poll_once

    called = {}

    def fake_snapshot(ctx, phase, tickers):
        called["args"] = (phase, tickers)
        return {"tickers": [{"ticker": "000660", "change_pct": 3.0, "trading_value": 80_000_000_000}]}

    monkeypatch.setattr("market_intelligence.stock.get_watchlist_intraday_snapshot", fake_snapshot)
    monkeypatch.setattr("orchestrator_v3.load_watchlist", lambda: [])
    monkeypatch.setattr("orchestrator_v3.save_watchlist", lambda wl: None)
    monkeypatch.setattr("run_premarket_watcher._save_triggered", lambda triggered: None)
    monkeypatch.setattr("run_premarket_watcher._try_lock", lambda: open(tmp_path / "lock", "w"))

    class _FakeOrch:
        _mil = object()
        run_intraday_v3_called = False

        def run_intraday_v3(self):
            self.run_intraday_v3_called = True
            return {}

        class _Telegram:
            def notify(self, msg):
                pass

        _telegram = _Telegram()

    orch = _FakeOrch()
    candidates = [
        {"ticker": "000660", "name": "SK하이닉스", "theme": "반도체", "setup": "REVERSAL",
         "entry_condition": {"min_open_change_pct": -2.0, "max_open_change_pct": 8.0,
                              "min_5min_trading_value": 1}},
    ]

    _poll_once(orch, candidates, triggered=set())

    assert called.get("args") == ("PREMARKET", ["000660"])
    assert orch.run_intraday_v3_called is True

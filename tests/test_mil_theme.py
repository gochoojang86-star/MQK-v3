"""market_intelligence/theme.py 테스트"""
from market_intelligence.base import MILContext
from market_intelligence.theme import get_theme_candidates


class StubKiwoomApi:
    available = True

    def __init__(self, groups, components_by_code):
        self._groups = groups
        self._components_by_code = components_by_code

    def theme_groups(self, qry_tp="0", date_tp="1", flu_pl_amt_tp="1", stex_tp="1"):
        return {"thema_grp": self._groups}

    def theme_components(self, theme_code, date_tp="2", stex_tp="1"):
        return {"thema_comp_stk": self._components_by_code.get(theme_code, [])}


def make_ctx(**kwargs):
    return MILContext(kis_api=None, kiwoom_api=StubKiwoomApi(**kwargs))


def test_get_theme_candidates_strips_kiwoom_direction_sign_from_price():
    """2026-07-03 000660 분봉 사고와 같은 근본원인: 키움 cur_prc는 등락 방향을 부호로
    표시한다. 하락 중인 테마 구성종목의 price가 음수로 새어나가면 trading_value(=price
    × volume) 계산까지 함께 오염된다."""
    ctx = make_ctx(
        groups=[{"thema_grp_cd": "100", "thema_nm": "반도체", "flu_rt": "3.2",
                 "dt_prft_rt": "5.0", "stk_num": "10", "rising_stk_num": "7",
                 "fall_stk_num": "3", "main_stk": "SK하이닉스"}],
        components_by_code={
            "100": [
                {"stk_cd": "000660", "stk_nm": "SK하이닉스", "cur_prc": "-2196000",
                 "flu_rt": "-1.5", "acc_trde_qty": "1000000"},
            ],
        },
    )

    result = get_theme_candidates(ctx, "SCAN")

    candidate = result["candidates"][0]
    assert candidate["price"] == 2196000.0
    assert candidate["trading_value"] == 2196000.0 * 1000000

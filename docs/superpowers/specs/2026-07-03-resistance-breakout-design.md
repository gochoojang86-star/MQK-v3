# RESISTANCE_BREAKOUT — 저항선/라운드피겨 돌파 셋업 설계 스펙

**작성일**: 2026-07-03
**상태**: 설계 확정, 구현 대기
**배경**: 마하세븐(국내 스윙 트레이더) 매매 기법 중 "차트의 상승/하락이 멈추는 구간"(전고점, 라운드 피겨) 연구를 MQK v3에 접목. 기존 SCAN/INTRADAY 셋업(VOLUME_SURGE_LEADER/THEME_CATALYST/REVERSAL)은 전부 "거래대금 폭증" 또는 "낙폭과대 반등"만 다루고, "저항선을 대량거래로 돌파했을 때 신규 방향성으로 본다"는 관점이 빠져 있었음 — 이번 스펙으로 채운다.

## 0. 참고: 왜 눌림목 매수는 이미 구현돼 있는가

마하세븐 기법 중 "음봉(조정)에서의 바닥권 분할 매수"(펀더멘털 문제없는 시장 주도주가 단기 센티먼트로 밀렸을 때 진입)는 이미 SCAN의 REVERSAL 셋업과 LATE_INTRADAY 낙주 전술로 구현되어 있다. 이번 스펙은 그 반대 방향 — "강세 지속/신고가권 돌파"를 다룬다.

---

## 1. 셋업 정의

### RESISTANCE_BREAKOUT — 저항선 돌파

**대상**: `role=본류 대장주`인 종목만 (테마 내 거래대금 1위 — 기존 SCAN role 판정 로직 재사용, 후발주 돌파는 대상 아님).

**진입 조건** (아래 두 저항선 중 하나 이상 돌파):
1. **20일 고점 돌파**: 현재가 > 최근 20거래일 중 최고가
2. **라운드 피겨 돌파**: 현재가가 가격대별 라운드 단위(아래 표)를 상향 통과

| 가격대 | 라운드 단위 |
|---|---|
| 1만원 미만 | 1,000원 |
| 1만~10만원 | 5,000원 |
| 10만~100만원 | 10,000원 |
| 100만원 이상 | 100,000원 |

**필수 확인**: 거래대금이 최근 5일 평균 대비 2배 이상 (REVERSAL 셋업의 패닉셀 검증과 동일 배수 기준).

**confidence 가산**: 20일 고점 + 라운드 피겨를 **동시에** 돌파하면 `theme_evidence`에 "동시 돌파" 명시, confidence 상향 가능.

**청산(가짜 돌파)**: 돌파했던 저항선(20일 고점가 또는 라운드피겨가) 아래로 분봉 종가가 재이탈하면 즉시 청산. 기존 `sell_type=PRICE_SIGNAL`을 재사용(새 sell_type 신설 안 함), 조건만 "돌파 저항선 재이탈"로 추가.

---

## 2. 아키텍처

### 2.1 계산 함수 (신규, 순수 함수)

`_compute_resistance_facts(candles: list[dict], current_price: float) -> dict`

- 입력: `get_ohlcv`가 반환하는 일봉 candle 리스트(`[{date, open, high, low, close, volume, trading_value}, ...]`, 최근 것이 마지막)와 현재가. 두 값 모두 **동일한 `get_ohlcv` 응답 하나**에서 나온다 — `candles`는 `output2`, `current_price`는 같은 응답의 `output1.current_price`. 별도 호출 없음.
- 장중 호출 시 `candles`의 마지막 항목은 당일(아직 마감 안 된) 봉이다. `resistance_20d_high` 계산은 이 마지막(당일) 항목을 제외한 직전 20개로 계산하고, `is_breakout_round_figure` 판정의 "당일 시가"는 이 마지막 항목의 `open` 값을 쓴다.
- 출력:
  ```python
  {
      "resistance_20d_high": float,       # 최근 20거래일(당일 제외) 최고가
      "pct_from_resistance": float,       # (current_price - resistance_20d_high) / resistance_20d_high * 100
      "round_figure_price": float,        # 현재가 근처 라운드 가격(위 표 단위로 계산)
      "pct_from_round_figure": float,
      "is_breakout_20d_high": bool,       # current_price > resistance_20d_high
      "is_breakout_round_figure": bool,   # 당일 시가는 라운드피겨 아래였는데 현재가는 위인 경우
      "volume_vs_5d_avg_ratio": float,    # 오늘 거래대금 / 최근 5일 평균 거래대금
  }
  ```
- 계산은 전부 코드가 수행. LLM은 결과값만 읽는다 — 산술 오류(트리 판정 오류) 원천 차단.
- 위치: `orchestrator_v3.py` (기존 `_diversify_by_theme`, `_risk_off_leader_priority_tuple` 등 순수 헬퍼 함수들과 같은 모듈 레벨).

### 2.2 SCAN — 후보 풀 프리페치

`run_scan_v3()`가 `candidate_pool`을 구성한 직후, 기존 `_prefetch_pool_news(pool, top_n=12)`와 나란히 `_prefetch_pool_resistance(pool, top_n=15)`를 신규 추가:

- pool 상위 15개 후보(기존 `_signal_count`/우선순위 정렬 기준)에 대해서만 `mil_stock.get_ohlcv(ticker, period=25)` 호출 (20거래일 + 여유분)
- 종목별로 `_compute_resistance_facts` 실행해 `item["facts"]["resistance"] = {...}` 로 embed
- API 호출 최대 15콜로 고정 — 기존 `_prefetch_pool_news`와 동일한 비용 상한 패턴

### 2.3 INTRADAY — watchlist 스냅샷 확장

`get_watchlist_intraday_snapshot`(market_intelligence/stock.py) 내부에서:

- 기존 로직(가격/등락률/분봉)에 더해 `mil_stock.get_ohlcv(ctx, phase, ticker, period=25)` 호출 → `_compute_resistance_facts` 실행 → 반환 dict에 `resistance` 키로 병합
- `get_ohlcv`는 이미 `ctx.cached_call`로 캐싱되므로, 같은 날 10분 틱마다 반복 호출해도 실제 외부 API 콜은 최초 1회만 발생 — 신규 캐싱 로직 불필요

---

## 3. 리스크 게이팅 (이중 안전장치)

### 3.1 exploration_policy 확장

`_build_context`가 만드는 `exploration_policy`(INTRADAY 전용)에 신규 필드 추가:

```python
"resistance_breakout_allowed": not (_is_risk_off_regime(regime) or is_crash)
```

`_is_risk_off_regime`/`is_crash` 둘 다 2026-07-02~03 사고 대응으로 이미 존재하는 시그널을 그대로 재사용 — 레짐 라벨이 stale해도 실시간 폭락(`is_crash`)이면 즉시 차단된다.

### 3.2 코드 레벨 강제 (핵심)

`_sanitize_intraday_result`에서: `exploration_policy.resistance_breakout_allowed=False`인데 `setup=RESISTANCE_BREAKOUT`인 BUY proposal이 들어오면 **코드가 강제로 제거**한다. 기존에 `action=HOLD`인데 proposal이 섞여 들어오면 걸러내는 안전 패턴과 동일한 위치·방식.

**설계 원칙**: 프롬프트 지시만으로 리스크 게이팅을 신뢰하지 않는다 (2026-07-02 leader_reentry_confidence_floor 사고의 교훈). SCAN 단계는 프롬프트 레벨 금지(risk_off_mode일 때 신규 등재 금지 문구)로 충분 — SCAN은 watchlist만 갱신하고 실매수는 안 하기 때문. 실매수가 걸리는 INTRADAY는 반드시 코드 레벨 강제.

### 3.3 프롬프트 반영

- `scan.md`: 4번째 setup 유형으로 RESISTANCE_BREAKOUT 추가(조건 3.1 기준 명시) + Forbidden에 "risk_off_mode에서 이 셋업으로 신규 등재 금지" 추가
- `intraday.md`: 진입 근거 테이블에 행 추가("저항선 상향 돌파 확인 + 돌파 봉 거래대금 유지 + `exploration_policy.resistance_breakout_allowed=true`") + 청산 근거 테이블에 PRICE_SIGNAL 조건 보강("또는 돌파했던 저항선 아래로 재이탈")

---

## 4. 테스트 계획

- `_compute_resistance_facts`: 라운드피겨 단위 스케일링 4개 가격대 경계값, 20일 고점 계산, 단독/동시 돌파 판정, 거래대금 배수 계산
- `_prefetch_pool_resistance`: top_n=15 초과분 호출 안 함, facts 정확히 embed
- `get_watchlist_intraday_snapshot`: resistance 필드 포함 확인, 캐시 재사용으로 중복 API 콜 없음
- `exploration_policy.resistance_breakout_allowed`: RED 레짐 케이스 + "레짐 stale, 실시간 is_crash" 케이스 — 2026-07-02/03 밤 `leader_reentry_confidence_floor` 테스트 2개와 동일 패턴으로 작성
- `_sanitize_intraday_result`: resistance_breakout_allowed=False인데 RESISTANCE_BREAKOUT BUY 오면 제거되는지
- 프롬프트 텍스트 테스트: scan.md/intraday.md에 새 셋업 설명 + risk_off 금지 문구 존재 확인 (기존 `test_scan_prompt_mentions_*` 패턴)

## 5. 롤아웃

settings_patch가 아니라 결정론적 코드 계산 + 프롬프트라 자기개선 백테스트 게이트 불필요. 코드 레벨 강제가 이중으로 걸려 있어 폭락장 오작동 리스크 낮음. 별도 단계적 배포 없이 테스트 통과 후 바로 반영. 첫 실전 발동 시 기존 매수 알림 로직을 통해 텔레그램으로 통보되므로 초기 며칠은 실제 발동 여부를 관찰 권장.

## 6. 범위 제외 (YAGNI)

- 52주 고점 — 20일 고점만 사용(브레인스토밍에서 확정)
- 새로운 MIL 도구 — 기존 `get_ohlcv` 재사용, 신규 도구 없음
- 새로운 sell_type — 기존 `PRICE_SIGNAL` 재사용
- pool 전체 스캔(C안) — 상위 15개 프리페치(A안)로 제한

# API 보관소

키움증권 REST API와 한국투자증권(KIS) API 레퍼런스.  
원본 Excel → Markdown 변환 (`/tmp/build_api_docs.py`).  
원본 파일 위치: `C:\Users\gocho\Downloads\`

---

## 키움 REST API

- **전체 목록**: [kiwoom_index.md](kiwoom_index.md)
- **상세 문서**: `docs/api/kiwoom/{api_id}.md`

### 사용 중인 API

| API ID | API명 | 용도 |
|--------|-------|------|
| [ka10080](kiwoom/ka10080.md) | 주식분봉차트조회 | 장중 1분봉 수집 (intraday candles) |
| [ka10081](kiwoom/ka10081.md) | 주식일봉차트조회 | 일봉 OHLCV 배치 수집 |
| [ka10099](kiwoom/ka10099.md) | 종목정보 리스트 | 전 종목 유니버스 갱신 |
| [ka00198](kiwoom/ka00198.md) | 실시간종목조회순위 | 실시간 거래대금/등락률 순위 |
| [ka10021](kiwoom/ka10021.md) | 호가잔량급증요청 | 수급 감지 |
| [ka10023](kiwoom/ka10023.md) | 거래량급증요청 | 거래량 급증 스캔 |
| [ka10035](kiwoom/ka10035.md) | 외인연속순매매상위 | 외인 수급 |
| [ka10051](kiwoom/ka10051.md) | 업종별투자자순매수 | 업종 수급 |
| [ka10065](kiwoom/ka10065.md) | 장중투자자별매매상위 | 기관/외인 장중 동향 |
| [ka10171](kiwoom/ka10171.md) | 조건검색 목록조회 | 조건검색 목록 |
| [ka10172](kiwoom/ka10172.md) | 조건검색 요청(일반) | 조건검색 종목 편입 |
| [ka90001](kiwoom/ka90001.md) | 테마그룹별요청 | 테마 목록 |
| [ka90002](kiwoom/ka90002.md) | 테마구성종목요청 | 테마 구성 종목 |
| [ka90003](kiwoom/ka90003.md) | 프로그램순매수상위50 | 프로그램 매수 상위 |
| [ka90009](kiwoom/ka90009.md) | 외국인기관매매상위 | 외인/기관 매매 상위 |

### 연속조회 (cont-yn / next-key)
키움 API는 페이지네이션을 응답 헤더로 처리한다.  
`resp.headers.get("cont-yn") == "Y"` 이면 다음 페이지 존재.  
다음 요청 시 `cont-yn: Y`, `next-key: {값}` 헤더를 함께 전송.

---

## KIS (한국투자증권) API

- **전체 목록**: [kis_index.md](kis_index.md)
- **상세 문서**: `docs/api/kis/{tr_id}.md`

### 사용 중인 API

| TR_ID | API명 | 용도 |
|-------|-------|------|
| [FHKST01010100](kis/FHKST01010100.md) | 주식현재가 시세 | 현재가·시가·고가·저가·거래대금 스냅샷 |
| [FHKST01010900](kis/FHKST01010900.md) | 주식현재가 투자자 | 기관/외인 당일 순매수 |
| FHKST03010100 | 국내주식기간별시세 | 일봉 (문서 미포함) |
| [FHKST03010230](kis/FHKST03010230.md) | 주식일별분봉조회 | 장중 분봉 (KIS 폴백) |
| FHKST03030100 | 해외주식기간별시세 | 미국 지수 (문서 미포함) |
| [FHPUP02100000](kis/FHPUP02100000.md) | 국내업종 현재지수 | 코스피/코스닥 지수 |
| [FHPUP02140000](kis/FHPUP02140000.md) | 국내업종 구분별전체시세 | 업종별 시세 |
| [FHPST01700000](kis/FHPST01700000.md) | 국내주식 등락률 순위 | 상승률 상위 스캔 |
| [FHPST01710000](kis/FHPST01710000.md) | 거래량순위 | 거래량 상위 스캔 |
| [FHPPG04650201](kis/FHPPG04650201.md) | 종목별 프로그램매매추이 | 프로그램 수급 |
| [TTTC0802U](kis/TTTC8434R.md) / VTTC0802U | 주식매수주문 | 매수 (실전/모의) |
| [TTTC0801U](kis/TTTC8434R.md) / VTTC0801U | 주식매도주문 | 매도 (실전/모의) |
| [TTTC0013U](kis/TTTC0013U.md) / VTTC0013U | 주식주문 정정취소 | 정정·취소 |
| [TTTC8434R](kis/TTTC8434R.md) / VTTC8434R | 주식잔고조회 | 보유 잔고 |
| [TTTC8908R](kis/TTTC8908R.md) / VTTC8908R | 매수가능조회 | 매수 가능 금액 |
| [TTTC0084R](kis/TTTC0084R.md) | 정정취소가능주문조회 | 미체결 주문 조회 |

### KIS 주요 필드 단위 참고
| 필드 | 단위 | 비고 |
|------|------|------|
| `stck_prpr` | 원(KRW) | 현재가 |
| `stck_oprc` | 원(KRW) | 당일 시가 → `day_open` |
| `stck_hgpr` | 원(KRW) | 당일 고가 → `day_high` |
| `stck_lwpr` | 원(KRW) | 당일 저가 → `day_low` |
| `acml_tr_pbmn` | 원(KRW) | 누적 거래대금 |
| `hts_avls` | 억원 | 시가총액 (×100,000,000 = 원) |

### 키움 일봉 단위 참고
| 필드 | 단위 | 비고 |
|------|------|------|
| `cur_prc` / `open_pric` / `high_pric` / `low_pric` | 원(KRW) | 부호 포함 문자열 → `_abs_float()` |
| `trde_qty` | 주 | 거래량 |
| `trde_prica` | **백만원** | 거래대금 → ×1,000,000 해야 원 단위 |

# TTTC0084R — 주식정정취소가능주문조회

- **API 통신방식**: REST
- **메뉴 위치**: [국내주식] 주문/계좌
- **API 명**: 주식정정취소가능주문조회
- **API ID**: v1_국내주식-004
- **실전 TR_ID**: TTTC0084R
- **모의 TR_ID**: 모의투자 미지원
- **HTTP Method**: GET
- **실전 Domain**: https://openapi.koreainvestment.com:9443
- **모의 Domain**: 모의투자 미지원
- **URL 명**: /uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl
- **개요**: 주식정정취소가능주문조회 API입니다. 한 번의 호출에 최대 50건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다.

※ 주식주문(정정취소) 호출 전에 반드시 주식정정취소가능주문조회 호출을 통해 정정취소가능수량(output &gt; psbl_qty)을 확인하신 후 정정취소주문 내시기 바랍니다.
- **구분**: Element
- **Request Header**: content-type
- **Request Query Parameter**: CANO
- **Response Header**: content-type
- **Response Body**: rt_cd
- **Request Example (Python)**: {
	"ACNT_PRDT_CD": "01",
	"CANO": "810XXXXX",
	"CTX_AREA_FK100": "",
	"CTX_AREA_NK100": "",
	"INQR_DVSN_1": "0",
	"INQR_DVSN_2": "0"
}
- **Response Example**: {
  "ctx_area_fk100": "81055689^01^                                                                                        ",
  "ctx_area_nk100": "                                                                                                    ",
  "output": [
    {
      "ord_gno_brno": "06010",
      "odno": "0001569139",
      "orgn_odno": "0001569136",
      "ord_dvsn_name": "지정가",
      "pdno": "009150",
      "prdt_name": "SamsungElecMech",
      "rvse_cncl_dvsn_name": "BUY AMEND*",
      "ord_qty": "1",
      "ord_unpr": "140000",
      "ord_tmd": "131438",
      "tot_ccld_qty": "0",
      "tot_ccld_amt": "0",
      "psbl_qty": "1",
      "sll_buy_dvsn_cd": "02",
      "ord_dvsn_cd": "00",
      "mgco_aptm_odno": ""
    },
    {
      "ord_gno_brno": "06010",
      "odno": "0001569138",
      "orgn_odno": "",
      "ord_dvsn_name": "지정가",
      "pdno": "009150",
      "prdt_name": "SamsungElecMech",
      "rvse_cncl_dvsn_name": "",
      "ord_qty": "1",
      "ord_unpr": "200000",
      "ord_tmd": "131421",
      "tot_ccld_qty": "0",
      "tot_ccld_amt": "0",
      "psbl_qty": "1",
      "sll_buy_dvsn_cd": "02",
      "ord_dvsn_cd": "00",
      "mgco_aptm_odno": ""
    }
	],
  "rt_cd": "0",
  "msg_cd": "KIOK0510",
  "msg1": "조회가 완료되었습니다                                                           "
}
# TTTC8908R — 매수가능조회

- **API 통신방식**: REST
- **메뉴 위치**: [국내주식] 주문/계좌
- **API 명**: 매수가능조회
- **API ID**: v1_국내주식-007
- **실전 TR_ID**: TTTC8908R
- **모의 TR_ID**: VTTC8908R
- **HTTP Method**: GET
- **실전 Domain**: https://openapi.koreainvestment.com:9443
- **모의 Domain**: https://openapivts.koreainvestment.com:29443
- **URL 명**: /uapi/domestic-stock/v1/trading/inquire-psbl-order
- **개요**: 매수가능 조회 API입니다. 
실전계좌/모의계좌의 경우, 한 번의 호출에 최대 1건까지 확인 가능합니다.


1) 매수가능금액 확인
 . 미수 사용 X: nrcvb_buy_amt(미수없는매수금액) 확인
 . 미수 사용 O: max_buy_amt(최대매수금액) 확인


2) 매수가능수량 확인
 . 특정 종목 전량매수 시 가능수량을 확인하실 경우 ORD_DVSN:00(지정가)는 종목증거금율이 반영되지 않습니다. 
   따라서 "반드시" ORD_DVSN:01(시장가)로 지정하여 종목증거금율이 반영된 가능수량을 확인하시기 바랍니다. 

   (다만, 조건부지정가 등 특정 주문구분(ex.IOC)으로 주문 시 가능수량을 확인할 경우 주문 시와 동일한 주문구분(ex.IOC) 입력하여 가능수량 확인)

 . 미수 사용 X: ORD_DVSN:01(시장가) or 특정 주문구분(ex.IOC)로 지정하여 nrcvb_buy_qty(미수없는매수수량) 확인
 . 미수 사용 O: ORD_DVSN:01(시장가) or 특정 주문구분(ex.IOC)로 지정하여 max_buy_qty(최대매수수량) 확인
- **구분**: Element
- **Request Header**: content-type
- **Request Query Parameter**: CANO
- **Response Header**: content-type
- **Response Body**: rt_cd
- **Request Example (Python)**: {
	"CANO": "810XXXXX",
	"ACNT_PRDT_CD": "01",
	"PDNO": "005930",
	"ORD_UNPR": "0",
	"ORD_DVSN": "01",
	"CMA_EVLU_AMT_ICLD_YN": "N",
	"OVRS_ICLD_YN": "N"
}
- **Response Example**: {
  "output": {
    "ord_psbl_cash": "741191178",
    "ord_psbl_sbst": "0",
    "ruse_psbl_amt": "0",
    "fund_rpch_chgs": "0",
    "psbl_qty_calc_unpr": "70000",
    "nrcvb_buy_amt": "107177377",
    "nrcvb_buy_qty": "1531",
    "max_buy_amt": "1482382356",
    "max_buy_qty": "21176",
    "cma_evlu_amt": "0",
    "ovrs_re_use_amt_wcrc": "0",
    "ord_psbl_frcr_amt_wcrc": "1468797045293"
  },
  "rt_cd": "0",
  "msg_cd": "KIOK0510",
  "msg1": "조회가 완료되었습니다                                                           "
}
# VTTC0013U — 주식주문(정정취소)

- **API 통신방식**: REST
- **메뉴 위치**: [국내주식] 주문/계좌
- **API 명**: 주식주문(정정취소)
- **API ID**: v1_국내주식-003
- **실전 TR_ID**: TTTC0013U
- **모의 TR_ID**: VTTC0013U
- **HTTP Method**: POST
- **실전 Domain**: https://openapi.koreainvestment.com:9443
- **모의 Domain**: https://openapivts.koreainvestment.com:29443
- **URL 명**: /uapi/domestic-stock/v1/trading/order-rvsecncl
- **개요**: 주문 건에 대하여 정정 및 취소하는 API입니다. 단, 이미 체결된 건은 정정 및 취소가 불가합니다.

※ 정정은 원주문에 대한 주문단가 혹은 주문구분을 변경하는 사항으로, 정정이 가능한 수량은 원주문수량을 초과 할 수 없습니다.

※ 주식주문(정정취소) 호출 전에 반드시 주식정정취소가능주문조회 호출을 통해 정정취소가능수량(output &gt; psbl_qty)을 확인하신 후 정정취소주문 내시기 바랍니다.

※ POST API의 경우 BODY값의 key값들을 대문자로 작성하셔야 합니다.
   (EX. "CANO" : "12345678", "ACNT_PRDT_CD": "01",...)
- **구분**: Element
- **Request Header**: content-type
- **Request Body**: CANO
- **Response Header**: content-type
- **Response Body**: rt_cd
- **Request Example (Python)**: {
"CANO": "810XXXXX",
"ACNT_PRDT_CD": "01",
"KRX_FWDG_ORD_ORGNO": "",
"ORGN_ODNO": "0001566017",
"ORD_DVSN": "00",
"RVSE_CNCL_DVSN_CD": "01",
"ORD_QTY": "1",
"ORD_UNPR": "180000",
"QTY_ALL_ORD_YN": "N"
}
- **Response Example**: {
  "rt_cd": "0",
  "msg_cd": "APBK0013",
  "msg1": "주문 전송 완료 되었습니다.",
  "output": {
    "KRX_FWDG_ORD_ORGNO": "06010",
    "ODNO": "0001569139",
    "ORD_TMD": "131438"
  }
}
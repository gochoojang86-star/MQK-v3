# TTTC8434R — 주식잔고조회

- **API 통신방식**: REST
- **메뉴 위치**: [국내주식] 주문/계좌
- **API 명**: 주식잔고조회
- **API ID**: v1_국내주식-006
- **실전 TR_ID**: TTTC8434R
- **모의 TR_ID**: VTTC8434R
- **HTTP Method**: GET
- **실전 Domain**: https://openapi.koreainvestment.com:9443
- **모의 Domain**: https://openapivts.koreainvestment.com:29443
- **URL 명**: /uapi/domestic-stock/v1/trading/inquire-balance
- **개요**: 주식 잔고조회 API입니다. 
실전계좌의 경우, 한 번의 호출에 최대 50건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다. 
모의계좌의 경우, 한 번의 호출에 최대 20건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다. 

* 당일 전량매도한 잔고도 보유수량 0으로 보여질 수 있으나, 해당 보유수량 0인 잔고는 최종 D-2일 이후에는 잔고에서 사라집니다.

※ 중요 : 해당 API는 제공 정보량이 많아 조회속도가 느린 API입니다. 주문 준비를 위해서는 주식매수/매도가능수량 조회 TR 사용을 권장 드립니다.
- **구분**: Element
- **Request Header**: content-type
- **Request Query Parameter**: CANO
- **Response Header**: content-type
- **Response Body**: rt_cd
- **Request Example (Python)**: {
	"CANO": "810XXXXX",
	"ACNT_PRDT_CD": "01",
	"AFHR_FLPR_YN": "N",
	"OFL_YN": "",
	"INQR_DVSN": "01",
	"UNPR_DVSN": "01",
	"FUND_STTL_ICLD_YN": "N",
	"FNCG_AMT_AUTO_RDPT_YN": "N",
	"PRCS_DVSN": "01",
	"CTX_AREA_FK100": "",
	"CTX_AREA_NK100": ""
}
- **Response Example**: {
  "ctx_area_fk100": "81055689^01^N^N^01^01^N^                                                                            ",
  "ctx_area_nk100": "                                                                                                    ",
  "output1": [
    {
      "pdno": "009150",
      "prdt_name": "삼성전기",
      "trad_dvsn_name": "현금",
      "bfdy_buy_qty": "12",
      "bfdy_sll_qty": "0",
      "thdt_buyqty": "1686",
      "thdt_sll_qty": "41",
      "hldg_qty": "1657",
      "ord_psbl_qty": "1611",
      "pchs_avg_pric": "135440.2517",
      "pchs_amt": "224424497",
      "prpr": "0",
      "evlu_amt": "0",
      "evlu_pfls_amt": "0",
      "evlu_pfls_rt": "0.00",
      "evlu_erng_rt": "0.00000000",
      "loan_dt": "",
      "loan_amt": "0",
      "stln_slng_chgs": "0",
      "expd_dt": "",
      "fltt_rt": "-100.00000000",
      "bfdy_cprs_icdc": "-184500",
      "item_mgna_rt_name": "",
      "grta_rt_name": "",
      "sbst_pric": "140220",
      "stck_loan_unpr": "0.0000"
    },
    {
      "pdno": "009150",
      "prdt_name": "삼성전기",
      "trad_dvsn_name": "자기융자",
      "bfdy_buy_qty": "3",
      "bfdy_sll_qty": "0",
      "thdt_buyqty": "0",
      "thdt_sll_qty": "0",
      "hldg_qty": "3",
      "ord_psbl_qty": "3",
      "pchs_avg_pric": "123000.0000",
      "pchs_amt": "369000",
      "prpr": "0",
      "evlu_amt": "0",
      "evlu_pfls_amt": "0",
      "evlu_pfls_rt": "0.00",
      "evlu_erng_rt": "0.00000000",
      "loan_dt": "20211223",
      "loan_amt": "369000",
      "stln_slng_chgs": "0",
      "expd_dt": "",
      "fltt_rt": "-100.00000000",
      "bfdy_cprs_icdc": "-184500",
      "item_mgna_rt_name": "",
      "grta_rt_name": "",
      "sbst_pric": "140220",
      "stck_loan_unpr": "123000.0000"
    }
	  ],
  "output2": [
        {
            "dnca_tot_amt": "346455",
            "nxdy_excc_amt": "346455",
            "prvs_rcdl_excc_amt": "346455",
            "cma_evlu_amt": "0",
            "bfdy_buy_amt": "0",
            "thdt_buy_amt": "0",
            "nxdy_auto_rdpt_amt": "0",
            "bfdy_sll_amt": "0",
            "thdt_sll_amt": "0",
            "d2_auto_rdpt_amt": "0",
            "bfdy_tlex_amt": "0",
            "thdt_tlex_amt": "0",
            "tot_loan_amt": "0",
            "scts_evlu_amt": "1759600",
            "tot_evlu_amt": "2106055",
            "nass_amt": "2106055",
            "fncg_gld_auto_rdpt_yn": "",
            "pchs_amt_smtl_amt": "2516522",
            "evlu_amt_smtl_amt": "1759600",
            "evlu_pfls_smtl_amt": "-756922",
            "tot_stln_slng_chgs": "0",
            "bfdy_tot_asst_evlu_amt": "2142945",
            "asst_icdc_amt": "-36890",
            "asst_icdc_erng_rt": "0.00000000"
        }
    ],
  "rt_cd": "0",
  "msg_cd": "KIOK0510",
  "msg1": "조회가 완료되었습니다                                                           "
}
# 키움 REST API 목록

| No | API ID | API명 | 대분류 | 중분류 | URL |
|----|--------|-------|--------|--------|-----|
| 1 | `au10001` | 접근토큰 발급 | OAuth 인증 | 접근토큰발급 | `/oauth2/token` |
| 2 | `au10002` | 접근토큰폐기 | OAuth 인증 | 접근토큰폐기 | `/oauth2/revoke` |
| 3 | `ka00001` | 계좌번호조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 4 | `ka00198` | 실시간종목조회순위 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 5 | `ka01690` | 일별잔고수익률 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 6 | `ka10001` | 주식기본정보요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 7 | `ka10002` | 주식거래원요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 8 | `ka10003` | 체결정보요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 9 | `ka10004` | 주식호가요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 10 | `ka10005` | 주식일주월시분요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 11 | `ka10006` | 주식시분요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 12 | `ka10007` | 시세표성정보요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 13 | `ka10008` | 주식외국인종목별매매동향 | 국내주식 | 기관/외국인 | `/api/dostk/frgnistt` |
| 14 | `ka10009` | 주식기관요청 | 국내주식 | 기관/외국인 | `/api/dostk/frgnistt` |
| 15 | `ka10010` | 업종프로그램요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 16 | `ka10011` | 신주인수권전체시세요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 17 | `ka10013` | 신용매매동향요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 18 | `ka10014` | 공매도추이요청 | 국내주식 | 공매도 | `/api/dostk/shsa` |
| 19 | `ka10015` | 일별거래상세요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 20 | `ka10016` | 신고저가요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 21 | `ka10017` | 상하한가요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 22 | `ka10018` | 고저가근접요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 23 | `ka10019` | 가격급등락요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 24 | `ka10020` | 호가잔량상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 25 | `ka10021` | 호가잔량급증요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 26 | `ka10022` | 잔량율급증요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 27 | `ka10023` | 거래량급증요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 28 | `ka10024` | 거래량갱신요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 29 | `ka10025` | 매물대집중요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 30 | `ka10026` | 고저PER요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 31 | `ka10027` | 전일대비등락률상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 32 | `ka10028` | 시가대비등락률요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 33 | `ka10029` | 예상체결등락률상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 34 | `ka10030` | 당일거래량상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 35 | `ka10031` | 전일거래량상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 36 | `ka10032` | 거래대금상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 37 | `ka10033` | 신용비율상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 38 | `ka10034` | 외인기간별매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 39 | `ka10035` | 외인연속순매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 40 | `ka10036` | 외인한도소진율증가상위 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 41 | `ka10037` | 외국계창구매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 42 | `ka10038` | 종목별증권사순위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 43 | `ka10039` | 증권사별매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 44 | `ka10040` | 당일주요거래원요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 45 | `ka10042` | 순매수거래원순위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 46 | `ka10043` | 거래원매물대분석요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 47 | `ka10044` | 일별기관매매종목요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 48 | `ka10045` | 종목별기관매매추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 49 | `ka10046` | 체결강도추이시간별요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 50 | `ka10047` | 체결강도추이일별요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 51 | `ka10048` | ELW일별민감도지표요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 52 | `ka10050` | ELW민감도지표요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 53 | `ka10051` | 업종별투자자순매수요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 54 | `ka10052` | 거래원순간거래량요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 55 | `ka10053` | 당일상위이탈원요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 56 | `ka10054` | 변동성완화장치발동종목요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 57 | `ka10055` | 당일전일체결량요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 58 | `ka10058` | 투자자별일별매매종목요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 59 | `ka10059` | 종목별투자자기관별요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 60 | `ka10060` | 종목별투자자기관별차트요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 61 | `ka10061` | 종목별투자자기관별합계요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 62 | `ka10062` | 동일순매매순위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 63 | `ka10063` | 장중투자자별매매요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 64 | `ka10064` | 장중투자자별매매차트요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 65 | `ka10065` | 장중투자자별매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 66 | `ka10066` | 장마감후투자자별매매요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 67 | `ka10068` | 대차거래추이요청 | 국내주식 | 대차거래 | `/api/dostk/slb` |
| 68 | `ka10069` | 대차거래상위10종목요청 | 국내주식 | 대차거래 | `/api/dostk/slb` |
| 69 | `ka10072` | 일자별종목별실현손익요청_일자 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 70 | `ka10073` | 일자별종목별실현손익요청_기간 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 71 | `ka10074` | 일자별실현손익요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 72 | `ka10075` | 미체결요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 73 | `ka10076` | 체결요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 74 | `ka10077` | 당일실현손익상세요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 75 | `ka10078` | 증권사별종목매매동향요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 76 | `ka10079` | 주식틱차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 77 | `ka10080` | 주식분봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 78 | `ka10081` | 주식일봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 79 | `ka10082` | 주식주봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 80 | `ka10083` | 주식월봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 81 | `ka10084` | 당일전일체결요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 82 | `ka10085` | 계좌수익률요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 83 | `ka10086` | 일별주가요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 84 | `ka10087` | 시간외단일가요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 85 | `ka10088` | 미체결 분할주문 상세 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 86 | `ka10094` | 주식년봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 87 | `ka10095` | 관심종목정보요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 88 | `ka10098` | 시간외단일가등락율순위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 89 | `ka10099` | 종목정보 리스트 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 90 | `ka10100` | 종목정보 조회 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 91 | `ka10101` | 업종코드 리스트 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 92 | `ka10102` | 회원사 리스트 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 93 | `ka10131` | 기관외국인연속매매현황요청 | 국내주식 | 기관/외국인 | `/api/dostk/frgnistt` |
| 94 | `ka10170` | 당일매매일지요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 95 | `ka10171` | 조건검색 목록조회 | 국내주식 | 조건검색 | `/api/dostk/websocket` |
| 96 | `ka10172` | 조건검색 요청 일반 | 국내주식 | 조건검색 | `/api/dostk/websocket` |
| 97 | `ka10173` | 조건검색 요청 실시간 | 국내주식 | 조건검색 | `/api/dostk/websocket` |
| 98 | `ka10174` | 조건검색 실시간 해제 | 국내주식 | 조건검색 | `/api/dostk/websocket` |
| 99 | `ka20001` | 업종현재가요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 100 | `ka20002` | 업종별주가요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 101 | `ka20003` | 전업종지수요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 102 | `ka20004` | 업종틱차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 103 | `ka20005` | 업종분봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 104 | `ka20006` | 업종일봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 105 | `ka20007` | 업종주봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 106 | `ka20008` | 업종월봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 107 | `ka20009` | 업종현재가일별요청 | 국내주식 | 업종 | `/api/dostk/sect` |
| 108 | `ka20019` | 업종년봉조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 109 | `ka20068` | 대차거래추이요청(종목별) | 국내주식 | 대차거래 | `/api/dostk/slb` |
| 110 | `ka30001` | ELW가격급등락요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 111 | `ka30002` | 거래원별ELW순매매상위요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 112 | `ka30003` | ELWLP보유일별추이요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 113 | `ka30004` | ELW괴리율요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 114 | `ka30005` | ELW조건검색요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 115 | `ka30009` | ELW등락율순위요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 116 | `ka30010` | ELW잔량순위요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 117 | `ka30011` | ELW근접율요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 118 | `ka30012` | ELW종목상세정보요청 | 국내주식 | ELW | `/api/dostk/elw` |
| 119 | `ka40001` | ETF수익율요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 120 | `ka40002` | ETF종목정보요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 121 | `ka40003` | ETF일별추이요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 122 | `ka40004` | ETF전체시세요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 123 | `ka40006` | ETF시간대별추이요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 124 | `ka40007` | ETF시간대별체결요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 125 | `ka40008` | ETF일자별체결요청 | 국내주식 | ETF | `/api/dostk/etf` |
| 126 | `ka40009` | ETF시간대별NAV현황 | 국내주식 | ETF | `/api/dostk/etf` |
| 127 | `ka40010` | ETF시간대별수급현황 | 국내주식 | ETF | `/api/dostk/etf` |
| 128 | `ka50010` | 금현물체결추이 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 129 | `ka50012` | 금현물일별추이 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 130 | `ka50079` | 금현물틱차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 131 | `ka50080` | 금현물분봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 132 | `ka50081` | 금현물일봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 133 | `ka50082` | 금현물주봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 134 | `ka50083` | 금현물월봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 135 | `ka50087` | 금현물예상체결 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 136 | `ka50091` | 금현물당일틱차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 137 | `ka50092` | 금현물당일분봉차트조회요청 | 국내주식 | 차트 | `/api/dostk/chart` |
| 138 | `ka50100` | 금현물 시세정보 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 139 | `ka50101` | 금현물 호가 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 140 | `ka52301` | 금현물투자자현황 | 국내주식 | 기관/외국인 | `/api/dostk/frgnistt` |
| 141 | `ka90001` | 테마그룹별요청 | 국내주식 | 테마 | `/api/dostk/thme` |
| 142 | `ka90002` | 테마구성종목요청 | 국내주식 | 테마 | `/api/dostk/thme` |
| 143 | `ka90003` | 프로그램순매수상위50요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 144 | `ka90004` | 종목별프로그램매매현황요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 145 | `ka90005` | 프로그램매매추이요청 시간대별 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 146 | `ka90006` | 프로그램매매차익잔고추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 147 | `ka90007` | 프로그램매매누적추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 148 | `ka90008` | 종목시간별프로그램매매추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 149 | `ka90009` | 외국인기관매매상위요청 | 국내주식 | 순위정보 | `/api/dostk/rkinfo` |
| 150 | `ka90010` | 프로그램매매추이요청 일자별 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 151 | `ka90012` | 대차거래내역요청 | 국내주식 | 대차거래 | `/api/dostk/slb` |
| 152 | `ka90013` | 종목일별프로그램매매추이요청 | 국내주식 | 시세 | `/api/dostk/mrkcond` |
| 153 | `kt00001` | 예수금상세현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 154 | `kt00002` | 일별추정예탁자산현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 155 | `kt00003` | 추정자산조회요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 156 | `kt00004` | 계좌평가현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 157 | `kt00005` | 체결잔고요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 158 | `kt00007` | 계좌별주문체결내역상세요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 159 | `kt00008` | 계좌별익일결제예정내역요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 160 | `kt00009` | 계좌별주문체결현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 161 | `kt00010` | 주문인출가능금액요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 162 | `kt00011` | 증거금율별주문가능수량조회요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 163 | `kt00012` | 신용보증금율별주문가능수량조회요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 164 | `kt00013` | 증거금세부내역조회요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 165 | `kt00015` | 위탁종합거래내역요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 166 | `kt00016` | 일별계좌수익률상세현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 167 | `kt00017` | 계좌별당일현황요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 168 | `kt00018` | 계좌평가잔고내역요청 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 169 | `kt10000` | 주식 매수주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 170 | `kt10001` | 주식 매도주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 171 | `kt10002` | 주식 정정주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 172 | `kt10003` | 주식 취소주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 173 | `kt10006` | 신용 매수주문 | 국내주식 | 신용주문 | `/api/dostk/crdordr` |
| 174 | `kt10007` | 신용 매도주문 | 국내주식 | 신용주문 | `/api/dostk/crdordr` |
| 175 | `kt10008` | 신용 정정주문 | 국내주식 | 신용주문 | `/api/dostk/crdordr` |
| 176 | `kt10009` | 신용 취소주문 | 국내주식 | 신용주문 | `/api/dostk/crdordr` |
| 177 | `kt20016` | 신용융자 가능종목요청 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 178 | `kt20017` | 신용융자 가능문의 | 국내주식 | 종목정보 | `/api/dostk/stkinfo` |
| 179 | `kt50000` | 금현물 매수주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 180 | `kt50001` | 금현물 매도주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 181 | `kt50002` | 금현물 정정주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 182 | `kt50003` | 금현물 취소주문 | 국내주식 | 주문 | `/api/dostk/ordr` |
| 183 | `kt50020` | 금현물 잔고확인 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 184 | `kt50021` | 금현물 예수금 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 185 | `kt50030` | 금현물 주문체결전체조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 186 | `kt50031` | 금현물 주문체결조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 187 | `kt50032` | 금현물 거래내역조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 188 | `kt50075` | 금현물 미체결조회 | 국내주식 | 계좌 | `/api/dostk/acnt` |
| 189 | `00` | 주문체결 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 190 | `04` | 잔고 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 191 | `0A` | 주식기세 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 192 | `0B` | 주식체결 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 193 | `0C` | 주식우선호가 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 194 | `0D` | 주식호가잔량 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 195 | `0E` | 주식시간외호가 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 196 | `0F` | 주식당일거래원 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 197 | `0G` | ETF NAV | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 198 | `0H` | 주식예상체결 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 199 | `0I` | 국제금환산가격 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 200 | `0J` | 업종지수 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 201 | `0U` | 업종등락 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 202 | `0g` | 주식종목정보 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 203 | `0m` | ELW 이론가 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 204 | `0s` | 장시작시간 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 205 | `0u` | ELW 지표 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 206 | `0w` | 종목프로그램매매 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 207 | `1h` | VI발동/해제 | 국내주식 | 실시간시세 | `/api/dostk/websocket` |
| 208 | `공통` | 오류코드 |  |  | `` |
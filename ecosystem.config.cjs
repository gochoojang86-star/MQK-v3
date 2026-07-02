// ecosystem.config.cjs
module.exports = {
  apps: [
    {
      name: "mqk-holiday-check",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "holiday_check" },
      cron_restart: "30 0 * * *",   // KST 00:30
      autorestart: false,
    },
    {
      name: "mqk-v3-premarket-early",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "premarket_sejuk" },
      // KST 08:45 — 장전 상한가 세력 검증 + 진입 후보 watchlist 선주입.
      cron_restart: "45 8 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-premarket-first",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "premarket_first" },
      // KST 08:50 — 장 열리기 전 첫 레짐 판단.
      // 미국 야간 데이터(나스닥/S&P500/VIX/환율) + 전일 확정 데이터 기반.
      // 09:03 일반 레짐과 달리 시가 전 판단이라 선제적 포지셔닝에 활용.
      cron_restart: "50 8 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-premarket",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "premarket" },
      // KST 09:03 / 11:03 / 13:03 — 장 시작 후 시가 흐름 반영 레짐 평가.
      // :03인 이유: intraday */10 틱(:00)과 flock 충돌을 피하기 위함.
      cron_restart: "3 9,11,13 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-scan",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "scan" },
      // KST 09:17/10:17/11:17/13:17 — 레짐 평가 직후 + 장중 신규 급등주 조기 탐지.
      // 10:17 추가: 09:17~11:17 사이 2시간 공백 해소 (장초반 급등 종목 +10% 수준에서 포착).
      // :17인 이유: intraday */10 틱(:10, :20)과 flock 충돌을 피하기 위함.
      cron_restart: "17 9,10,11,13 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-scan-eod",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "scan" },
      // KST 15:00 — 장마감 전 마지막 watchlist 갱신 (기존 14:17에서 이동).
      // close(15:18) 직전 최신 watchlist 확보 목적.
      cron_restart: "0 15 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-intraday",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "intraday" },
      // KST 09:00~14:50, 10분 간격 (LLM 비용 절감 — Tier2 드리프트 감시 주기도 10분).
      // 09:03 레짐 생성 전 틱(09:00)이나 premarket 실패일에는 당일-레짐 가드가 스킵.
      // watchlist 0 + 보유 0 + STABLE이면 코드 게이트가 LLM 호출 없이 스킵.
      cron_restart: "*/10 9-14 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-premarket-close",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "premarket_close" },
      // KST 15:10 — 마감 직전 레짐 재평가. 직전 13:03 레짐과 비교해 마감 국면 판단.
      // close(15:18)보다 먼저 실행해 최신 레짐을 close context에 반영.
      cron_restart: "10 15 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-late-intraday",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "late_intraday" },
      // KST 15:08/15:13 — 폭락일(지수 -3%↓ 또는 RED) 전용 과매도 낙주 종가 부근 진입.
      // 평상시에는 코드 게이트가 LLM 호출 없이 즉시 스킵한다 (비용 0).
      // close(15:18)와의 flock 충돌을 피해 앞당김.
      cron_restart: "8,13 15 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-premarket-watcher",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_premarket_watcher.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      // KST 09:00 — 장초반 선진입 후보 감시 (09:05~09:17 실제 폴링, 09:17 종료).
      // market_close가 남긴 premarket_entry_candidates 조건 충족 시 intraday 즉시 트리거.
      cron_restart: "0 9 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-psearch-watcher",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_psearch_watcher.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      // KST 09:01 기동 → 내부 루프(90초 폴링)로 15:06까지 조건검색 편입 감시 (유사 웹훅).
      // 신규 편입: 알림 + watchlist 병합 + intraday LLM 즉시 트리거 (낙주는 알림만).
      cron_restart: "1 9 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-close",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "close" },
      // KST 15:18 — 정규장 내 청산 판단(일반 주문, 동시호가 직전 = 사실상 종가 청산).
      // 모의투자가 장후 시간외(06) 주문을 미지원하므로 정규장 내로 당김. 복기는 market_close(17:00)가 수행.
      cron_restart: "18 15 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-v3-market-close",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/run_schedule_v3.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      env: { MQK_PHASE: "market_close" },
      cron_restart: "0 17 * * 1-5",  // KST 17:00
      autorestart: false,
    },
    // MCP 비활성화
    // {
    //   name: "mqk-kis-mcp",
    //   script: "server.py",
    //   cwd: "/home/gochoojang/kis-mcp-source/MCP/Kis Trading MCP",
    //   interpreter: "/home/gochoojang/kis-mcp-source/MCP/Kis Trading MCP/.venv/bin/python",
    //   env: { ENV: "mqk" },
    //   autorestart: true,
    //   restart_delay: 3000,
    // },
    {
      name: "mqk-ohlcv-collect",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "/mnt/c/Users/gocho/MQK-v2/collect_ohlcv.py",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      // KST 19:00 평일 — 종가 확정(15:30) 후 충분한 여유를 두고 실행.
      // 전 종목 60일치 수집 약 23분 소요. 완료 후 프로세스 종료.
      cron_restart: "0 19 * * 1-5",
      autorestart: false,
    },
    {
      name: "mqk-telegram-news",
      script: "/mnt/c/Users/gocho/MQK-v2/.venv/bin/python",
      args: "-m broker.telegram_news",
      cwd: "/mnt/c/Users/gocho/MQK-v2",
      autorestart: true,
      restart_delay: 3000,
    },
  ],
};

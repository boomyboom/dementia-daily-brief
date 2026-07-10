# 치매·AD 데일리 브리프

치매·알츠하이머병 연구, 진단 소프트웨어 규제·인허가(신의료기술 포함), 시장·투자,
경쟁사 동향을 매일 오전 8시(신규)·오후 2시(갱신, KST)에 자동 수집·요약하는 정적 대시보드.

- `index.html` — 대시보드 (GitLab Pages로 서빙: https://beaubrainsbpark.gitlab.io/dementia-daily-brief/)
- `briefs/YYYY-MM-DD.json` — 일별 브리핑 데이터 (30일 지나면 자동 삭제)
- `briefs/manifest.json` — 날짜 목록
- `briefs/seen_urls.json` — 중복 게재 방지용 원문 URL 목록
- `BRIEFING_GUIDE.md` — 브리핑 생성 규칙, 경쟁사 추적 목록
- `BRIEF_PROMPT.md` — 자동 실행 프롬프트
- `run_daily_brief.sh` — launchd가 호출하는 실행 스크립트
- `cleanup_old_briefs.py` — 30일 경과 브리핑 정리
- `slack_notify.py` — Slack 발송(평일만, 갱신분만)
- `holidays_kr.json` — Slack 스킵 대상 공휴일

자동 실행: macOS launchd(`~/Library/LaunchAgents/com.beaubrain.dailybrief.plist`)가
매일 08:00·14:00에 `run_daily_brief.sh`를 실행 → 헤드리스 `claude`가 `BRIEF_PROMPT.md`를 따라
브리핑을 생성/갱신하고 GitLab에 push한다.

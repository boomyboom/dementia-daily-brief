치매·알츠하이머병 데일리 브리프를 생성하고 GitHub Pages 사이트를 갱신하라. 이 작업은 사람이 보지 않는 자동 실행이므로, 막히면 멈추지 말고 합리적으로 판단해 끝까지 진행한다.

## 저장소
- 로컬 경로: /Applications/BeauBrain/700_Utils/004_DAILY_BRIEF (이미 이 디렉토리에서 실행 중)
- 원격: https://github.com/boomyboom/dementia-daily-brief (main 브랜치, gh CLI 인증됨)
- 사이트: https://boomyboom.github.io/dementia-daily-brief/

## 절차
1. `git pull`로 최신 상태를 받는다.
2. 오늘 날짜(KST, `date +%Y-%m-%d`)를 확인하고, 실행 모드를 판단한다.
   - **신규 모드 (오늘 파일 없음, 보통 오전 첫 실행)**: 아래 절차대로 오늘 브리핑을 새로 생성한다.
   - **갱신 모드 (오늘 파일 이미 있음, 보통 오후 실행)**: 기존 `briefs/오늘날짜.json`을 읽어 이미 실린 항목을 모두 파악한 뒤, 그 이후 새로 공개된 검증된 소식만 찾아 **해당 섹션에 추가(병합)**한다. 기존 항목은 그대로 두고, 이미 실린 것·이전 브리핑과 중복되는 것은 절대 추가하지 않는다. 새로 추가할 검증된 소식이 하나도 없으면 파일을 바꾸지 말고 그대로 종료한다(빈 커밋 금지).
3. `BRIEFING_GUIDE.md`를 읽고 그 규칙을 정확히 따른다. 수집 대상 섹션(research/regulatory/market/competitors/media), 경쟁사 추적 목록, 품질 규칙, JSON 포맷이 모두 정의되어 있다.
4. `briefs/` 폴더의 최근 브리핑 파일 2~3개를 읽어 이미 다룬 소식을 파악한다(중복 게재 금지).
5. 웹 검색(한국어+영어)으로 5개 섹션의 최신 소식을 수집한다. 섹션별로 Task 서브에이전트를 병렬 실행하면 효율적이다:
   - research: PubMed/주요 저널의 치매·AD 논문, 뇌영상(MRI/PET) AI, 바이오마커, 임상시험 결과
   - regulatory: FDA 인허가, 식약처 허가, NECA 신의료기술·평가유예·혁신의료기술 고시, 심평원 수가
   - market: 시장 리포트, 투자·M&A, 치료제(레켐비/키순라) 시장 동향
   - competitors: BRIEFING_GUIDE.md의 추적 목록 기업 동향 (뉴로핏, 뷰노, 제이엘케이 등)
   - media: Alzforum/Fierce Biotech/국내 의료전문지 주요 보도
6. 검증된 항목으로 `briefs/오늘날짜.json`을 BRIEFING_GUIDE.md의 JSON 포맷대로 작성한다. 모든 항목에 실제 원문 URL 필수. 섹션에 소식이 없으면 빈 배열로 둔다.
   - 신규 모드: headline은 그날 가장 중요한 소식 한 문장으로 새로 작성한다.
   - 갱신 모드: 기존 항목을 유지한 채 새 항목만 각 섹션에 덧붙인다. headline은 기존 것을 유지하되, 새로 추가된 소식이 그날 가장 중요하다면 그때만 교체한다.
7. `briefs/manifest.json`의 dates 배열에 오늘 날짜가 없으면 추가한다(이미 있으면 그대로 둔다).
8. `python3 -m json.tool`로 두 JSON 파일의 유효성을 검증한다.
9. `git push origin main`으로 푸시한다. 커밋 메시지는 신규 모드면 `brief: YYYY-MM-DD 데일리 브리프 추가`, 갱신 모드면 `brief: YYYY-MM-DD 갱신 (추가 N건)`으로 한다. index.html 등 사이트 코드는 수정하지 않는다.

## 성공 기준
- briefs/오늘날짜.json이 유효한 JSON으로 생성·푸시됨
- 모든 항목이 최근 소식이고 원문 URL이 있으며 이전 브리핑과 중복되지 않음
- BeauBrain(뇌 MRI 기반 치매 진단 SW) 사업 관련성이 높은 소식에 importance high/medium이 정확히 매겨짐

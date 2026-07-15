치매·알츠하이머병 데일리 브리프를 생성하고 GitHub Pages 사이트를 갱신하라. 이 작업은 사람이 보지 않는 자동 실행이므로, 막히면 멈추지 말고 합리적으로 판단해 끝까지 진행한다.

## 저장소
- 로컬 경로: /Applications/BeauBrain/700_Utils/004_DAILY_BRIEF (이미 이 디렉토리에서 실행 중)
- 원격: https://gitlab.com/beaubrainsbpark/dementia-daily-brief (main 브랜치, 토큰 인증됨)
- 사이트: https://beaubrainsbpark.gitlab.io/dementia-daily-brief/

## 절차
1. `git pull`로 최신 상태를 받는다.
2. 오늘 날짜(KST, `date +%Y-%m-%d`)를 확인하고, 실행 모드를 판단한다.
   - **신규 모드 (오늘 파일 없음, 보통 오전 첫 실행)**: 아래 절차대로 오늘 브리핑을 새로 생성한다.
   - **갱신 모드 (오늘 파일 이미 있음, 보통 오후 실행)**: 기존 `briefs/오늘날짜.json`을 읽어 이미 실린 항목을 모두 파악한 뒤, 그 이후 새로 공개된 검증된 소식만 찾아 **해당 섹션에 추가(병합)**한다. 기존 항목은 그대로 두고, 이미 실린 것·이전 브리핑과 중복되는 것은 절대 추가하지 않는다. 새로 추가할 검증된 소식이 하나도 없으면 파일을 바꾸지 말고 그대로 종료한다(빈 커밋 금지).
3. `BRIEFING_GUIDE.md`를 읽고 그 규칙을 정확히 따른다. 수집 대상 섹션(research/regulatory/market/competitors/media), 경쟁사 추적 목록, 품질 규칙, JSON 포맷이 모두 정의되어 있다.
4. 중복과 낡은 자료를 방지한다.
   - `briefs/seen_urls.json`(지금까지 게재한 모든 원문 URL 목록)을 읽는다. **이 목록에 이미 있는 URL은 절대 다시 게재하지 않는다(하드 차단).**
   - 추가로 `briefs/` 폴더의 최근 브리핑 파일 5~7개를 읽어, **URL이 달라도 같은 사건·같은 논문·같은 정책을 다룬 항목은 중복으로 보고 제외**한다. (예: "제5차 치매관리종합계획", 특정 제품의 같은 인허가 등 — 다른 매체가 재보도해도 이미 다뤘으면 넣지 않는다.)
   - **신선도**: 원문 발행일이 오늘로부터 7일 이상 지난 것은 넣지 않는다. 정부계획·제도처럼 "새 소식이 아니라 기존 사실의 재보도"인 경우도 제외한다. 억지로 채우지 말고, 신규·검증된 소식이 없는 섹션은 빈 배열로 둔다.
5. 웹 검색(한국어+영어)으로 5개 섹션의 최신 소식을 수집한다. 섹션별로 Task 서브에이전트를 병렬 실행하면 효율적이다:
   - research: PubMed/주요 저널의 치매·AD 논문, 뇌영상(MRI/PET) AI, 바이오마커, 임상시험 결과
   - regulatory: FDA 인허가, 식약처 허가, NECA 신의료기술·평가유예·혁신의료기술 고시, 심평원 수가
   - market: 시장 리포트, 투자·M&A, 치료제(레켐비/키순라) 시장 동향
   - competitors: BRIEFING_GUIDE.md의 추적 목록 기업 동향 (뉴로핏, 뷰노, 제이엘케이 등)
   - media: Alzforum/Fierce Biotech/국내 의료전문지 주요 보도
6. 검증된 항목으로 `briefs/오늘날짜.json`을 BRIEFING_GUIDE.md의 JSON 포맷대로 작성한다. 모든 항목에 실제 원문 URL 필수. 섹션에 소식이 없으면 빈 배열로 둔다.
   - 신규 모드: headline은 그날 가장 중요한 소식 한 문장으로 새로 작성한다.
   - 갱신 모드: 기존 항목을 유지한 채 새 항목만 각 섹션에 덧붙인다. headline은 기존 것을 유지하되, 새로 추가된 소식이 그날 가장 중요하다면 그때만 교체한다.
7. `python3 cleanup_old_briefs.py`를 실행한다. 이 스크립트가 30일 지난 브리핑 파일을 삭제하고, `briefs/manifest.json`(날짜 목록)과 `briefs/seen_urls.json`(중복 차단용 URL 목록)을 남은 브리핑 기준으로 자동 재생성한다. (manifest·seen_urls를 손으로 고칠 필요 없음)
8. `python3 -m json.tool`로 오늘 브리핑·manifest.json·seen_urls.json의 유효성을 검증한다.
9. `git add -A`로 변경(신규·삭제 포함)을 스테이징한 뒤 **GitLab과 GitHub 양쪽에 push**한다: `git push gitlab main` 그리고 `git push origin main`. (한쪽이 실패해도 다른 쪽은 시도한다.) 커밋 메시지는 신규 모드면 `brief: YYYY-MM-DD 데일리 브리프 추가`, 갱신 모드면 `brief: YYYY-MM-DD 갱신 (추가 N건)`으로 한다. index.html 등 사이트 코드는 수정하지 않는다.

## 성공 기준
- briefs/오늘날짜.json이 유효한 JSON으로 생성·푸시됨
- 모든 항목이 최근 소식이고 원문 URL이 있으며 이전 브리핑과 중복되지 않음
- BeauBrain(뇌 MRI 기반 치매 진단 SW) 사업 관련성이 높은 소식에 importance high/medium이 정확히 매겨짐

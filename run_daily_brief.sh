#!/bin/bash
# 치매·AD 데일리 브리프 — 매일 오전 8시(신규) / 오후 2시(갱신) 자동 실행 (launchd가 호출)
# claude CLI를 헤드리스로 실행해 브리핑을 생성·갱신·커밋·푸시한다.

export PATH="/Users/sbpark/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# 병렬 리서치 서브에이전트가 기본 600초 제한에 걸려 강제 종료되면(2026-09-02 14시 사례)
# 커밋이 안 되고 Slack 발송까지 통째로 건너뛴다. 실행 간격이 6시간이므로 넉넉히 40분까지 허용.
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=2400000

REPO="/Applications/BeauBrain/700_Utils/004_DAILY_BRIEF"
cd "$REPO" || exit 1

mkdir -p "$REPO/logs"
TODAY="$(date +%Y-%m-%d)"
LOG="$REPO/logs/$TODAY.log"

echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') 시작 =====" >> "$LOG"

# 특정 회차 건너뛰기(.skip_runs). 맥을 꺼두는 날 등에 사용.
# 형식: "YYYY-MM-DD morning" | "YYYY-MM-DD afternoon" | "YYYY-MM-DD all"  (한 줄에 하나)
# 오전=12시 이전. launchd가 놓친 작업을 뒤늦게 따라잡아 실행하는 경우도 함께 막는다.
SKIP_FILE="$REPO/.skip_runs"
if [ "$(date +%H)" -lt 12 ]; then SLOT="morning"; else SLOT="afternoon"; fi
if [ -f "$SKIP_FILE" ] && grep -qE "^[[:space:]]*$TODAY[[:space:]]+(all|$SLOT)[[:space:]]*$" "$SKIP_FILE"; then
  echo "----- $TODAY $SLOT 회차는 건너뛰기로 지정됨 — 종료 -----" >> "$LOG"
  echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') 종료 (건너뜀) =====" >> "$LOG"
  exit 0
fi

PROMPT="$(cat "$REPO/BRIEF_PROMPT.md")"

BEFORE_REV="$(git rev-parse HEAD 2>/dev/null)"
# 실패 감지는 "이번 실행분" 로그만 본다. 로그는 하루 한 파일이라 전체를 grep하면
# 아침 회차의 옛 오류를 오후 회차가 다시 잡아 오탐 경고를 보낸다(2026-10-06 14:19 사례).
LOG_START_LINE="$(wc -l < "$LOG")"

claude -p "$PROMPT" \
  --allowedTools "Task,Bash,WebSearch,WebFetch,Read,Write,Edit,Glob,Grep" \
  >> "$LOG" 2>&1

# 이번 실행으로 새 커밋이 생겼으면(=브리핑이 새로 생성·갱신됨) 후처리
AFTER_REV="$(git rev-parse HEAD 2>/dev/null)"
if [ "$BEFORE_REV" != "$AFTER_REV" ]; then
  echo "----- 변경 감지 -----" >> "$LOG"
  # (1) Teams 요약 발송 (평일만 — 스킵 로직은 스크립트 내부)
  python3 "$REPO/teams_notify.py" >> "$LOG" 2>&1
  # (2) Obsidian vault에 연구논문 적재 (주말·공휴일 포함 매일)
  python3 "$REPO/brief_to_obsidian.py" >> "$LOG" 2>&1
else
  echo "----- 변경 없음, 후처리 생략 -----" >> "$LOG"
fi

# 인증 만료 등 치명적 실패는 조용히 넘기지 말고 Teams로 경고한다
# (실패해도 브리핑 생성만 멈추고 로그에만 남아 며칠간 모르고 지나가는 것을 방지)
RUN_LOG="$(tail -n +"$((LOG_START_LINE + 1))" "$LOG")"
if printf '%s\n' "$RUN_LOG" | grep -q "Failed to authenticate\|OAuth session expired\|Invalid authentication"; then
  echo "----- 인증 실패 감지, 경고 발송 -----" >> "$LOG"
  python3 "$REPO/notify_failure.py" "auth" >> "$LOG" 2>&1
elif [ "$BEFORE_REV" = "$AFTER_REV" ] && printf '%s\n' "$RUN_LOG" | grep -q "Background tasks still running"; then
  echo "----- 시간초과 강제종료 감지, 경고 발송 -----" >> "$LOG"
  python3 "$REPO/notify_failure.py" "timeout" >> "$LOG" 2>&1
elif printf '%s\n' "$RUN_LOG" | grep -q "blocked by hook"; then
  # 2026-10-06: 삭제된 005_VIRTUAL_OFFICE/hook.py를 가리키는 훅이 프롬프트를 차단해 4일간 조용히 실패
  echo "----- 훅 차단 감지, 경고 발송 -----" >> "$LOG"
  python3 "$REPO/notify_failure.py" "hook" >> "$LOG" 2>&1
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') 종료 (exit=$?) =====" >> "$LOG"

#!/bin/bash
# 치매·AD 데일리 브리프 — 매일 오전 8시(신규) / 오후 2시(갱신) 자동 실행 (launchd가 호출)
# claude CLI를 헤드리스로 실행해 브리핑을 생성·갱신·커밋·푸시한다.

export PATH="/Users/sbpark/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO="/Applications/BeauBrain/700_Utils/004_DAILY_BRIEF"
cd "$REPO" || exit 1

mkdir -p "$REPO/logs"
TODAY="$(date +%Y-%m-%d)"
LOG="$REPO/logs/$TODAY.log"

echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') 시작 =====" >> "$LOG"

PROMPT="$(cat "$REPO/BRIEF_PROMPT.md")"

claude -p "$PROMPT" \
  --allowedTools "Task,Bash,WebSearch,WebFetch,Read,Write,Edit,Glob,Grep" \
  >> "$LOG" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') 종료 (exit=$?) =====" >> "$LOG"

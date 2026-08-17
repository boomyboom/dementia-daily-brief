#!/usr/bin/env python3
"""자동 실행 실패를 Slack으로 경고한다.

인증 만료처럼 브리핑 생성이 통째로 멈추는 실패는 로그에만 남아 며칠간 눈치채지 못하기 쉽다.
같은 사유로 하루 여러 번 알림이 쌓이지 않도록 .slack_alert/{사유}-{날짜} 로 1일 1회만 발송한다.
사용: python3 notify_failure.py auth
"""
import os
import sys
import json
import urllib.request
from datetime import datetime, timezone, timedelta

REPO = os.path.dirname(os.path.abspath(__file__))

MESSAGES = {
    "auth": (
        ":warning: *데일리 브리프 자동 실행 실패 — claude 로그인 만료*\n"
        "브리핑 생성이 중단된 상태입니다. 터미널에서 아래를 실행해 다시 로그인해 주세요.\n"
        "```\nclaude\n```\n"
        "→ `/login` 입력 → 브라우저 로그인 → `/exit` → `claude -p \"ok\"` 로 확인"
    ),
}


def webhook():
    u = os.environ.get("SLACK_WEBHOOK", "").strip()
    if u:
        return u
    p = os.path.join(REPO, ".slack_webhook")
    return open(p).read().strip() if os.path.exists(p) else ""


def main():
    reason = sys.argv[1] if len(sys.argv) > 1 else "auth"
    hook = webhook()
    if not hook:
        print("[alert] webhook 미설정 — 경고 생략")
        return

    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    d = os.path.join(REPO, ".slack_alert")
    os.makedirs(d, exist_ok=True)
    stamp = os.path.join(d, f"{reason}-{today}")
    if os.path.exists(stamp):
        print(f"[alert] {reason} 경고는 오늘 이미 발송함 — 생략")
        return

    text = MESSAGES.get(reason, f":warning: 데일리 브리프 자동 실행 실패 ({reason})")
    req = urllib.request.Request(
        hook,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"[alert] 경고 발송 완료 (HTTP {r.status}, 사유={reason})")
        open(stamp, "w").close()
    except Exception as e:
        print(f"[alert] 경고 발송 실패: {e}")


if __name__ == "__main__":
    main()

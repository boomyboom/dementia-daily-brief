#!/usr/bin/env python3
"""오늘자 브리핑 요약을 Slack Incoming Webhook으로 발송.
Webhook URL은 환경변수 SLACK_WEBHOOK 또는 같은 폴더의 .slack_webhook 파일에서 읽는다.
브리핑이 없거나 webhook이 없으면 조용히 종료한다(정상)."""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

REPO = os.path.dirname(os.path.abspath(__file__))
SITE_URL = os.environ.get("BRIEF_SITE_URL", "https://boomyboom.github.io/dementia-daily-brief/")


def get_webhook():
    url = os.environ.get("SLACK_WEBHOOK", "").strip()
    if url:
        return url
    path = os.path.join(REPO, ".slack_webhook")
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return ""


def today_kst():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")


def main():
    webhook = get_webhook()
    if not webhook:
        print("[slack] webhook 미설정 — 발송 생략")
        return

    date = sys.argv[1] if len(sys.argv) > 1 else today_kst()
    brief_path = os.path.join(REPO, "briefs", f"{date}.json")
    if not os.path.exists(brief_path):
        print(f"[slack] {date}.json 없음 — 발송 생략")
        return

    with open(brief_path) as f:
        brief = json.load(f)

    lines = [f":brain: *치매·AD 데일리 브리프* — {date}"]
    if brief.get("headline"):
        lines.append(f"*{brief['headline']}*")
    lines.append("")

    for sec in brief.get("sections", []):
        items = sec.get("items", [])
        if not items:
            continue
        lines.append(f"*{sec.get('title', '')}* ({len(items)}건)")
        for it in items:
            title = it.get("title", "")
            url = it.get("url", "")
            mark = " ⭐" if it.get("importance") == "high" else ""
            if url:
                lines.append(f"• <{url}|{title}>{mark}")
            else:
                lines.append(f"• {title}{mark}")
        lines.append("")

    lines.append(f"<{SITE_URL}|전체 브리핑 보기>")
    payload = {"text": "\n".join(lines).strip(), "unfurl_links": False}

    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[slack] 발송 완료 (HTTP {resp.status})")
    except Exception as e:
        print(f"[slack] 발송 실패: {e}")


if __name__ == "__main__":
    main()

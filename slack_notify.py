#!/usr/bin/env python3
"""오늘자 브리핑 요약을 Slack Incoming Webhook으로 발송.

- Webhook URL: 환경변수 SLACK_WEBHOOK 또는 같은 폴더의 .slack_webhook 파일.
- 토·일·한국 공휴일(holidays_kr.json)에는 발송하지 않는다(브리핑 생성은 별개).
- '이미 보낸 항목'은 .slack_sent/{date}.json 에 기록해두고, 매번 그 이후 추가된 항목만 보낸다.
  → 오전 첫 발송은 전체, 오후 갱신 발송은 새로 추가된 항목만 표시. 새 항목이 없으면 발송 생략.
- SLACK_FORCE=1 이면 공휴일/이미보냄 무시하고 전체를 강제 발송(수동 테스트용).
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

REPO = os.path.dirname(os.path.abspath(__file__))
SITE_URL = os.environ.get("BRIEF_SITE_URL", "https://beaubrainsbpark.gitlab.io/dementia-daily-brief/")
FORCE = os.environ.get("SLACK_FORCE") == "1"


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


def skip_reason(date_str):
    """토·일·한국 공휴일이면 (True, 사유) 반환."""
    if FORCE:
        return False, ""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False, ""
    if d.weekday() == 5:
        return True, "토요일"
    if d.weekday() == 6:
        return True, "일요일"
    path = os.path.join(REPO, "holidays_kr.json")
    if os.path.exists(path):
        try:
            hol = json.load(open(path, encoding="utf-8"))
        except Exception:
            hol = {}
        if date_str in hol:
            return True, hol[date_str]
    return False, ""


def item_key(it):
    return it.get("url") or it.get("title", "")


def sent_path(date_str):
    return os.path.join(REPO, ".slack_sent", f"{date_str}.json")


def load_sent(date_str):
    if FORCE:
        return set()
    p = sent_path(date_str)
    if os.path.exists(p):
        try:
            return set(json.load(open(p, encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_sent(date_str, keys):
    d = os.path.join(REPO, ".slack_sent")
    os.makedirs(d, exist_ok=True)
    with open(sent_path(date_str), "w", encoding="utf-8") as f:
        json.dump(sorted(keys), f, ensure_ascii=False)


def post(webhook, text):
    req = urllib.request.Request(
        webhook,
        data=json.dumps({"text": text, "unfurl_links": False}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status


def main():
    webhook = get_webhook()
    if not webhook:
        print("[slack] webhook 미설정 — 발송 생략")
        return

    date = sys.argv[1] if len(sys.argv) > 1 else today_kst()

    skip, reason = skip_reason(date)
    if skip:
        print(f"[slack] {date} 은(는) {reason} — 발송 생략(브리핑은 정상 생성됨)")
        return

    brief_path = os.path.join(REPO, "briefs", f"{date}.json")
    if not os.path.exists(brief_path):
        print(f"[slack] {date}.json 없음 — 발송 생략")
        return

    with open(brief_path, encoding="utf-8") as f:
        brief = json.load(f)

    sent = load_sent(date)
    is_update = len(sent) > 0  # 이미 오늘 뭔가 보냈으면 갱신 발송

    all_keys = set()
    fresh_sections = []  # (title, [새 항목...])
    new_count = 0
    for sec in brief.get("sections", []):
        items = sec.get("items", [])
        all_keys |= {item_key(it) for it in items}
        new_items = [it for it in items if item_key(it) not in sent]
        if new_items:
            fresh_sections.append((sec.get("title", ""), new_items))
            new_count += len(new_items)

    if new_count == 0:
        print(f"[slack] {date} 새로 추가된 항목 없음 — 발송 생략")
        return

    if is_update:
        lines = [f"🔔 *<{SITE_URL}|데일리 브리프 업데이트 — {date}>* (추가 {new_count}건)", ""]
    else:
        lines = [f":brain: *<{SITE_URL}|치매·AD 데일리 브리프 — {date}>*"]
        if brief.get("headline"):
            lines.append(f"_{brief['headline']}_")
        lines.append("")

    for title, items in fresh_sections:
        lines.append(f"*{title}* ({len(items)}건)")
        for it in items:
            mark = " ⭐" if it.get("importance") == "high" else ""
            url = it.get("url", "")
            t = it.get("title", "")
            lines.append(f"• <{url}|{t}>{mark}" if url else f"• {t}{mark}")
        lines.append("")

    lines.append(f"👉 *<{SITE_URL}|데일리 브리프 사이트에서 전체 보기>*")

    try:
        status = post(webhook, "\n".join(lines).strip())
        print(f"[slack] 발송 완료 (HTTP {status}, {'업데이트' if is_update else '전체'} {new_count}건)")
        save_sent(date, sent | all_keys)
    except Exception as e:
        print(f"[slack] 발송 실패: {e}")


if __name__ == "__main__":
    main()

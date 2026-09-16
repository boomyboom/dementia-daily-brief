#!/usr/bin/env python3
"""브리핑 요약을 Microsoft Teams로 발송 (Adaptive Card).

Slack판(slack_notify.py)과 동작 규칙은 같다:
- 토·일·한국 공휴일에는 발송하지 않음
- 근무일 첫 발송 시 직전 비근무일의 미발송분을 함께 묶음(주말분은 ⭐중요 항목만)
- .teams_sent/{date}.json 으로 이미 보낸 항목을 기록해 추가분만 발송

Slack과 다른 점 (형식 변환이 필요한 부분):
- 엔드포인트: Power Automate Workflows 웹훅 (Office 365 커넥터는 2026-05 폐지)
- 페이로드: {"text": ...} 가 아니라 Adaptive Card JSON
- 링크: Slack의 <url|텍스트> 가 아니라 마크다운 [텍스트](url)
- 이스케이프: Slack은 &,<,> 를 치환해야 했지만 Teams는 불필요
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone, timedelta

REPO = os.path.dirname(os.path.abspath(__file__))
SITE_URL = os.environ.get("BRIEF_SITE_URL", "https://beaubrainsbpark.gitlab.io/dementia-daily-brief/")
FORCE = os.environ.get("TEAMS_FORCE") == "1"

# Slack판의 요일·공휴일·백필 판정 로직을 그대로 재사용한다
sys.path.insert(0, REPO)
from slack_notify import is_nonworking, backfill_dates, item_key, md  # noqa: E402


def webhook():
    u = os.environ.get("TEAMS_WEBHOOK", "").strip()
    if u:
        return u
    p = os.path.join(REPO, ".teams_webhook")
    return open(p).read().strip() if os.path.exists(p) else ""


def today_kst():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")


def sent_path(d):
    return os.path.join(REPO, ".teams_sent", f"{d}.json")


def load_sent(d):
    if FORCE:
        return set()
    p = sent_path(d)
    try:
        return set(json.load(open(p, encoding="utf-8"))) if os.path.exists(p) else set()
    except Exception:
        return set()


def save_sent(d, keys):
    os.makedirs(os.path.join(REPO, ".teams_sent"), exist_ok=True)
    json.dump(sorted(keys), open(sent_path(d), "w", encoding="utf-8"), ensure_ascii=False)


def build_card(date, brief, sections, new_count, is_update, pending, omitted):
    """Adaptive Card 구성. Teams는 마크다운을 쓰므로 링크는 [텍스트](url)."""
    if is_update:
        title, sub = f"🔔 데일리 브리프 업데이트 — {date}", f"추가 {new_count}건"
    elif pending:
        title = f"🧠 치매·AD 데일리 브리프 — {date}"
        sub = f"주말·휴일 {md(pending[0])}~{md(date)} 종합 · {new_count}건"
    else:
        title, sub = f"🧠 치매·AD 데일리 브리프 — {date}", f"{new_count}건"

    body = [
        {"type": "TextBlock", "text": title, "size": "Large", "weight": "Bolder", "wrap": True},
        {"type": "TextBlock", "text": sub, "isSubtle": True, "spacing": "None", "wrap": True},
    ]
    if not is_update and brief.get("headline"):
        body.append({"type": "TextBlock", "text": brief["headline"], "wrap": True,
                     "spacing": "Medium", "color": "Accent"})
    if omitted:
        body.append({"type": "TextBlock", "text": f"주말분은 ⭐중요 항목만 실었습니다 — 그 외 {omitted}건은 사이트에서 확인",
                     "isSubtle": True, "wrap": True, "size": "Small"})

    for sec_title, items in sections:
        body.append({"type": "TextBlock", "text": f"**{sec_title}** ({len(items)}건)",
                     "wrap": True, "spacing": "Medium", "separator": True})
        lines = []
        for it in items:
            mark = " ⭐" if it.get("importance") == "high" else ""
            day = f"[{md(it['_from'])}] " if it.get("_from") else ""
            t, u = it.get("title", ""), it.get("url", "")
            lines.append(f"- {day}[{t}]({u}){mark}" if u else f"- {day}{t}{mark}")
        body.append({"type": "TextBlock", "text": "\n".join(lines), "wrap": True, "spacing": "Small"})

    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard", "version": "1.4", "body": body,
                "actions": [{"type": "Action.OpenUrl", "title": "전체 브리핑 보기", "url": SITE_URL}],
            },
        }],
    }


def main():
    hook = webhook()
    if not hook:
        print("[teams] webhook 미설정 — 발송 생략")
        return
    date = sys.argv[1] if len(sys.argv) > 1 else today_kst()
    if not FORCE:
        non, why = is_nonworking(date)
        if non:
            print(f"[teams] {date} 은(는) {why} — 발송 생략")
            return
    if not os.path.exists(os.path.join(REPO, "briefs", f"{date}.json")):
        print(f"[teams] {date}.json 없음 — 발송 생략")
        return

    sent = load_sent(date)
    is_update = len(sent) > 0
    pending = [] if is_update else backfill_dates(date)

    seen, order, merged, keys_by_date, omitted = set(sent), [], {}, {}, 0
    for dt in pending + [date]:
        p = os.path.join(REPO, "briefs", f"{dt}.json")
        if not os.path.exists(p):
            continue
        b = json.load(open(p, encoding="utf-8"))
        keys_by_date[dt] = set()
        for sec in b.get("sections", []):
            sid = sec.get("id") or sec.get("title", "")
            if sid not in merged:
                merged[sid] = {"title": sec.get("title", ""), "items": []}
                order.append(sid)
            for it in sec.get("items", []):
                k = item_key(it)
                keys_by_date[dt].add(k)
                if k in seen:
                    continue
                seen.add(k)
                if dt != date and it.get("importance") != "high":
                    omitted += 1
                    continue
                row = dict(it)
                if dt != date:
                    row["_from"] = dt
                merged[sid]["items"].append(row)

    sections = [(merged[s]["title"], merged[s]["items"]) for s in order if merged[s]["items"]]
    new_count = sum(len(i) for _, i in sections)
    if new_count == 0:
        print(f"[teams] {date} 새로 추가된 항목 없음 — 발송 생략")
        return

    brief = json.load(open(os.path.join(REPO, "briefs", f"{date}.json"), encoding="utf-8"))
    card = build_card(date, brief, sections, new_count, is_update, pending, omitted)

    if os.environ.get("TEAMS_DRYRUN") == "1":
        print(json.dumps(card, ensure_ascii=False, indent=1))
        return

    req = urllib.request.Request(hook, data=json.dumps(card).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"[teams] 발송 완료 (HTTP {r.status}, {'업데이트' if is_update else '전체'} {new_count}건)")
        save_sent(date, sent | keys_by_date.get(date, set()))
        for dt in pending:
            save_sent(dt, keys_by_date.get(dt, set()))
    except Exception as e:
        print(f"[teams] 발송 실패: {e}")


if __name__ == "__main__":
    main()

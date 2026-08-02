#!/usr/bin/env python3
"""오늘자 브리핑 요약을 Slack Incoming Webhook으로 발송.

- Webhook URL: 환경변수 SLACK_WEBHOOK 또는 같은 폴더의 .slack_webhook 파일.
- 토·일·한국 공휴일(holidays_kr.json)에는 발송하지 않는다(브리핑 생성은 별개).
- 근무일 첫 발송 시, 바로 앞의 연속된 비근무일(주말·연휴) 중 아직 슬랙으로 못 보낸 브리핑을
  함께 묶어 보낸다. → 월요일 아침에 토·일 내용까지 종합 발송.
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


def is_nonworking(date_str):
    """토·일·한국 공휴일이면 (True, 사유) 반환. SLACK_FORCE와 무관한 사실 판정."""
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


def skip_reason(date_str):
    """발송을 건너뛸지 판단(FORCE면 항상 발송)."""
    if FORCE:
        return False, ""
    return is_nonworking(date_str)


def backfill_dates(date_str, max_back=7):
    """직전의 연속된 비근무일 중 브리핑은 있으나 슬랙 발송 기록이 없는 날짜들(오래된 순)."""
    out = []
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return out
    for i in range(1, max_back + 1):
        prev = (d - timedelta(days=i)).strftime("%Y-%m-%d")
        non, _ = is_nonworking(prev)
        if not non:
            break  # 근무일을 만나면 중단(그날은 이미 발송됐을 것)
        has_brief = os.path.exists(os.path.join(REPO, "briefs", f"{prev}.json"))
        if has_brief and not os.path.exists(sent_path(prev)):
            out.append(prev)
    return sorted(out)


def md(date_str):
    """2026-08-03 → 8/3"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return f"{d.month}/{d.day}"
    except ValueError:
        return date_str


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

    sent = load_sent(date)
    is_update = len(sent) > 0  # 이미 오늘 뭔가 보냈으면 갱신 발송

    # 오늘 첫 발송일 때만 직전 주말·연휴 브리핑을 함께 묶는다
    pending = [] if is_update else backfill_dates(date)
    dates = pending + [date]

    briefs = {}
    for dt in dates:
        p = os.path.join(REPO, "briefs", f"{dt}.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                briefs[dt] = json.load(f)

    # 섹션별로 여러 날짜의 항목을 병합(중복 제거, 이미 보낸 것 제외)
    # 주말·연휴분은 양이 많아(하루 40건 내외) 중요(high) 항목만 추리고, 나머지는 건수만 안내
    seen = set(sent)
    order, merged = [], {}
    keys_by_date = {}
    omitted = 0
    for dt in dates:
        b = briefs.get(dt)
        if not b:
            continue
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
                    omitted += 1     # 주말 비중요 항목은 생략(사이트에서 확인)
                    continue
                row = dict(it)
                if dt != date:
                    row["_from"] = dt   # 주말·연휴분 표시용
                merged[sid]["items"].append(row)

    new_count = sum(len(m["items"]) for m in merged.values())
    if new_count == 0:
        print(f"[slack] {date} 새로 추가된 항목 없음 — 발송 생략")
        return

    brief = briefs.get(date, {})
    if is_update:
        lines = [f"🔔 *<{SITE_URL}|데일리 브리프 업데이트 — {date}>* (추가 {new_count}건)", ""]
    elif pending:
        span = f"{md(pending[0])}~{md(date)}"
        lines = [f":brain: *<{SITE_URL}|치매·AD 데일리 브리프 — {date}>* (주말·휴일 {span} 종합, {new_count}건)"]
        if brief.get("headline"):
            lines.append(f"_{brief['headline']}_")
        if omitted:
            lines.append(f"_주말분은 ⭐중요 항목만 실었습니다 — 그 외 {omitted}건은 사이트에서 확인_")
        lines.append("")
    else:
        lines = [f":brain: *<{SITE_URL}|치매·AD 데일리 브리프 — {date}>*"]
        if brief.get("headline"):
            lines.append(f"_{brief['headline']}_")
        lines.append("")

    for sid in order:
        items = merged[sid]["items"]
        if not items:
            continue
        lines.append(f"*{merged[sid]['title']}* ({len(items)}건)")
        for it in items:
            mark = " ⭐" if it.get("importance") == "high" else ""
            day = f"[{md(it['_from'])}] " if it.get("_from") else ""
            url, t = it.get("url", ""), it.get("title", "")
            lines.append(f"• {day}<{url}|{t}>{mark}" if url else f"• {day}{t}{mark}")
        lines.append("")

    lines.append(f"👉 *<{SITE_URL}|데일리 브리프 사이트에서 전체 보기>*")

    try:
        status = post(webhook, "\n".join(lines).strip())
        label = "업데이트" if is_update else ("주말종합" if pending else "전체")
        print(f"[slack] 발송 완료 (HTTP {status}, {label} {new_count}건"
              + (f", 포함일자 {', '.join(pending)}" if pending else "") + ")")
        # 오늘분 + 함께 보낸 주말·연휴분 모두 발송 완료로 기록
        save_sent(date, sent | keys_by_date.get(date, set()))
        for dt in pending:
            save_sent(dt, keys_by_date.get(dt, set()))
    except Exception as e:
        print(f"[slack] 발송 실패: {e}")


if __name__ == "__main__":
    main()

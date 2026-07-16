#!/usr/bin/env python3
"""데일리 브리프의 research(학술·연구) 항목을 Obsidian vault에 Tier 2 노트로 적재.

- 대상: briefs/{date}.json 의 research 섹션 항목 (원하면 SECTIONS 조정)
- 저장 위치: <VAULT>/10_DailyBrief/YYYY-MM/ 아래 1항목 1노트
- 중복: 이미 적재한 URL은 .obsidian_archived.json(레포, gitignore)으로 하드 차단
- 주말·공휴일 상관없이 매일 적재(휘발성 Slack과 달리 아카이브는 계속 쌓는다)
"""
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

REPO = os.path.dirname(os.path.abspath(__file__))
VAULT = os.environ.get("OBSIDIAN_VAULT", "/Applications/BeauBrain/500_Obsidian/Obsidian")
ARCHIVE = os.path.join(VAULT, "10_DailyBrief")
LEDGER = os.path.join(REPO, ".obsidian_archived.json")
SECTIONS = {"research"}  # 적재할 섹션 id (필요하면 "regulatory" 등 추가)


def today_kst():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")


def load_ledger():
    if os.path.exists(LEDGER):
        try:
            return set(json.load(open(LEDGER, encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_ledger(s):
    json.dump(sorted(s), open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False)


def slug(title):
    t = re.sub(r"[\\/:*?\"<>|#^\[\]]", "", title).strip()
    return t[:60] if t else "untitled"


def esc_yaml(s):
    return str(s or "").replace('"', "'")


def main():
    if not os.path.isdir(VAULT):
        print(f"[obsidian] vault 없음: {VAULT} — 적재 생략")
        return
    date = sys.argv[1] if len(sys.argv) > 1 else today_kst()
    brief_path = os.path.join(REPO, "briefs", f"{date}.json")
    if not os.path.exists(brief_path):
        print(f"[obsidian] {date}.json 없음 — 적재 생략")
        return

    brief = json.load(open(brief_path, encoding="utf-8"))
    ledger = load_ledger()
    month_dir = os.path.join(ARCHIVE, date[:7])
    os.makedirs(month_dir, exist_ok=True)

    added = []
    for sec in brief.get("sections", []):
        if sec.get("id") not in SECTIONS:
            continue
        for it in sec.get("items", []):
            url = it.get("url", "")
            key = url or it.get("title", "")
            if not key or key in ledger:
                continue
            title = it.get("title", "제목없음")
            fname = f"{date} {slug(title)}.md"
            fpath = os.path.join(month_dir, fname)
            tags = it.get("tags", []) + ["brief-paper", "tier2"]
            body = f"""---
type: brief-paper
tier: 2
verbatim: false
title: "{esc_yaml(title)}"
source: "{esc_yaml(it.get('source'))}"
url: "{esc_yaml(url)}"
brief_date: "{date}"
section: "{esc_yaml(sec.get('title'))}"
importance: "{esc_yaml(it.get('importance'))}"
tags: [{', '.join(tags)}]
---

# {title}

> ⚠️ Tier 2 (브리프 요약). 규제 소명 직접 인용에는 원문(Tier 1)을 쓸 것 → [[TIER_GUIDE]]

## 요약
{it.get('summary', '')}

## 메모 (직접 작성)
-

## 원문
- 출처: {it.get('source', '')}
- {url}

---
데일리 브리프 {date} 에서 자동 적재 · 원문 PDF를 등록하려면 `paper-to-wiki` 사용
"""
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(body)
            ledger.add(key)
            added.append((date, title, os.path.relpath(fpath, VAULT)))

    if added:
        # 인덱스에 링크 추가
        idx = os.path.join(ARCHIVE, "_index.md")
        lines = []
        for d, title, rel in added:
            note = os.path.splitext(os.path.basename(rel))[0]
            lines.append(f"- {d} · [[{note}]]")
        with open(idx, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(lines))
        save_ledger(ledger)
        print(f"[obsidian] {len(added)}건 적재 → {month_dir}")
    else:
        print(f"[obsidian] {date} 새로 적재할 연구 항목 없음")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""30일 지난 브리핑 파일을 삭제하고 manifest.json·seen_urls.json을 재생성한다.
날짜 이름(YYYY-MM-DD.json) 파일만 대상으로 하며 manifest/seen_urls는 건드리지 않는다."""
import datetime
import glob
import json
import os

REPO = os.path.dirname(os.path.abspath(__file__))
BRIEFS = os.path.join(REPO, "briefs")
KEEP_DAYS = 30


def today_kst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()


def main():
    cutoff = today_kst() - datetime.timedelta(days=KEEP_DAYS)
    kept, removed = [], []

    for path in glob.glob(os.path.join(BRIEFS, "*.json")):
        name = os.path.basename(path)[:-5]
        try:
            d = datetime.date.fromisoformat(name)
        except ValueError:
            continue  # manifest.json, seen_urls.json 등은 건너뜀
        if d < cutoff:
            os.remove(path)
            removed.append(name)
        else:
            kept.append(name)

    kept.sort()

    with open(os.path.join(BRIEFS, "manifest.json"), "w", encoding="utf-8") as fp:
        json.dump({"dates": kept}, fp, ensure_ascii=False, indent=2)

    # 남아 있는 브리핑들의 모든 원문 URL로 seen_urls.json 재생성 (중복차단 목록, 30일 범위)
    urls = set()
    for name in kept:
        try:
            b = json.load(open(os.path.join(BRIEFS, f"{name}.json"), encoding="utf-8"))
        except Exception:
            continue
        for sec in b.get("sections", []):
            for it in sec.get("items", []):
                u = it.get("url")
                if u:
                    urls.add(u)
    with open(os.path.join(BRIEFS, "seen_urls.json"), "w", encoding="utf-8") as fp:
        json.dump(sorted(urls), fp, ensure_ascii=False, indent=0)

    print(f"[cleanup] 삭제 {len(removed)}건 / 유지 {len(kept)}건 / seen_urls {len(urls)}개")
    if removed:
        print("[cleanup] 삭제됨:", ", ".join(sorted(removed)))


if __name__ == "__main__":
    main()

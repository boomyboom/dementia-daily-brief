#!/usr/bin/env python3
"""브리핑 링크 건전성 검사. 발행 전에 실행해 위험·죽은 링크를 걸러낸다.

검출 대상
- 평문 HTTP로 끝나는 링크(브라우저·보안SW 경고 유발)
- 원 도메인과 무관한 곳으로 튕기는 크로스도메인 리다이렉트(예: 국내 언론 CMS의 공용 오류페이지 se-cu.com)
- 실제로 삭제된 링크(브라우저 User-Agent + GET으로 재확인해 봇 차단과 구분)

주의: 국내 언론사 CMS(NDsoft 계열)는 HEAD 요청을 차단하고 se-cu.com 오류페이지로 302를 보낸다.
HEAD로 검사하면 멀쩡한 기사가 죽은 링크로 오판되므로 반드시 GET으로 확인할 것.

사용: python3 check_links.py [YYYY-MM-DD ...]   (인자 없으면 오늘)
종료코드 1 = 문제 발견
"""
import json, os, sys, glob, re
import urllib.request, urllib.error
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
# 학술 DOI·출판사 정상 이동은 크로스도메인이어도 문제 아님
SAFE_REDIRECT_ORIGINS = ("doi.org", "dx.doi.org", "pmc.ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov")


def today_kst():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")


def base(host):
    return re.sub(r"^www\.", "", (host or "").lower())


def probe(url):
    """(문제사유들, 최종URL) 반환. 브라우저 UA로 실제 접근 결과를 본다."""
    issues = []
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    final = url
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            final = r.geturl()
            code = r.status
    except urllib.error.HTTPError as e:
        final = getattr(e, "url", url)
        code = e.code
        if code in (404, 410):
            issues.append(f"삭제됨({code})")
    except Exception as e:
        return [f"접속불가({type(e).__name__})"], url

    fp, op = urlparse(final), urlparse(url)
    if fp.scheme == "http":
        issues.append("평문HTTP")
    if base(fp.netloc) != base(op.netloc) and base(op.netloc) not in SAFE_REDIRECT_ORIGINS:
        ob, fb = base(op.netloc), base(fp.netloc)
        if ob.split(".")[0] not in fb and fb.split(".")[0] not in ob:
            issues.append(f"타도메인이동({fp.netloc})")
    if re.search(r"error|parking|suspend|blocked", fp.path, re.I):
        issues.append("오류페이지")
    return issues, final


def main():
    dates = sys.argv[1:] or [today_kst()]
    targets = []
    for d in dates:
        p = os.path.join(REPO, "briefs", f"{d}.json")
        if not os.path.exists(p):
            print(f"[links] {d}.json 없음 — 건너뜀")
            continue
        b = json.load(open(p, encoding="utf-8"))
        for s in b.get("sections", []):
            for it in s.get("items", []):
                if it.get("url"):
                    targets.append((d, s.get("title", ""), it["title"], it["url"]))

    if not targets:
        print("[links] 검사할 링크 없음")
        return 0

    bad = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(lambda t: probe(t[3]), targets))
    for (d, sec, title, url), (issues, final) in zip(targets, results):
        if issues:
            bad.append((d, sec, title, url, issues, final))

    print(f"[links] {len(targets)}건 검사 → 문제 {len(bad)}건")
    for d, sec, title, url, issues, final in bad:
        print(f"  ⚠️ {' '.join(issues)} | {d} [{sec}] {title[:45]}")
        print(f"     {url}")
        if final != url:
            print(f"     → {final}")
    if bad:
        print("[links] 위 링크는 요약을 남기고 url을 제거하거나, 살아있는 대체 출처로 교체할 것.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

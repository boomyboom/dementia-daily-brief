#!/usr/bin/env python3
"""후보 URL 중복 확인 도구 (check_url.py의 보수적 대안).

사용법: python3 dedup_check.py <url> [<url> ...]

check_url.py의 norm()은 쿼리 키를 대소문자 구분해 비교하기 때문에
DART의 rcpNo=, 일부 언론사의 newsId= 같은 식별자 쿼리를 버린다.
그 결과 서로 다른 공시·기사가 같은 키로 뭉개져 전부 SEEN으로 오판정된다.

여기서는 (1) 쿼리 키를 소문자로 비교하고, (2) URL에서 뽑아낸 긴 숫자 식별자를
seen_urls 전체 문자열에 대해 따로 대조해 두 경로로 중복을 잡는다.
"""
import json
import os
import re
import sys
from urllib.parse import urlsplit, parse_qsl

REPO = os.path.dirname(os.path.abspath(__file__))
ID_KEYS = ("idxno", "id", "no", "seq", "bid", "art", "doi", "articleid",
           "rcpno", "newsid", "list_no", "wr_id", "ncode", "key", "linkid")


def norm(u):
    p = urlsplit(u.strip())
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/").lower()
    keep = []
    for k, v in parse_qsl(p.query, keep_blank_values=True):
        if k.lower() in ID_KEYS:
            keep.append(f"{k.lower()}={v.lower()}")
    q = "&".join(sorted(keep))
    return f"{host}{path}?{q}" if q else f"{host}{path}"


def ids(u):
    """URL에서 6자리 이상 숫자 식별자를 뽑는다 (PMID, 기사번호, 공시번호 등)."""
    return set(re.findall(r"\d{6,}", u))


def main(urls):
    seen = json.load(open(os.path.join(REPO, "briefs", "seen_urls.json")))
    index = {norm(u) for u in seen}
    blob = "\n".join(seen).lower()

    worst = 0
    for u in urls:
        reasons = []
        if norm(u) in index:
            reasons.append("정규화URL일치")
        for i in ids(u):
            if i in blob:
                reasons.append(f"식별자{i}가 기존URL에 등장")
        if reasons:
            worst = 1
            print(f"SEEN  {u}\n      -> {'; '.join(reasons)}")
        else:
            print(f"NEW   {u}")
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

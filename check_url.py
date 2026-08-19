#!/usr/bin/env python3
"""중복 URL 확인 도구. 사용법: python3 check_url.py <url> [<url> ...]

seen_urls.json(지금까지 게재한 모든 URL)에 있으면 SEEN, 없으면 NEW를 출력한다.
쿼리스트링·트레일링 슬래시·http/https 차이를 무시하고 비교한다.
"""
import json
import sys
from urllib.parse import urlsplit


def norm(u):
    p = urlsplit(u.strip())
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/")
    q = p.query
    # 게시판형 URL은 쿼리가 식별자이므로 유지, 그 외 추적 파라미터는 무시
    if q and not any(k in q for k in ("idxno", "id=", "no=", "seq", "bid", "art", "doi", "articleid")):
        q = ""
    return f"{host}{path}?{q}" if q else f"{host}{path}"


seen = json.load(open("briefs/seen_urls.json"))
index = {norm(u) for u in seen}

for u in sys.argv[1:]:
    print(("SEEN" if norm(u) in index else "NEW"), u)

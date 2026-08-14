#!/usr/bin/env python3
"""최근 30일 브리핑에서 키워드(업체명·기술용어)를 집계해 순위와 전일 대비 등락을 만든다.

출력: briefs/keywords.json
- 태그를 기본 신호로 쓰되, 표기 흔들림(혈액바이오마커/혈액 바이오마커, 뇌MRI/뇌 MRI)을 정규화한다.
- 태그에 없더라도 회사명·핵심 용어는 제목/요약에서 별칭으로 탐지한다.
- 전일 순위와 비교해 delta(상승/하락/신규)를 계산한다. 같은 날 재실행 시 기준일은 유지된다.
"""
import json
import glob
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

REPO = os.path.dirname(os.path.abspath(__file__))
BRIEFS = os.path.join(REPO, "briefs")
OUT = os.path.join(BRIEFS, "keywords.json")
WINDOW_DAYS = 30
TOP_N = 20          # 저장 개수(화면은 10위까지 표시)
MAX_ITEMS = 25      # 키워드당 첨부할 기사 수

# 표준명 → 별칭들. 태그·제목·요약에서 별칭이 잡히면 표준명으로 집계한다.
# (대소문자 무시, 공백 유무 무시)
ALIASES = {
    # 바이오마커·기술
    "p-tau217": ["ptau217", "p-tau217", "인산화타우217", "pTau217"],
    "p-tau181": ["ptau181", "p-tau181"],
    "GFAP": ["gfap"],
    "NfL": ["nfl", "신경필라멘트"],
    "혈액 바이오마커": ["혈액바이오마커", "혈액 바이오마커", "혈장바이오마커", "혈장 바이오마커", "혈액검사"],
    "아밀로이드 PET": ["아밀로이드pet", "아밀로이드 pet"],
    "타우 PET": ["타우pet", "타우 pet"],
    "뇌 MRI": ["뇌mri", "뇌 mri", "구조mri", "구조 mri", "정량mri", "정량 mri"],
    "MRI": ["mri"],
    "PET": ["pet"],
    "ARIA": ["aria", "아밀로이드 관련 영상 이상"],
    "Centiloid": ["centiloid", "센틸로이드"],
    "아밀로이드": ["아밀로이드", "amyloid", "abeta", "aβ"],
    "타우": ["타우", "tau"],
    "APOE": ["apoe", "apoe4", "apoe ε4"],
    # AI·방법론
    "딥러닝": ["딥러닝", "deep learning", "심층학습"],
    "머신러닝": ["머신러닝", "machine learning"],
    "AI 진단": ["ai진단", "ai 진단", "인공지능 진단", "cad"],
    "조기진단": ["조기진단", "조기 진단", "조기발견"],
    "감별진단": ["감별진단", "감별 진단"],
    # 치료제
    "레켐비": ["레켐비", "leqembi", "레카네맙", "lecanemab"],
    "키순라": ["키순라", "kisunla", "도나네맙", "donanemab"],
    # 규제기관
    "FDA": ["fda", "510(k)", "510k"],
    "식약처": ["식약처", "mfds", "식품의약품안전처"],
    "신의료기술": ["신의료기술", "평가유예", "혁신의료기술"],
    "심평원": ["심평원", "hira", "건강보험심사평가원"],
    "급여·수가": ["급여", "수가", "보험적용", "요양급여"],
    "NECA": ["neca", "보건의료연구원"],
    "CE 인증": ["ce마크", "ce 마크", "ce-mdr", "ce인증", "ce 인증"],
    # 국내 기업
    "뉴로핏": ["뉴로핏", "neurophet"],
    "뷰노": ["뷰노", "vuno"],
    "제이엘케이": ["제이엘케이", "jlk"],
    "휴런": ["휴런", "heuron"],
    "딥노이드": ["딥노이드", "deepnoid"],
    "아이메디신": ["아이메디신", "imedisync"],
    # 해외 기업
    "icometrix": ["icometrix"],
    "Cortechs.ai": ["cortechs", "neuroquant"],
    "Brainomix": ["brainomix"],
    "Quibim": ["quibim"],
    "C2N": ["c2n", "precivityad"],
    "Quanterix": ["quanterix"],
    "Fujirebio": ["fujirebio", "후지레비오", "lumipulse"],
    "Roche": ["roche", "로슈", "elecsys"],
    "Eisai": ["eisai", "에자이"],
    "Biogen": ["biogen", "바이오젠"],
    "Eli Lilly": ["lilly", "릴리", "일라이릴리"],
    "Linus Health": ["linus health"],
    # 주제
    "위험인자": ["위험인자", "위험요인"],
    "예방": ["예방", "생활습관"],
    "역학": ["역학", "코호트연구"],
    "임상시험": ["임상시험", "임상 시험", "clinical trial", "상 임상"],
    "정책": ["정책", "치매관리종합계획", "국가전략"],
}

# 더 구체적인 키워드가 잡히면 포괄어는 세지 않는다(MRI/아밀로이드가 상위를 독식하는 것 방지)
# 기업·기관은 별도 순위로 보여준다(포괄 주제어에 묻히지 않도록)
COMPANIES = {
    "뉴로핏", "뷰노", "제이엘케이", "휴런", "딥노이드", "아이메디신",
    "icometrix", "Cortechs.ai", "Brainomix", "Quibim", "C2N", "Quanterix",
    "Fujirebio", "Roche", "Eisai", "Biogen", "Eli Lilly", "Linus Health",
}

SUPPRESS = {
    "뇌 MRI": ["MRI"],
    "아밀로이드 PET": ["아밀로이드", "PET"],
    "타우 PET": ["타우", "PET"],
    "p-tau217": ["타우"],
    "p-tau181": ["타우"],
    "Centiloid": ["아밀로이드"],
}


def norm(s):
    return re.sub(r"[\s\-_·]", "", str(s or "")).lower()


ALIAS_MAP = {}
for canon, alist in ALIASES.items():
    ALIAS_MAP[norm(canon)] = canon
    for a in alist:
        ALIAS_MAP[norm(a)] = canon


def _flex(a):
    """공백·하이픈 표기 흔들림을 흡수하는 패턴 조각."""
    parts = re.split(r"[\s\-_·]+", a.strip())
    return r"[\s\-_·]*".join(re.escape(p) for p in parts)


def _build_patterns():
    """본문 탐지용 정규식. 라틴 별칭은 단어경계를 강제해 오탐(competition 속 'pet')을 막는다."""
    pats = {}
    for canon, alist in ALIASES.items():
        subs = []
        for a in [canon] + alist:
            core = _flex(a)
            if re.search(r"[가-힣]", a):
                subs.append(core)                      # 한글은 경계 개념이 없음
            else:
                subs.append(rf"(?<![A-Za-z0-9]){core}(?![A-Za-z0-9])")
        pats[canon] = re.compile("|".join(subs), re.IGNORECASE)
    return pats


PATTERNS = _build_patterns()


def today_kst():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")


def recent_files():
    cutoff = (datetime.strptime(today_kst(), "%Y-%m-%d").date()
              - timedelta(days=WINDOW_DAYS)).isoformat()
    out = []
    for f in sorted(glob.glob(os.path.join(BRIEFS, "2*.json"))):
        name = os.path.basename(f)[:-5]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", name) and name >= cutoff:
            out.append((name, f))
    return out


def keywords_of(item):
    """항목에서 표준 키워드 집합 추출: 태그(정확일치) + 제목·요약(정규식 탐지) → 포괄어 억제."""
    found = set()
    for t in item.get("tags", []):
        c = ALIAS_MAP.get(norm(t))
        if c:
            found.add(c)
    text = f"{item.get('title', '')} {item.get('summary', '')}"
    for canon, pat in PATTERNS.items():
        if pat.search(text):
            found.add(canon)
    for specific, parents in SUPPRESS.items():
        if specific in found:
            found -= set(parents)
    return found


def main():
    counts = Counter()
    items_by_kw = defaultdict(list)

    for date, path in recent_files():
        try:
            b = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        for sec in b.get("sections", []):
            for it in sec.get("items", []):
                for kw in keywords_of(it):
                    counts[kw] += 1
                    items_by_kw[kw].append({
                        "date": date,
                        "title": it.get("title", ""),
                        "url": it.get("url", ""),
                        "section": sec.get("title", ""),
                        "importance": it.get("importance"),
                    })

    # 이전 순위 불러오기 (같은 날 재실행이면 기준일 유지)
    prev_ranks, prev_date = {}, None
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
            old_all = old.get("topics", []) + old.get("companies", [])
            if old.get("date") == today_kst():
                prev_ranks = {k["keyword"]: k.get("prev_rank") for k in old_all}
                prev_date = old.get("prev_date")
            else:
                prev_ranks = {k["keyword"]: k["rank"] for k in old_all}
                prev_date = old.get("date")
        except Exception:
            pass

    def rank_group(pairs):
        out = []
        for i, (kw, n) in enumerate(pairs, start=1):
            pr = prev_ranks.get(kw)
            if pr is None:
                delta, state = None, "new"
            elif pr > i:
                delta, state = pr - i, "up"
            elif pr < i:
                delta, state = i - pr, "down"
            else:
                delta, state = 0, "same"
            out.append({
                "rank": i, "keyword": kw, "count": n,
                "prev_rank": pr, "delta": delta, "state": state,
                "items": sorted(items_by_kw[kw], key=lambda x: x["date"], reverse=True)[:MAX_ITEMS],
            })
        return out

    ordered = counts.most_common()
    topics = rank_group([(k, n) for k, n in ordered if k not in COMPANIES][:TOP_N])
    companies = rank_group([(k, n) for k, n in ordered if k in COMPANIES][:TOP_N])

    out = {
        "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
        "date": today_kst(),
        "prev_date": prev_date,
        "window_days": WINDOW_DAYS,
        "topics": topics,
        "companies": companies,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    sym = lambda k: {"up": f"▲{k['delta']}", "down": f"▼{k['delta']}",
                     "same": "-", "new": "NEW"}[k["state"]]
    print(f"[keywords] 기간 {WINDOW_DAYS}일, 전일 {prev_date or '없음'}")
    print("  ── 키워드 ──")
    for k in topics[:10]:
        print(f"  {k['rank']:2}. {k['keyword']:<14} {k['count']:3}건  {sym(k)}")
    print("  ── 기업 ──")
    for k in companies[:10]:
        print(f"  {k['rank']:2}. {k['keyword']:<14} {k['count']:3}건  {sym(k)}")


if __name__ == "__main__":
    main()

# 치매·AD 데일리 브리프 — 작성 가이드

이 문서는 매일 아침 브리핑을 생성하는 에이전트가 따라야 하는 규칙이다.

## 임무

전날(및 최근 2~3일) 공개된 치매·알츠하이머병 관련 주요 정보를 웹에서 수집·검증·요약하여
`briefs/YYYY-MM-DD.json`을 생성하고 `briefs/manifest.json`의 `dates` 배열에 날짜를 추가한 뒤
커밋·푸시한다. 날짜는 KST 기준 오늘 날짜를 사용한다.

## 수집 대상 (섹션별)

### 1. `research` — 학술·연구
- PubMed 및 주요 저널의 신규 논문. 특히 다음 고임팩트·전문 저널을 매일 우선 확인한다:
  - **종합의학**: NEJM(New England Journal of Medicine), The Lancet, JAMA, Nature, Science, Cell
  - **신경과/치매 전문**: JAMA Neurology, Lancet Neurology, Nature Medicine, Nature Aging, Neurology, Brain, Alzheimer's & Dementia, Acta Neuropathologica, Molecular Neurodegeneration, Annals of Neurology
  - **영상의학/AI**: Radiology, Radiology: Artificial Intelligence, NeuroImage, npj Digital Medicine
- 치매/AD 바이오마커(아밀로이드, 타우, 혈액검사), 뇌영상(MRI/PET) 분석, AI 진단 모델 관련 논문 우선
- 주요 임상시험 결과 발표 (ClinicalTrials.gov, 학회 발표 — AAIC, CTAD, AD/PD 등)
- arXiv/medRxiv의 의료 AI·신경영상 분석 관련 프리프린트

### 2. `regulatory` — 규제·인허가·정책
- FDA: 510(k), De Novo, PMA 승인 — 특히 neurology/radiology AI 소프트웨어(SaMD)
- 한국 식약처: 의료기기 허가, 혁신의료기기 지정
- 보건복지부/한국보건의료연구원(NECA): **신의료기술 평가, 평가유예 신의료기술, 혁신의료기술** 고시·지정
- 건강보험 수가/급여 관련 (HIRA 심평원)
- CE-MDR 인증, 일본 PMDA 등 해외 인허가
- **국가 보건의료 정책·전략 문서** (신규 발표 또는 개정 시): 관계부처 합동/국가AI전략위원회·보건복지부·과기정통부의 전략·계획·국정과제, R&D·디지털헬스·의료AI 육성 정책, 예산·사업 공고, 국회 법안 등.
  - 예: **AI 기본의료 전략**(2026-07, 관계부처 합동 — 공공의료 AI 플랫폼·AI 진료지원·의료AI 제도화), 제N차 국가 계획 등.
  - **회사 관련성 필터**: 전체를 요약하지 말고, **BeauBrain(뇌 MRI 기반 치매 진단 SW) 사업과 직접 관련된 부분만 발췌**한다 — 의료 AI 산업 육성·AI 의료기기 급여/신의료기술, 뇌영상·치매 진단, 공공의료 AI 플랫폼의 영상분석/판독지원, 관련 R&D·실증사업·예산 등. "이 정책이 우리 사업에 어떤 의미인지" 관점으로 1~2문장 덧붙인다.
  - 이미 다룬 전략의 단순 재보도는 제외(신선도 규칙 적용). 새 발표·개정·후속 세부계획일 때만 포함.
  - 소스 예: 보건복지부·과기정통부 보도자료, 약사공론·메디포뉴스·라포르시안·청년의사·히트뉴스, health.chosun.com 등.

### 3. `market` — 시장·투자
- 치매 진단/디지털 헬스 시장 리포트, 시장 규모 전망
- 관련 기업 투자 유치, M&A, IPO, 파트너십
- 치료제(레켐비/Leqembi, 키순라/Kisunla 등) 시장 확대가 진단 수요에 미치는 영향

### 4. `competitors` — 경쟁사 동향
아래 추적 목록 기업들의 신규 발표, 제품 출시, 인허가, 논문, 투자, 인사 등:

**국내 (뇌영상 AI 진단)**
- 뉴로핏 (Neurophet) — AQUA, SCALE PET
- 뷰노 (VUNO) — VUNO Med DeepBrain
- 제이엘케이 (JLK)
- 휴런 (Heuron)
- 아이메디신 (iMediSync) — EEG 기반
- 딥노이드 (Deepnoid)

**글로벌 (뇌영상 정량분석/AD 진단)**
- icometrix (벨기에) — icobrain
- Cortechs.ai (미국) — NeuroQuant
- Qynapse (프랑스) — QyScore
- Combinostics (핀란드) — cNeuro
- Quibim (스페인)
- Darmiyan (미국) — BrainSee
- Brainomix (영국)

**혈액 바이오마커·기타 진단**
- C2N Diagnostics — PrecivityAD
- Quanterix
- Fujirebio, Roche Diagnostics (AD 혈액/CSF 검사)

**디지털 인지평가**
- Linus Health, Cogstate, Altoida

목록에 없어도 치매 진단 분야 신규 플레이어가 눈에 띄면 포함하고, 반복적으로 등장하면 이 목록에 추가·커밋한다.

### 5. `media` — 주요 언론 보도
- Alzforum, Fierce Biotech, MedTech Dive, STAT News, Endpoints News
- 국내: 메디게이트뉴스, 청년의사, 히트뉴스, 데일리팜, 의협신문 등 의료 전문지
- 일반 언론의 비중 있는 치매 관련 보도 (정책, 국가책임제, 돌봄 등)

## 품질 규칙

- **공신력**: 출처가 불명확한 블로그/홍보성 글 제외. 반드시 원문 URL 포함.
- **신선도**: 최근 3일 이내 공개된 것 우선. 오래된 내용 재탕 금지. 이전 브리핑(`briefs/` 폴더의 최근 파일 2~3개)을 확인해 **중복 게재 금지**.
- **분량**: 섹션당 0~6건. 억지로 채우지 말 것 — 없으면 빈 배열(`"items": []`).
- **요약**: 각 항목 2~3문장 한국어 요약. 핵심 수치(효과 크기, 승인 종류, 투자액)를 포함. 과장 금지.
- **중요도**: BeauBrain(뇌 MRI 기반 치매 진단 SW 개발사) 사업과 직결되는 소식(경쟁사 인허가, 신의료기술 고시, 뇌영상 AI 논문 등)은 `"importance": "high"`, 주목할 만하면 `"medium"`, 그 외는 생략.
- **headline**: 그날 가장 중요한 소식 1개를 한 문장으로.

## JSON 포맷

`briefs/YYYY-MM-DD.json`:

```json
{
  "date": "2026-06-11",
  "generated_at": "2026-06-11T09:00:00+09:00",
  "headline": "한 줄 핵심 요약",
  "sections": [
    {
      "id": "research",
      "title": "학술·연구",
      "items": [
        {
          "title": "항목 제목 (한국어)",
          "summary": "2~3문장 요약.",
          "source": "Nature Medicine",
          "url": "https://...",
          "tags": ["혈액 바이오마커"],
          "importance": "high"
        }
      ]
    },
    { "id": "regulatory", "title": "규제·인허가", "items": [] },
    { "id": "market", "title": "시장·투자", "items": [] },
    { "id": "competitors", "title": "경쟁사 동향", "items": [] },
    { "id": "media", "title": "주요 언론", "items": [] }
  ]
}
```

`briefs/manifest.json`:

```json
{ "dates": ["2026-06-11", "2026-06-12"] }
```

## 커밋 규칙

- 커밋 메시지: `brief: YYYY-MM-DD 데일리 브리프 추가`
- `index.html` 등 사이트 코드는 수정하지 않는다 (브리핑 데이터만 추가).

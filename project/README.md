# 🧞 FinGenie - AI 투자 어드바이저 챗봇

> 생성형 AI와 실시간 검색·분석 기능을 활용한 개인 맞춤형 투자 분석 비서

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)

## 📋 목차

- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [프로젝트 구조](#-프로젝트-구조)
- [주요 기능 설명](#-주요-기능-설명)

## ✨ 주요 기능

### 1. 📊 실시간 종목 분석
- Yahoo Finance API를 통한 실시간 주가 데이터 수집
- 캔들스틱 차트와 거래량 시각화
- 기간별 가격 변동 분석 (1일 ~ 1년)

### 2. 📰 뉴스 기반 감성 분석
- Google News RSS를 통한 최신 뉴스 수집
- 키워드 기반 감성 분석 (긍정/부정/중립)
- LLM 기반 뉴스 요약 (OpenAI API 사용 시)

### 3. ⚠️ AI 위험도 평가
- 가격 변동성 분석
- 뉴스 감성과 결합한 종합 위험도 점수
- 위험 요인 자동 탐지 및 알림

### 4. 💡 개인 맞춤형 투자 조언
- 4가지 투자 성향 프로필 (안정형/중립형/공격형/성장형)
- 사용자 성향에 맞는 AI 투자 조언
- LangGraph 워크플로우 기반 단계별 분석

### 5. 📊 포트폴리오 관리
- 보유 종목 관리 및 평가금액 계산
- 포트폴리오 전체 위험도 분석
- 고위험 종목 자동 탐지

### 6. 📜 분석 기록 관리
- 과거 분석 결과 저장 및 조회
- 시간대별 분석 히스토리

## 🛠️ 기술 스택

### Core Technologies
- **Streamlit**: 웹 대시보드 UI 프레임워크
- **LangChain**: LLM 기반 애플리케이션 개발
- **LangGraph**: 워크플로우 그래프 구성
- **OpenAI GPT**: 자연어 처리 및 분석

### Data & Visualization
- **yfinance**: Yahoo Finance API 클라이언트
- **Plotly**: 인터랙티브 차트 생성
- **Pandas**: 데이터 처리 및 분석
- **feedparser**: RSS 뉴스 피드 파싱

### Architecture
```
사용자 입력
    ↓
LangGraph Workflow
    ↓
[1단계] 데이터 수집 (주가 + 뉴스)
    ↓
[2단계] 뉴스 요약 (LLM)
    ↓
[3단계] 감성 분석
    ↓
[4단계] 위험도 평가
    ↓
[5단계] 투자 조언 생성 (LLM)
    ↓
Streamlit UI 표시
```

## 📦 설치 방법

### 1. 저장소 클론
```bash
git clone <repository-url>
cd week10
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
```

**Windows (PowerShell)**:
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD)**:
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux**:
```bash
source venv/bin/activate
```

### 3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 OpenAI API 키를 설정합니다:

```bash
# .env.example을 복사하여 .env 생성
copy .env.example .env
```

`.env` 파일을 열어 API 키를 입력:
```
OPENAI_API_KEY=your_actual_openai_api_key_here
```

> ⚠️ **주의**: OpenAI API 키가 없어도 기본 기능은 동작하지만, 
> LLM 기반 뉴스 요약과 상세한 투자 조언 기능은 제한됩니다.

## 🚀 사용 방법

### 애플리케이션 실행
```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`로 접속됩니다.

### 기본 사용 흐름

1. **투자 성향 설정**
   - 사이드바에서 투자 성향 선택 (안정형/중립형/공격형/성장형)

2. **종목 분석**
   - 종목 코드 입력 (예: `005930.KS` 삼성전자)
   - 분석 기간 선택 (1일 ~ 1년)
   - "분석하기" 버튼 클릭

3. **결과 확인**
   - 실시간 주가 및 차트
   - 뉴스 요약 및 감성 분석
   - 위험도 평가
   - AI 투자 조언

4. **포트폴리오 관리** (선택)
   - 포트폴리오 탭에서 보유 종목 추가
   - 전체 포트폴리오 위험도 분석

### 종목 코드 입력 예시

**한국 주식**:
- 삼성전자: `005930.KS`
- SK하이닉스: `000660.KS`
- 카카오: `035720.KS`
- 네이버: `035420.KS`

**미국 주식**:
- Apple: `AAPL`
- Tesla: `TSLA`
- Microsoft: `MSFT`
- Google: `GOOGL`

## 📁 프로젝트 구조

```
week10/
├── app.py                 # Streamlit 메인 애플리케이션
├── config.py              # 설정 및 상수
├── tools.py               # LangChain Tools 함수들
├── workflow.py            # LangGraph 워크플로우
├── requirements.txt       # 의존성 패키지 목록
├── .env.example          # 환경 변수 템플릿
├── .env                  # 환경 변수 (git ignore)
└── README.md             # 프로젝트 문서
```

## 🎯 주요 기능 설명

### LangGraph 워크플로우

5단계 분석 파이프라인:

1. **fetch_data**: 주가 데이터 및 뉴스 수집
2. **summarize**: LLM 기반 뉴스 요약
3. **sentiment**: 감성 분석 수행
4. **risk**: 위험도 평가
5. **advice**: 투자 조언 생성

각 단계는 이전 단계의 결과를 활용하여 점진적으로 분석을 심화합니다.

### Tools 구현

#### `get_stock_summary(ticker, period)`
- yfinance를 통한 주가 데이터 수집
- 현재가, 변동률, 거래량 등 기본 정보 제공

#### `get_stock_news(stock_name, max_results)`
- Google News RSS 피드 파싱
- 종목 관련 최신 뉴스 수집

#### `get_sentiment_analysis(news_list)`
- 키워드 기반 감성 분석
- 긍정/부정/중립 분류 및 점수화

#### `calculate_risk_score(stock_data, sentiment_data)`
- 가격 변동성과 뉴스 감성을 결합한 위험도 계산
- 0-100 점수 및 위험 수준 분류

#### `get_portfolio_analysis(portfolio)`
- 포트폴리오 전체 분석
- 고위험 종목 탐지

### UI/UX 특징

- **반응형 대시보드**: 3개 탭 구조 (종목 분석/포트폴리오/기록)
- **인터랙티브 차트**: Plotly를 통한 동적 차트
- **실시간 피드백**: 로딩 스피너 및 상태 메시지
- **사용자 친화적**: 인기 종목 원클릭, 가이드 제공

## 🎤 발표 포인트

### 1. 상업성
- **타겟**: 젊은 투자 초보자 (20-30대)
- **비즈니스 모델**: 
  - 무료: 기본 분석 (일 5회 제한)
  - 프리미엄: 무제한 분석 + 상세 리포트 (월 9,900원)
  - 프로: 포트폴리오 자동 리밸런싱 (월 29,900원)

### 2. 기술성
- ✅ LangChain + LangGraph 활용
- ✅ RAG (검색 증강 생성) 패턴
- ✅ 2개 이상의 Tools 구현
- ✅ 실시간 데이터 통합

### 3. 창의성
- 투자 성향 기반 맞춤형 조언
- 시각화된 위험도 평가
- 포트폴리오 통합 관리
- 분석 히스토리 관리

### 4. 완성도
- 완전한 UI/UX 구현
- 에러 핸들링
- API 키 없이도 기본 동작
- 실제 사용 가능한 수준

## ⚠️ 주의사항

- 본 서비스는 투자 참고용이며, 실제 투자 결정의 책임은 사용자에게 있습니다.
- OpenAI API 사용 시 요금이 발생할 수 있습니다.
- 네트워크 연결이 필요합니다 (주가 데이터 및 뉴스 수집).

## 🔧 트러블슈팅

### API 키 관련
```
문제: OpenAI API 키 오류
해결: .env 파일에 올바른 API 키 설정
```

### 종목 코드 오류
```
문제: 종목 데이터를 찾을 수 없음
해결: 올바른 종목 코드 형식 사용 (한국: .KS/.KQ, 미국: 심볼)
```

### 차트 표시 안됨
```
문제: 차트가 로딩되지 않음
해결: 인터넷 연결 확인, 종목 코드 재확인
```

## 📝 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.

## 👥 개발팀

- **팀명**: [팀 이름]
- **팀원**: [팀원 이름]
- **개발 기간**: 2025년 11월

---

**Made with ❤️ and 🤖 AI**

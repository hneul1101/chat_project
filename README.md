# 🧞 FinGenie - AI 투자 어드바이저

FinGenie는 **Streamlit** 기반의 AI 투자 어드바이저 챗봇 애플리케이션입니다. LangChain, LangGraph를 활용하여 실시간 주가 분석, 뉴스 감성 분석, 포트폴리오 관리 등 종합적인 투자 분석 서비스를 제공합니다.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)

---

## 📁 프로젝트 구조

```
project/
│
├── app.py                  # 🚀 Streamlit 메인 애플리케이션 (진입점)
├── config.py               # ⚙️ 환경설정 및 상수 정의
├── database.py             # 🗄️ SQLite 데이터베이스 관리 (SQLAlchemy ORM)
├── tools.py                # 🔧 주가 분석, 뉴스, 감성 분석 도구 함수
├── tools_agent.py          # 🤖 AI 에이전트 도구 사용 기능 (Function Calling)
├── workflow.py             # 📊 LangGraph 워크플로우 (분석 파이프라인)
├── utils.py                # 🛠️ 유틸리티 함수 (PDF 생성 등)
├── rag_utils.py            # 📚 RAG 유틸리티 (문서 파싱, 청킹, 검색, QA)
├── voice_utils.py          # 🎤 음성 기능 (TTS, STT)
├── requirements.txt        # 📦 의존성 패키지 목록
├── test_pdf.py             # 🧪 PDF 기능 테스트
├── test_setup.py           # 🧪 환경 설정 테스트
│
├── .env                    # 🔑 환경 변수 (API 키) - gitignore 대상
├── fingenie.db             # 💾 SQLite 데이터베이스 파일 (자동 생성)
│
└── __pycache__/            # 🐍 Python 캐시 디렉토리
```

---

## 🏗️ 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Streamlit Frontend                          │
│                           (app.py)                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  로그인/회원가입  │  │  AI 챗봇 페이지 │  │  종목 분석 탭  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │ 포트폴리오 관리 │  │  분석 기록    │                                │
│  └──────────────┘  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Backend Services                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    LangGraph Workflow                        │  │
│  │                     (workflow.py)                            │  │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐  │  │
│  │  │주가 수집│ → │뉴스 요약│ → │감성 분석│ → │투자 조언 생성│  │  │
│  │  └─────────┘   └─────────┘   └─────────┘   └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Tools Agent    │  │  Analysis Tools  │  │  Database Layer  │  │
│  │ (tools_agent.py) │  │   (tools.py)     │  │  (database.py)   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        External APIs                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  OpenAI API  │  │  Yahoo Finance │  │ Google News  │              │
│  │  (GPT-4o)    │  │  (yfinance)   │  │ (RSS Feed)   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📄 파일별 상세 설명

### 1️⃣ `app.py` - 메인 애플리케이션

Streamlit 기반의 메인 UI 애플리케이션입니다.

**주요 기능:**
- **로그인/회원가입 시스템**: 사용자 인증 및 투자 성향 설정
- **AI 챗봇 페이지**: 실시간 스트리밍 응답, 도구 사용 표시
- **종목 분석 탭**: 실시간 주가 차트, 기술적/기본적 분석, 경쟁사 비교
- **포트폴리오 관리**: 국내/해외 주식 분리, 위험도 분석, 백테스팅
- **PDF 내보내기**: 대화 기록을 PDF로 저장

**주요 함수:**
```python
def main()                      # 메인 엔트리 포인트
def login_page()               # 로그인/회원가입 UI
def render_chat_page()         # AI 챗봇 페이지
def display_analysis_result()  # 분석 결과 시각화
def plot_stock_chart()         # Plotly 캔들스틱 차트
```

---

### 2️⃣ `config.py` - 환경 설정

API 키, 투자 성향 프로필, 인기 종목 등 설정값을 관리합니다.

**주요 설정:**
```python
OPENAI_API_KEY              # OpenAI API 키 (.env에서 로드)

INVESTMENT_PROFILES = {
    "conservative": {...},  # 안정형
    "moderate": {...},      # 중립형
    "aggressive": {...},    # 공격형
    "growth": {...}         # 성장형
}

POPULAR_STOCKS = [          # 인기 종목 목록
    {"ticker": "005930.KS", "name": "삼성전자"},
    {"ticker": "AAPL", "name": "Apple"},
    ...
]
```

---

### 3️⃣ `database.py` - 데이터베이스 관리

SQLAlchemy ORM을 사용한 SQLite 데이터베이스 관리 모듈입니다.

**데이터베이스 모델:**

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|----------|
| `User` | 사용자 정보 | id, username, password_hash, settings |
| `Portfolio` | 포트폴리오 | user_id, ticker, shares, avg_price |
| `ChatLog` | 대화 기록 | user_id, role, content, timestamp |

**DBManager 클래스 메서드:**
```python
# 사용자 관리
create_user(username, password, profile)
login_user(username, password)
update_user_profile(user_id, profile)

# 포트폴리오 관리
get_portfolio(user_id)
add_to_portfolio(user_id, ticker, shares)
remove_from_portfolio(user_id, ticker)
clear_portfolio(user_id)

# 대화 기록
add_chat_message(user_id, role, content)
get_chat_history(user_id, limit=50)
clear_chat_history(user_id)
```

---

### 4️⃣ `tools.py` - 분석 도구 함수

주가 데이터 수집, 뉴스 크롤링, 감성 분석 등 핵심 도구 함수들입니다.

**주요 함수:**

| 함수 | 설명 | 반환값 |
|------|------|--------|
| `normalize_ticker()` | 종목명→종목코드 변환 (GPT 활용) | `{"ticker": "005930.KS", "name": "삼성전자"}` |
| `get_stock_summary()` | 주가 데이터 요약 | 현재가, 변동률, 거래량 등 |
| `get_stock_news()` | Google News RSS 크롤링 | 뉴스 제목, 링크, 날짜 |
| `get_technical_indicators()` | 기술적 지표 계산 | RSI, MACD, 볼린저밴드 |
| `get_fundamental_analysis()` | 기본적 분석 | PER, PBR, ROE 등 |
| `get_peer_analysis()` | 경쟁사 비교 | 경쟁사 목록 및 지표 |
| `get_sentiment_analysis()` | 뉴스 감성 분석 | 긍정/부정/중립 비율 |
| `calculate_risk_score()` | 위험도 점수 계산 | 위험 점수, 위험 요인 |
| `chat_with_ai()` | AI 챗봇 대화 | AI 응답 문자열 |
| `analyze_stock_for_chat()` | 챗봇용 종목 분석 | 포맷팅된 분석 결과 |

---

### 5️⃣ `tools_agent.py` - AI 에이전트 (Function Calling)

OpenAI Function Calling을 활용하여 AI가 자동으로 도구를 사용하도록 합니다.

**핵심 기능:**
- 사용자 질문을 분석하여 필요한 도구 자동 선택
- 실시간 스트리밍 응답 지원
- 사용된 도구 목록 반환

**정의된 도구:**
```python
tools = [
    {
        "name": "get_stock_analysis",
        "description": "특정 종목의 실시간 주가, 뉴스, 감성 분석, 위험도 평가를 제공"
    }
]
```

**사용 예시:**
```python
response_generator, used_tools = chat_with_tools_streaming(
    "삼성전자 분석해줘",
    chat_history,
    user_profile
)
```

---

### 6️⃣ `workflow.py` - LangGraph 워크플로우

LangGraph를 사용한 분석 파이프라인입니다.

**워크플로우 단계:**

```
[fetch_data] → [summarize] → [sentiment] → [risk] → [advice] → [END]
     │              │             │           │          │
     ▼              ▼             ▼           ▼          ▼
  주가 수집      뉴스 요약     감성 분석    위험도 평가  투자 조언 생성
```

**상태 구조 (InvestmentState):**
```python
class InvestmentState(TypedDict):
    ticker: str                 # 종목 코드
    stock_name: str             # 종목명
    period: str                 # 분석 기간
    user_profile: str           # 투자 성향
    stock_data: Dict            # 주가 데이터
    technical_indicators: Dict  # 기술적 지표
    fundamental_data: Dict      # 기본적 분석
    peer_data: List[Dict]       # 경쟁사 데이터
    news_data: List[Dict]       # 뉴스 데이터
    news_summary: str           # 뉴스 요약
    sentiment_data: Dict        # 감성 분석 결과
    risk_assessment: Dict       # 위험도 평가
    investment_advice: str      # 투자 조언
    error: str                  # 에러 메시지
```

---

### 7️⃣ `utils.py` - 유틸리티 함수

PDF 생성, 텍스트 처리 등 유틸리티 함수입니다.

**주요 함수:**
```python
def remove_emojis(text)           # 이모지 제거 (PDF 호환성)
def download_font_if_missing()    # 한글 폰트 다운로드 (NanumGothic)
def generate_pdf_report()         # 대화 기록 PDF 생성
```

---

### 8️⃣ `rag_utils.py` - RAG 유틸리티

문서 파싱, 청킹, 검색 및 문서 기반 QA 기능입니다.

**주요 클래스 및 함수:**
```python
class DocumentStore:              # 문서 저장소 클래스
    def add_document()            # 문서 추가 (PDF, TXT, MD)
    def remove_document()         # 문서 제거
    def search()                  # 문서 검색
    def get_document_list()       # 문서 목록 조회

def parse_pdf(file_bytes)         # PDF 텍스트 추출
def parse_text(file_bytes)        # 텍스트 파일 파싱
def chunk_text(text, size, overlap)  # 텍스트 청킹
def simple_retrieval(query, chunks)  # 키워드 기반 검색
def answer_with_rag(query, store)    # RAG 기반 질의응답
def summarize_document(store)        # 문서 요약 생성
```

---

### 9️⃣ `voice_utils.py` - 음성 기능 유틸리티

TTS(음성 출력) 및 STT(음성 입력) 기능입니다.

**주요 함수:**
```python
def text_to_speech(text, lang)    # gTTS를 사용한 음성 합성
def get_audio_player_html(bytes)  # HTML 오디오 플레이어 생성
def speech_to_text_whisper(bytes) # Whisper API를 사용한 음성 인식
def process_audio_input(data)     # 마이크 입력 처리
```

---

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. 애플리케이션 실행

```bash
streamlit run app.py
```

기본적으로 `http://localhost:8501`에서 실행됩니다.

---

## 📦 주요 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `streamlit` | ≥1.28.0 | 웹 UI 프레임워크 |
| `langchain` | ≥0.1.0 | LLM 통합 프레임워크 |
| `langchain-openai` | ≥0.0.2 | OpenAI 연동 |
| `langgraph` | ≥0.0.20 | 워크플로우 그래프 |
| `yfinance` | ≥0.2.0 | 주가 데이터 수집 |
| `plotly` | ≥5.18.0 | 인터랙티브 차트 |
| `pandas` | ≥2.0.0 | 데이터 처리 |
| `pandas_ta` | ≥0.4.67b0 | 기술적 지표 계산 |
| `sqlalchemy` | ≥2.0.0 | ORM 데이터베이스 |
| `feedparser` | ≥6.0.10 | RSS 뉴스 파싱 |
| `fpdf2` | ≥2.7.0 | PDF 생성 |
| `bcrypt` | ≥4.0.0 | 비밀번호 해싱 |
| `aiohttp` | ≥3.9.0 | 비동기 HTTP 요청 |
| `gTTS` | ≥2.4.0 | 텍스트 음성 변환 (TTS) |
| `streamlit-mic-recorder` | ≥0.0.4 | 음성 입력 (STT) |
| `pypdf` | ≥3.17.0 | PDF 문서 파싱 (RAG) |

---

## ✨ 주요 기능

### 🔍 종목 분석
- **스마트 종목 검색**: 한글/영어/오타 허용 (GPT 기반)
- **실시간 주가 차트**: Plotly 캔들스틱 + 거래량
- **기술적 분석**: RSI, MACD, 볼린저 밴드
- **기본적 분석**: PER, PBR, ROE, 부채비율
- **경쟁사 비교**: 동종 업계 지표 비교

### 💬 AI 챗봇
- **Function Calling**: 자동 도구 사용
- **스트리밍 응답**: 실시간 텍스트 표시
- **투자 성향 맞춤**: 안정형/중립형/공격형/성장형
- **대화 기록 저장**: PDF 내보내기 지원

### 📊 포트폴리오 관리
- **국내/해외 분리 관리**: 원화/달러 별도 계산
- **파이 차트 시각화**: 비중 분석
- **위험도 분석**: 고위험 종목 경고
- **1년 백테스팅**: 과거 수익률 계산
- **리밸런싱 제안**: 투자 성향 기반 조언

### 📰 뉴스 & 감성 분석 (인터넷 검색)
- **Google News RSS**: 실시간 뉴스 수집
- **키워드 기반 감성 분석**: 긍정/부정/중립
- **감성 게이지 차트**: 시각적 표현

### 📚 RAG (문서 기반 QA)
- **문서 업로드**: PDF, TXT, MD 파일 지원
- **자동 청킹**: 문서를 검색 가능한 청크로 분할
- **문서 검색**: 질문과 관련된 내용 자동 검색
- **문서 기반 답변**: 업로드된 문서 내용 기반 QA
- **문서 요약**: 업로드된 문서 자동 요약

### 🎤 음성 기능
- **음성 입력 (STT)**: 마이크로 질문 입력 (Whisper API)
- **음성 출력 (TTS)**: AI 응답을 음성으로 출력 (gTTS)
- **한국어 지원**: 한국어 음성 인식 및 합성

---

## 🔐 보안 고려사항

- **비밀번호 해싱**: bcrypt 사용
- **API 키 관리**: `.env` 파일 (gitignore 필수)
- **세션 상태 관리**: Streamlit session_state 활용

---

## 📝 라이선스

이 프로젝트는 교육 및 개인 사용 목적으로 개발되었습니다.

---

## ✅ 평가 기준 충족 현황

### Ⅱ. 구현 및 기술성 (50점)

| 평가 항목 | 배점 | 충족 여부 | 구현 내용 |
|-----------|------|----------|----------|
| **LangChain & LangGraph 사용** | 5점 | ✅ 충족 | `workflow.py`에서 LangGraph 워크플로우 구현, `tools.py`에서 LangChain 활용 |
| **RAG & 인터넷 검색** | 5점 | ✅ 충족 | `rag_utils.py`에서 RAG 구현, Google News RSS로 인터넷 검색 |
| **자체 Tools 2개 이상** | 5점 | ✅ 충족 | `get_stock_analysis`, `get_stock_news`, `normalize_ticker`, `get_technical_indicators` 등 다수 구현 |
| **기술 통합 및 자동화** | 10점 | ✅ 충족 | 검색→요약→분류→음성 기능이 자연스럽게 연결됨 |
| **UI/UX 완성도** | 10점 | ✅ 충족 | Streamlit GUI, 아이콘/이모지 활용, 직관적인 탭 구조 |
| **데이터/사용자 중심성** | 10점 | ✅ 충족 | 투자 성향별 맞춤 조언, 사용자 입력에 따른 동적 응답 |
| **창의성 및 확장성** | 5점 | ✅ 충족 | 음성 기능, RAG 모듈, PDF 내보내기 등 자체 모듈 추가 |

### 구현된 핵심 기술 요소

```
✅ LangChain - LLM 통합 및 프롬프트 관리
✅ LangGraph - 워크플로우 기반 분석 파이프라인
✅ RAG - 문서 업로드, 청킹, 검색, QA
✅ 인터넷 검색 - Google News RSS 실시간 크롤링
✅ Function Calling - AI 에이전트 자동 도구 선택
✅ TTS/STT - 음성 입출력 기능
✅ GUI - Streamlit 기반 웹 인터페이스
```

---

## ⚠️ 면책 조항

본 서비스는 **투자 참고용**이며, 실제 투자 결정은 사용자 본인의 책임입니다. AI가 제공하는 분석 및 조언은 참고 자료일 뿐, 투자 손실에 대한 책임을 지지 않습니다.

---

## 🤝 기여

이슈나 PR은 언제든 환영합니다!

```bash
# 개발 환경 설정
git clone <repository-url>
cd project
pip install -r requirements.txt
streamlit run app.py
```

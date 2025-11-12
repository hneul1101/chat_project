# 🚀 FinGenie 설치 및 실행 가이드

## 빠른 시작 (5분 완성)

### 1️⃣ 가상환경 설정

**PowerShell 사용자**:
```powershell
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
.\venv\Scripts\Activate.ps1
```

PowerShell 실행 정책 오류 발생 시:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**CMD 사용자**:
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### 2️⃣ 패키지 설치

```bash
pip install -r requirements.txt
```

설치 시간: 약 2-3분 소요

### 3️⃣ 환경 변수 설정 (선택)

OpenAI API를 사용하려면:

```powershell
# .env.example을 .env로 복사
copy .env.example .env
```

그 다음 `.env` 파일을 열어서 API 키를 입력:
```
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

> 💡 **중요**: API 키가 없어도 기본 기능은 모두 사용 가능합니다!
> - 주가 데이터 조회 ✅
> - 뉴스 수집 ✅
> - 감성 분석 ✅
> - 위험도 평가 ✅
> - 기본 투자 조언 ✅
>
> API 키가 있으면:
> - LLM 기반 뉴스 요약 🎁
> - 상세한 투자 조언 🎁

### 4️⃣ 설치 테스트

```bash
python test_setup.py
```

모든 테스트가 통과하면 설치 완료!

### 5️⃣ 애플리케이션 실행

**방법 1: 배치 파일 사용 (가장 쉬움)**
```
run.bat  (CMD 사용자)
또는
.\run.ps1  (PowerShell 사용자)
```

**방법 2: 직접 실행**
```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`로 접속됩니다.

---

## 🎯 첫 번째 분석 해보기

### Step 1: 투자 성향 선택
왼쪽 사이드바에서 투자 성향을 선택하세요:
- 안정형: 원금 보존 중시
- 중립형: 균형잡힌 투자
- 공격형: 높은 수익 추구
- 성장형: 장기 성장주 선호

### Step 2: 종목 분석
1. 종목 코드 입력란에 코드 입력
   - 예: `005930.KS` (삼성전자)
   - 예: `AAPL` (애플)

2. 분석 기간 선택
   - 1일, 5일, 1개월, 3개월, 6개월, 1년

3. "📊 분석하기" 버튼 클릭

### Step 3: 결과 확인
- 📈 주가 차트 (캔들스틱 + 거래량)
- 📰 최신 뉴스 요약
- 😊 시장 감성 분석
- ⚠️ 위험도 평가
- 💡 AI 투자 조언

---

## 📚 주요 종목 코드

### 🇰🇷 한국 주식
| 종목명 | 코드 |
|--------|------|
| 삼성전자 | `005930.KS` |
| SK하이닉스 | `000660.KS` |
| NAVER | `035420.KS` |
| 카카오 | `035720.KS` |
| 현대차 | `005380.KS` |
| LG화학 | `051910.KS` |
| 삼성바이오로직스 | `207940.KS` |

### 🇺🇸 미국 주식
| 종목명 | 코드 |
|--------|------|
| Apple | `AAPL` |
| Microsoft | `MSFT` |
| Tesla | `TSLA` |
| Amazon | `AMZN` |
| Google | `GOOGL` |
| NVIDIA | `NVDA` |
| Meta | `META` |

---

## 🔧 문제 해결

### 문제 1: 가상환경 활성화 안됨 (PowerShell)
**증상**: `Activate.ps1 cannot be loaded`

**해결**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 문제 2: 패키지 설치 실패
**해결**:
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 캐시 없이 재설치
pip install -r requirements.txt --no-cache-dir
```

### 문제 3: Streamlit 실행 안됨
**해결**:
```bash
# 직접 모듈로 실행
python -m streamlit run app.py
```

### 문제 4: 종목 데이터를 찾을 수 없음
**원인**: 잘못된 종목 코드 또는 네트워크 문제

**해결**:
1. 올바른 종목 코드 형식 확인
   - 한국: 6자리 + `.KS` (코스피) 또는 `.KQ` (코스닥)
   - 미국: 티커 심볼만 (예: AAPL)
2. 인터넷 연결 확인
3. 다른 종목으로 시도

### 문제 5: 차트가 표시되지 않음
**해결**:
1. 브라우저 새로고침 (F5)
2. 브라우저 캐시 삭제
3. 다른 브라우저 시도 (Chrome 권장)

### 문제 6: OpenAI API 오류
**증상**: LLM 기반 기능 작동 안함

**해결**:
1. `.env` 파일에 올바른 API 키 설정 확인
2. API 키 형식: `sk-...`로 시작
3. API 키가 없으면 기본 기능만 사용 (정상)

---

## 🎓 추가 기능 활용

### 포트폴리오 관리
1. "📊 포트폴리오" 탭 클릭
2. 종목 코드와 보유 수량 입력
3. "➕ 포트폴리오에 추가" 클릭
4. "🔍 포트폴리오 위험도 분석" 클릭

### 분석 기록 조회
1. "📜 분석 기록" 탭 클릭
2. 과거 분석 결과 확인
3. 각 항목을 클릭하면 상세 정보 표시

---

## 💻 시스템 요구사항

- **Python**: 3.8 이상
- **OS**: Windows 10/11, macOS, Linux
- **메모리**: 최소 4GB RAM
- **네트워크**: 인터넷 연결 필요
- **브라우저**: Chrome, Firefox, Edge (최신 버전)

---

## 📞 지원

문제가 계속되거나 질문이 있으면:
1. `README.md` 문서 확인
2. `test_setup.py` 실행하여 진단
3. GitHub Issues 등록

---

## 🎉 설치 완료!

이제 FinGenie를 사용할 준비가 되었습니다!

```bash
# 실행하려면:
streamlit run app.py

# 또는
run.bat  (CMD)
.\run.ps1  (PowerShell)
```

즐거운 투자 분석 되세요! 🚀📈

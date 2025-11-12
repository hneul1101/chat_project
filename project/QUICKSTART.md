# FinGenie 빠른 시작 가이드

## 1단계: 가상환경 생성 및 활성화

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

만약 실행 정책 오류가 발생하면:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Windows (CMD)
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

## 2단계: 패키지 설치
```bash
pip install -r requirements.txt
```

## 3단계: 환경 변수 설정 (선택사항)

OpenAI API를 사용하려면:

1. `.env.example`을 `.env`로 복사
   ```bash
   copy .env.example .env
   ```

2. `.env` 파일 편집하여 API 키 입력
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

> 💡 API 키가 없어도 기본 기능은 사용 가능합니다!

## 4단계: 애플리케이션 실행
```bash
streamlit run app.py
```

자동으로 브라우저가 열립니다. 열리지 않으면:
http://localhost:8501

## 5단계: 첫 번째 분석 해보기

1. 사이드바에서 투자 성향 선택
2. 종목 코드 입력 (예: `005930.KS`)
3. "분석하기" 버튼 클릭
4. 결과 확인!

## 주요 종목 코드

### 한국 주식
- 삼성전자: `005930.KS`
- SK하이닉스: `000660.KS`
- NAVER: `035420.KS`
- 카카오: `035720.KS`
- 현대차: `005380.KS`

### 미국 주식
- Apple: `AAPL`
- Microsoft: `MSFT`
- Tesla: `TSLA`
- Amazon: `AMZN`
- Google: `GOOGL`

## 문제 해결

### 패키지 설치 오류
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Streamlit 실행 오류
```bash
python -m streamlit run app.py
```

### 방화벽 경고
- Windows 방화벽 경고가 나타나면 "액세스 허용" 클릭

## 더 많은 정보

자세한 내용은 `README.md`를 참조하세요.

---

문제가 계속되면 이슈를 등록해주세요!

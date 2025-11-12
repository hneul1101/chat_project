import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 투자 성향 프로필
INVESTMENT_PROFILES = {
    "conservative": {
        "name": "안정형",
        "description": "원금 보존을 최우선으로, 낮은 위험 선호",
        "risk_tolerance": "낮음"
    },
    "moderate": {
        "name": "중립형",
        "description": "적절한 수익과 위험의 균형 추구",
        "risk_tolerance": "중간"
    },
    "aggressive": {
        "name": "공격형",
        "description": "높은 수익을 위해 높은 위험 감수",
        "risk_tolerance": "높음"
    },
    "growth": {
        "name": "성장형",
        "description": "장기 투자 관점의 성장주 선호",
        "risk_tolerance": "중상"
    }
}

# 주요 한국 종목 리스트 (예시)
POPULAR_STOCKS = [
    {"ticker": "005930.KS", "name": "삼성전자"},
    {"ticker": "000660.KS", "name": "SK하이닉스"},
    {"ticker": "035420.KS", "name": "NAVER"},
    {"ticker": "005380.KS", "name": "현대차"},
    {"ticker": "051910.KS", "name": "LG화학"},
    {"ticker": "035720.KS", "name": "카카오"},
    {"ticker": "006400.KS", "name": "삼성SDI"},
    {"ticker": "207940.KS", "name": "삼성바이오로직스"},
]

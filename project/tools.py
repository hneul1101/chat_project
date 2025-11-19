"""
LangChain Tools for FinGenie AI Investment Advisor
"""
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def normalize_ticker(user_input: str) -> Dict[str, str]:
    """
    사용자가 입력한 종목명(한글/영어) 또는 오타를 올바른 종목 코드로 변환합니다.
    GPT를 사용하여 지능적으로 종목 코드를 추론합니다.
    
    Args:
        user_input: 사용자가 입력한 문자열 (예: "삼성전쟈", "삼성", "Apple", "테슬라")
    
    Returns:
        {"ticker": "005930.KS", "name": "삼성전자", "original": "삼성전쟈"}
        또는 {"error": "종목을 찾을 수 없습니다."}
    """
    # 이미 올바른 종목 코드 형식인지 확인 (예: 005930.KS, AAPL)
    if _is_valid_ticker_format(user_input.strip().upper()):
        # 해당 종목이 실제로 존재하는지 확인
        test_ticker = user_input.strip().upper()
        try:
            stock = yf.Ticker(test_ticker)
            info = stock.info
            if info and info.get("regularMarketPrice"):
                return {
                    "ticker": test_ticker,
                    "name": info.get("longName", info.get("shortName", test_ticker)),
                    "original": user_input
                }
        except:
            pass
    
    # GPT를 사용하여 종목 코드 추론
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        # API 키가 없으면 기본 매칭만 시도
        return _basic_ticker_match(user_input)
    
    try:
        llm = ChatOpenAI(
            model="gpt-5-mini-2025-08-07",
            temperature=0,
            api_key=config.OPENAI_API_KEY
        )
        
        # 인기 종목 리스트를 컨텍스트로 제공
        popular_stocks_text = "\n".join([
            f"- {stock['name']}: {stock['ticker']}"
            for stock in config.POPULAR_STOCKS
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 주식 종목 코드 전문가입니다. 
사용자가 입력한 종목명(한글, 영어, 오타 포함)을 정확한 종목 코드로 변환해주세요.

**규칙:**
1. 한국 주식은 6자리 숫자 + .KS (코스피) 또는 .KQ (코스닥) 형식입니다.
2. 미국 주식은 티커 심볼만 사용합니다 (예: AAPL, TSLA)
3. 오타가 있어도 최대한 유사한 종목을 찾아주세요.
4. 확실하지 않으면 가장 유명한 종목을 선택하세요.

**응답 형식 (JSON):**
{{"ticker": "종목코드", "name": "정확한 종목명"}}

**예시:**
- "삼성전쟈" → {{"ticker": "005930.KS", "name": "삼성전자"}}
- "삼성" → {{"ticker": "005930.KS", "name": "삼성전자"}}
- "애플" → {{"ticker": "AAPL", "name": "Apple Inc."}}
- "테슬라" → {{"ticker": "TSLA", "name": "Tesla, Inc."}}
- "SK하닉스" → {{"ticker": "000660.KS", "name": "SK하이닉스"}}

**참고 인기 종목:**
{popular_stocks}"""),
            ("human", "입력: {user_input}\n\nJSON 형식으로만 응답해주세요.")
        ])
        
        response = llm.invoke(
            prompt.format_messages(
                popular_stocks=popular_stocks_text,
                user_input=user_input
            )
        )
        
        # JSON 파싱
        import json
        import re
        
        # JSON 부분만 추출
        content = response.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            ticker = result.get("ticker", "").strip().upper()
            name = result.get("name", "")
            
            # 변환된 종목 코드가 실제로 존재하는지 확인
            if ticker and _verify_ticker_exists(ticker):
                return {
                    "ticker": ticker,
                    "name": name,
                    "original": user_input
                }
        
        # GPT 응답을 파싱할 수 없는 경우 기본 매칭 시도
        return _basic_ticker_match(user_input)
        
    except Exception as e:
        print(f"GPT 종목 코드 변환 오류: {str(e)}")
        return _basic_ticker_match(user_input)


def _is_valid_ticker_format(ticker: str) -> bool:
    """종목 코드 형식이 유효한지 확인"""
    import re
    # 한국 주식: 6자리.KS 또는 6자리.KQ
    # 미국 주식: 1-5자리 알파벳
    korean_pattern = r'^\d{6}\.(KS|KQ)$'
    us_pattern = r'^[A-Z]{1,5}$'
    
    return bool(re.match(korean_pattern, ticker) or re.match(us_pattern, ticker))


def _verify_ticker_exists(ticker: str) -> bool:
    """종목 코드가 실제로 존재하는지 확인"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # regularMarketPrice나 다른 가격 정보가 있으면 유효한 종목
        return bool(info and (
            info.get("regularMarketPrice") or 
            info.get("currentPrice") or 
            info.get("previousClose")
        ))
    except:
        return False


def _basic_ticker_match(user_input: str) -> Dict[str, str]:
    """기본 종목명 매칭 (API 키 없을 때 사용)"""
    user_input_lower = user_input.lower().strip()
    
    # 인기 종목에서 검색
    for stock in config.POPULAR_STOCKS:
        stock_name_lower = stock['name'].lower()
        ticker = stock['ticker']
        
        # 완전 일치 또는 부분 일치
        if user_input_lower in stock_name_lower or stock_name_lower in user_input_lower:
            return {
                "ticker": ticker,
                "name": stock['name'],
                "original": user_input
            }
    
    # 일반적인 영어 종목명 매칭
    common_stocks = {
        "apple": "AAPL",
        "애플": "AAPL",
        "tesla": "TSLA",
        "테슬라": "TSLA",
        "microsoft": "MSFT",
        "마이크로소프트": "MSFT",
        "amazon": "AMZN",
        "아마존": "AMZN",
        "google": "GOOGL",
        "구글": "GOOGL",
        "nvidia": "NVDA",
        "엔비디아": "NVDA",
    }
    
    for key, ticker in common_stocks.items():
        if key in user_input_lower:
            if _verify_ticker_exists(ticker):
                stock = yf.Ticker(ticker)
                name = stock.info.get("longName", ticker)
                return {
                    "ticker": ticker,
                    "name": name,
                    "original": user_input
                }
    
    return {"error": f"'{user_input}'에 해당하는 종목을 찾을 수 없습니다. 정확한 종목 코드를 입력해주세요."}


def get_stock_summary(ticker: str, period: str = "1mo") -> Dict:
    """
    특정 종목의 주가 정보 및 기본 통계를 가져옵니다.
    
    Args:
        ticker: 종목 코드 (예: "005930.KS" for 삼성전자)
        period: 조회 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        주가 데이터 요약 딕셔너리
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        info = stock.info
        
        if hist.empty:
            return {"error": f"종목 코드 {ticker}에 대한 데이터를 찾을 수 없습니다."}
        
        current_price = hist['Close'].iloc[-1]
        start_price = hist['Close'].iloc[0]
        price_change = ((current_price - start_price) / start_price) * 100
        
        summary = {
            "ticker": ticker,
            "name": info.get("longName", "N/A"),
            "current_price": round(current_price, 2),
            "period": period,
            "price_change_percent": round(price_change, 2),
            "high": round(hist['High'].max(), 2),
            "low": round(hist['Low'].min(), 2),
            "volume_avg": int(hist['Volume'].mean()),
            "market_cap": info.get("marketCap", "N/A"),
            "sector": info.get("sector", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
        }
        
        return summary
    except Exception as e:
        return {"error": str(e)}


def get_stock_news(stock_name: str, max_results: int = 5) -> List[Dict]:
    """
    특정 종목의 최신 뉴스를 가져옵니다.
    
    Args:
        stock_name: 종목 이름 (예: "삼성전자")
        max_results: 가져올 뉴스 개수
    
    Returns:
        뉴스 리스트
    """
    try:
        # Google News RSS 피드 사용
        query = stock_name + " 주가"
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        
        feed = feedparser.parse(url)
        news_list = []
        
        for entry in feed.entries[:max_results]:
            news_item = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published if hasattr(entry, 'published') else "N/A",
                "source": entry.source.title if hasattr(entry, 'source') else "N/A"
            }
            news_list.append(news_item)
        
        return news_list
    except Exception as e:
        return [{"error": str(e)}]


def get_sentiment_analysis(news_list: List[Dict]) -> Dict:
    """
    뉴스 리스트에 대한 간단한 감성 분석을 수행합니다.
    (실제로는 OpenAI API를 통해 더 정교한 분석 가능)
    
    Args:
        news_list: 뉴스 딕셔너리 리스트
    
    Returns:
        감성 분석 결과
    """
    # 긍정/부정 키워드 기반 간단한 분석
    positive_keywords = ["상승", "증가", "성장", "호재", "개선", "확대", "급등", "최고", "신고가"]
    negative_keywords = ["하락", "감소", "악화", "악재", "하락세", "급락", "최저", "위기", "손실"]
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for news in news_list:
        if "error" in news:
            continue
        
        title = news.get("title", "")
        
        has_positive = any(keyword in title for keyword in positive_keywords)
        has_negative = any(keyword in title for keyword in negative_keywords)
        
        if has_positive and not has_negative:
            positive_count += 1
        elif has_negative and not has_positive:
            negative_count += 1
        else:
            neutral_count += 1
    
    total = positive_count + negative_count + neutral_count
    
    if total == 0:
        sentiment = "중립"
        score = 50
    else:
        score = ((positive_count - negative_count) / total) * 100 + 50
        
        if score > 60:
            sentiment = "긍정적"
        elif score < 40:
            sentiment = "부정적"
        else:
            sentiment = "중립"
    
    return {
        "sentiment": sentiment,
        "score": round(score, 1),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "total_analyzed": total
    }


def calculate_risk_score(stock_data: Dict, sentiment_data: Dict) -> Dict:
    """
    주가 데이터와 감성 분석을 기반으로 위험도 점수를 계산합니다.
    
    Args:
        stock_data: 주가 데이터
        sentiment_data: 감성 분석 데이터
    
    Returns:
        위험도 평가 결과
    """
    risk_score = 50  # 기본 점수
    risk_factors = []
    
    # 가격 변동성 체크
    if "price_change_percent" in stock_data:
        price_change = abs(stock_data["price_change_percent"])
        if price_change > 20:
            risk_score += 15
            risk_factors.append("높은 가격 변동성")
        elif price_change > 10:
            risk_score += 8
            risk_factors.append("중간 가격 변동성")
    
    # 감성 분석 반영
    if "score" in sentiment_data:
        sentiment_score = sentiment_data["score"]
        if sentiment_score < 40:
            risk_score += 20
            risk_factors.append("부정적 뉴스 트렌드")
        elif sentiment_score < 50:
            risk_score += 10
            risk_factors.append("약한 부정적 뉴스")
    
    # 위험도 레벨 결정
    if risk_score >= 70:
        risk_level = "높음"
        color = "🔴"
    elif risk_score >= 50:
        risk_level = "중간"
        color = "🟡"
    else:
        risk_level = "낮음"
        color = "🟢"
    
    return {
        "risk_score": min(risk_score, 100),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "color": color
    }


def get_portfolio_analysis(portfolio: List[Dict]) -> Dict:
    """
    포트폴리오 전체에 대한 분석을 수행합니다.
    
    Args:
        portfolio: 종목 리스트 [{"ticker": "005930.KS", "shares": 10}, ...]
    
    Returns:
        포트폴리오 분석 결과
    """
    total_value = 0
    high_risk_stocks = []
    
    for item in portfolio:
        ticker = item.get("ticker")
        shares = item.get("shares", 1)
        
        stock_data = get_stock_summary(ticker, period="1mo")
        if "error" not in stock_data:
            value = stock_data["current_price"] * shares
            total_value += value
            
            news = get_stock_news(stock_data.get("name", ticker), max_results=3)
            sentiment = get_sentiment_analysis(news)
            risk = calculate_risk_score(stock_data, sentiment)
            
            if risk["risk_level"] == "높음":
                high_risk_stocks.append({
                    "ticker": ticker,
                    "name": stock_data.get("name"),
                    "risk_score": risk["risk_score"]
                })
    
    return {
        "total_value": round(total_value, 2),
        "total_stocks": len(portfolio),
        "high_risk_count": len(high_risk_stocks),
        "high_risk_stocks": high_risk_stocks
    }

"""
LangChain Tools for Finsearcher AI Investment Advisor
"""
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import json
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


import asyncio
import aiohttp
import feedparser
import pandas_ta as ta

async def fetch_feed(session, url):
    async with session.get(url) as response:
        return await response.text()

async def get_stock_news_async(stock_name: str, max_results: int = 5) -> List[Dict]:
    """
    비동기로 특정 종목의 최신 뉴스를 가져옵니다.
    """
    try:
        query = stock_name + " 주가"
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        
        async with aiohttp.ClientSession() as session:
            xml_data = await fetch_feed(session, url)
            
        feed = feedparser.parse(xml_data)
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

def get_stock_news(stock_name: str, max_results: int = 5) -> List[Dict]:
    """
    동기 래퍼 함수 (기존 코드 호환성 유지)
    """
    return asyncio.run(get_stock_news_async(stock_name, max_results))

def get_technical_indicators(ticker: str, period: str = "6mo") -> Dict:
    """
    기술적 지표(RSI, MACD, BB)를 계산합니다.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            return {"error": "데이터 부족"}
        
        # RSI
        df.ta.rsi(length=14, append=True)
        # MACD
        df.ta.macd(append=True)
        # Bollinger Bands
        df.ta.bbands(length=20, std=2, append=True)
        
        last_row = df.iloc[-1]
        
        return {
            "rsi": round(last_row.get('RSI_14', 0), 2),
            "macd": round(last_row.get('MACD_12_26_9', 0), 2),
            "macd_signal": round(last_row.get('MACDs_12_26_9', 0), 2),
            "bb_upper": round(last_row.get('BBU_20_2.0', 0), 2),
            "bb_lower": round(last_row.get('BBL_20_2.0', 0), 2),
            "close": round(last_row['Close'], 2)
        }
    except Exception as e:
        return {"error": str(e)}

def get_fundamental_analysis(ticker: str) -> Dict:
    """
    기본적 분석 데이터(PER, PBR, ROE 등)를 가져옵니다.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            "per": info.get("trailingPE", "N/A"),
            "pbr": info.get("priceToBook", "N/A"),
            "roe": info.get("returnOnEquity", "N/A"),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "free_cashflow": info.get("freeCashflow", "N/A")
        }
    except Exception as e:
        return {"error": str(e)}

def get_peer_analysis(ticker: str) -> List[Dict]:
    """
    경쟁사 비교 분석 데이터를 가져옵니다.
    """
    try:
        stock = yf.Ticker(ticker)
        sector = stock.info.get("sector")
        industry = stock.info.get("industry")
        
        if not sector or not industry:
            return []
            
        # 같은 산업군의 종목을 찾기 어렵기 때문에, 미리 정의된 경쟁사 리스트 사용
        # 실제로는 스크리닝 API가 필요하지만, 여기서는 주요 종목에 대해 하드코딩된 리스트 사용
        peers_map = {
            "005930.KS": ["000660.KS", "MU"],  # 삼성전자 -> 하이닉스, 마이크론
            "000660.KS": ["005930.KS", "MU"],
            "AAPL": ["MSFT", "GOOGL"],
            "TSLA": ["F", "GM", "TM"],
        }
        
        peer_tickers = peers_map.get(ticker, [])
        peers_data = []
        
        for p_ticker in peer_tickers:
            p_stock = yf.Ticker(p_ticker)
            p_info = p_stock.info
            peers_data.append({
                "ticker": p_ticker,
                "name": p_info.get("longName", p_ticker),
                "per": p_info.get("trailingPE", "N/A"),
                "pbr": p_info.get("priceToBook", "N/A"),
                "roe": p_info.get("returnOnEquity", "N/A")
            })
            
        return peers_data
    except Exception as e:
        return []


def get_sentiment_analysis(news_list: List[Dict]) -> Dict:
    """
    뉴스 리스트에 대한 감성 분석을 수행합니다.
    OpenAI API를 사용하여 정교한 분석을 수행하며, 실패 시 키워드 기반 분석으로 대체합니다.
    
    Args:
        news_list: 뉴스 딕셔너리 리스트
    
    Returns:
        감성 분석 결과
    """
    # 뉴스 데이터 전처리
    valid_news = [news for news in news_list if "error" not in news]
    if not valid_news:
        return {
            "sentiment": "중립",
            "score": 50,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "total_analyzed": 0,
            "reason": "분석할 뉴스가 없습니다."
        }

    # OpenAI API 사용 가능 여부 확인
    if config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your_openai_api_key_here":
        try:
            llm = ChatOpenAI(
                model="gpt-5-mini-2025-08-07",
                temperature=0,
                api_key=config.OPENAI_API_KEY
            )
            
            news_titles = [f"- {news.get('title', '')}" for news in valid_news[:20]] # 최대 20개만 분석
            news_text = "\n".join(news_titles)
            
            prompt = f"""
            다음은 특정 주식 종목과 관련된 최근 뉴스 헤드라인들입니다:
            
            {news_text}
            
            이 뉴스들을 바탕으로 시장의 감성을 분석해주세요.
            다음 JSON 형식으로만 응답해주세요:
            {{
                "sentiment": "긍정적" 또는 "부정적" 또는 "중립",
                "score": 0에서 100 사이의 점수 (0: 매우 부정, 50: 중립, 100: 매우 긍정),
                "reason": "분석 이유 요약 (한 문장)"
            }}
            """
            
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            # JSON 파싱 시도
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            result = json.loads(content)
            
            # 기존 포맷과 호환성을 위해 count 필드 추가 (추정치)
            score = result.get("score", 50)
            total = len(valid_news)
            
            if score > 60:
                pos = int(total * 0.7)
                neg = int(total * 0.1)
            elif score < 40:
                pos = int(total * 0.1)
                neg = int(total * 0.7)
            else:
                pos = int(total * 0.2)
                neg = int(total * 0.2)
                
            neu = total - pos - neg
            
            return {
                "sentiment": result.get("sentiment", "중립"),
                "score": score,
                "positive_count": pos,
                "negative_count": neg,
                "neutral_count": neu,
                "total_analyzed": total,
                "reason": result.get("reason", "")
            }
            
        except Exception as e:
            print(f"OpenAI 감성 분석 실패: {e}")
            # 실패 시 아래 키워드 기반 분석으로 진행
            pass

    # 긍정/부정 키워드 기반 간단한 분석 (백업)
    positive_keywords = ["상승", "증가", "성장", "호재", "개선", "확대", "급등", "최고", "신고가", "매수", "기대"]
    negative_keywords = ["하락", "감소", "악화", "악재", "하락세", "급락", "최저", "위기", "손실", "매도", "우려"]
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for news in valid_news:
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
        # 점수 계산 로직 개선
        sentiment_index = (positive_count - negative_count) / total # -1 ~ 1
        score = (sentiment_index + 1) * 50 # 0 ~ 100
        
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


def get_competitor_analysis(ticker: str, stock_name: str = "", max_competitors: int = 2) -> List[Dict]:
    """
    특정 종목의 경쟁사 데이터를 가져옵니다.
    GPT를 사용하여 경쟁사를 식별하고, yfinance로 데이터를 가져옵니다.
    
    Args:
        ticker: 기준 종목 코드
        stock_name: 기준 종목명 (선택 사항, 없으면 yfinance로 조회)
        max_competitors: 가져올 최대 경쟁사 수 (기본 2)
        
    Returns:
        경쟁사 데이터 리스트
    """
    competitors_data = []
    
    # 1. 종목명 확인
    if not stock_name:
        try:
            stock = yf.Ticker(ticker)
            stock_name = stock.info.get("longName", stock.info.get("shortName", ticker))
        except:
            stock_name = ticker

    # 2. GPT로 경쟁사 식별
    if config.OPENAI_API_KEY:
        try:
            llm = ChatOpenAI(
                model="gpt-5-mini-2025-08-07",
                temperature=0,
                api_key=config.OPENAI_API_KEY
            )
            
            prompt = f"""
            주식 종목 '{{stock_name}}' ({{ticker}})의 주요 경쟁사 {{max_competitors}}개를 알려주세요.
            한국 주식이면 한국 경쟁사, 미국 주식이면 미국/글로벌 경쟁사를 추천해주세요.
            
            다음 JSON 형식으로만 응답해주세요:
            {{{{
                "competitors": [
                    {{{{ "ticker": "종목코드1", "name": "경쟁사명1", "reason": "경쟁 이유" }}}},
                    {{{{ "ticker": "종목코드2", "name": "경쟁사명2", "reason": "경쟁 이유" }}}}
                ]
            }}}}
            
            주의:
            - 한국 주식 코드는 반드시 '.KS' 또는 '.KQ'를 포함해야 합니다 (예: 000660.KS).
            - 미국 주식은 티커 심볼만 사용합니다 (예: AAPL).
            - 정확한 티커를 제공해야 합니다.
            """
            
            response = llm.invoke(prompt.format(stock_name=stock_name, ticker=ticker, max_competitors=max_competitors))
            content = response.content.strip()
            
            # JSON 파싱
            import json
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            result = json.loads(content)
            competitors_list = result.get("competitors", [])
            
            # 3. 각 경쟁사 데이터 조회
            for comp in competitors_list[:max_competitors]:
                comp_ticker = comp.get("ticker")
                comp_name = comp.get("name")
                reason = comp.get("reason")
                
                # 주가 데이터 조회
                summary = get_stock_summary(comp_ticker)
                
                if "error" not in summary:
                    summary["reason"] = reason
                    competitors_data.append(summary)
                    
        except Exception as e:
            print(f"경쟁사 분석 실패: {{e}}")
            pass
            
    return competitors_data


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


def chat_with_ai(user_message: str, chat_history: List[Dict] = None, user_profile: str = "moderate") -> str:
    """
    사용자와 AI 챗봇 간의 대화를 처리합니다.
    투자 관련 질문에 답변하고, 필요시 종목 분석도 수행합니다.
    
    Args:
        user_message: 사용자의 메시지
        chat_history: 이전 대화 내역 [{"role": "user", "content": "..."}, ...]
        user_profile: 사용자의 투자 성향
    
    Returns:
        AI의 응답 메시지
    """
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        return "⚠️ OpenAI API 키가 설정되지 않았습니다. .env 파일에 API 키를 설정해주세요."
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        llm = ChatOpenAI(
            model="gpt-5-nano-2025-08-07",
            api_key=config.OPENAI_API_KEY
        )
        
        # 투자 성향 정보
        profile_info = config.INVESTMENT_PROFILES.get(user_profile, config.INVESTMENT_PROFILES["moderate"])
        
        # 시스템 프롬프트
        system_message = f"""당신은 Finsearcher, 전문적인 AI 투자 어드바이저입니다.

**당신의 역할:**
- 친절하고 전문적으로 투자 관련 질문에 답변합니다
- 종목 분석, 시장 동향, 투자 전략 등에 대해 조언합니다
- 사용자의 투자 성향을 고려하여 맞춤형 조언을 제공합니다
- 복잡한 금융 개념을 쉽게 설명합니다

**사용자 투자 성향:**
- 유형: {profile_info['name']}
- 설명: {profile_info['description']}
- 위험 허용도: {profile_info['risk_tolerance']}

**답변 가이드라인:**
1. 명확하고 구체적으로 답변하세요
2. 필요시 예시를 들어 설명하세요
3. 위험성도 함께 언급하세요
4. 한국 시장과 미국 시장 모두 다룰 수 있습니다
5. 투자 결정은 최종적으로 사용자의 책임임을 상기시키세요

**주요 기능:**
- 종목명이나 코드를 언급하면 실시간 정보를 조회할 수 있습니다
- 포트폴리오 구성, 위험 관리, 투자 전략 등에 대해 조언할 수 있습니다
- 시장 뉴스나 트렌드에 대해 설명할 수 있습니다

답변은 친근하면서도 전문적인 톤으로 작성하세요. 이모지를 적절히 사용하여 가독성을 높이세요."""
        
        # 메시지 구성
        messages = [SystemMessage(content=system_message)]
        
        # 이전 대화 내역 추가
        if chat_history:
            for msg in chat_history[-10:]:  # 최근 10개만 유지
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # 현재 사용자 메시지 추가
        messages.append(HumanMessage(content=user_message))
        
        # AI 응답 생성
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        return f"❌ 오류가 발생했습니다: {str(e)}\n\n다시 시도해주세요."


def analyze_stock_for_chat(ticker_or_name: str) -> str:
    """
    채팅에서 종목 분석을 요청할 때 사용하는 간단한 분석 함수
    
    Args:
        ticker_or_name: 종목 코드 또는 이름
    
    Returns:
        분석 결과 텍스트
    """
    try:
        # 종목 코드 정규화
        normalized = normalize_ticker(ticker_or_name)
        
        if "error" in normalized:
            return f"❌ {normalized['error']}"
        
        ticker = normalized['ticker']
        name = normalized['name']
        
        # 주가 정보 가져오기
        stock_data = get_stock_summary(ticker, period="1mo")
        
        if "error" in stock_data:
            return f"❌ {stock_data['error']}"
        
        # 뉴스 및 감성 분석
        news_data = get_stock_news(name, max_results=3)
        sentiment_data = get_sentiment_analysis(news_data)
        risk_data = calculate_risk_score(stock_data, sentiment_data)
        
        # 결과 포맷팅
        result = f"""
📊 **{name}** ({ticker}) 분석 결과

**현재 주가 정보:**
- 현재가: ₩{stock_data['current_price']:,}
- 변동률: {stock_data['price_change_percent']:+.2f}%
- 최고가: ₩{stock_data['high']:,}
- 최저가: ₩{stock_data['low']:,}

**시장 감성:**
- 감성: {sentiment_data['sentiment']}
- 감성 점수: {sentiment_data['score']}/100
- 긍정 뉴스: {sentiment_data['positive_count']}개
- 부정 뉴스: {sentiment_data['negative_count']}개

**위험도 평가:**
- 위험 수준: {risk_data['color']} {risk_data['risk_level']}
- 위험 점수: {risk_data['risk_score']}/100
"""
        
        if risk_data['risk_factors']:
            result += f"- 위험 요인: {', '.join(risk_data['risk_factors'])}\n"
        
        # 최근 뉴스 추가
        result += "\n**최근 뉴스:**\n"
        for i, news in enumerate(news_data[:3], 1):
            if "error" not in news:
                result += f"{i}. {news['title']}\n"
        
        return result
        
    except Exception as e:
        return f"❌ 분석 중 오류가 발생했습니다: {str(e)}"


def analyze_competitors_for_chat(ticker_or_name: str) -> str:
    """
    채팅에서 경쟁사 분석을 요청할 때 사용하는 함수
    
    Args:
        ticker_or_name: 종목 코드 또는 이름
        
    Returns:
        경쟁사 분석 결과 텍스트
    """
    try:
        # 종목 코드 정규화
        normalized = normalize_ticker(ticker_or_name)
        
        if "error" in normalized:
            return f"❌ {normalized['error']}"
        
        ticker = normalized['ticker']
        name = normalized['name']
        
        # 경쟁사 데이터 가져오기
        competitors = get_competitor_analysis(ticker, name, max_competitors=2)
        
        if not competitors:
            return f"ℹ️ {name}의 경쟁사 정보를 찾을 수 없습니다."
            
        result = f"🏢 **{name}** 경쟁사 분석 (최대 2개)\n\n"
        
        for comp in competitors:
            comp_name = comp.get('name', 'N/A')
            comp_ticker = comp.get('ticker', 'N/A')
            price = comp.get('current_price', 0)
            change = comp.get('price_change_percent', 0)
            reason = comp.get('reason', '')
            
            icon = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
            
            # 통화 기호 처리 (간단하게)
            currency = "₩" if ".KS" in comp_ticker or ".KQ" in comp_ticker else "$"
            
            result += f"**{comp_name}** ({comp_ticker})\n"
            result += f"- 현재가: {currency}{price:,.2f}\n"
            result += f"- 등락률: {icon} {change:+.2f}%\n"
            result += f"- 경쟁 이유: {reason}\n\n"
            
        return result
        
    except Exception as e:
        return f"❌ 경쟁사 분석 중 오류 발생: {str(e)}"


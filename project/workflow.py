"""
LangGraph Workflow for FinGenie AI Investment Advisor
뉴스 요약 → 감성 분석 → 투자 조언 순서의 그래프 워크플로우
"""
from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import config
from tools import (
    get_stock_summary,
    get_stock_news,
    get_sentiment_analysis,
    calculate_risk_score
)


class InvestmentState(TypedDict):
    """투자 분석 워크플로우의 상태"""
    ticker: str
    stock_name: str
    period: str
    user_profile: str
    stock_data: Dict
    news_data: List[Dict]
    news_summary: str
    sentiment_data: Dict
    risk_assessment: Dict
    investment_advice: str
    error: str


def fetch_stock_data(state: InvestmentState) -> InvestmentState:
    """Step 1: 주가 데이터 및 뉴스 수집"""
    print("📊 주가 데이터 수집 중...")
    
    ticker = state["ticker"]
    period = state.get("period", "1mo")
    
    # 주가 데이터 가져오기
    stock_data = get_stock_summary(ticker, period)
    
    if "error" in stock_data:
        state["error"] = stock_data["error"]
        return state
    
    state["stock_data"] = stock_data
    state["stock_name"] = stock_data.get("name", ticker)
    
    # 뉴스 데이터 가져오기
    print("📰 뉴스 데이터 수집 중...")
    news_data = get_stock_news(state["stock_name"], max_results=5)
    state["news_data"] = news_data
    
    return state


def summarize_news(state: InvestmentState) -> InvestmentState:
    """Step 2: 뉴스 요약 (LLM 사용)"""
    print("📝 뉴스 요약 생성 중...")
    
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        # API 키가 없으면 간단한 요약만 제공
        news_list = state["news_data"]
        summary = "최근 뉴스:\n"
        for i, news in enumerate(news_list[:3], 1):
            if "error" not in news:
                summary += f"{i}. {news['title']}\n"
        state["news_summary"] = summary
        return state
    
    try:
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=config.OPENAI_API_KEY
        )
        
        news_list = state["news_data"]
        news_text = "\n".join([f"- {news['title']}" for news in news_list if "error" not in news])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 금융 뉴스 전문 요약가입니다. 주어진 뉴스 제목들을 분석하여 핵심 내용을 간결하게 요약하세요."),
            ("human", f"다음 뉴스들을 3-4문장으로 요약해주세요:\n\n{news_text}")
        ])
        
        response = llm.invoke(prompt.format_messages())
        state["news_summary"] = response.content
        
    except Exception as e:
        # LLM 호출 실패 시 기본 요약
        news_list = state["news_data"]
        summary = "최근 뉴스:\n"
        for i, news in enumerate(news_list[:3], 1):
            if "error" not in news:
                summary += f"{i}. {news['title']}\n"
        state["news_summary"] = summary
    
    return state


def analyze_sentiment(state: InvestmentState) -> InvestmentState:
    """Step 3: 감성 분석"""
    print("😊 감성 분석 수행 중...")
    
    news_data = state["news_data"]
    sentiment_data = get_sentiment_analysis(news_data)
    state["sentiment_data"] = sentiment_data
    
    return state


def assess_risk(state: InvestmentState) -> InvestmentState:
    """Step 4: 위험도 평가"""
    print("⚠️ 위험도 평가 중...")
    
    stock_data = state["stock_data"]
    sentiment_data = state["sentiment_data"]
    
    risk_assessment = calculate_risk_score(stock_data, sentiment_data)
    state["risk_assessment"] = risk_assessment
    
    return state


def generate_investment_advice(state: InvestmentState) -> InvestmentState:
    """Step 5: 투자 조언 생성 (LLM 사용)"""
    print("💡 투자 조언 생성 중...")
    
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        # API 키가 없으면 규칙 기반 조언
        risk_level = state["risk_assessment"]["risk_level"]
        sentiment = state["sentiment_data"]["sentiment"]
        user_profile = state.get("user_profile", "moderate")
        
        advice = f"""
### 투자 조언

**위험도**: {risk_level}
**시장 감성**: {sentiment}
**투자 성향**: {config.INVESTMENT_PROFILES[user_profile]['name']}

"""
        if risk_level == "높음":
            advice += "⚠️ 현재 높은 위험도가 감지되었습니다. 신중한 접근이 필요합니다.\n"
        elif risk_level == "중간":
            advice += "📊 중간 수준의 위험도입니다. 적절한 분산 투자를 고려하세요.\n"
        else:
            advice += "✅ 상대적으로 안정적인 상태입니다.\n"
        
        state["investment_advice"] = advice
        return state
    
    try:
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=config.OPENAI_API_KEY
        )
        
        stock_data = state["stock_data"]
        risk_data = state["risk_assessment"]
        sentiment_data = state["sentiment_data"]
        news_summary = state["news_summary"]
        user_profile = state.get("user_profile", "moderate")
        profile_info = config.INVESTMENT_PROFILES[user_profile]
        
        context = f"""
종목: {state['stock_name']} ({state['ticker']})
현재가: {stock_data['current_price']}
기간 변동률: {stock_data['price_change_percent']}%
위험도: {risk_data['risk_level']} (점수: {risk_data['risk_score']})
시장 감성: {sentiment_data['sentiment']} (점수: {sentiment_data['score']})

뉴스 요약:
{news_summary}

투자자 성향: {profile_info['name']} - {profile_info['description']}
위험 허용도: {profile_info['risk_tolerance']}
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문 투자 어드바이저입니다. 
주어진 데이터를 바탕으로 투자자의 성향에 맞는 구체적이고 실용적인 투자 조언을 제공하세요.
조언은 명확하고 이해하기 쉬워야 하며, 구체적인 근거를 포함해야 합니다."""),
            ("human", f"다음 정보를 분석하여 투자 조언을 작성해주세요:\n\n{context}")
        ])
        
        response = llm.invoke(prompt.format_messages())
        state["investment_advice"] = response.content
        
    except Exception as e:
        # LLM 호출 실패 시 기본 조언
        risk_level = state["risk_assessment"]["risk_level"]
        sentiment = state["sentiment_data"]["sentiment"]
        
        advice = f"""
### 투자 조언

**위험도**: {risk_level}
**시장 감성**: {sentiment}

현재 수집된 데이터를 기반으로 한 기본 분석입니다.
더 상세한 분석을 위해서는 OpenAI API 키 설정이 필요합니다.
"""
        state["investment_advice"] = advice
    
    return state


def check_error(state: InvestmentState) -> str:
    """에러 체크"""
    if state.get("error"):
        return "error"
    return "continue"


# LangGraph 워크플로우 생성
def create_investment_workflow():
    """투자 분석 워크플로우 생성"""
    workflow = StateGraph(InvestmentState)
    
    # 노드 추가
    workflow.add_node("fetch_data", fetch_stock_data)
    workflow.add_node("summarize", summarize_news)
    workflow.add_node("sentiment", analyze_sentiment)
    workflow.add_node("risk", assess_risk)
    workflow.add_node("advice", generate_investment_advice)
    
    # 엣지 연결
    workflow.set_entry_point("fetch_data")
    workflow.add_conditional_edges(
        "fetch_data",
        check_error,
        {
            "continue": "summarize",
            "error": END
        }
    )
    workflow.add_edge("summarize", "sentiment")
    workflow.add_edge("sentiment", "risk")
    workflow.add_edge("risk", "advice")
    workflow.add_edge("advice", END)
    
    return workflow.compile()


# 간편한 분석 함수
def analyze_stock(ticker: str, period: str = "1mo", user_profile: str = "moderate") -> InvestmentState:
    """
    주식을 분석하는 메인 함수
    
    Args:
        ticker: 종목 코드
        period: 분석 기간
        user_profile: 사용자 투자 성향
    
    Returns:
        분석 결과 상태
    """
    workflow = create_investment_workflow()
    
    initial_state = {
        "ticker": ticker,
        "stock_name": "",
        "period": period,
        "user_profile": user_profile,
        "stock_data": {},
        "news_data": [],
        "news_summary": "",
        "sentiment_data": {},
        "risk_assessment": {},
        "investment_advice": "",
        "error": ""
    }
    
    result = workflow.invoke(initial_state)
    return result

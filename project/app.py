"""
FinGenie - AI Investment Advisor Chatbot
Streamlit Dashboard Application
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
import config
from workflow import analyze_stock
from tools import get_stock_summary, get_portfolio_analysis, normalize_ticker
import yfinance as yf


# 페이지 설정
st.set_page_config(
    page_title="FinGenie - AI 투자 어드바이저",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stock-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    .metric-card {
        text-align: center;
        padding: 1rem;
        border-radius: 8px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .risk-high {
        background-color: #ff4444;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
    }
    .risk-medium {
        background-color: #ffbb33;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
    }
    .risk-low {
        background-color: #00c851;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """세션 상태 초기화"""
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = 'moderate'
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []


def plot_stock_chart(ticker: str, period: str = "1mo", chart_key: str = "main"):
    """주가 차트 생성"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            st.warning("차트 데이터를 가져올 수 없습니다.")
            return
        
        fig = go.Figure()
        
        # 캔들스틱 차트
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='주가'
        ))
        
        # 거래량
        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist['Volume'],
            name='거래량',
            yaxis='y2',
            opacity=0.3
        ))
        
        fig.update_layout(
            title=f"{ticker} 주가 차트",
            yaxis_title='주가',
            yaxis2=dict(
                title='거래량',
                overlaying='y',
                side='right'
            ),
            xaxis_rangeslider_visible=False,
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}_{period}_{chart_key}")
        
    except Exception as e:
        st.error(f"차트 생성 중 오류 발생: {str(e)}")


def display_analysis_result(result, result_key="main"):
    """분석 결과 표시"""
    if result.get("error"):
        st.error(f"❌ 오류: {result['error']}")
        return
    
    # 기본 정보
    st.markdown(f"## 📊 {result['stock_name']} ({result['ticker']})")
    
    # 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)
    
    stock_data = result['stock_data']
    with col1:
        st.metric(
            label="현재가",
            value=f"₩{stock_data['current_price']:,.2f}",
            delta=f"{stock_data['price_change_percent']:.2f}%"
        )
    
    with col2:
        st.metric(
            label="기간 최고가",
            value=f"₩{stock_data['high']:,.2f}"
        )
    
    with col3:
        st.metric(
            label="기간 최저가",
            value=f"₩{stock_data['low']:,.2f}"
        )
    
    with col4:
        st.metric(
            label="평균 거래량",
            value=f"{stock_data['volume_avg']:,}"
        )
    
    # 차트
    st.markdown("### 📈 주가 차트")
    plot_stock_chart(result['ticker'], result['period'], chart_key=result_key)
    
    # 뉴스 요약 및 감성 분석
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📰 뉴스 요약")
        st.info(result['news_summary'])
        
        st.markdown("#### 최근 뉴스")
        for i, news in enumerate(result['news_data'][:3], 1):
            if "error" not in news:
                st.markdown(f"**{i}.** [{news['title']}]({news['link']})")
    
    with col2:
        st.markdown("### 😊 감성 분석")
        sentiment_data = result['sentiment_data']
        
        # 감성 점수 게이지
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=sentiment_data['score'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "시장 감성 점수"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightcoral"},
                    {'range': [40, 60], 'color': "lightyellow"},
                    {'range': [60, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': sentiment_data['score']
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True, key=f"sentiment_{result['ticker']}_{result_key}")
        
        st.markdown(f"""
        - **전체 감성**: {sentiment_data['sentiment']}
        - 긍정 뉴스: {sentiment_data['positive_count']}개
        - 부정 뉴스: {sentiment_data['negative_count']}개
        - 중립 뉴스: {sentiment_data['neutral_count']}개
        """)
    
    # 위험도 평가
    st.markdown("### ⚠️ 위험도 평가")
    risk_data = result['risk_assessment']
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        risk_level = risk_data['risk_level']
        if risk_level == "높음":
            st.markdown('<div class="risk-high">🔴 위험도: 높음</div>', unsafe_allow_html=True)
        elif risk_level == "중간":
            st.markdown('<div class="risk-medium">🟡 위험도: 중간</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="risk-low">🟢 위험도: 낮음</div>', unsafe_allow_html=True)
        
        st.metric("위험 점수", f"{risk_data['risk_score']}/100")
    
    with col2:
        if risk_data['risk_factors']:
            st.markdown("**위험 요인:**")
            for factor in risk_data['risk_factors']:
                st.markdown(f"- {factor}")
        else:
            st.success("특별한 위험 요인이 감지되지 않았습니다.")
    
    # 투자 조언
    st.markdown("### 💡 AI 투자 조언")
    st.markdown(result['investment_advice'])
    
    # 분석 시간
    st.caption(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """메인 애플리케이션"""
    initialize_session_state()
    
    # 헤더
    st.markdown('<div class="main-header">🧞 FinGenie</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI 기반 개인 맞춤형 투자 분석 비서</div>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/667eea/ffffff?text=FinGenie", use_container_width=True)
        
        st.markdown("## ⚙️ 설정")
        
        # 투자 성향 선택
        profile_names = {k: v['name'] for k, v in config.INVESTMENT_PROFILES.items()}
        selected_profile = st.selectbox(
            "투자 성향",
            options=list(profile_names.keys()),
            format_func=lambda x: profile_names[x],
            index=list(profile_names.keys()).index(st.session_state.user_profile)
        )
        st.session_state.user_profile = selected_profile
        
        profile_info = config.INVESTMENT_PROFILES[selected_profile]
        st.info(f"**{profile_info['name']}**\n\n{profile_info['description']}\n\n위험 허용도: {profile_info['risk_tolerance']}")
        
        st.markdown("---")
        
        # 인기 종목
        st.markdown("## 🔥 인기 종목")
        for stock in config.POPULAR_STOCKS[:5]:
            if st.button(f"{stock['name']}", key=f"popular_{stock['ticker']}"):
                st.session_state.selected_ticker = stock['ticker']
                st.session_state.selected_name = stock['name']
        
        st.markdown("---")
        
        # API 키 상태
        if config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your_openai_api_key_here":
            st.success("✅ OpenAI API 연결됨")
        else:
            st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다.\n\n.env 파일에 API 키를 설정하면 더 상세한 분석을 받을 수 있습니다.")
    
    # 메인 컨텐츠
    tabs = st.tabs(["🔍 종목 분석", "📊 포트폴리오", "📜 분석 기록"])
    
    # 탭 1: 종목 분석
    with tabs[0]:
        st.markdown("## 🔍 종목 분석")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # 종목 입력
            ticker_input = st.text_input(
                "종목 코드 입력",
                value=st.session_state.get('selected_ticker', '005930.KS'),
                placeholder="예: 005930.KS (삼성전자)"
            )
        
        with col2:
            period = st.selectbox(
                "분석 기간",
                options=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
                index=2
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_button = st.button("📊 분석하기", type="primary", use_container_width=True)
        
        # 분석 실행
        if analyze_button:
            if ticker_input:
                with st.spinner("종목 코드 확인 중..."):
                    # 사용자 입력을 종목 코드로 변환
                    normalized = normalize_ticker(ticker_input)
                    
                    if "error" in normalized:
                        st.error(f"❌ {normalized['error']}")
                    else:
                        # 변환된 종목 정보 표시
                        if normalized['original'] != normalized['ticker']:
                            st.success(f"✅ '{normalized['original']}' → **{normalized['name']}** ({normalized['ticker']})")
                        
                        with st.spinner("분석 중입니다... 잠시만 기다려주세요."):
                            result = analyze_stock(
                                ticker=normalized['ticker'],
                                period=period,
                                user_profile=st.session_state.user_profile
                            )
                            
                            # 결과 표시
                            display_analysis_result(result, result_key="current_analysis")
                            
                            # 히스토리에 추가
                            if not result.get("error"):
                                st.session_state.analysis_history.insert(0, {
                                    "timestamp": datetime.now(),
                                    "result": result
                                })
            else:
                st.warning("종목 코드를 입력해주세요.")
        
        # 종목 코드 가이드
        with st.expander("📘 종목 코드 입력 가이드"):
            st.markdown("""
            **🎯 이제 더 쉽게 입력할 수 있습니다!**
            
            **한글 종목명 입력 가능:**
            - 예) `삼성전자`, `SK하이닉스`, `카카오`
            - 오타도 괜찮아요: `삼성전쟈`, `SK하닉스`
            
            **영어 종목명 입력 가능:**
            - 예) `Apple`, `Tesla`, `Microsoft`
            - 한글도 가능: `애플`, `테슬라`
            
            **정확한 종목 코드:**
            - 한국 주식: 종목코드 + `.KS` 또는 `.KQ`
              - 예) 삼성전자: `005930.KS`
              - 예) 카카오: `035720.KS`
            
            - 미국 주식: 티커 심볼
              - 예) Apple: `AAPL`
              - 예) Tesla: `TSLA`
            
            **💡 팁**: 
            - 사이드바의 인기 종목을 클릭하면 자동으로 입력됩니다.
            - AI가 자동으로 올바른 종목 코드를 찾아줍니다!
            """)
    
    # 탭 2: 포트폴리오
    with tabs[1]:
        st.markdown("## 📊 나의 포트폴리오")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            new_ticker = st.text_input("종목 추가", placeholder="종목명 또는 코드 입력 (예: 삼성전자, AAPL)")
        
        with col2:
            new_shares = st.number_input("보유 수량", min_value=1, value=1)
        
        if st.button("➕ 포트폴리오에 추가"):
            if new_ticker:
                with st.spinner("종목 확인 중..."):
                    # 사용자 입력을 종목 코드로 변환
                    normalized = normalize_ticker(new_ticker)
                    
                    if "error" in normalized:
                        st.error(f"❌ {normalized['error']}")
                    else:
                        st.session_state.portfolio.append({
                            "ticker": normalized['ticker'],
                            "shares": new_shares
                        })
                        st.success(f"✅ **{normalized['name']}** ({normalized['ticker']}) 종목이 포트폴리오에 추가되었습니다!")
                        st.rerun()
        
        if st.session_state.portfolio:
            st.markdown("### 보유 종목")
            
            portfolio_data = []
            for item in st.session_state.portfolio:
                ticker = item['ticker']
                shares = item['shares']
                
                stock_data = get_stock_summary(ticker, period="1d")
                if "error" not in stock_data:
                    portfolio_data.append({
                        "종목코드": ticker,
                        "종목명": stock_data.get("name", "N/A"),
                        "보유수량": shares,
                        "현재가": stock_data.get("current_price", 0),
                        "평가금액": stock_data.get("current_price", 0) * shares,
                        "변동률": f"{stock_data.get('price_change_percent', 0):.2f}%"
                    })
            
            if portfolio_data:
                df = pd.DataFrame(portfolio_data)
                st.dataframe(df, use_container_width=True)
                
                total_value = df['평가금액'].sum()
                st.metric("총 평가금액", f"₩{total_value:,.2f}")
                
                # 포트폴리오 분석
                if st.button("🔍 포트폴리오 위험도 분석"):
                    with st.spinner("분석 중..."):
                        analysis = get_portfolio_analysis(st.session_state.portfolio)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("보유 종목 수", analysis['total_stocks'])
                        with col2:
                            st.metric("총 평가액", f"₩{analysis['total_value']:,.2f}")
                        with col3:
                            st.metric("고위험 종목", analysis['high_risk_count'])
                        
                        if analysis['high_risk_stocks']:
                            st.warning("⚠️ 주의가 필요한 종목")
                            for stock in analysis['high_risk_stocks']:
                                st.markdown(f"- **{stock['name']}** (위험점수: {stock['risk_score']})")
            
            if st.button("🗑️ 포트폴리오 초기화"):
                st.session_state.portfolio = []
                st.rerun()
        else:
            st.info("포트폴리오가 비어있습니다. 종목을 추가해보세요!")
    
    # 탭 3: 분석 기록
    with tabs[2]:
        st.markdown("## 📜 분석 기록")
        
        if st.session_state.analysis_history:
            for i, item in enumerate(st.session_state.analysis_history[:10]):
                with st.expander(f"{item['timestamp'].strftime('%Y-%m-%d %H:%M')} - {item['result'].get('stock_name', 'N/A')}"):
                    display_analysis_result(item['result'], result_key=f"history_{i}")
            
            if st.button("🗑️ 기록 삭제"):
                st.session_state.analysis_history = []
                st.rerun()
        else:
            st.info("아직 분석 기록이 없습니다.")
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🧞 <strong>FinGenie</strong> - AI 기반 투자 분석 비서</p>
        <p style="font-size: 0.8rem;">
            ⚠️ 본 서비스는 투자 참고용이며, 실제 투자 결정은 신중히 하시기 바랍니다.
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

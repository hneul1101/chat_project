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
from utils import generate_pdf_report
from database import DBManager
from tools import (
    get_stock_summary, 
    get_portfolio_analysis, 
    normalize_ticker,
    chat_with_ai,
    analyze_stock_for_chat,
    get_stock_news
)
from tools_agent import chat_with_tools_streaming
import yfinance as yf

# DB Manager 초기화
if 'db' not in st.session_state:
    st.session_state.db = DBManager()

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
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = 'moderate'
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False

def login_page():
    """로그인/회원가입 페이지"""
    st.markdown('<div class="main-header">🧞 FinGenie</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">로그인이 필요합니다</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("사용자명")
            password = st.text_input("비밀번호", type="password")
            submit = st.form_submit_button("로그인", width='stretch')
            
            if submit:
                user = st.session_state.db.login_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.user_profile = user.settings.get('profile', 'moderate')
                    # Load data from DB
                    st.session_state.portfolio = st.session_state.db.get_portfolio(user.id)
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("사용자명 또는 비밀번호가 잘못되었습니다.")
    
    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("사용자명")
            new_password = st.text_input("비밀번호", type="password")
            confirm_password = st.text_input("비밀번호 확인", type="password")
            profile = st.selectbox("투자 성향", options=list(config.INVESTMENT_PROFILES.keys()))
            submit = st.form_submit_button("회원가입", width='stretch')
            
            if submit:
                if new_password != confirm_password:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif len(new_password) < 4:
                    st.error("비밀번호는 4자 이상이어야 합니다.")
                else:
                    user, error = st.session_state.db.create_user(new_username, new_password, profile)
                    if error:
                        st.error(f"회원가입 실패: {error}")
                    else:
                        st.success("회원가입이 완료되었습니다! 로그인해주세요.")

def render_chat_page():
    """독립된 AI 챗봇 페이지"""
    # 페이지 설정
    st.markdown('<div class="main-header">💬 FinGenie AI 챗봇</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI와 대화하며 투자 조언을 받아보세요</div>', unsafe_allow_html=True)

    with st.sidebar:
        # st.image("https://via.placeholder.com/300x100/667eea/ffffff?text=FinGenie", width='stretch')
        
        # 뒤로 가기 버튼
        if st.button("← 메인으로 돌아가기", width='stretch'):
            st.session_state.show_chat = False
            st.rerun()
        
        st.markdown("---")
        
        # 투자 성향 표시
        profile_info = config.INVESTMENT_PROFILES[st.session_state.user_profile]
        st.markdown("## ⚙️ 현재 설정")
        st.info(f"**투자 성향: {profile_info['name']}**\n\n{profile_info['description']}")
        
        st.markdown("---")
        
        # 대화 통계
        st.markdown("## 📊 대화 통계")
        st.metric("전체 메시지", len(st.session_state.chat_messages))
        st.metric("대화 기록", len(st.session_state.chat_history))
        
        st.markdown("---")
        
        # 대화 초기화
        if st.button("🗑️ 대화 기록 삭제", width='stretch'):
            st.session_state.chat_messages = []
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")

        # 투자 일기 내보내기 (PDF)
        st.markdown("## 📥 투자 일기")
        if st.button("📄 PDF로 내보내기", width='stretch'):
            if not st.session_state.chat_history:
                st.warning("내보낼 대화 기록이 없습니다.")
            else:
                with st.spinner("PDF 생성 중... (폰트 다운로드로 인해 시간이 걸릴 수 있습니다)"):
                    pdf_file, error = generate_pdf_report(
                        st.session_state.chat_history,
                        st.session_state.user_profile
                    )
                    
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        with open(pdf_file, "rb") as f:
                            st.download_button(
                                label="⬇️ PDF 다운로드",
                                data=f,
                                file_name=pdf_file,
                                mime="application/pdf",
                                width='stretch'
                            )
                        st.success("✅ PDF가 생성되었습니다!")
        
        st.markdown("---")
        
        # API 상태
        if config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your_openai_api_key_here":
            st.success("✅ OpenAI API 연결됨")
        else:
            st.error("❌ OpenAI API 키 필요")
    
    # API 키 확인
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        st.error("⚠️ OpenAI API 키가 설정되지 않았습니다.")
        st.info("`.env` 파일에 다음과 같이 API 키를 설정해주세요:\n\n```\nOPENAI_API_KEY=sk-your-api-key-here\n```")
        return
    
    # 환영 메시지
    if not st.session_state.chat_messages:
        with st.chat_message("assistant"):
            st.markdown("""
            안녕하세요! 저는 **FinGenie AI 투자 어드바이저**입니다. 🧞✨
            
            **제가 도와드릴 수 있는 것들:**
            - 📊 특정 종목 분석 및 투자 조언
            - 💼 포트폴리오 구성 및 관리 전략
            - 📈 시장 동향 및 트렌드 분석
            - 🎯 투자 전략 및 리스크 관리
            - 💡 투자 관련 용어 및 개념 설명
            
            무엇을 도와드릴까요? 😊
            """)
    
    # 이전 메시지들 표시
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 예시 질문 버튼들 (메시지가 없을 때만 표시)
    if len(st.session_state.chat_messages) == 0:
        st.markdown("### 💡 예시 질문을 클릭해보세요")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 삼성전자 분석해줘", width='stretch'):
                st.session_state.pending_input = "삼성전자 종목을 분석해주고 지금 매수하기 좋은지 투자 의견을 알려줘"
                st.rerun()
        
        with col2:
            if st.button("💼 포트폴리오 구성법", width='stretch'):
                st.session_state.pending_input = "초보 투자자를 위한 안전한 포트폴리오 구성 방법을 알려줘"
                st.rerun()
        
        with col3:
            if st.button("🎯 장기 투자 전략", width='stretch'):
                st.session_state.pending_input = "안정적인 장기 투자 전략에 대해 자세히 알려줘"
                st.rerun()
    
    # 채팅 입력 (하단 고정)
    if prompt := st.chat_input("메시지를 입력하세요...", key="chat_input_main"):
        # 사용자 메시지 처리
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # AI 응답 처리
        with st.chat_message("assistant"):
            # 빈 컨테이너로 시작 (깜빡임 방지)
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                with st.spinner("분석 중..."):
                    # 도구를 사용하는 AI 호출
                    response_generator, used_tools = chat_with_tools_streaming(
                        prompt,
                        st.session_state.chat_history[:-1],
                        st.session_state.user_profile
                    )
                
                # 사용된 도구 표시 (Expander로 깔끔하게)
                if used_tools:
                    tool_names = {
                        "get_stock_analysis": "📊 실시간 종목 분석",
                        "get_stock_news": "📰 뉴스 검색",
                        "get_market_status": "� 시장 현황"
                    }
                    tool_display = " • ".join([tool_names.get(t, t) for t in used_tools])
                    with st.expander(f"🔧 사용된 도구: {tool_display}"):
                        st.json(used_tools)

                # 스트리밍 응답
                for chunk in response_generator:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                
                # 최종 응답 표시 (커서 제거)
                message_placeholder.markdown(full_response)
                
                # 응답 저장
                st.session_state.chat_messages.append({"role": "assistant", "content": full_response})
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_msg = f"❌ 오류가 발생했습니다: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})

    # 예시 버튼 처리 (pending_input)
    if 'pending_input' in st.session_state and st.session_state.pending_input:
        prompt = st.session_state.pending_input
        del st.session_state.pending_input
        
        # 사용자 메시지 추가
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        st.rerun()


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
        
        st.plotly_chart(fig, width='stretch', key=f"chart_{ticker}_{period}_{chart_key}")
        
    except Exception as e:
        st.error(f"차트 생성 중 오류 발생: {str(e)}")


def display_analysis_result(result, result_key="main"):
    """분석 결과 표시"""
    if result.get("error"):
        st.error(f"❌ 오류: {result['error']}")
        return
    
    # 기본 정보
    st.markdown(f"## 📊 {result['stock_name']} ({result['ticker']})")
    
    # 통화 기호 결정
    currency_symbol = "₩"
    ticker = result['ticker']
    if not (ticker.endswith(".KS") or ticker.endswith(".KQ")):
        currency_symbol = "$"

    # 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)
    
    stock_data = result['stock_data']
    with col1:
        st.metric(
            label="현재가",
            value=f"{currency_symbol}{stock_data['current_price']:,.2f}",
            delta=f"{stock_data['price_change_percent']:.2f}%"
        )
    
    with col2:
        st.metric(
            label="기간 최고가",
            value=f"{currency_symbol}{stock_data['high']:,.2f}"
        )
    
    with col3:
        st.metric(
            label="기간 최저가",
            value=f"{currency_symbol}{stock_data['low']:,.2f}"
        )
    
    with col4:
        st.metric(
            label="평균 거래량",
            value=f"{stock_data['volume_avg']:,}"
        )
    
    # 차트
    st.markdown("### 📈 주가 차트")
    plot_stock_chart(result['ticker'], result['period'], chart_key=result_key)
    
    # 기술적/기본적 분석 탭
    tab1, tab2, tab3 = st.tabs(["📊 기술적 분석", "🏢 기본적 분석", "👥 경쟁사 비교"])
    
    with tab1:
        tech = result.get('technical_indicators', {})
        if tech:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RSI (14)", tech.get('rsi', 'N/A'))
            with col2:
                st.metric("MACD", tech.get('macd', 'N/A'), delta=tech.get('macd_signal', 'N/A'))
            with col3:
                st.metric("볼린저 상단", tech.get('bb_upper', 'N/A'))
                st.metric("볼린저 하단", tech.get('bb_lower', 'N/A'))
        else:
            st.info("기술적 분석 데이터가 없습니다.")

    with tab2:
        fund = result.get('fundamental_data', {})
        if fund:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("PER", fund.get('per', 'N/A'))
                st.metric("부채비율", fund.get('debt_to_equity', 'N/A'))
            with col2:
                st.metric("PBR", fund.get('pbr', 'N/A'))
                st.metric("ROE", fund.get('roe', 'N/A'))
            with col3:
                st.metric("매출성장률", fund.get('revenue_growth', 'N/A'))
                st.metric("잉여현금흐름", fund.get('free_cashflow', 'N/A'))
        else:
            st.info("기본적 분석 데이터가 없습니다.")
            
    with tab3:
        peers = result.get('peer_data', [])
        if peers:
            st.dataframe(pd.DataFrame(peers), width='stretch')
        else:
            st.info("경쟁사 데이터가 없습니다.")
    
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
        st.plotly_chart(fig, width='stretch', key=f"sentiment_{result['ticker']}_{result_key}")
        
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
    # 세션 상태 초기화
    initialize_session_state()
    
    # 로그인 체크
    if not st.session_state.user:
        login_page()
        return
    
    # 채팅 페이지 라우팅
    if st.session_state.show_chat:
        render_chat_page()
        return
    
    # 사이드바
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user.username}")
        
        if st.button("🚪 로그아웃", width='stretch'):
            st.session_state.user = None
            st.session_state.portfolio = []
            st.session_state.chat_history = []
            st.session_state.chat_messages = []
            st.rerun()
        
        st.markdown("---")
        
        # AI 챗봇 버튼
        st.markdown("## 💬 AI 어드바이저")
        if st.button("🤖 AI 챗봇과 대화하기", width='stretch', type="primary"):
            st.session_state.show_chat = True
            st.rerun()
        
        st.caption("AI와 대화하며 투자 조언을 받아보세요!")
        
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
            analyze_button = st.button("📊 분석하기", type="primary", width='stretch')
        
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
                        # DB에 추가
                        st.session_state.db.add_to_portfolio(
                            st.session_state.user.id,
                            normalized['ticker'],
                            new_shares
                        )
                        # 포트폴리오 새로고침
                        st.session_state.portfolio = st.session_state.db.get_portfolio(st.session_state.user.id)
                        
                        st.success(f"✅ **{normalized['name']}** ({normalized['ticker']}) 종목이 포트폴리오에 추가되었습니다!")
                        st.rerun()
        
        if st.session_state.portfolio:
            st.markdown("### 보유 종목")
            
            korean_stocks = []
            foreign_stocks = []
            
            # DB 객체 리스트를 순회하며 국내/해외 분리
            for item in st.session_state.portfolio:
                ticker = item.ticker
                shares = item.shares
                
                stock_data = get_stock_summary(ticker, period="1d")
                if "error" not in stock_data:
                    is_korean = ticker.endswith(".KS") or ticker.endswith(".KQ")
                    currency_symbol = "₩" if is_korean else "$"
                    
                    stock_info = {
                        "종목코드": ticker,
                        "종목명": stock_data.get("name", "N/A"),
                        "보유수량": shares,
                        "현재가": stock_data.get("current_price", 0),
                        "평가금액": stock_data.get("current_price", 0) * shares,
                        "변동률": f"{stock_data.get('price_change_percent', 0):.2f}%",
                        "통화": currency_symbol
                    }
                    
                    if is_korean:
                        korean_stocks.append(stock_info)
                    else:
                        foreign_stocks.append(stock_info)
            
            # 좌우 분할: 국내 주식 (왼쪽) vs 해외 주식 (오른쪽)
            col_kr, col_us = st.columns(2)
            
            # 왼쪽: 국내 주식
            with col_kr:
                st.markdown("#### 🇰🇷 국내 주식")
                if korean_stocks:
                    df_kr = pd.DataFrame(korean_stocks)
                    display_df_kr = df_kr.drop(columns=['통화'])
                    st.dataframe(display_df_kr, width='stretch')
                    
                    total_value_kr = df_kr['평가금액'].sum()
                    st.metric("총 평가금액", f"₩{total_value_kr:,.0f}")
                    
                    # 국내 주식 시각화
                    st.markdown("##### 📊 국내 주식 비중")
                    fig_pie_kr = px.pie(df_kr, values='평가금액', names='종목명', title='')
                    st.plotly_chart(fig_pie_kr, width='stretch')
                else:
                    st.info("국내 주식이 없습니다.")
            
            # 오른쪽: 해외 주식
            with col_us:
                st.markdown("#### � 해외 주식")
                if foreign_stocks:
                    df_us = pd.DataFrame(foreign_stocks)
                    display_df_us = df_us.drop(columns=['통화'])
                    st.dataframe(display_df_us, width='stretch')
                    
                    total_value_us = df_us['평가금액'].sum()
                    st.metric("총 평가금액", f"${total_value_us:,.2f}")
                    
                    # 해외 주식 시각화
                    st.markdown("##### 📊 해외 주식 비중")
                    fig_pie_us = px.pie(df_us, values='평가금액', names='종목명', title='')
                    st.plotly_chart(fig_pie_us, width='stretch')
                else:
                    st.info("해외 주식이 없습니다.")
            
            # 포트폴리오 분석 및 관리 버튼
            st.markdown("---")
            col_kr_btn, col_us_btn = st.columns(2)
            
            # 왼쪽: 국내 주식 분석
            with col_kr_btn:
                if korean_stocks:
                    if st.button("🔍 국내 주식 위험도 분석", width='stretch', key="kr_risk"):
                        with st.spinner("국내 주식 분석 중..."):
                            kr_portfolio = [{"ticker": item.ticker, "shares": item.shares} 
                                          for item in st.session_state.portfolio 
                                          if item.ticker.endswith(".KS") or item.ticker.endswith(".KQ")]
                            analysis = get_portfolio_analysis(kr_portfolio)
                            
                            st.info(f"**국내 주식 총 평가액**: ₩{analysis['total_value']:,.0f}")
                            st.info(f"**고위험 종목 수**: {analysis['high_risk_count']}개")
                            
                            if analysis['high_risk_stocks']:
                                st.warning("⚠️ 주의가 필요한 종목")
                                for stock in analysis['high_risk_stocks']:
                                    st.markdown(f"- **{stock['name']}** (위험점수: {stock['risk_score']})")
                    
                    if st.button("� 국내 주식 1년 백테스팅", width='stretch', key="kr_backtest"):
                        with st.spinner("국내 주식 과거 데이터 분석 중..."):
                            total_initial = 0
                            total_current = 0
                            
                            for item in st.session_state.portfolio:
                                if item.ticker.endswith(".KS") or item.ticker.endswith(".KQ"):
                                    try:
                                        stock = yf.Ticker(item.ticker)
                                        hist = stock.history(period="1y")
                                        if not hist.empty:
                                            total_initial += hist['Close'].iloc[0] * item.shares
                                            total_current += hist['Close'].iloc[-1] * item.shares
                                    except:
                                        pass
                            
                            if total_initial > 0:
                                return_rate = ((total_current - total_initial) / total_initial) * 100
                                color = "green" if return_rate >= 0 else "red"
                                st.markdown(f"""
                                **📊 국내 주식 1년 수익률**
                                - 1년 전: ₩{total_initial:,.0f}
                                - 현재: ₩{total_current:,.0f}
                                - 수익률: <span style='color:{color}; font-weight: bold'>{return_rate:+.2f}%</span>
                                """, unsafe_allow_html=True)
                            else:
                                st.error("데이터 부족")
            
            # 오른쪽: 해외 주식 분석
            with col_us_btn:
                if foreign_stocks:
                    if st.button("🔍 해외 주식 위험도 분석", width='stretch', key="us_risk"):
                        with st.spinner("해외 주식 분석 중..."):
                            us_portfolio = [{"ticker": item.ticker, "shares": item.shares} 
                                          for item in st.session_state.portfolio 
                                          if not (item.ticker.endswith(".KS") or item.ticker.endswith(".KQ"))]
                            analysis = get_portfolio_analysis(us_portfolio)
                            
                            st.info(f"**해외 주식 총 평가액**: ${analysis['total_value']:,.2f}")
                            st.info(f"**고위험 종목 수**: {analysis['high_risk_count']}개")
                            
                            if analysis['high_risk_stocks']:
                                st.warning("⚠️ 주의가 필요한 종목")
                                for stock in analysis['high_risk_stocks']:
                                    st.markdown(f"- **{stock['name']}** (위험점수: {stock['risk_score']})")
                    
                    if st.button("📅 해외 주식 1년 백테스팅", width='stretch', key="us_backtest"):
                        with st.spinner("해외 주식 과거 데이터 분석 중..."):
                            total_initial = 0
                            total_current = 0
                            
                            for item in st.session_state.portfolio:
                                if not (item.ticker.endswith(".KS") or item.ticker.endswith(".KQ")):
                                    try:
                                        stock = yf.Ticker(item.ticker)
                                        hist = stock.history(period="1y")
                                        if not hist.empty:
                                            total_initial += hist['Close'].iloc[0] * item.shares
                                            total_current += hist['Close'].iloc[-1] * item.shares
                                    except:
                                        pass
                            
                            if total_initial > 0:
                                return_rate = ((total_current - total_initial) / total_initial) * 100
                                color = "green" if return_rate >= 0 else "red"
                                st.markdown(f"""
                                **📊 해외 주식 1년 수익률**
                                - 1년 전: ${total_initial:,.2f}
                                - 현재: ${total_current:,.2f}
                                - 수익률: <span style='color:{color}; font-weight: bold'>{return_rate:+.2f}%</span>
                                """, unsafe_allow_html=True)
                            else:
                                st.error("데이터 부족")
            
            # 전체 포트폴리오 관리
            st.markdown("---")
            col_rebal, col_clear = st.columns(2)
            
            with col_rebal:
                if st.button("⚖️ 리밸런싱 제안 받기", width='stretch'):
                    with st.spinner("AI가 포트폴리오를 분석 중입니다..."):
                        profile = st.session_state.user_profile
                        st.markdown(f"### 💡 {config.INVESTMENT_PROFILES[profile]['name']} 맞춤 리밸런싱")
                        
                        if profile == "conservative":
                            st.info("안정형 투자자이시군요. 변동성이 큰 기술주 비중을 줄이고, 배당주나 대형주 위주로 구성을 변경하는 것을 추천합니다.")
                        elif profile == "aggressive":
                            st.info("공격형 투자자이시군요. 현재 포트폴리오의 성장성을 더 높이기 위해 신흥 기술주 비중을 10% 정도 늘리는 것을 고려해보세요.")
                        else:
                            st.info("중립형 투자자이시군요. 현재 포트폴리오의 균형이 나쁘지 않습니다. 특정 섹터에 쏠리지 않도록 주기적으로 점검하세요.")
            
            with col_clear:
                if st.button("🗑️ 포트폴리오 초기화", width='stretch'):
                    st.session_state.db.clear_portfolio(st.session_state.user.id)
                    st.session_state.portfolio = []
                    st.rerun()
        else:
            st.info("포트폴리오가 비어있습니다. 종목을 추가해보세요!")
    
    # 탭 3: 분석 기록
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

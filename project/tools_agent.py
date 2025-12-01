# tools_agent.py - AI 에이전트 도구 사용 기능
"""
AI가 자동으로 실시간 데이터 도구를 사용할 수 있도록 하는 함수들
"""
from typing import Dict, List, Generator
import config
from tools import analyze_stock_for_chat, get_stock_news, get_stock_summary


def chat_with_tools_streaming(user_message: str, chat_history: List[Dict] = None, user_profile: str = "moderate") -> tuple:
    """
    도구를 자동으로 사용하는 AI 챗봇 (스트리밍 지원)
    
    Returns:
        (스트리밍 제너레이터, 사용된 도구 목록)
    """
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        def error_gen():
            yield "⚠️ OpenAI API 키가 설정되지 않았습니다."
        return error_gen(), []
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        # 투자 성향 정보
        profile_info = config.INVESTMENT_PROFILES.get(user_profile, config.INVESTMENT_PROFILES["moderate"])
        
        # 도구 정의
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_stock_analysis",
                    "description": "특정 종목의 실시간 주가, 뉴스, 감성 분석, 위험도 평가를 제공합니다. 사용자가 종목의 현재 가격이나 분석을 물어볼 때 반드시 사용하세요.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker_or_name": {
                                "type": "string",
                                "description": "종목명 또는 종목 코드 (예: '삼성전자', 'AAPL', '005930.KS')"
                            }
                        },
                        "required": ["ticker_or_name"]
                    }
                }
            }
        ]
        
        # LLM 초기화
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=config.OPENAI_API_KEY
        )
        
        # 시스템 프롬프트
        system_prompt = f"""당신은 Finsearcher, 전문적인 AI 투자 어드바이저입니다.

**사용자 투자 성향:** {profile_info['name']} - {profile_info['description']}

**중요 규칙:**
- 사용자가 종목의 가격, 분석, 추천 등을 물어보면 반드시 get_stock_analysis 도구를 사용하세요
- "실시간 데이터에 접근할 수 없다"고 절대 말하지 마세요. 도구를 사용하면 됩니다!
- 도구로 얻은 실제 데이터를 기반으로 구체적으로 답변하세요

답변은 친근하고 전문적으로, 이모지를 적절히 사용하세요."""
        
        # 메시지 구성
        messages = [SystemMessage(content=system_prompt)]
        
        # 이전 대화 내역 추가
        if chat_history:
            for msg in chat_history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=user_message))
        
        # 첫 번째 호출 - 도구 사용 확인
        llm_with_tools = llm.bind(tools=tools)
        response = llm_with_tools.invoke(messages)
        
        used_tools = []
        
        # 도구 호출 확인
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                used_tools.append(tool_name)
                
                # 도구 실행
                if tool_name == "get_stock_analysis":
                    tool_result = analyze_stock_for_chat(tool_args['ticker_or_name'])
                else:
                    tool_result = "도구를 찾을 수 없습니다."
                
                # 도구 결과를 메시지에 추가
                from langchain_core.messages import ToolMessage
                messages.append(response)
                messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call['id']))
            
            # 최종 응답 생성 (스트리밍)
            def response_generator():
                for chunk in llm.stream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        yield chunk.content
            
            return response_generator(), used_tools
        else:
            # 도구 없이 직접 응답 (스트리밍)
            def response_generator():
                for chunk in llm.stream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        yield chunk.content
            
            return response_generator(), used_tools
        
    except Exception as e:
        def error_gen():
            yield f"❌ 오류: {str(e)}"
        return error_gen(), []

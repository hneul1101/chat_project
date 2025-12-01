"""
간단한 테스트 스크립트
Finsearcher의 주요 기능을 테스트합니다.
"""
import sys

print("=" * 50)
print("Finsearcher 테스트 스크립트")
print("=" * 50)

# 1. 기본 임포트 테스트
print("\n[1/5] 기본 모듈 임포트 테스트...")
try:
    import config
    print("✅ config 모듈 임포트 성공")
except Exception as e:
    print(f"❌ config 모듈 임포트 실패: {e}")
    sys.exit(1)

# 2. Tools 임포트 테스트
print("\n[2/5] Tools 모듈 임포트 테스트...")
try:
    from tools import get_stock_summary, get_stock_news, get_sentiment_analysis
    print("✅ tools 모듈 임포트 성공")
except Exception as e:
    print(f"❌ tools 모듈 임포트 실패: {e}")
    print("패키지 설치가 필요합니다: pip install -r requirements.txt")
    sys.exit(1)

# 3. 주가 데이터 수집 테스트
print("\n[3/5] 주가 데이터 수집 테스트...")
try:
    ticker = "005930.KS"  # 삼성전자
    print(f"종목 코드: {ticker}")
    stock_data = get_stock_summary(ticker, period="5d")
    
    if "error" in stock_data:
        print(f"⚠️ 데이터 수집 중 오류: {stock_data['error']}")
        print("인터넷 연결을 확인하거나 다른 종목 코드를 시도해보세요.")
    else:
        print(f"✅ 주가 데이터 수집 성공")
        print(f"   종목명: {stock_data.get('name', 'N/A')}")
        print(f"   현재가: {stock_data.get('current_price', 'N/A')}")
        print(f"   변동률: {stock_data.get('price_change_percent', 'N/A')}%")
except Exception as e:
    print(f"❌ 주가 데이터 수집 실패: {e}")

# 4. 뉴스 수집 테스트
print("\n[4/5] 뉴스 수집 테스트...")
try:
    news_data = get_stock_news("삼성전자", max_results=3)
    
    if news_data and "error" not in news_data[0]:
        print(f"✅ 뉴스 수집 성공 ({len(news_data)}개)")
        for i, news in enumerate(news_data[:2], 1):
            print(f"   {i}. {news.get('title', 'N/A')[:50]}...")
    else:
        print("⚠️ 뉴스 수집 실패 또는 데이터 없음")
except Exception as e:
    print(f"❌ 뉴스 수집 실패: {e}")

# 5. 감성 분석 테스트
print("\n[5/5] 감성 분석 테스트...")
try:
    if news_data and "error" not in news_data[0]:
        sentiment = get_sentiment_analysis(news_data)
        print(f"✅ 감성 분석 성공")
        print(f"   감성: {sentiment.get('sentiment', 'N/A')}")
        print(f"   점수: {sentiment.get('score', 'N/A')}/100")
        print(f"   긍정: {sentiment.get('positive_count', 0)}개, "
              f"부정: {sentiment.get('negative_count', 0)}개, "
              f"중립: {sentiment.get('neutral_count', 0)}개")
    else:
        print("⚠️ 뉴스 데이터가 없어 감성 분석을 건너뜁니다.")
except Exception as e:
    print(f"❌ 감성 분석 실패: {e}")

# API 키 체크
print("\n" + "=" * 50)
print("환경 설정 확인")
print("=" * 50)

if config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your_openai_api_key_here":
    print("✅ OpenAI API 키가 설정되어 있습니다.")
    print("   → LLM 기반 뉴스 요약 및 투자 조언 사용 가능")
else:
    print("⚠️ OpenAI API 키가 설정되지 않았습니다.")
    print("   → 기본 기능만 사용 가능")
    print("   → .env 파일에 OPENAI_API_KEY를 설정하면 전체 기능 사용 가능")

print("\n" + "=" * 50)
print("테스트 완료!")
print("=" * 50)
print("\n애플리케이션을 실행하려면:")
print("  streamlit run app.py")
print()

"""
Utility functions for FinGenie
"""
import os
import re
import requests
from fpdf import FPDF
from datetime import datetime
import config

def remove_emojis(text):
    """
    텍스트에서 이모지 및 지원되지 않는 특수문자를 제거합니다.
    NanumGothic이 지원하지 않는 문자들을 필터링합니다.
    """
    # 기본 다국어 평면(BMP) 이외의 문자(이모지 등) 제거
    # 및 일부 특수 기호 범위 제거
    return re.sub(r'[^\u0000-\uFFFF]', '', text)

def download_font_if_missing(font_path="NanumGothic.ttf"):
    """
    한글 폰트가 없으면 다운로드합니다.
    """
    if os.path.exists(font_path):
        return True
        
    print(f"폰트 다운로드 중: {font_path}")
    try:
        # 구글 폰트 NanumGothic URL
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        response = requests.get(url)
        with open(font_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"폰트 다운로드 실패: {e}")
        return False

def generate_pdf_report(chat_history, user_profile):
    """
    대화 기록을 PDF로 생성합니다.
    """
    # 폰트 준비
    font_path = "NanumGothic.ttf"
    if not download_font_if_missing(font_path):
        return None, "폰트 다운로드에 실패했습니다."

    class PDF(FPDF):
        def header(self):
            # 로고나 헤더 텍스트
            self.set_font('NanumGothic', 'B', 15)
            self.cell(0, 10, 'FinGenie 투자 일기', 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('NanumGothic', '', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    
    # 한글 폰트 등록
    try:
        pdf.add_font('NanumGothic', '', font_path)
        pdf.add_font('NanumGothic', 'B', font_path)
    except Exception as e:
        return None, f"폰트 등록 오류: {str(e)}"

    pdf.add_page()
    
    # 1. 기본 정보
    pdf.set_font("NanumGothic", "B", 12)
    pdf.cell(0, 10, f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    
    profile_info = config.INVESTMENT_PROFILES.get(user_profile, config.INVESTMENT_PROFILES['moderate'])
    pdf.cell(0, 10, f"투자 성향: {profile_info['name']}", 0, 1)
    pdf.ln(5)
    
    # 2. 대화 내용
    pdf.set_font("NanumGothic", "B", 14)
    pdf.cell(0, 10, "대화 기록", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("NanumGothic", "", 10)
    
    for msg in chat_history:
        role = "사용자" if msg["role"] == "user" else "FinGenie"
        content = msg["content"]
        
        # 역할 표시
        pdf.set_font("NanumGothic", "B", 11)
        if role == "사용자":
            pdf.set_text_color(0, 0, 128)  # Navy
        else:
            pdf.set_text_color(0, 100, 0)  # Dark Green
            
        pdf.cell(0, 8, f"[{role}]", 0, 1)
        
        # 내용 표시
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("NanumGothic", "", 10)
        
        # 마크다운 제거 등 간단한 텍스트 정제
        clean_content = content.replace("**", "").replace("### ", "").replace("## ", "")
        # 이모지 제거
        clean_content = remove_emojis(clean_content)
        
        # 멀티라인 출력
        pdf.multi_cell(0, 6, clean_content)
        pdf.ln(5)
        
    # 파일 저장
    filename = f"investment_diary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    try:
        pdf.output(filename)
        return filename, None
    except Exception as e:
        return None, f"PDF 생성 오류: {str(e)}"

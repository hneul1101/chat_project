"""
Voice Utilities for FinGenie
Handles Text-to-Speech (TTS) and Speech-to-Text (STT) functionality.
"""
import io
import base64
import tempfile
import os
from typing import Optional, Tuple
from gtts import gTTS
import config


def text_to_speech(text: str, lang: str = "ko") -> Tuple[Optional[bytes], Optional[str]]:
    """
    텍스트를 음성으로 변환 (gTTS 사용)
    
    Args:
        text: 변환할 텍스트
        lang: 언어 코드 (기본: 한국어)
    
    Returns:
        (음성 바이트 데이터, 에러 메시지)
    """
    try:
        # 이모지 및 특수문자 제거
        import re
        clean_text = re.sub(r'[^\u0000-\uFFFF]', '', text)
        clean_text = re.sub(r'\*+', '', clean_text)  # 마크다운 별표 제거
        clean_text = re.sub(r'#+\s*', '', clean_text)  # 마크다운 헤딩 제거
        clean_text = clean_text.strip()
        
        if not clean_text:
            return None, "변환할 텍스트가 없습니다."
        
        # 텍스트가 너무 길면 잘라내기 (gTTS 제한)
        if len(clean_text) > 5000:
            clean_text = clean_text[:5000] + "... 이하 생략"
        
        # gTTS로 음성 생성
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        
        # 메모리에 저장
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return audio_buffer.read(), None
        
    except Exception as e:
        return None, f"음성 변환 중 오류: {str(e)}"


def get_audio_player_html(audio_bytes: bytes) -> str:
    """
    오디오 바이트를 HTML 오디오 플레이어로 변환
    
    Args:
        audio_bytes: 오디오 데이터
    
    Returns:
        HTML 문자열
    """
    audio_base64 = base64.b64encode(audio_bytes).decode()
    return f'''
    <audio controls autoplay>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        브라우저가 오디오를 지원하지 않습니다.
    </audio>
    '''


def speech_to_text_whisper(audio_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
    """
    OpenAI Whisper API를 사용한 음성-텍스트 변환
    
    Args:
        audio_bytes: 오디오 데이터 (wav 형식)
    
    Returns:
        (텍스트, 에러 메시지)
    """
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        return None, "OpenAI API 키가 설정되지 않았습니다."
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # 임시 파일로 저장 (Whisper API는 파일 경로 필요)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            with open(temp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ko"
                )
            
            return transcript.text, None
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return None, f"음성 인식 중 오류: {str(e)}"


def process_audio_input(audio_data: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    streamlit-mic-recorder의 오디오 데이터 처리
    
    Args:
        audio_data: {"bytes": bytes, "sample_rate": int, ...}
    
    Returns:
        (텍스트, 에러 메시지)
    """
    if not audio_data or "bytes" not in audio_data:
        return None, "오디오 데이터가 없습니다."
    
    audio_bytes = audio_data["bytes"]
    
    # Whisper API로 음성 인식
    return speech_to_text_whisper(audio_bytes)

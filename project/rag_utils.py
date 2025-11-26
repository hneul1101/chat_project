"""
RAG Utilities for FinGenie
Handles document parsing (PDF, Text) and simple retrieval.
"""
import pypdf
import io
from typing import List, Dict

def parse_pdf(file_bytes: bytes) -> str:
    """PDF 파일에서 텍스트 추출"""
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

def parse_text(file_bytes: bytes) -> str:
    """텍스트 파일에서 텍스트 추출"""
    try:
        return file_bytes.decode("utf-8")
    except Exception as e:
        return f"Error parsing text: {str(e)}"

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """텍스트를 청크로 분할"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
        
    return chunks

def simple_retrieval(query: str, chunks: List[str], top_k: int = 3) -> List[str]:
    """
    간단한 키워드 매칭 기반 검색 (임베딩 없이 구현)
    실제 프로덕션에서는 Vector DB 사용 권장
    """
    scores = []
    query_terms = query.split()
    
    for chunk in chunks:
        score = 0
        for term in query_terms:
            if term in chunk:
                score += 1
        scores.append((score, chunk))
    
    # 점수 내림차순 정렬
    scores.sort(key=lambda x: x[0], reverse=True)
    
    return [chunk for score, chunk in scores[:top_k] if score > 0]

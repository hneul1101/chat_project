"""
RAG Utilities for Finsearcher
Handles document parsing (PDF, Text), embedding-based retrieval, and document QA.
"""
import pypdf
import io
from typing import List, Dict, Optional, Tuple
import os
import config

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
    개선된 키워드 매칭 기반 검색
    - 한글/영어 형태소 고려
    - 부분 매칭 지원
    - 문장 유사도 계산
    """
    if not chunks:
        return []
    
    scores = []
    query_lower = query.lower()
    
    # 쿼리 토큰화 (공백, 조사 등 제거)
    import re
    # 한글, 영문, 숫자만 추출
    query_terms = re.findall(r'[가-힣]+|[a-zA-Z]+|[0-9]+', query_lower)
    
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = 0
        
        # 1. 정확한 쿼리 문자열 매칭 (높은 점수)
        if query_lower in chunk_lower:
            score += 10
        
        # 2. 각 토큰 매칭
        for term in query_terms:
            if len(term) < 2:  # 너무 짧은 단어 무시
                continue
            if term in chunk_lower:
                score += 3
            # 부분 매칭 (긴 단어의 경우)
            elif len(term) >= 3:
                for i in range(len(chunk_lower) - len(term) + 1):
                    if chunk_lower[i:i+len(term)] == term:
                        score += 2
                        break
        
        # 3. 문자 n-gram 유사도 (2-gram)
        def get_ngrams(text, n=2):
            return set(text[i:i+n] for i in range(len(text)-n+1))
        
        query_ngrams = get_ngrams(query_lower)
        chunk_ngrams = get_ngrams(chunk_lower[:500])  # 청크 앞부분만
        
        if query_ngrams and chunk_ngrams:
            overlap = len(query_ngrams & chunk_ngrams)
            score += overlap * 0.1
        
        scores.append((score, chunk))
    
    # 점수 내림차순 정렬
    scores.sort(key=lambda x: x[0], reverse=True)
    
    # 점수가 0보다 큰 것만 반환, 없으면 상위 청크 반환
    result = [chunk for score, chunk in scores[:top_k] if score > 0]
    
    # 매칭되는 것이 없으면 상위 청크라도 반환
    if not result and chunks:
        result = [scores[0][1]] if scores else chunks[:top_k]
    
    return result


class DocumentStore:
    """
    문서 저장소 클래스 - RAG를 위한 문서 관리
    """
    def __init__(self):
        self.documents: Dict[str, Dict] = {}  # filename -> {text, chunks}
    
    def add_document(self, filename: str, file_bytes: bytes) -> Tuple[bool, str]:
        """
        문서 추가 (PDF 또는 텍스트 파일)
        
        Args:
            filename: 파일명
            file_bytes: 파일 바이트 데이터
        
        Returns:
            (성공여부, 메시지)
        """
        try:
            # 파일 확장자에 따라 파싱
            if filename.lower().endswith('.pdf'):
                text = parse_pdf(file_bytes)
            elif filename.lower().endswith(('.txt', '.md')):
                text = parse_text(file_bytes)
            else:
                return False, "지원하지 않는 파일 형식입니다. (PDF, TXT, MD 지원)"
            
            if text.startswith("Error"):
                return False, text
            
            # 텍스트 청킹
            chunks = chunk_text(text, chunk_size=800, overlap=100)
            
            # 저장
            self.documents[filename] = {
                "text": text,
                "chunks": chunks,
                "chunk_count": len(chunks)
            }
            
            return True, f"'{filename}' 문서가 추가되었습니다. ({len(chunks)}개 청크)"
        
        except Exception as e:
            return False, f"문서 처리 중 오류: {str(e)}"
    
    def remove_document(self, filename: str) -> bool:
        """문서 제거"""
        if filename in self.documents:
            del self.documents[filename]
            return True
        return False
    
    def get_all_chunks(self) -> List[str]:
        """모든 문서의 청크 반환"""
        all_chunks = []
        for doc in self.documents.values():
            all_chunks.extend(doc["chunks"])
        return all_chunks
    
    def search(self, query: str, top_k: int = 5) -> List[str]:
        """모든 문서에서 검색"""
        all_chunks = self.get_all_chunks()
        if not all_chunks:
            return []
        return simple_retrieval(query, all_chunks, top_k)
    
    def get_document_list(self) -> List[Dict]:
        """문서 목록 반환"""
        return [
            {"filename": fname, "chunk_count": doc["chunk_count"]}
            for fname, doc in self.documents.items()
        ]
    
    def clear(self):
        """모든 문서 삭제"""
        self.documents.clear()


def answer_with_rag(query: str, document_store: DocumentStore, chat_history: List[Dict] = None) -> str:
    """
    RAG를 사용하여 문서 기반 질의응답
    
    Args:
        query: 사용자 질문
        document_store: 문서 저장소
        chat_history: 이전 대화 기록
    
    Returns:
        AI 응답
    """
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        return "⚠️ OpenAI API 키가 설정되지 않았습니다."
    
    # 관련 문서 검색
    relevant_chunks = document_store.search(query, top_k=5)
    
    # 검색 결과가 없으면 전체 문서 청크 사용 (Fallback)
    if not relevant_chunks:
        all_chunks = document_store.get_all_chunks()
        if not all_chunks:
            return "📚 업로드된 문서가 없습니다. 먼저 문서를 업로드해주세요."
        # 전체 문서의 앞부분 청크들 사용
        relevant_chunks = all_chunks[:5]
    
    # 컨텍스트 구성
    context = "\n\n---\n\n".join(relevant_chunks)
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=config.OPENAI_API_KEY
        )
        
        system_prompt = f"""당신은 투자 문서 분석 전문가입니다. 
사용자가 업로드한 문서의 내용을 기반으로 질문에 답변해주세요.

**참고 문서 내용:**
{context}

**답변 가이드라인:**
1. 반드시 제공된 문서 내용을 기반으로 답변하세요.
2. 문서에 없는 내용은 "문서에서 해당 정보를 찾을 수 없습니다"라고 답변하세요.
3. 답변은 명확하고 구체적으로 작성하세요.
4. 관련 인용구가 있다면 함께 언급하세요."""
        
        messages = [SystemMessage(content=system_prompt)]
        
        # 이전 대화 기록 추가
        if chat_history:
            for msg in chat_history[-4:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=query))
        
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        return f"❌ 오류가 발생했습니다: {str(e)}"


def summarize_document(document_store: DocumentStore, filename: str = None) -> str:
    """
    문서 요약 생성
    
    Args:
        document_store: 문서 저장소
        filename: 특정 파일명 (None이면 전체)
    
    Returns:
        요약 텍스트
    """
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        return "⚠️ OpenAI API 키가 설정되지 않았습니다."
    
    if filename:
        if filename not in document_store.documents:
            return f"'{filename}' 문서를 찾을 수 없습니다."
        text = document_store.documents[filename]["text"][:4000]  # 토큰 제한
    else:
        all_text = " ".join([doc["text"][:2000] for doc in document_store.documents.values()])
        text = all_text[:4000]
    
    if not text.strip():
        return "요약할 문서가 없습니다."
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=config.OPENAI_API_KEY
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 문서 요약 전문가입니다. 투자 관련 문서를 핵심 내용 위주로 요약해주세요."),
            ("human", f"다음 문서를 3-5개의 핵심 포인트로 요약해주세요:\n\n{text}")
        ])
        
        response = llm.invoke(prompt.format_messages())
        return response.content
        
    except Exception as e:
        return f"❌ 요약 중 오류가 발생했습니다: {str(e)}"

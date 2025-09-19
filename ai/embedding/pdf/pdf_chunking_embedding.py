import fitz  # PyMuPDF
import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from services.chromadb_service import ChromaDBService

# 환경변수 로드
load_dotenv()

class PDFChunkingService:
    def __init__(self,
                 collection_name: str = "spam_prevention_documents",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 50):
        """
        PDF 청킹 및 ChromaDB 저장 서비스 초기화

        Args:
            collection_name: ChromaDB 컬렉션 이름
            chunk_size: 텍스트 청크 크기
            chunk_overlap: 청크 간 겹치는 문자 수
        """
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # ChromaDB 서비스 초기화
        self.chroma_service = ChromaDBService(collection_name=collection_name)

        # 텍스트 분할기 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # OpenAI API 키 확인
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    def extract_text_from_pdf(self, pdf_path: str) -> List[Document]:
        """
        PDF 파일에서 텍스트 추출하여 Document 리스트로 변환

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            Document 객체 리스트
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

        documents = []

        try:
            doc = fitz.open(pdf_path)
            print(f"📄 PDF 파일 로드 완료: {pdf_path}")
            print(f"📊 총 페이지 수: {len(doc)}")

            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")

                # 빈 페이지 스킵
                if not text.strip():
                    continue

                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "page": page_num,
                            "source": pdf_path,
                            "filename": os.path.basename(pdf_path)
                        }
                    )
                )

            doc.close()
            print(f"✅ {len(documents)}개 페이지에서 텍스트 추출 완료")
            return documents

        except Exception as e:
            raise Exception(f"PDF 텍스트 추출 실패: {str(e)}")

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Document 리스트를 청크 단위로 분할

        Args:
            documents: 분할할 Document 리스트

        Returns:
            청크로 분할된 Document 리스트
        """
        try:
            splits = self.text_splitter.split_documents(documents)

            # 청크에 추가 메타데이터 부여
            for i, split in enumerate(splits):
                split.metadata["chunk_id"] = i
                split.metadata["chunk_size"] = len(split.page_content)

            print(f"📝 {len(documents)}개 문서가 {len(splits)}개 청크로 분할됨")
            return splits

        except Exception as e:
            raise Exception(f"문서 청킹 실패: {str(e)}")

    async def store_chunks_to_chromadb(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        청크들을 ChromaDB에 저장

        Args:
            chunks: 저장할 청크 리스트

        Returns:
            저장 결과 정보
        """
        try:
            # 문서 내용과 메타데이터 준비
            documents = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [str(uuid.uuid4()) for _ in chunks]

            # ChromaDB에 저장
            result = await self.chroma_service.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            print(f"💾 {len(chunks)}개 청크가 ChromaDB에 저장됨")
            return result

        except Exception as e:
            raise Exception(f"ChromaDB 저장 실패: {str(e)}")

    async def process_pdf_to_chromadb(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF 파일을 처리하여 ChromaDB에 저장하는 전체 프로세스

        Args:
            pdf_path: 처리할 PDF 파일 경로

        Returns:
            처리 결과 정보
        """
        try:
            print(f"🚀 PDF 처리 시작: {pdf_path}")

            # 1. PDF에서 텍스트 추출
            documents = self.extract_text_from_pdf(pdf_path)

            # 2. 문서 청킹
            chunks = self.chunk_documents(documents)

            # 3. ChromaDB에 저장
            store_result = await self.store_chunks_to_chromadb(chunks)

            # 4. 컬렉션 정보 조회
            collection_info = await self.chroma_service.get_collection_info()

            result = {
                "pdf_path": pdf_path,
                "total_pages": len(documents),
                "total_chunks": len(chunks),
                "collection_name": self.collection_name,
                "collection_info": collection_info,
                "store_result": store_result,
                "status": "success"
            }

            print("✅ PDF 처리 완료!")
            print(f"📊 결과 요약:")
            print(f"   - 총 페이지: {result['total_pages']}")
            print(f"   - 총 청크: {result['total_chunks']}")
            print(f"   - 컬렉션: {result['collection_name']}")

            return result

        except Exception as e:
            print(f"❌ PDF 처리 실패: {str(e)}")
            raise

    async def search_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        저장된 문서에서 검색

        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            results = await self.chroma_service.search_documents(
                query=query,
                n_results=n_results
            )

            print(f"🔍 검색 완료: '{query}'")
            print(f"📊 {len(results['documents'])}개 결과 반환")

            return results

        except Exception as e:
            raise Exception(f"문서 검색 실패: {str(e)}")

    def inspect_collection_data(self, limit: int = 5) -> Dict[str, Any]:
        """
        컬렉션에 저장된 데이터 샘플 조회

        Args:
            limit: 조회할 샘플 수

        Returns:
            저장된 데이터 샘플
        """
        try:
            if self.chroma_service.is_mock or self.chroma_service.collection is None:
                print("⚠️ Mock 모드이거나 컬렉션이 없습니다.")
                return {"message": "Mock 모드 또는 컬렉션 없음"}

            # ChromaDB에서 직접 데이터 조회
            sample_data = self.chroma_service.collection.get(
                limit=limit,
                include=["documents", "metadatas", "embeddings"]
            )

            print(f"🔍 컬렉션 '{self.collection_name}' 데이터 샘플:")
            print(f"📊 총 문서 수: {self.chroma_service.collection.count()}")
            print(f"📄 샘플 수: {len(sample_data.get('documents', []))}")

            # 샘플 데이터 출력
            if sample_data.get('documents'):
                for i, doc in enumerate(sample_data['documents'][:limit], 1):
                    print(f"\n📄 문서 {i}:")
                    print(f"ID: {sample_data['ids'][i-1]}")
                    print(f"내용 (처음 300자): {doc[:300]}...")
                    if sample_data.get('metadatas') and len(sample_data['metadatas']) >= i:
                        metadata = sample_data['metadatas'][i-1]
                        print(f"메타데이터: {metadata}")
                    print("-" * 80)

            return sample_data

        except Exception as e:
            print(f"❌ 데이터 조회 실패: {str(e)}")
            return {"error": str(e)}

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        컬렉션 상세 통계 정보

        Returns:
            컬렉션 통계
        """
        try:
            if self.chroma_service.is_mock or self.chroma_service.collection is None:
                return {"message": "Mock 모드 또는 컬렉션 없음"}

            count = self.chroma_service.collection.count()

            # 전체 데이터 조회 (메타데이터만)
            all_data = self.chroma_service.collection.get(include=["metadatas"])

            stats = {
                "collection_name": self.collection_name,
                "total_documents": count,
                "sample_metadata": all_data.get('metadatas', [])[:3] if all_data.get('metadatas') else []
            }

            # 메타데이터 분석
            if all_data.get('metadatas'):
                pages = set()
                sources = set()
                chunk_sizes = []

                for metadata in all_data['metadatas']:
                    if 'page' in metadata:
                        pages.add(metadata['page'])
                    if 'source' in metadata:
                        sources.add(metadata['source'])
                    if 'chunk_size' in metadata:
                        chunk_sizes.append(metadata['chunk_size'])

                stats.update({
                    "unique_pages": len(pages),
                    "unique_sources": len(sources),
                    "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                    "page_range": f"{min(pages)} - {max(pages)}" if pages else "N/A"
                })

            print(f"📊 컬렉션 '{self.collection_name}' 통계:")
            print(f"   - 총 문서 수: {stats['total_documents']}")
            print(f"   - 페이지 수: {stats.get('unique_pages', 'N/A')}")
            print(f"   - 페이지 범위: {stats.get('page_range', 'N/A')}")
            print(f"   - 평균 청크 크기: {stats.get('avg_chunk_size', 'N/A'):.0f}자")

            return stats

        except Exception as e:
            print(f"❌ 통계 조회 실패: {str(e)}")
            return {"error": str(e)}


class PDFCollectionManager:
    """여러 PDF 파일을 관리하는 클래스"""

    def __init__(self, base_collection_name: str = "legal_documents"):
        self.base_collection_name = base_collection_name
        self.services = {}

    def create_service_for_pdf(self, pdf_path: str,
                               collection_suffix: str = None) -> PDFChunkingService:
        """특정 PDF를 위한 서비스 생성"""
        filename = os.path.basename(pdf_path).replace('.pdf', '').replace(' ', '_')
        collection_name = f"{self.base_collection_name}_{collection_suffix or filename}"

        service = PDFChunkingService(collection_name=collection_name)
        self.services[pdf_path] = service
        return service

    async def process_multiple_pdfs(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """여러 PDF 파일을 병렬로 처리"""
        results = {}

        for pdf_path in pdf_paths:
            try:
                service = self.create_service_for_pdf(pdf_path)
                result = await service.process_pdf_to_chromadb(pdf_path)
                results[pdf_path] = result
            except Exception as e:
                results[pdf_path] = {"status": "failed", "error": str(e)}

        return results


# 사용 예시 함수들
async def main():
    """메인 실행 함수"""
    try:
        # PDF 파일 경로 설정 (여기서 경로를 수정하세요!)
        pdf_path = input("PDF 파일 경로를 입력하세요: ").strip()

        # 파일 존재 확인
        if not os.path.exists(pdf_path):
            print(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
            return

        # PDF 청킹 서비스 초기화
        service = PDFChunkingService(
            collection_name="spam_prevention_guide",
            chunk_size=1000,
            chunk_overlap=50
        )

        # PDF 처리 및 ChromaDB 저장
        result = await service.process_pdf_to_chromadb(pdf_path)

        # 검색 테스트
        print("\n🔍 검색 테스트:")
        search_query = "광고성 정보 전송시 명시사항"
        search_results = await service.search_documents(search_query, n_results=3)

        for i, doc in enumerate(search_results['documents'], 1):
            print(f"\n📄 결과 {i}:")
            print(f"내용: {doc[:200]}...")
            if i < len(search_results['metadatas']):
                metadata = search_results['metadatas'][i-1]
                print(f"메타데이터: 페이지 {metadata.get('page', 'N/A')}")

        return result

    except Exception as e:
        print(f"❌ 실행 실패: {str(e)}")
        raise


async def process_specific_pdf(pdf_path: str, collection_name: str = None):
    """특정 PDF 파일 처리 함수"""
    try:
        print(f"🚀 PDF 처리 시작: {pdf_path}")

        # 컬렉션 이름 자동 생성 (파일명 기반)
        if not collection_name:
            filename = os.path.basename(pdf_path).replace('.pdf', '').replace(' ', '_').replace('(', '').replace(')', '')
            collection_name = f"pdf_{filename}"

        # PDF 청킹 서비스 초기화
        service = PDFChunkingService(
            collection_name=collection_name,
            chunk_size=1000,
            chunk_overlap=50
        )

        # PDF 처리 및 ChromaDB 저장
        result = await service.process_pdf_to_chromadb(pdf_path)
        print(f"✅ 처리 완료! 컬렉션 이름: {collection_name}")

        return service, result

    except Exception as e:
        print(f"❌ PDF 처리 실패: {str(e)}")
        raise


async def batch_process_pdfs():
    """여러 PDF 파일 일괄 처리 예시"""
    # 여기에 처리하고 싶은 PDF 파일들의 경로를 입력하세요
    pdf_paths = [
        # 예시:
        # "./documents/spam_prevention_guide.pdf",
        # "./documents/privacy_policy.pdf",
        # "./documents/terms_of_service.pdf",
    ]

    # 사용자로부터 PDF 경로들 입력받기
    print("처리할 PDF 파일 경로들을 입력하세요 (빈 줄 입력시 종료):")
    while True:
        path = input("PDF 경로: ").strip()
        if not path:
            break
        if os.path.exists(path):
            pdf_paths.append(path)
            print(f"✅ 추가됨: {path}")
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {path}")

    if not pdf_paths:
        print("처리할 PDF 파일이 없습니다.")
        return

    manager = PDFCollectionManager("legal_docs")
    results = await manager.process_multiple_pdfs(pdf_paths)

    print("\n📊 일괄 처리 결과:")
    for pdf_path, result in results.items():
        status = result.get('status', 'unknown')
        print(f"📁 {os.path.basename(pdf_path)}: {status}")
        if status == "success":
            print(f"   - 청크 수: {result.get('total_chunks', 0)}")
            print(f"   - 컬렉션: {result.get('collection_name', 'N/A')}")


# 직접 실행용 함수
async def quick_process():
    """빠른 처리를 위한 함수 - 여기서 직접 경로 지정"""
    # 🔽 여기에 직접 PDF 파일 경로를 입력하세요! 🔽
    pdf_path = "./your_pdf_file.pdf"  # 이 부분을 실제 PDF 경로로 변경하세요

    # 파일 존재 확인
    if not os.path.exists(pdf_path):
        print(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
        print("🔧 pdf_path 변수에 올바른 PDF 파일 경로를 입력해주세요.")
        return

    service, result = await process_specific_pdf(pdf_path, "my_document_collection")

    # 데이터 저장 상태 확인
    print("\n🔍 저장된 데이터 확인:")
    sample_data = service.inspect_collection_data(limit=3)

    # 컬렉션 통계 확인
    print("\n📊 컬렉션 통계:")
    stats = service.get_collection_stats()

    # 검색 테스트
    while True:
        query = input("\n🔍 검색할 내용을 입력하세요 (종료: quit): ").strip()
        if query.lower() in ['quit', 'exit', '종료']:
            break

        if query:
            search_results = await service.search_documents(query, n_results=3)
            for i, doc in enumerate(search_results['documents'], 1):
                print(f"\n📄 결과 {i}:")
                print(f"내용: {doc[:300]}...")
                if i <= len(search_results['metadatas']):
                    metadata = search_results['metadatas'][i-1]
                    print(f"📍 페이지: {metadata.get('page', 'N/A')}, 파일: {metadata.get('filename', 'N/A')}")


async def inspect_existing_collection(collection_name: str):
    """기존 컬렉션 데이터 확인용 함수"""
    try:
        print(f"🔍 컬렉션 '{collection_name}' 데이터 확인 중...")

        # 서비스 초기화 (기존 컬렉션 연결)
        service = PDFChunkingService(collection_name=collection_name)

        # 컬렉션 통계
        stats = service.get_collection_stats()

        # 샘플 데이터 조회
        sample_data = service.inspect_collection_data(limit=5)

        # 검색 테스트
        while True:
            query = input(f"\n🔍 '{collection_name}'에서 검색 (종료: quit): ").strip()
            if query.lower() in ['quit', 'exit', '종료']:
                break

            if query:
                search_results = await service.search_documents(query, n_results=3)
                for i, doc in enumerate(search_results['documents'], 1):
                    print(f"\n📄 결과 {i}:")
                    print(f"내용: {doc[:200]}...")
                    if i <= len(search_results['metadatas']):
                        metadata = search_results['metadatas'][i-1]
                        print(f"📍 페이지: {metadata.get('page', 'N/A')}")

    except Exception as e:
        print(f"❌ 컬렉션 확인 실패: {str(e)}")


if __name__ == "__main__":
    print("🚀 PDF ChromaDB 처리 시스템")
    print("1. quick_process() - 코드에서 직접 경로 지정")
    print("2. main() - 실행시 경로 입력")
    print("3. batch_process_pdfs() - 여러 파일 일괄 처리")
    print("4. inspect_existing_collection() - 기존 컬렉션 데이터 확인")

    # 🔽 원하는 함수를 선택해서 실행하세요 🔽

    # 방법 1: 코드에서 직접 경로 지정 (권장)
    # asyncio.run(quick_process())

    # 방법 2: 실행시 경로 입력
    # asyncio.run(main())

    # 방법 3: 여러 파일 일괄 처리
    # asyncio.run(batch_process_pdfs())

    # 방법 4: 기존 컬렉션 데이터 확인
    asyncio.run(inspect_existing_collection("spam_prevention_documents"))
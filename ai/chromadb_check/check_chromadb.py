#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB 컬렉션 및 데이터 확인 스크립트
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 상위 디렉토리를 경로에 추가하여 모듈 import 가능하게 함
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    print("❌ ChromaDB 패키지가 설치되지 않았습니다.")
    print("설치 명령: pip install chromadb")
    sys.exit(1)

# .env 파일 로드
load_dotenv()

def get_chromadb_client():
    """ChromaDB 클라이언트 생성"""
    chroma_host = os.getenv('CHROMA_HOST')
    chroma_port = os.getenv('CHROMA_PORT')
    
    if chroma_host and chroma_port:
        try:
            client = chromadb.HttpClient(
                host=chroma_host, 
                port=int(chroma_port), 
                settings=Settings(anonymized_telemetry=False)
            )
            client.heartbeat()
            print(f"✅ ChromaDB HTTP 연결 성공: {chroma_host}:{chroma_port}")
            return client
        except Exception as e:
            print(f"❌ ChromaDB HTTP 연결 실패: {e}")
            return None
    else:
        persist_dir = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')
        try:
            client = chromadb.PersistentClient(path=persist_dir)
            print(f"✅ 로컬 ChromaDB 연결 성공: {persist_dir}")
            return client
        except Exception as e:
            print(f"❌ 로컬 ChromaDB 연결 실패: {e}")
            return None

def print_collection_info(collection, collection_name):
    """컬렉션 정보 출력"""
    try:
        count = collection.count()
        print(f"\n{'='*80}")
        print(f"컬렉션 이름: {collection_name}")
        print(f"데이터 개수: {count}")
        print(f"{'='*80}")
        
        if count == 0:
            print("⚠️  이 컬렉션에는 데이터가 없습니다.")
            return
        
        # 모든 데이터 가져오기
        results = collection.get(include=['documents', 'metadatas'])
        
        ids = results.get('ids', [])
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        for idx, (doc_id, doc, metadata) in enumerate(zip(ids, documents, metadatas), 1):
            print(f"\n[항목 {idx}]")
            print(f"  ID: {doc_id}")
            print(f"  문서 내용:")
            # 문서 내용이 길면 일부만 표시
            doc_preview = doc[:200] + "..." if len(doc) > 200 else doc
            print(f"    {doc_preview}")
            print(f"  메타데이터:")
            if metadata:
                for key, value in metadata.items():
                    print(f"    {key}: {value}")
            else:
                print("    (메타데이터 없음)")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ 컬렉션 '{collection_name}' 정보 조회 중 오류: {e}")

def main():
    """메인 함수"""
    print("="*80)
    print("ChromaDB 컬렉션 및 데이터 확인")
    print("="*80)
    
    # ChromaDB 클라이언트 연결
    client = get_chromadb_client()
    if not client:
        print("❌ ChromaDB 연결에 실패했습니다.")
        sys.exit(1)
    
    try:
        # 모든 컬렉션 목록 가져오기
        existing_collections = client.list_collections()
        
        # 예상되는 컬렉션 목록 (chromadb_service.py에서 정의된 컬렉션들)
        expected_collections = [
            "approved_templates",
            "public_templates",
            "denied_templates",
            "blacklist",
            "rejection_reasons",
        ]
        
        if not existing_collections:
            print("\n⚠️  ChromaDB에 컬렉션이 없습니다.")
            print("\n📋 예상되는 컬렉션 목록:")
            for col_name in expected_collections:
                print(f"  - {col_name} (생성되지 않음)")
            
            print("\n💡 참고: 컬렉션은 서비스가 처음 실행될 때 자동으로 생성됩니다.")
            print("   또는 아래 명령으로 컬렉션을 확인할 수 있습니다:")
            print("   - get_or_create_collection()을 사용하여 컬렉션 생성")
            return
        
        print(f"\n📋 총 {len(existing_collections)}개의 컬렉션을 찾았습니다:")
        existing_collection_names = [col.name for col in existing_collections]
        for col in existing_collections:
            print(f"  - {col.name}")
        
        # 예상되지만 존재하지 않는 컬렉션 확인
        missing_collections = set(expected_collections) - set(existing_collection_names)
        if missing_collections:
            print(f"\n⚠️  예상되지만 존재하지 않는 컬렉션:")
            for col_name in missing_collections:
                print(f"  - {col_name}")
        
        # 각 컬렉션의 데이터 출력
        for collection_info in existing_collections:
            collection_name = collection_info.name
            collection = client.get_collection(collection_name)
            print_collection_info(collection, collection_name)
        
        print(f"\n{'='*80}")
        print("✅ 확인 완료")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
approved.jsonl 파일의 데이터를 로컬 ChromaDB에 임베딩하는 스크립트
- 기존 'approved_templates' 컬렉션 데이터 삭제
- approved.jsonl 파일에서 새로운 데이터 추가
"""

import os
import sys
import json
import uuid
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    print("❌ ChromaDB 패키지가 설치되지 않았습니다.")
    print("설치 방법: pip install chromadb")
    sys.exit(1)

from dotenv import load_dotenv

# --- 스크립트 설정 ---
COLLECTION_NAME = "approved_templates"
DATA_FILE = "embedding/approved_fixed.jsonl"
# --------------------

# 환경 변수 로드
load_dotenv()

def get_chromadb_client():
    """무조건 로컬 ChromaDB 클라이언트 생성"""
    persist_dir = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')
    print(f"💾 로컬 ChromaDB에 연결: {persist_dir}")

    # 디렉토리가 없으면 생성
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False)
    )
    return client, persist_dir

def print_separator(title: str):
    """구분선 출력"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def load_approved_data(file_path: str):
    """approved.json 배열 파일에서 데이터 로드"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)  # 전체 배열 읽기
        print(f"✅ '{file_path}' 파일에서 {len(data)}개의 데이터를 성공적으로 로드했습니다.")
        return data
    except FileNotFoundError:
        print(f"❌ 오류: '{file_path}' 파일을 찾을 수 없습니다.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 오류: '{file_path}' 파일의 JSON 형식이 잘못되었습니다. (오류: {e})")
        sys.exit(1)

def clear_collection(client, collection_name: str):
    """지정된 컬렉션의 모든 데이터 삭제"""
    try:
        client.delete_collection(name=collection_name)
        print(f"✅ 기존 '{collection_name}' 컬렉션이 삭제되었습니다.")
    except Exception as e:
        if "does not exist" in str(e).lower():
            print(f"ℹ️  기존 '{collection_name}' 컬렉션이 존재하지 않습니다. 새로 생성합니다.")
        else:
            print(f"⚠️  기존 컬렉션 삭제 중 예상치 못한 오류 발생: {e}")
    return True

def embed_data(client, collection_name: str, data: list):
    """데이터를 ChromaDB 컬렉션에 임베딩"""
    try:
        collection = client.get_or_create_collection(name=collection_name)

        documents = []
        metadatas = []
        ids = []

        for item in data:
            documents.append(item["document"])

            metadata = item.get("metadata", {})
            metadata["type"] = "approved_template"
            metadata["source"] = DATA_FILE
            metadatas.append(metadata)

            template_id = f"approved_{item['id']}_{uuid.uuid4().hex[:8]}"
            ids.append(template_id)

        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            print(f"  - {i + len(batch_ids)} / {len(documents)}개 데이터 추가 완료...")

        print(f"\n✅ {len(data)}개의 템플릿이 '{collection_name}' 컬렉션에 추가되었습니다.")
        return True

    except Exception as e:
        print(f"❌ 데이터 추가 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_data(client, collection_name: str):
    """임베딩된 데이터 검증"""
    try:
        collection = client.get_collection(name=collection_name)
        count = collection.count()

        print(f"📊 '{collection_name}' 컬렉션 검증:")
        print(f"   - 총 문서 수: {count}")

        if count == 0:
            print("   - 데이터가 없어 카테고리별 분포를 확인할 수 없습니다.")
            return True

        results = collection.get()
        categories = {}

        if results.get('metadatas'):
            for metadata in results['metadatas']:
                category = metadata.get('분류 1차', 'Unknown')
                categories[category] = categories.get(category, 0) + 1

        print(f"   - '분류 1차' 기준 분포:")
        for category, num in sorted(categories.items()):
            print(f"     * {category}: {num}개")

        return True

    except Exception as e:
        print(f"❌ 데이터 검증 실패: {e}")
        return False

def main():
    """메인 함수"""
    print_separator(f"'{COLLECTION_NAME}' 컬렉션 업데이트 스크립트")

    try:
        client, db_location = get_chromadb_client()
        print(f"📍 데이터베이스 위치: {db_location}")

        data_to_embed = load_approved_data(DATA_FILE)
        if not data_to_embed:
            print("❌ 임베딩할 데이터가 없습니다. 스크립트를 종료합니다.")
            return

        print(f"\n⚠️  이 작업은 기존 '{COLLECTION_NAME}' 컬렉션의 모든 데이터를 삭제하고")
        print(f"   '{DATA_FILE}' 파일의 내용으로 새롭게 데이터를 추가합니다.")
        confirm = input("계속하시겠습니까? (y/N): ").strip().lower()

        if confirm not in ['y', 'yes']:
            print("❌ 작업이 취소되었습니다.")
            return

        print_separator(f"1단계: 기존 '{COLLECTION_NAME}' 컬렉션 데이터 삭제")
        if not clear_collection(client, COLLECTION_NAME):
            return

        print_separator(f"2단계: '{DATA_FILE}' 데이터 추가")
        if not embed_data(client, COLLECTION_NAME, data_to_embed):
            return

        print_separator("3단계: 데이터 검증")
        if not verify_data(client, COLLECTION_NAME):
            return

        print_separator("✨ 작업 완료 ✨")
        print(f"✅ '{COLLECTION_NAME}' 컬렉션이 성공적으로 업데이트되었습니다!")

    except Exception as e:
        print(f"\n❌ 스크립트 실행 중 심각한 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

# 이 파일이 직접 실행된 경우에만 아래 코드를 실행하라
# 파일이 import 될 때는 실행되지 않게 막아주는 안전장치
if __name__ == "__main__":
    main()
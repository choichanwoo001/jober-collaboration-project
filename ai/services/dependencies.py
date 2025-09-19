# services/dependencies.py

from .openai_service import OpenAIService
from .chromadb_service import ChromaDBService
import logging

logger = logging.getLogger(__name__)

# --- 서비스 초기화 (싱글턴 인스턴스) ---
# FastAPI 앱이 시작될 때 딱 한 번만 실행됩니다.
logger.info("싱글턴 서비스 인스턴스 초기화 시작...")
try:
    openai_service_instance = OpenAIService()
    logger.info("✅ OpenAI 서비스 인스턴스 생성 완료")
except Exception as e:
    logger.error(f"❌ OpenAI 서비스 인스턴스 생성 실패: {e}")
    openai_service_instance = None

try:
    chromadb_service_instance = ChromaDBService()
    logger.info("✅ ChromaDB 서비스 인스턴스 생성 완료")
except Exception as e:
    logger.error(f"❌ ChromaDB 서비스 인스턴스 생성 실패: {e}")
    chromadb_service_instance = None

logger.info("싱글턴 서비스 인스턴스 초기화 완료!")

# --- 의존성 주입 함수 ---
def get_openai_service() -> OpenAIService:
    if openai_service_instance is None:
        raise RuntimeError("OpenAI 서비스가 초기화되지 않았습니다.")
    return openai_service_instance

def get_chromadb_service() -> ChromaDBService:
    if chromadb_service_instance is None:
        raise RuntimeError("ChromaDB 서비스가 초기화되지 않았습니다.")
    return chromadb_service_instance

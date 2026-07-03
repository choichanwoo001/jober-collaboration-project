import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    # MySQL 데이터베이스 설정 (환경변수에서 가져오기)
    DB_URL: str = os.getenv("DB_URL", "jdbc:mysql://localhost:3306/final_project?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Seoul")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # 애플리케이션 설정
    APP_NAME: str = "AlimTalk Template Generator"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # OpenAI 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ChromaDB 설정 (환경변수에서 가져오기)
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: str = os.getenv("CHROMA_PORT", "8001")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # Celery 설정
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://:1234@localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://:1234@localhost:6379/0")


    # 카테고리 관련 설정
    CATEGORY_CONFIDENCE_THRESHOLD: int = 70
    AUTO_CREATE_CATEGORIES: bool = True
    MAX_CATEGORY_NAME_LENGTH: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra="ignore"

# 전역 설정 인스턴스
settings = Settings()

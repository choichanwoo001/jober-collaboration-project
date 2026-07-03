from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from celery import Celery
from core.config import settings

# Celery 애플리케이션 인스턴스 생성
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["services.openai_service", "api.routes.template_routes"]  # tasks가 포함된 모듈
)

# Celery 설정을 업데이트합니다.
celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    # 필요에 따라 다른 Celery 설정을 여기에 추가할 수 있습니다.
)

# OpenAI API 속도 제한에 맞춰 task 속도 제한 설정 (예: 분당 480개)
# 이 설정은 task 별로도 적용할 수 있습니다.
# celery_app.conf.task_routes = {
#     'ai.services.openai_service.*': {'rate_limit': '480/m'},
# }

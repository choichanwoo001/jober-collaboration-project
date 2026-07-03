# api/routes/template_routes.py
import asyncio
import json
import logging
from typing import List, Dict

import os
import redis
import redis.asyncio as redis_async
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAIError

from celery_app import celery_app
from services.dependencies import get_openai_service, get_chromadb_service
from services.openai_service import OpenAIService
from services.chromadb_service import ChromaDBService
from templateEngine.pipeline import run_template_generation_pipeline
from core.database import get_db, SessionLocal
from templateEngine.prompts.message_analyzer_prompts import PromptDefense
from templateEngine.prompts.builders import SuitabilityCheckPromptBuilder
from core.config import settings

router = APIRouter(prefix="/template", tags=["Template Generation"])
logger = logging.getLogger(__name__)


# --- Pydantic 모델 ---
class GenerationRequest(BaseModel):
    userMessage: str


class GenerationResponse(BaseModel):
    template_content: str
    variables: List[Dict[str, str]]
    category: str
    model: str
    template_title: str
    generation_method: str
    similarity_score: float

class GenerationTaskResponse(BaseModel):
    task_id: str
    message: str


# --- Celery 작업 ---
async def _run_full_pipeline(user_message: str, db_session: Session) -> dict:
    """
    LangGraph 기반의 지능형 템플릿 생성 파이프라인을 실행합니다.
    MOCK_OPENAI=1 이면 OpenAI 호출 없이 더미 응답 반환 (k6 등 부하 테스트용).
    """
    # k6/부하 테스트 시 API 한도 소진 방지: mock 모드면 즉시 더미 200 반환
    if os.getenv("MOCK_OPENAI", "").lower() in ("1", "true", "yes"):
        return GenerationResponse(
            template_content="[MOCK] 부하 테스트용 더미 템플릿입니다.",
            variables=[{"name": "고객명", "type": "string", "description": "변수: 고객명"}],
            category="기타",
            model="gpt-4o-mini",
            template_title="[MOCK] 테스트 제목",
            generation_method="mock",
            similarity_score=0.0,
        )
    
    openai_service = OpenAIService()
    chromadb_service = ChromaDBService()
    
    from openai import AsyncOpenAI
    from core.config import settings
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        # Part 1: Suitability Check
        suitability_builder = SuitabilityCheckPromptBuilder(user_message)
        suitability_messages = suitability_builder.build()

        async def _direct_chat_completion(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.2,
            )
            return response.choices[0].message.content

        suitability_result = await _direct_chat_completion(suitability_messages)

        try:
            suitability_data = json.loads(suitability_result)
            if not suitability_data.get("is_suitable", True):
                reason = suitability_data.get("reason", "메시지가 알림톡 템플릿 생성에 적합하지 않습니다.")
                if "욕설" in reason or "부적절한 언어" in reason:
                    user_message_detail = "입력하신 내용에 부적절한 표현이 포함되어 있습니다. 다시 작성해 주세요."
                elif "무관한 내용" in reason:
                    user_message_detail = "알림톡 템플릿과 관련 없는 내용입니다. 서비스 안내나 고객 소통 관련 내용으로 다시 작성해 주세요."
                else:
                    user_message_detail = "입력하신 내용을 알림톡 템플릿으로 생성할 수 없습니다. 다시 작성해 주세요."
                return {"pipeline_success": False, "error_message": user_message_detail}
        except json.JSONDecodeError:
            logger.warning(f"Suitability check response parsing failed: {suitability_result}")

        # Part 2: Main Generation Pipeline
        return await run_template_generation_pipeline(
            userMessage=user_message,
            openai_service=openai_service,
            chromadb_service=chromadb_service,
            db_session=db_session
        )
    except OpenAIError:
        # OpenAI 관련 에러(429 Rate Limit 등)는 재시도를 위해 상위로 전파
        raise
    except Exception as e:
        logger.error(f"Error during suitability check or pipeline: {e}", exc_info=True)
        return {"pipeline_success": False, "error_message": "템플릿 생성 중 오류가 발생했습니다."}
    finally:
        await client.close()


@celery_app.task(bind=True, autoretry_for=(OpenAIError,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def run_pipeline_task(self, user_message: str) -> dict:
    """Celery task to run suitability check and then the template generation pipeline."""
    db_session = SessionLocal()
    try:
        # Since _run_full_pipeline is async, run it in a new event loop
        result = asyncio.run(_run_full_pipeline(user_message, db_session))

        # [Redis Pub/Sub] 작업 완료 시 결과 발행 (Publish)
        # config의 설정을 사용하여 Redis 연결
        try:
            with redis.from_url(settings.CELERY_BROKER_URL) as r:
                r.publish(f"task_result:{self.request.id}", json.dumps(result, default=str))
        except Exception as e:
            logger.error(f"Redis publish failed for task {self.request.id}: {e}")

        return result
    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {e}", exc_info=True)
        # Re-raise the exception to mark the task as FAILED in Celery
        raise
    finally:
        db_session.close()


# --- API 엔드포인트 ---
@router.post("/generate", response_model=GenerationTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_template_endpoint(
        request: GenerationRequest,
):
    """
    Accepts a user message and queues the template generation task.
    Returns a task ID for polling the result.
    """
    try:
        sanitize_userMessage = PromptDefense.sanitize_user_input(request.userMessage)

        # Queue the combined task for background processing
        task = run_pipeline_task.delay(user_message=sanitize_userMessage)

        return GenerationTaskResponse(task_id=task.id, message="Template generation has been queued.")

    except Exception as e:
        logger.error(f"Error in /generate endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="템플릿 생성 요청 중 오류가 발생했습니다.")


@router.get("/generate/stream", summary="SSE Template Generation (Redis Pub/Sub)")
async def generate_template_stream(
    userMessage: str = Query(..., description="사용자 요청 메시지")
):
    """
    Redis Pub/Sub을 활용한 이벤트 기반 SSE 스트리밍.
    서버 리소스를 점유하는 폴링 없이, Celery 작업 완료 신호를 즉시 받아 응답합니다.
    """
    async def event_stream():
        redis_client = None
        pubsub = None
        try:
            # 1. Celery 작업 등록
            sanitize_userMessage = PromptDefense.sanitize_user_input(userMessage)
            task = run_pipeline_task.delay(user_message=sanitize_userMessage)

            # 2. Redis 채널 구독 (Subscribe)
            # config의 설정을 사용하여 Redis 연결
            redis_client = redis_async.from_url(settings.CELERY_BROKER_URL)
            pubsub = redis_client.pubsub()
            channel_name = f"task_result:{task.id}"
            await pubsub.subscribe(channel_name)

            # 대기 시작 알림
            yield f"data: {json.dumps({'status': 'QUEUED', 'task_id': task.id})}\n\n"

            # 3. 메시지 대기 (이벤트 루프를 차단하지 않음)
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data_str = message['data']
                    if isinstance(data_str, bytes):
                        data_str = data_str.decode('utf-8')

                    result_data = json.loads(data_str)

                    if not result_data.get("pipeline_success", False):
                        error_msg = result_data.get("error_message", "생성 실패")
                        yield f"data: {json.dumps({'status': 'FAILURE', 'error': error_msg}, ensure_ascii=False)}\n\n"
                    else:
                        response_data = {
                            "status": "SUCCESS",
                            "template_content": result_data.get("template_text", ""),
                            "variables": [
                                {"name": var, "type": "string", "description": f"변수: {var}"}
                                for var in result_data.get("variables", [])
                            ],
                            "category": result_data.get("category_sub") or "기타",
                            "model": "gpt-4o-mini",
                            "template_title": result_data.get("template_title", ""),
                            "generation_method": result_data.get("generation_method", ""),
                            "similarity_score": result_data.get("similarity_score", 0.0)
                        }
                        yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
                    break  # 결과 전송 후 루프 종료

        except Exception as e:
            logger.error(f"SSE Error: {e}", exc_info=True)
            yield f"data: {json.dumps({'status': 'ERROR', 'error': str(e)})}\n\n"
        finally:
            if pubsub: await pubsub.unsubscribe()
            if redis_client: await redis_client.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/generate/task/{task_id}", tags=["Template Generation Status"])
async def get_generation_task_status(
        task_id: str,
        openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Polls for the result of a template generation task.
    """
    task_result = await openai_service.get_task_result(task_id)

    if task_result["status"] == "FAILURE":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"템플릿 생성에 실패했습니다: {task_result['result']}")

    if task_result["status"] != "SUCCESS":
        return task_result  # Return current status (e.g., PENDING, STARTED)

    # Task succeeded, process the result
    result_data = task_result["result"]
    if not result_data or not result_data.get("pipeline_success", False):
        error_message = result_data.get("error_message", "알 수 없는 오류로 템플릿 생성에 실패했습니다.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    # Format the successful result into the final response model
    response_data = {
        "template_content": result_data.get("template_text", ""),
        "variables": [
            {"name": var, "type": "string", "description": f"변수: {var}"}
            for var in result_data.get("variables", [])
        ],
        "category": result_data.get("category_sub") or "기타",
        "model": "gpt-4o-mini",
        "template_title": result_data.get("template_title", ""),
        "generation_method": result_data.get("generation_method", ""),
        "similarity_score": result_data.get("similarity_score", 0.0)
    }

    return GenerationResponse(**response_data)

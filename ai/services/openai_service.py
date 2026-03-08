import os
import asyncio
from typing import List, Dict

from celery.result import AsyncResult, allow_join_result
from openai import AsyncOpenAI, OpenAIError

from celery_app import celery_app
from core.config import settings


@celery_app.task(bind=True, rate_limit='480/m')
def chat_completion_task(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
    """
    OpenAI 채팅 완성 API를 호출하는 Celery 작업
    """
    async def _main():
        # Celery 작업 내에서 클라이언트 인스턴스화
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.2
            )
            return response.choices[0].message.content

        except OpenAIError as e:
            # 재시도 로직을 위해 예외를 다시 발생시킬 수 있습니다.
            # self.retry(exc=e, countdown=int(e.retry_after) if e.retry_after else 5)
            # 현재는 그대로 예외를 발생시켜 실패 상태로 만듭니다.
            raise e
        except Exception as e:
            raise RuntimeError("Unexpected error in OpenAI task") from e
        finally:
            await client.close()
    return asyncio.run(_main())


class OpenAIService:
    def __init__(self):
        # Celery 작업으로 분리되었으므로, 서비스 클래스에서 더 이상 OpenAI 클라이언트를 직접 관리할 필요가 없습니다.
        # self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pass

    def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
        """
        OpenAI 채팅 완성 작업을 큐에 넣고 작업 ID를 반환합니다.
        """
        task = chat_completion_task.delay(messages=messages, model=model)
        return task.id

    async def chat_completion_blocking(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
        """
        [수정] OpenAI 채팅 완성 작업을 직접 비동기로 수행합니다.
        
        Celery Task 내부에서 또 다른 Task를 기다릴 경우(Nested Task),
        워커 풀이 고갈되면 데드락(Deadlock)이 발생하여 타임아웃이 일어납니다.
        따라서 Celery를 거치지 않고 직접 API를 호출하여 데드락을 방지합니다.
        """
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.2,
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            raise RuntimeError(f"OpenAI API Error: {e}") from e
        finally:
            await client.close()


    async def get_task_result(self, task_id: str) -> dict:
        """
        주어진 작업 ID의 상태와 결과를 확인합니다.
        """
        task_result = AsyncResult(task_id, app=celery_app)
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None
        }
        if task_result.failed():
            # 실패한 경우, 에러 정보를 결과에 추가
            response['result'] = str(task_result.info)
        return response

    def generate_response(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        프롬프트를 받아서 OpenAI 응답 생성 작업을 큐에 넣고 작업 ID를 반환합니다.
        """
        messages = [
            {"role": "system", "content": "알림톡 템플릿 검증 전문가입니다."},
            {"role": "user", "content": prompt}
        ]
        return self.chat_completion(messages, model)

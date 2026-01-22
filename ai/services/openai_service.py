import os
from typing import List, Dict
from openai import AsyncOpenAI, OpenAIError


class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
        """
        OpenAI 채팅 완성 API 호출
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=1000,
                temperature=0.2
            )
            return response.choices[0].message.content

        # OpenAI SDK에서 던진 예외는 타입/정보 유지
        except OpenAIError:
            raise

        # 나머지는 "진짜 내부 오류"로만 감싸기 (원인 연결)
        except Exception as e:
            raise RuntimeError("Unexpected error in OpenAI service") from e

    async def generate_response(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        프롬프트를 받아서 OpenAI 응답을 생성하는 편의 메서드
        """
        messages = [
            {"role": "system", "content": "알림톡 템플릿 검증 전문가입니다."},
            {"role": "user", "content": prompt}
        ]
        return await self.chat_completion(messages, model)

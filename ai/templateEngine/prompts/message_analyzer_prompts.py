"""
템플릿 수정용 프롬프트 빌더
"""
from abc import ABC, abstractmethod

class BasePromptBuilder(ABC):
    def __init__(self, user_text: str):
        self.user_text = user_text
        self.hints: list[dict] = []

    def add_hint(self, description: str, content: str):
        """모든 힌트는 system role"""
        self.hints.append({"description": description, "content": content})
        return self

    def _build_hint_messages(self) -> list[dict]:
        return [
            {
                "role": "system",
                "content": h["content"]  # 문자열 그대로 넣음
            }
            for h in self.hints
        ]

    @abstractmethod
    def build(self) -> list[str]:
        """프롬프트 빌드 로직은 구체 빌더가 구현"""
        pass


class TemplateModificationPromptBuilder:
    def __init__(self, current_template: str, user_message: str, chat_context: str = ""):
        self.current_template = current_template
        self.user_message = user_message
        self.chat_context = chat_context

    def build(self) -> str:
        """템플릿 수정 프롬프트 생성"""
        return f"""
        현재 알림톡 템플릿:
        {self.current_template}

        채팅 히스토리:
        {self.chat_context}

        사용자 요청: {self.user_message}

        위 정보를 바탕으로 사용자의 요청에 따라 템플릿을 수정해주세요.

        중요한 규칙:
        1. 기존 템플릿의 구조와 변수는 유지하면서 요청사항을 반영
        2. 변수(#{{변수명}}) 형태는 그대로 유지
        3. 수정된 템플릿만 반환하세요
        4. 설명, 해설, 변경사항 설명 등은 절대 포함하지 마세요
        5. "수정된 템플릿:", "설명:", "변경사항:" 등의 헤더도 사용하지 마세요

        응답 형식:
        수정된 템플릿:
        [수정된 템플릿 내용만 여기에 작성]

        예시:
        수정된 템플릿:
        안녕하세요! #{{고객명}}님, 주문이 완료되었습니다. 감사합니다.
        """
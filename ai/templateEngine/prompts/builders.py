from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
from graph.state.alimtalk_graph import TemplateGenerationState

class BasePromptBuilder(ABC):
    """기본 프롬프트 빌더"""
    def __init__(self, user_text: str):
        self.user_text = user_text
        self.hints: List[Dict] = []

    def add_hint(self, description: str, content: str):
        self.hints.append({"description": description, "content": content})
        return self

    def _build_hint_messages(self) -> List[Dict]:
        return [{"role": "system", "content": h["content"]} for h in self.hints]

    @abstractmethod
    def build(self) -> List[Dict]:
        pass

class FieldsPromptBuilder(BasePromptBuilder):
    """메시지에서 변수로 처리할 필드를 추출하는 프롬프트 빌더"""
    def build(self) -> List[Dict]:
        # 👇 오늘 날짜를 YYYY-MM-DD 형식으로 가져옵니다.

        today_str = datetime.now().strftime('%Y-%m-%d')
        system_prompt = """
당신은 텍스트에서 변수를 추출하고 정제하는 '데이터 엔지니어'입니다.
주어진 본문과 오늘 날짜를 참고하여, 고객별로 달라지는 정보를 찾아, 아래 규칙에 따라 변수로 추출하세요.

**오늘 날짜: {today_str}**

**변수 추출 및 정제 규칙:**
1.  **날짜 추론:** '오늘', '내일', '모레'와 같은 상대적인 날짜 표현이 나오면, **오늘 날짜({today_str})를 기준**으로 실제 날짜(YYYY-MM-DD)를 계산하여 값으로 사용해야 합니다.
    - 예: 오늘이 2024-01-15이고 본문에 '내일'이 있으면, 값은 '2024-01-16'이 됩니다.
2.  **변수명 규칙:**
    - **영문 소문자**와 **스네이크 케이스(snake_case)**만 사용해야 합니다. (예: `order_id`, `product_name`)
    - 고객 이름("김철수님", "고객님")은 예외 없이 **`customer_name`**으로 통일합니다.
    - 도착 예정일은 **`arrival_date`**로 명명합니다.
3.  날짜는 `date`, 금액은 `amount`, 주문번호는 `order_id`와 같이 일반적이고 예측 가능한 이름을 사용하세요.

**출력 형식:**
- 추출된 값과 그에 해당하는 변수명을 JSON 형식으로 매핑하세요.
- 변수화할 필드가 없으면 빈 JSON 객체 `{}`를 반환하세요.

**완벽한 예시 1:**
- 본문: "김철수님, 주문번호 ORD-123이 50,000원 결제 완료되었습니다."
- 응답:
{
    "customer_name": "김철수",
    "order_id": "ORD-123",
    "amount": "50,000"
}

**완벽한 예시 2:**
- 오늘 날짜: 2024-01-15
- 본문: "고객님의 상품이 내일 도착 예정입니다."
- 응답:
{{
    "arrival_date": "2024-01-16"
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            *self._build_hint_messages(), # 힌트가 있다면 여기에 추가됨
            {"role": "user", "content": f"분석할 본문:\n{self.user_text}"}
        ]
        return messages

class CategoryPromptBuilder(BasePromptBuilder):
    """카테고리 분류 프롬프트 빌더 - 적합성 판단 기능 추가"""
    def __init__(self, user_text: str, category_sub_list: List[str]):
        super().__init__(user_text)
        self.category_sub_list = category_sub_list

    def build(self) -> List[Dict]:
        system_prompt = f"""
당신은 카카오 알림톡 카테고리 분류 전문가입니다.
주어진 메시지를 분석하여, 아래 '서브 카테고리 후보' 중 가장 적합한 것을 선택하세요.

서브 카테고리 후보:
{', '.join(self.category_sub_list)}

중요: 만약 후보 중에 적합한 카테고리가 **없다고 판단되면**, "is_appropriate" 값을 false로 설정하고 그 이유를 명확히 설명해주세요.

JSON 형식으로 응답하세요:
{{
    "is_appropriate": true,
    "category_sub": "선택된 서브 카테고리",
    "confidence": 85,
    "selection_reason": "최종 선택 근거 상세 설명"
}}
// 또는, 적합한 것이 없을 경우:
{{
    "is_appropriate": false,
    "category_sub": null,
    "confidence": 30,
    "selection_reason": "예: '사전 점검 및 AS 안내'는 단순 '방문서비스'나 '이용안내'와는 성격이 달라 적합한 후보가 없습니다."
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"분석할 메시지:\n{self.user_text}"}
        ]
        return messages


class NewCategoryPromptBuilder(BasePromptBuilder):
    """신규 카테고리 생성 프롬프트 빌더"""
    def __init__(self, user_text: str, existing_categories: List[str]):
        super().__init__(user_text)
        self.existing_categories = existing_categories

    def build(self) -> List[Dict]:
        system_prompt = f"""
당신은 카테고리 네이밍 전문가입니다.
다음 메시지 내용의 핵심을 가장 잘 나타내는 새로운 카테고리명을 1개 생성해주세요.

생성 규칙:
1. 기존 카테고리들의 스타일과 형식을 반드시 따르세요. (예: '구매완료', '배송상태' 처럼 '명사' 또는 '명사+동사' 형태)
2. 간결하고 명확해야 합니다. (2~5자 내외)
3. 생성된 카테고리명만 JSON 형식으로 응답하세요.

기존 카테고리 스타일 참고:
{', '.join(self.existing_categories[:10])} # 일부만 보여줘도 스타일 파악 가능

JSON 응답 형식:
{{
    "new_category": "생성된 카테고리명"
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"다음 메시지에 대한 새로운 카테고리명을 생성해주세요:\n{self.user_text}"}
        ]
        return messages

async def parallel_title_category_node(state: TemplateGenerationState) -> TemplateGenerationState:
    """노드 2: 제목 생성 및 카테고리 분류 (병렬) - 신규 카테고리 생성 기능 추가"""
    logger.info("=" * 60)
    logger.info("2단계: 제목 생성 및 카테고리 분류 (병렬) 시작")
    logger.info("=" * 60)

    async def generate_title_task():
        # ... (기존과 동일)
        logger.info("제목 생성 작업 시작")
        title_builder = TemplateTitlePromptBuilder(state["user_text"])
        messages = title_builder.build()
        result = await state["openai_service"].chat_completion(messages)
        logger.info(f"생성된 제목: '{result}'")
        return result

    async def classify_or_create_category_task():
        """카테고리를 분류하거나, 적합하지 않으면 새로 생성하는 태스크"""
        logger.info("카테고리 분류/생성 작업 시작")

        # --- 1단계: 기존 리스트 내에서 분류 시도 ---
        logger.info("1차: 기존 카테고리 내에서 분류 시도...")
        category_builder = CategoryPromptBuilder(state["user_text"], state["category_sub_list"])
        messages = category_builder.build()
        response = await state["openai_service"].chat_completion(messages)
        first_attempt_result = json.loads(response)

        logger.info(f"1차 시도 결과: 적합성={first_attempt_result.get('is_appropriate')}, 신뢰도={first_attempt_result.get('confidence')}%")

        # --- 2단계: 결과에 따른 분기 처리 ---
        CONFIDENCE_THRESHOLD = 70
        is_appropriate = first_attempt_result.get("is_appropriate", False)
        confidence = first_attempt_result.get("confidence", 0)

        if is_appropriate and confidence >= CONFIDENCE_THRESHOLD:
            logger.info("✅ 1차 분류 성공. 기존 카테고리를 사용합니다.")
            # 최종 결과 형식에 맞게 재구성
            final_category_result = {
                "category_sub": first_attempt_result.get("category_sub"),
                "confidence": confidence,
                "selection_reason": first_attempt_result.get("selection_reason"),
                "generation_source": "classified_existing" # 출처 명시
            }
            return final_category_result
        else:
            logger.warning("⚠️ 1차 분류 실패 또는 신뢰도 낮음. 신규 카테고리 생성을 시도합니다.")
            logger.info(f"사유: {first_attempt_result.get('selection_reason')}")

            # --- 3단계: 신규 카테고리 생성 ---
            new_category_builder = NewCategoryPromptBuilder(state["user_text"], state["category_sub_list"])
            messages = new_category_builder.build()
            response = await state["openai_service"].chat_completion(messages)
            new_category_result = json.loads(response)

            new_category = new_category_result.get("new_category")
            logger.info(f"✨ 생성된 신규 카테고리: '{new_category}'")

            final_category_result = {
                "category_sub": new_category,
                "confidence": 95, # 새로 생성했으므로 신뢰도는 높게 설정
                "selection_reason": f"기존 리스트에 적합한 카테고리가 없어 '{new_category}'를 새로 생성함.",
                "generation_source": "created_new" # 출처 명시
            }
            return final_category_result

    try:
        # 병렬 실행
        title_result, category_result = await asyncio.gather(
            generate_title_task(),
            classify_or_create_category_task()
        )

        state["generated_title"] = title_result.strip()
        state["category_result"] = category_result

        logger.info("병렬 작업 완료")
        logger.info(f"최종 제목: '{state['generated_title']}'")
        logger.info(f"최종 카테고리: {category_result.get('category_sub')} (출처: {category_result.get('generation_source')})")

    except Exception as e:
        # ... (기존 예외 처리)
        logger.error(f"병렬 처리 실패: {e}")
        state["generated_title"] = "알림톡 안내"
        state["category_result"] = {
            "category_sub": "기타",
            "confidence": 0,
            "selection_reason": "오류로 인한 기본값",
            "generation_source": "error"
        }


    return state
class TypePromptBuilder(BasePromptBuilder):
    def __init__(self, user_text: str):
        super().__init__(user_text)

    def build(self) -> list[dict]:
        prompt = [
            {
                "role": "system",
                "content": """
        너는 카카오 알림 메세지의 유형을 판정하는 분류기다.
        [메세지 유형 정의]
        - BASIC: 핵심 목적(알림/안내/확인 등)만 전달. 링크가 있을 수 있으나, "채널 추가/채널 방문" 목적이 아니면 기본형으로 본다. 
        - 고객에게 반드시 전달되어야 하는 정보
        - EXTRA_INFO:핵심 목적 외에 주의사항·정책·문의·절차·상세 가이드 등 실질적인 추가 설명이 붙음.
        - 이용안내 등 보조적인 정보메시지
        - CHANNEL_ADD: 카카오 채널/브랜드 채널/오픈채팅 등을 추가·구독·방문하도록 유도하는 맥락이 존재. 
        - HYBRID: 채널 추가형 조건 + 부가 정보형 조건을 동시에 충족.  
        [메세지 유형 판정 원칙] 
        1) 먼저 채널 추가 유도 여부를 본다. 단순 웹사이트/배송조회/결제 안내는 채널 추가형이 아니다. 
        2) 다음으로 핵심 목적 외에 실질적인 부가 설명이 있는지 본다. 
        3) 최종 결정: 
        - 둘 다 있으면 HYBRID 
        - 채널 추가만 있으면 CHANNEL_ADD 
        - 부가 설명만 있으면 EXTRA_INFO 
        - 둘 다 없으면 BASIC 
        4) 애매하면 가장 합리적인 단일 유형을 고르고 이유를 간단히 남긴다.  
        [출력 형식(JSON만 출력)] 
        {
        "has_channel_link": true/false,
        "has_extra_info": true/false,
        "type": "BASIC | EXTRA_INFO | CHANNEL_ADD | HYBRID",
        "explain_type": "한 줄 이유"
        }
                """
            },
            *self._build_hint_messages(),
            {
                "role": "user",
                "content": """
        에이프릴키친 입니다.
        라이언님, 안녕하세요.
        소중한 주문이 접수완료 되었습니다.
        - 주문일자: 2024.05.01(토)
        - 금액: 12,0000원
        - 주문번호
        """
            },
            {
                "role": "assistant",
                "content": """
        {
        "has_channel_link": false,
        "has_extra_info": false,
        "type": "BASIC",
        "explain_type": "기본 정보만 포함"
        }
        """
            },
            {
                "role": "user",
                "content": """
        라이언님 안녕하세요.
        객실 정보 안내드립니다.
        - 예약번호: 1234
        - 객실명: 420호
        차량 이용시, 주차가능 여부를 반드시 문의하시기 바랍니다.
        * 예약 취소 시 최소규정에 따라 수수료가 부과될 수 있습니다.
        """
            },
            {
                "role": "assistant",
                "content": """
        {
        "has_channel_link": false,
        "has_extra_info": true,
        "type": "EXTRA_INFO",
        "explain_type": "부가 정보 포함"
        }
        """
            },
            {
                "role": "user",
                "content": """
        [국민카드] 홍길동 1234승인
        50,000원
        3개월
        2025-09-08
        14:35
        ABC 전자상가

        채널 추가하고 이 채널의 마케팅 메시지 등을 카카오톡으로 받기

        [카카오톡 채널 추가 버튼]
        """
            },
            {
                "role": "assistant",
                "content": """
        {
        "has_channel_link": true,
        "has_extra_info": false,
        "type": "CHANNEL_ADD",
        "explain_type": "채널 추가 정보 포함"
        }
        """
            },
            {
                "role": "user",
                "content": """
        카카오톡 명세서 라이언 회원님 결제 명세서 입니다.
        - 당일 결제 금액: 100원
        * 개인정보 보호를 위해 메세지 발송완료 부터 100일까지만, 위의 링크를 통한 상세내용 확인이 가능합니다.
        채널 추가하고 이 채널의 마케팅메세지 등을 카카오톡으로 받기
        """
            },
            {
                "role": "assistant",
                "content": """
        {
        "has_channel_link": true,
        "has_extra_info": true,
        "type": "HYBRID",
        "explain_type": "채널 추가 정보, 부가 정보 포함"
        }
        """
            },
            {
                "role": "user",
                "content": f"본문: {self.user_text}"
            }
        ]
        return prompt
# @TODO: TypePromptBuilder langGraph 동작 확인 시, 주석 버전 삭제하기
# class TypePromptBuilder(BasePromptBuilder):
#     """메시지 유형 분류 프롬프트 빌더"""
#     def build(self) -> List[Dict]:
#         system_prompt = """
# 당신은 카카오 알림톡 메시지 유형 분류 전문가입니다.
# 메시지를 다음 4가지 유형으로 분류해주세요:
#
# 1. BASIC: 기본 정보만 포함 (이름, 일시, 금액 등)
# 2. EXTRA_INFO: 기본 정보 + 부가 설명이나 안내사항
# 3. CHANNEL_ADD: 기본 정보 + 채널 추가/링크 유도
# 4. HYBRID: 기본 정보 + 부가 설명 + 채널 링크
#
# 분석 요소:
# - has_channel_link: 채널톡, 카카오톡 채널, 웹사이트 링크 포함 여부
# - has_extra_info: 추가 안내사항, 주의사항, 부가 설명 포함 여부
#
# JSON 형식으로 응답하세요:
# {
#     "type": "분류 결과",
#     "has_channel_link": true/false,
#     "has_extra_info": true/false,
#     "explain_type": "분류 이유 설명"
# }
# """
#
#         messages = [
#             {"role": "system", "content": system_prompt},
#             *self._build_hint_messages(),
#             {"role": "user", "content": f"분석할 메시지:\n{self.user_text}"}
#         ]
#
#         return messages

class TemplateTitlePromptBuilder:
    """템플릿 제목 생성 프롬프트 빌더"""
    def __init__(self, user_text: str):
        self.user_text = user_text

    def build(self) -> List[Dict]:
        system_prompt = """
카카오 알림톡 템플릿의 제목을 생성하는 전문가입니다.
다음 규칙을 따라 제목을 생성하세요:

1. 10자 이내로 간결하게
2. 메시지의 핵심 내용을 포함
3. 사용자가 쉽게 이해할 수 있는 명확한 표현
4. 제목만 출력 (추가 설명 불필요)

예시:
- "주문완료 안내"
- "배송출발 알림"
- "예약확정 통보"
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"다음 메시지의 제목을 생성해주세요:\n{self.user_text}"}
        ]

        return messages

class ReferenceBasedTemplatePromptBuilder:
    """참고 템플릿 기반 생성 프롬프트 빌더"""
    def __init__(self, user_text: str, reference_templates: List[Dict], extracted_fields: Dict):
        self.user_text = user_text
        self.reference_templates = reference_templates
        self.extracted_fields = extracted_fields

    def build(self) -> List[Dict]:
        # 참고 템플릿들을 문자열로 구성
        reference_context = ""
        for i, template in enumerate(self.reference_templates, 1):
            similarity = template.get('similarity', 0)
            reference_context += f"\n=== 참고 템플릿 {i} (유사도: {similarity:.3f}) ===\n{template.get('text', '')}\n"

        # 👇 변수 처리 규칙을 명시적으로 추가
        variable_rules = ""
        if self.extracted_fields:
            variable_rules = "\n\n**중요 변수 처리 규칙:**\n"
            variable_rules += "다음 텍스트는 반드시 지정된 변수명으로 대체하여 `#{변수명}` 형태로 표현해야 합니다.\n"
            for value, var_name in self.extracted_fields.items():
                variable_rules += f"- '{value}'는 -> `#{{{var_name}}}'\n`으로 변경하세요.\n"

        system_prompt = f"""
카카오 알림톡 템플릿 생성 전문가입니다.
{variable_rules}
다음 승인된 템플릿들을 참고하여 새로운 템플릿을 생성하세요:

{reference_context}

생성 규칙:
1. 변수는 #{{변수명}} 형태로 표현
2. 참고 템플릿의 구조와 톤앤매너 유지
3. 광고성 내용 금지, 정보성/안내성 내용만
4. 발송 근거를 하단에 명시 (*로 시작)
5. 카카오톡 알림톡 규정 준수
6. 사용자 요청에 맞게 내용 조정

템플릿 본문만 출력하세요 (변수 설명이나 추가 안내 불포함):
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"사용자 요청:\n{self.user_text}"}
        ]

        return messages

class NewTemplatePromptBuilder:
    """신규 템플릿 생성 프롬프트 빌더 - 카카오 공용 템플릿 기반"""
    def __init__(self, user_text: str,  extracted_fields: Dict, public_templates: Optional[List[Dict]] = None):
        self.user_text = user_text
        self.extracted_fields = extracted_fields  # 👈 전달받은 인자를 self.extracted_fields에 저장
        self.public_templates = public_templates or []

    def build(self) -> List[Dict]:
        public_context = ""
        if self.public_templates:
            public_context = "\n\n=== 카카오 공용 템플릿 참고 ===\n"
            for i, template in enumerate(self.public_templates[:3], 1):  # 최대 3개만
                public_context += f"{i}. {template.get('text', '')}\n\n"
        # 👇 변수 처리 규칙을 명시적으로 추가
        variable_rules = ""
        if self.extracted_fields:
            variable_rules = "\n\n**중요 변수 처리 규칙:**\n"
            variable_rules += "다음 텍스트는 반드시 지정된 변수명으로 대체하여 `#{변수명}` 형태로 표현해야 합니다.\n"
            # extracted_fields가 { "변수값": "변수명" } 형태라고 가정
            for value, var_name in self.extracted_fields.items():
                variable_rules += f"- '{value}' -> `#{{{var_name}}}`으로 변경하세요.\n"

        system_prompt = f"""
**[당신의 역할]**
당신은 10년차 카피라이터이자 카카오 알림톡 템플릿 검수 전문가입니다.
고객에게 전달되는 메시지인 만큼, 명확하고 친절하며 프로페셔널한 톤앤매너를 유지해야 합니다.
사용자가 제공한 '변수 처리 규칙'을 완벽하게 준수해야 합니다.

{variable_rules}

**[좋은 템플릿의 조건]**
1.  **친절함:** 딱딱하지 않고 부드러운 문장으로 시작하고 끝냅니다.
2.  **명확성:** 핵심 정보를 쉽게 파악할 수 있도록 줄 바꿈과 구성을 활용합니다.
3.  **정확성:** 변수 규칙을 포함한 모든 규칙을 100% 준수합니다.

**[생성 예시]**
- 사용자 요청: "김철수님, 주문하신 상품(스마트폰)이 정상적으로 접수되었습니다. 주문번호는 ORD-2024-001이며, 결제금액은 850,000원입니다."
- 변수 규칙: '김철수' -> `customer_name`, 'ORD-2024-001' -> `order_id`, '850,000' -> `amount`
- 좋은 템플릿 결과:
안녕하세요, #{{customer_name}}님.
주문하신 상품이 정상적으로 접수되었습니다.

■ 주문번호: #{{order_id}}
■ 결제금액: #{{amount}}원

상품 준비 후 배송이 시작되면 다시 한번 안내해 드리겠습니다.
저희 서비스를 이용해 주셔서 감사합니다.

*본 알림은 정보통신망법에 따라 발송되었습니다.

---
위 예시처럼, 주어진 요청과 규칙에 맞춰 최고의 템플릿을 생성해주세요.

{public_context}

템플릿 본문만 출력하세요:
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"다음 요청에 맞는 알림톡 템플릿을 생성해주세요:\n{self.user_text}"}
        ]

        return messages

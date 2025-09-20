import json
import logging
from typing import TypedDict, List, Literal, Optional, Dict, Any
from templateEngine.message_analyzer import MessageAnalyzer
from templateEngine.template_generator import TemplateGenerator
from langgraph.graph import StateGraph, END
from services.openai_service import OpenAIService
from services.chromadb_service import ChromaDBService
import asyncio
import langgraph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- LangGraph 상태 정의 ---
class TemplateGenerationState(TypedDict):
    """
    LangGraph 상태 정의 클래스

    Attributes:
        userMessage(str): 사용자 작성 프롬프트
        question_idx(int): 현재 노드가 이동한 위치
        task_types(str): 질문 의도
        table_columns(List[str]): 키워드와 매핑된 테이블의 컬럼들
        sql_queries(str): NL2SQL로 생성한 SQL
        query_results(str): SQL 실행 결과
        results_log(List[str]): 노드 실행 결과를 쌓는 리스트
        retry(bool): 재실행 여부
        loop_decision(str): 재실행할 노드 이름
        current_question_idx(int): 미사용. 분리된 질문 중 몇 번째 질문 실행 중인지
        vector_result(str): Vector DB 에서 키워드와 컬럼 유사도 측정한 결과
        retriever_result(Dict[str, Any]): Vector DB 에서 질문과 도서 데이터 유사도 측정한 결과
        aladin_result(Dict[str, Any]): 알라딘 API 에 질문에 대한 책 검색 결과
        final_response(str): 모든 응답을 종합한 최종 결과
        has_books(bool): 알라딘 API 가 아닌 곳에서 결과가 있는지 여부
        error_message(str): 에러 메세지
        start_time(float): 작업 시작 시간
    """
    userMessage: str # 👈 userMessage 사용
    category_sub_list: List[str]
    openai_service: OpenAIService
    chromadb_service: ChromaDBService
    message_type_result: Optional[Dict]
    category_result: Optional[Dict]
    generated_title: Optional[str]
    similar_templates: List[Dict]
    max_similarity: float
    pulblic_templates: List[Dict] # 👈 pulblic_templates 사용
    generation_hint: Optional[str]
    generated_template: str
    extracted_fields: Optional[Dict[str, Any]]
    final_result: Dict

# --- LangGraph 노드(단계) 정의 ---

# 서비스 인스턴스화
openai_service = OpenAIService()
analyzer = MessageAnalyzer(openai_service)
generator = TemplateGenerator()
chromadb_service = ChromaDBService()

# --- 병렬 실행을 위한 커스텀 노드 ---
async def title_and_category_parallel(state: TemplateGenerationState) -> TemplateGenerationState:
    """[노드 2] 제목 생성과 카테고리 분류를 병렬로 실행하는 노드"""
    logger.info("--- 2. 제목 생성 및 카테고리 분류 (병렬) 시작 ---")

    # asyncio.gather를 사용하여 두 메서드를 동시에 실행
    # 각 메서드는 state를 인자로 받고, 수정된 state를 반환해야 함
    # 하지만 각자 다른 부분을 수정하므로, 결과를 병합해야 함
    title_task = generator.generate_title(state.copy())
    category_task = analyzer.classify_message_category(state.copy())

    results = await asyncio.gather(title_task, category_task)

    # 각 태스크에서 반환된 state의 수정 사항을 현재 state에 병합
    state["generated_title"] = results[0]["generated_title"]
    state["category_sub"] = results[1]["category_sub"]

    return state

async def classify_message_type(state: TemplateGenerationState) -> TemplateGenerationState:
    logger.info("--- 1. 메시지 유형 분류 시작 ---")
    analyzer = state["analyzer"]
    result = await analyzer.classify_message_type(state["userMessage"])  # await 필수
    state["message_type"] = result.get("type")
    logger.info(f"결과: {state['message_type']}")
    return state

# def generate_title_and_classify_category(state: TemplateGenerationState) -> TemplateGenerationState:
#     """2. 제목 자동 생성 및 2차 카테고리 판단"""
#     logger.info("--- 2. 제목 생성 및 카테고리 분류 시작 ---")
#
#     # 제목 생성
#     title_prompt = build_prompt(task_type="title", userMessage=state["userMessage"])
#     state["generated_title"] = openai_service.chat_completion(title_prompt)
#     logger.info(f"생성된 제목: {state['generated_title']}")
#
#     # 카테고리 분류
#     category_prompt = build_prompt(
#         task_type="category",
#         userMessage=state["userMessage"],
#         category_main=state["category_main"],
#         category_sub_list=state["category_sub_list"]
#     )
#     response = openai_service.chat_completion(category_prompt)
#     result = json.loads(response)
#     state["category_sub"] = result.get("category_sub")
#     logger.info(f"분류된 2차 카테고리: {state['category_sub']}")
#
#     return state

def search_approved_templates(state: TemplateGenerationState) -> TemplateGenerationState:
    logger.info("--- 3. RAG - 유사 템플릿 검색 시작 ---")
    generator = state["generator"]

    if not state["category_sub"]:
        logger.warning("2차 카테고리가 없어 검색을 건너뜁니다.")
        state["similar_templates"] = []
        state["similarity_score"] = 0.0
        return state

    results = generator.search_similar_templates(
        query_text=state["userMessage"],
        category_sub=state["category_sub"],
        top_k=1
    )

    if results:
        similarity = 1 - results[0].get("distance", 1.0)
        state["similar_templates"] = results
        state["similarity_score"] = similarity
        logger.info(f"검색 결과: 유사도 {similarity:.2f}")
    else:
        state["similar_templates"] = []
        state["similarity_score"] = 0.0
        logger.info("유사한 템플릿을 찾지 못했습니다.")
    return state


def decide_hint_addition(state: TemplateGenerationState) -> Literal["add_hint", "no_hint"]:
    """4. 유사도 0.7 만족 여부 판단"""
    logger.info("--- 4. 힌트 추가 여부 결정 ---")
    SIMILARITY_THRESHOLD = 0.7
    if state["similarity_score"] >= SIMILARITY_THRESHOLD:
        logger.info(f"유사도({state['similarity_score']:.2f})가 기준({SIMILARITY_THRESHOLD}) 이상. 힌트를 추가합니다.")
        return "add_hint"
    else:
        logger.info(f"유사도({state['similarity_score']:.2f})가 기준({SIMILARITY_THRESHOLD}) 미만. 힌트 없이 생성합니다.")
        return "no_hint"

def add_generation_hint(state: TemplateGenerationState) -> TemplateGenerationState:
    """5a. 생성 프롬프트에 필드 관련 힌트 추가"""
    logger.info("--- 5a. 생성 힌트 추가 ---")
    reference_template = state["similar_templates"][0]["text"]
    state["generation_hint"] = f"다음 승인 템플릿의 구조와 스타일을 참고하세요: '{reference_template}'"
    return state

def generate_final_template(state: TemplateGenerationState) -> TemplateGenerationState:
    logger.info("--- 6. 최종 템플릿 생성 시작 ---")
    generator = state["generator"]
    userMessage = state["userMessage"]
    hint = state.get("generation_hint")

    if hint:
        logger.info("참고 템플릿 기반 생성")
        state["generated_template"] = generator.generate_template_with_reference(userMessage, hint)
    else:
        logger.info("신규 템플릿 생성")
        state["generated_template"] = generator.generate_new_template(userMessage)

    logger.info("최종 템플릿 생성 완료.")

    state["final_result"] = {
        "title": state["generated_title"],
        "template": state["generated_template"],
        "message_type": state["message_type"],
        "category_sub": state["category_sub"],
        "generation_method": "reference_based" if hint else "new_creation",
        "similarity_score": state.get("similarity_score", 0.0),
        "reference_templates": state.get("similar_templates", [])
    }
    return state

# --- LangGraph 그래프 구성 ---
workflow = StateGraph(TemplateGenerationState)

# 노드 추가
workflow.add_node("classify_type", classify_message_type)
workflow.add_node("title_and_category", title_and_category_parallel)
workflow.add_node("search_templates", search_approved_templates)
workflow.add_node("add_hint", add_generation_hint)
workflow.add_node("generate_template", generate_final_template)

# 엣지(흐름) 연결
workflow.set_entry_point("classify_type")
workflow.add_edge("classify_type", "title_and_category")
workflow.add_edge("title_and_category", "search_templates")

# 조건부 엣지 (유사도에 따른 분기)
workflow.add_conditional_edges(
    "search_templates",
    decide_hint_addition,
    {
        "add_hint": "add_hint",
        "no_hint": "generate_template" # 힌트 없으면 바로 생성으로
    }
)

workflow.add_edge("add_hint", "generate_template")
workflow.add_edge("generate_template", END)

# 그래프 컴파일
app = workflow.compile()

# --- 실행 ---
if __name__ == "__main__":
    # 사용자 입력 예시
    user_input = {
        "userMessage": "안녕하세요 라이언님, 주문하신 상품이 정상적으로 접수되었습니다. 주문번호는 12345입니다.",
        "category_main": "주문",
        "category_sub_list": [
            "구매완료", "구매취소", "기타", "뉴스레터", "리마인드", "방문서비스",
            "배송상태", "배송완료", "배송예정", "배송실패", "상품가입", "신청접수",
            "예약상태", "예약완료", "예약취소", "이용도구", "이용안내/공지",
            "요금청구", "주문/예약", "쿠폰발급", "피드백", "피드백 요청", "회원가입"
        ]
    }

    # 파이프라인 실행
    final_state = app.invoke(user_input)

    print("\n--- 최종 생성 결과 ---")
    print(json.dumps(final_state.get("final_result"), indent=2, ensure_ascii=False))

# templateEngine/nodes.py

import json
import logging
import re
from typing import Dict, Any, Literal
import asyncio  # 👈 1. asyncio 임포트 추가!

from .state import TemplateGenerationState
from .prompts.builders import (
    TypePromptBuilder,
    TemplateTitlePromptBuilder,
    CategoryPromptBuilder,
    FieldsPromptBuilder,
    NewCategoryPromptBuilder,
    ReferenceBasedTemplatePromptBuilder,
    NewTemplatePromptBuilder
)

logger = logging.getLogger(__name__)

# --- 노드 함수들 ---

async def classify_message_type_node(state: TemplateGenerationState) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("1단계: 메시지 유형 분류 시작")
    try:
        prompt_builder = TypePromptBuilder(state["userMessage"])
        messages = prompt_builder.build()
        response = await state["openai_service"].chat_completion(messages)
        result = json.loads(response)
        logger.info(f"✅ 메시지 유형 분류 성공: {result.get('type')}")
        return {"message_type_result": result}
    except Exception as e:
        logger.error(f"❌ 메시지 유형 분류 실패: {e}", exc_info=True)
        return {"message_type_result": {"type": "BASIC", "explain_type": "분류 실패로 기본값 적용"}}

async def parallel_title_category_node(state: TemplateGenerationState) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("2단계: 제목 생성 및 카테고리 분류 (병렬) 시작")
    try:
        async def generate_title_task():
            title_builder = TemplateTitlePromptBuilder(state["userMessage"])
            messages = title_builder.build()
            return await state["openai_service"].chat_completion(messages)

        async def classify_or_create_category_task():
            logger.info("카테고리 분류/생성 작업 시작")
            logger.info("1차: 기존 카테고리 내에서 분류 시도...")
            category_builder = CategoryPromptBuilder(state["userMessage"], state["category_sub_list"])
            messages = category_builder.build()
            response = await state["openai_service"].chat_completion(messages)
            first_attempt_result = json.loads(response)
            logger.info(f"기존 카테고리 사용 1차 시도 결과: 적합성={first_attempt_result.get('is_appropriate')}, 신뢰도={first_attempt_result.get('confidence')}%")

            CONFIDENCE_THRESHOLD = 70
            if first_attempt_result.get("is_appropriate") and first_attempt_result.get("confidence", 0) >= CONFIDENCE_THRESHOLD:
                logger.info("✅ 1차 분류 성공. 기존 카테고리를 사용합니다.")
                return {
                    "category_sub": first_attempt_result.get("category_sub"), "confidence": first_attempt_result.get("confidence"),
                    "selection_reason": first_attempt_result.get("selection_reason"), "generation_source": "classified_existing"
                }
            else:
                logger.warning("⚠️ 1차 분류 실패 또는 신뢰도 낮음. 신규 카테고리 생성을 시도합니다.")
                logger.info(f"사유: {first_attempt_result.get('selection_reason')}")
                new_category_builder = NewCategoryPromptBuilder(state["userMessage"], state["category_sub_list"])
                messages = new_category_builder.build()
                response = await state["openai_service"].chat_completion(messages)
                new_category_result = json.loads(response)
                new_category = new_category_result.get("new_category")
                logger.info(f"✨ 생성된 신규 카테고리: '{new_category}'")
                return {
                    "category_sub": new_category, "confidence": 95,
                    "selection_reason": f"기존 리스트에 적합한 카테고리가 없어 '{new_category}'를 새로 생성함.", "generation_source": "created_new"
                }

        title_result, category_result = await asyncio.gather(generate_title_task(), classify_or_create_category_task())

        logger.info("병렬 작업 완료")
        logger.info(f"✅ 제목 생성 성공: '{title_result.strip()}'")
        logger.info(f"✅ 카테고리 분류 성공: {category_result.get('category_sub')}")

        return {"generated_title": title_result.strip(), "category_result": category_result}
    except Exception as e:
        logger.error(f"❌ 병렬 처리 실패: {e}", exc_info=True)
        return {"generated_title": "제목 생성 실패", "category_result": {"category_sub": "기타", "selection_reason": "분류 실패"}}

async def search_templates_node(state: TemplateGenerationState) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("3단계: RAG - 유사 템플릿 검색 시작")
    category_sub = state.get("category_result", {}).get("category_sub")
    if not category_sub:
        logger.warning("⚠️ 서브 카테고리가 없어 검색을 건너뜁니다.")
        return {"similar_templates": [], "max_similarity": 0.0}
    try:
        templates, max_similarity = state["chromadb_service"].search_approved_templates(
            query_text=state["userMessage"],
            category_sub=category_sub,
            top_k=3
        )
        logger.info(f"✅ 유사 템플릿 검색 완료. 최대 유사도: {max_similarity:.3f}")
        return {"similar_templates": templates, "max_similarity": max_similarity}
    except Exception as e:
        logger.error(f"❌ 유사 템플릿 검색 실패: {e}", exc_info=True)
        return {"similar_templates": [], "max_similarity": 0.0}

async def extract_fields_node(state: TemplateGenerationState) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("✨ 추가 단계: 변수 필드 추출 시작")
    try:
        prompt_builder = FieldsPromptBuilder(state["userMessage"])
        messages = prompt_builder.build()
        response = await state["openai_service"].chat_completion(messages)

        clean_response = response.strip().replace("```json", "").replace("```", "").strip()
        if not clean_response:
            logger.warning("⚠️ 변수 추출 결과가 비어있습니다. 빈 객체를 반환합니다.")
            return {"extracted_fields": {}}

        result = json.loads(clean_response)
        logger.info(f"✅ 추출된 변수 필드: {result}")
        return {"extracted_fields": result}
    except json.JSONDecodeError as e:
        logger.error(f"❌ 변수 필드 추출 JSON 파싱 실패: {e}", exc_info=True)
        logger.error(f"   파싱 실패한 원본 응답: {response}")
        return {"extracted_fields": {}}
    except Exception as e:
        logger.error(f"❌ 변수 필드 추출 실패: {e}", exc_info=True)
        return {"extracted_fields": {}}

def decide_generation_method(state: TemplateGenerationState) -> Literal["with_reference", "search_public"]:
    logger.info("=" * 60)
    logger.info("4단계: 생성 방법 결정")
    SIMILARITY_THRESHOLD = 0.75
    if state.get("max_similarity", 0.0) >= SIMILARITY_THRESHOLD:
        logger.info(f"✅ 결정: 유사도({state['max_similarity']:.3f})가 기준 이상. [참고 템플릿 기반 생성]으로 진행합니다.")
        return "with_reference"
    else:
        logger.info(f"⚠️ 결정: 유사도({state['max_similarity']:.3f})가 기준 미만. [신규 생성]으로 진행합니다.")
        return "search_public"

async def generate_with_reference_node(state: TemplateGenerationState) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("5a단계: 참고 템플릿 기반 생성 시작")
    try:
        prompt_builder = ReferenceBasedTemplatePromptBuilder(
            userMessage=state["userMessage"],
            reference_templates=state["similar_templates"],
            extracted_fields=state["extracted_fields"]
        )
        messages = prompt_builder.build()
        template = await state["openai_service"].chat_completion(messages)
        logger.info("✅ 참고 템플릿 기반 생성 성공")
        return {"generated_template": template, "generation_hint": "reference_based"}
    except Exception as e:
        logger.error(f"❌ 참고 템플릿 기반 생성 실패: {e}", exc_info=True)
        return {"generated_template": "템플릿 생성 중 오류 발생", "generation_hint": "error"}

async def search_public_and_generate_node(state: TemplateGenerationState) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("5b단계: 신규 생성 시작")
    try:
        pulblic_templates = state["chromadb_service"].search_public_templates(
            query_text=state["userMessage"], top_k=3
        )
        hint = "pulblic_templates_based" if pulblic_templates else "from_scratch"

        # 👇 4. user_text -> userMessage로 수정
        prompt_builder = NewTemplatePromptBuilder(
            userMessage=state["userMessage"],
            extracted_fields=state["extracted_fields"],
            public_templates=pulblic_templates
        )
        messages = prompt_builder.build()
        template = await state["openai_service"].chat_completion(messages)
        logger.info(f"✅ 신규 생성 성공 (방식: {hint})")
        return {"generated_template": template, "generation_hint": hint, "pulblic_templates": pulblic_templates}
    except Exception as e:
        logger.error(f"❌ 신규 생성 실패: {e}", exc_info=True)
        return {"generated_template": "템플릿 생성 중 오류 발생", "generation_hint": "error", "pulblic_templates": []}

def finalize_result_node(state: TemplateGenerationState) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("6단계: 최종 결과 정리")
    variables = extract_variables_from_template(state.get("generated_template", ""))
    final_result = {
        "pipeline_success": True,
        "error_message": None,
        "template_text": state.get("generated_template", ""),
        "template_title": state.get("generated_title", "제목 없음"),
        "variables": variables,
        "generation_method": state.get("generation_hint", "unknown"),
        "message_type": state.get("message_type_result", {}).get("type"),
        "category_sub": state.get("category_result", {}).get("category_sub"),
        "category_analysis": state.get("category_result"),
        "similarity_score": state.get("max_similarity", 0.0),
        "reference_templates": state.get("similar_templates", []),
        "pulblic_templates": state.get("pulblic_templates", []),
    }
    logger.info("✅ 파이프라인 최종 결과 생성 완료.")
    # 👇 --- 최종 생성된 템플릿을 터미널에 명확하게 출력 --- 👇
    logger.info("-" * 60)
    logger.info(">>> 최종 생성된 템플릿 본문 <<<")
    logger.info(final_result.get("template_text"))
    logger.info("-" * 60)
    return {"final_result": final_result}

def extract_variables_from_template(template_text: str) -> list[str]:
    if not template_text: return []
    return sorted(list(set(re.findall(r'#\{([^}]+)\}', template_text))))


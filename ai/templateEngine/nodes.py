# template_engine/nodes.py
import json
import logging
import re
from typing import Dict, Any, Literal, List
from datetime import datetime, timedelta
# 👇 이제 다른 모듈에서 필요한 것들을 import 합니다.
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

async def classify_message_type_node(state: TemplateGenerationState)  -> Dict[str, Any]: # 반환 타입을 Dict로 변경
    """노드 1: 메시지 유형 분류"""
    logger.info("=" * 60)
    logger.info("1단계: 메시지 유형 분류 시작")
    logger.info("=" * 60)
    logger.info(f"입력 텍스트: '{state['user_text']}'")

    try:
        prompt_builder = TypePromptBuilder(state["user_text"])
        messages = prompt_builder.build()

        response = await state["openai_service"].chat_completion(messages)
        result = json.loads(response)

        state["message_type_result"] = result
        logger.info(f"메시지 유형: {result.get('type', 'UNKNOWN')}")
        logger.info(f"채널 링크 여부: {result.get('has_channel_link', False)}")
        logger.info(f"부가 정보 여부: {result.get('has_extra_info', False)}")
        logger.info(f"분류 이유: {result.get('explain_type', '미상')}")
        return {"message_type_result": result}
    except Exception as e:
        logger.error(f"메시지 유형 분류 실패: {e}")
        state["message_type_result"] = {
            "type": "BASIC",
            "has_channel_link": False,
            "has_extra_info": False,
            "explain_type": "분류 실패로 기본값 적용"
        }
    # 👇 변경된 값만 dict로 반환
    return {"message_type_result": {
        "type": "BASIC",
        "has_channel_link": False,
        "has_extra_info": False,
        "explain_type": "분류 실패로 기본값 적용"
    }}

async def parallel_title_category_node(state: TemplateGenerationState) -> Dict[str, Any]: # 👈 반환 타입을 Dict로 변경
    """노드 2: 제목 생성 및 카테고리 분류 (병렬) - 상세한 분류 분석"""
    logger.info("=" * 60)
    logger.info("2단계: 제목 생성 및 카테고리 분류 (병렬) 시작")
    logger.info("=" * 60)

    async def generate_title_task():
        logger.info("제목 생성 작업 시작")
        title_builder = TemplateTitlePromptBuilder(state["user_text"])
        messages = title_builder.build()
        result = await state["openai_service"].chat_completion(messages)
        logger.info(f"생성된 제목: '{result}'")
        return result

    async def classify_category_task():
        logger.info("카테고리 분류 작업 시작")
        logger.info(f"서브 카테고리 후보 ({len(state['category_sub_list'])}개): {state['category_sub_list']}")

        category_builder = CategoryPromptBuilder(state["user_text"], state["category_sub_list"])
        messages = category_builder.build()
        response = await state["openai_service"].chat_completion(messages)
        result = json.loads(response)

        # 상세한 카테고리 분석 결과 로깅
        logger.info("=" * 40)
        logger.info("카테고리 분류 상세 분석 결과")
        logger.info("=" * 40)
        logger.info(f"선택된 카테고리: {result.get('category_sub', 'UNKNOWN')}")
        logger.info(f"신뢰도: {result.get('confidence', 0)}%")
        logger.info(f"핵심 키워드: {result.get('key_words', [])}")
        logger.info(f"분석 과정: {result.get('analysis_process', '미상')}")
        logger.info(f"선택 근거: {result.get('selection_reason', '미상')}")
        logger.info(f"고려한 다른 후보: {result.get('alternative_categories', [])}")
        logger.info("=" * 40)

        return result

    try:
        # 병렬 실행
        logger.info("병렬 작업 시작...")
        title_result, category_result = await asyncio.gather(
            generate_title_task(),
            classify_category_task()
        )

        state["generated_title"] = title_result.strip()
        state["category_result"] = category_result

        logger.info("병렬 작업 완료")
        logger.info(f"최종 제목: '{state['generated_title']}'")
        logger.info(f"최종 카테고리: {category_result.get('category_sub', 'UNKNOWN')}")
        # 👇 변경된 두 개의 값만 dict로 반환
        return {
            "generated_title": title_result.strip(),
            "category_result": category_result
        }
    except Exception as e:
        logger.error(f"병렬 처리 실패: {e}")
        state["generated_title"] = "알림톡 안내"
        state["category_result"] = {
            "category_sub": state["category_sub_list"][0] if state["category_sub_list"] else "기타",
            "confidence": 50,
            "key_words": [],
            "analysis_process": "분류 실패로 기본값 적용",
            "selection_reason": "오류로 인한 기본 선택",
            "alternative_categories": []
        }
        # 👇 변경된 두 개의 값만 dict로 반환
        return {
            "generated_title": "알림톡 안내",
            "category_result": {
                "category_sub": "기타",
                # ...
            }
        }

    return state

async def search_templates_node(state: TemplateGenerationState) -> Dict[str, Any]: # 👈 반환 타입을 Dict로 변경
    """노드 3: RAG 검색 - 승인된 템플릿에서 서브 카테고리 기반 검색"""
    """user_text 임베딩"""
    logger.info("=" * 60)
    logger.info("3단계: RAG 검색 - 승인된 템플릿 검색 시작")
    logger.info("=" * 60)

    category_sub = state["category_result"].get("category_sub") if state["category_result"] else None
    logger.info(f"검색 대상 서브 카테고리: {category_sub}")

    if not category_sub:
        logger.warning("서브 카테고리가 없어 검색 건너뜀")
        state["similar_templates"] = []
        state["max_similarity"] = 0.0
        return state

    try:
        # 승인된 템플릿에서 검색
        templates, max_similarity = state["chromadb_service"].search_approved_templates(
            query_text=state["user_text"],
            category_sub=category_sub,
            top_k=5
        )


        # 상위 템플릿들 선택 (유사도가 있는 것들만)
        filtered_templates = [t for t in templates if t['similarity'] > 0.3]  # 최소 유사도 필터
        selected_templates = filtered_templates[:3]  # 최대 3개

        state["similar_templates"] = selected_templates
        state["max_similarity"] = max_similarity

        logger.info(f"검색 결과 요약:")
        logger.info(f"  전체 검색 결과: {len(templates)}개")
        logger.info(f"  필터링 후: {len(filtered_templates)}개")
        logger.info(f"  최종 선택: {len(selected_templates)}개")
        logger.info(f"  최대 유사도: {max_similarity:.3f}")

        # 유사도 점수의 의미를 명확히 함
        if max_similarity > 0:
            logger.info(f"  최대 유사도: {max_similarity:.3f} (가장 유사한 템플릿과의 점수)")
        else:
            logger.warning("  최대 유사도: 0.000 (참고할 만한 유사 템플릿이 데이터베이스에 없음)")

        if selected_templates:
            logger.info("선택된 승인 템플릿:")
            for i, template in enumerate(selected_templates, 1):
                logger.info(f"  {i}. ID: {template['id']}")
                logger.info(f"     유사도: {template['similarity']:.3f}")
                logger.info(f"     내용: {template['text'][:50]}...")
        return {
            "similar_templates": selected_templates,
            "max_similarity": max_similarity
        }
    except Exception as e:
        logger.error(f"템플릿 검색 실패: {e}")
        state["similar_templates"] = []
        state["max_similarity"] = 0.0
        # 👇 변경된 값들만 dict로 반환
        return {
            "similar_templates": [],
            "max_similarity": 0.0
        }
    # return state

def decide_generation_method(state: TemplateGenerationState) -> Literal["with_reference", "search_public", "new_creation"]:
    """분기 조건: 유사도 0.75 기준으로 생성 방법 결정"""
    logger.info("=" * 60)
    logger.info("4단계: 생성 방법 결정")
    logger.info("=" * 60)

    SIMILARITY_THRESHOLD = 0.75
    similarity = state["max_similarity"]
    template_count = len(state["similar_templates"])

    logger.info(f"판단 기준:")
    logger.info(f"  현재 최대 유사도: {similarity:.3f}")
    logger.info(f"  기준 유사도: {SIMILARITY_THRESHOLD}")
    logger.info(f"  승인된 템플릿 수: {template_count}개")

    if similarity >= SIMILARITY_THRESHOLD and template_count > 0:
        logger.info(f"결정: 승인된 템플릿 기반 생성")
        logger.info(f"  이유: 유사도 {similarity:.3f} >= {SIMILARITY_THRESHOLD}")
        return "with_reference"
    else:
        logger.info(f"결정: 공용 템플릿 검색 후 신규 생성")
        if template_count == 0:
            logger.info(f"  이유: 참고할 만한 승인 템플릿이 전혀 없습니다 (유사도: {similarity:.3f}).")
        else:
            logger.info(f"  이유: 최대 유사도({similarity:.3f})가 기준점({SIMILARITY_THRESHOLD})보다 낮습니다.")
        return "search_public"

async def generate_with_reference_node(state: TemplateGenerationState) -> Dict[str, Any]: # 👈 반환 타입을 Dict로 변경
    """노드 5a: 승인된 템플릿 기반 생성"""
    logger.info("=" * 60)
    logger.info("5a단계: 승인된 템플릿 기반 생성")
    logger.info("=" * 60)

    logger.info(f"참고할 승인된 템플릿 수: {len(state['similar_templates'])}개")
    for i, template in enumerate(state["similar_templates"], 1):
        logger.info(f"  참고 템플릿 {i}:")
        logger.info(f"    ID: {template['id']}")
        logger.info(f"    유사도: {template['similarity']:.3f}")

    try:
        prompt_builder = ReferenceBasedTemplatePromptBuilder(
            state["user_text"],
            state["similar_templates"],
            state["extracted_fields"] # 👈 추출된 변수 정보 전달
        )
        messages = prompt_builder.build()

        template = await state["openai_service"].chat_completion(messages)
        state["generated_template"] = template.strip()
        state["generation_hint"] = "승인된 템플릿 기반"

        logger.info(f"승인된 템플릿 기반 생성 완료: {len(template)}자")
        # 👇 변경된 값들만 dict로 반환
        return {
            "generated_template": template.strip(),
            "generation_hint": "승인된 템플릿 기반"
        }
    except Exception as e:
        logger.error(f"승인된 템플릿 기반 생성 실패: {e}")
        # 실패 시 공용 템플릿 검색으로 fallback
        await search_public_and_generate_node(state)

    return state

async def search_public_and_generate_node(state: TemplateGenerationState) -> TemplateGenerationState:
    """노드 5b: 공용 템플릿 검색 후 신규 생성"""
    logger.info("=" * 60)
    logger.info("5b단계: 공용 템플릿 검색 후 신규 생성")
    logger.info("=" * 60)

    try:
        # 카카오 공용 템플릿 검색
        logger.info("카카오 공용 템플릿 검색 중...")
        public_templates = state["chromadb_service"].search_public_templates(
            query_text=state["user_text"],
            top_k=3
        )
        # 👇 NewTemplatePromptBuilder 호출 시 인자 순서 및 내용 수정
        prompt_builder = NewTemplatePromptBuilder(
            user_text=state["user_text"],
            extracted_fields=state["extracted_fields"], # 👈 추출된 변수 정보 전달
            public_templates=public_templates
        )
        messages = prompt_builder.build()
        template = await state["openai_service"].chat_completion(messages)
        return {
            "generated_template": template.strip(),
            "generation_hint": "공용 템플릿 참고 신규 생성" if public_templates else "완전 신규 생성",
            "public_templates": public_templates
        }
        # state["public_templates"] = public_templates

        # if public_templates:
        #     logger.info(f"공용 템플릿 {len(public_templates)}개 검색 완료:")
        #     for i, template in enumerate(public_templates, 1):
        #         logger.info(f"  {i}. 유사도: {template['similarity']:.3f}")
        #         logger.info(f"     내용: {template['text'][:50]}...")
        #
        # # 공용 템플릿을 참고하여 신규 생성
        # prompt_builder = NewTemplatePromptBuilder(state["user_text"], public_templates)
        # # messages = prompt_builder.build()
        #
        # template = await state["openai_service"].chat_completion(messages)
        # state["generated_template"] = template.strip()
        # state["generation_hint"] = "공용 템플릿 참고 신규 생성" if public_templates else "완전 신규 생성"
        #
        # logger.info(f"신규 템플릿 생성 완료: {len(template)}자")
        # logger.info(f"생성 방식: {state['generation_hint']}")

    except Exception as e:
        logger.error(f"공용 템플릿 검색 및 생성 실패: {e}")
        state["generated_template"] = "템플릿 생성 중 오류가 발생했습니다."
        state["generation_hint"] = "생성 실패"
        state["public_templates"] = []

        return {
            "generated_template": "템플릿 생성 중 오류가 발생했습니다.",
            "generation_hint": "생성 실패",
            "public_templates": []
        }

# 파이프라인이 성공적으로 끝났을 때만 호출
def finalize_result_node(state: TemplateGenerationState) -> Dict[str, Any]: # 👈 반환 타입을 Dict로 변경
    """노드 6: 최종 결과 정리"""
    logger.info("=" * 60)
    logger.info("6단계: 최종 결과 정리")
    logger.info("=" * 60)

    # 변수 추출
    variables = extract_variables_from_template(state["generated_template"])

    # 최종 결과 구성
    # state 딕셔너리의 'final_result' 키에 직접 결과를 할당합니다.
    state["final_result"] = {
        "pipeline_success": True,
        "error_message": None,
        "template_text": state.get("generated_template", "템플릿 생성 결과가 없습니다."),
        "template_title": state.get("generated_title", "제목 없음"),
        "variables": variables,
        "generation_method": state.get("generation_hint", "unknown"),
        "message_type": state.get("message_type_result", {}).get("type"),
        "category_sub": state.get("category_result", {}).get("category_sub"),
        "category_analysis": state.get("category_result"),
        "similarity_score": state.get("max_similarity", 0.0),
        "reference_templates": state.get("similar_templates", []),
        "public_templates": state.get("public_templates", []),
    }

    # 로그 출력 부분도 state["final_result"]를 사용하도록 통일
    logger.info("✅ 파이프라인 성공적으로 완료. 최종 결과 요약:")
    final_result = state["final_result"]
    logger.info(f"  템플릿 제목: '{final_result.get('template_title')}'")
    logger.info(f"  메시지 유형: {final_result.get('message_type')}")
    logger.info(f"  서브 카테고리: {final_result.get('category_sub')}")
    logger.info(f"  생성 방법: {final_result.get('generation_method')}")
    logger.info(f"  유사도: {final_result.get('similarity_score', 0.0):.3f}")
    logger.info(f"  추출된 변수: {len(final_result.get('variables', []))}개")
    if final_result.get('variables'):
        logger.info(f"    변수 목록: {', '.join(final_result.get('variables', []))}")

    return {"final_result": state["final_result"]}

def extract_variables_from_template(template_text: str) -> List[str]:
    """템플릿에서 변수 추출"""
    if not template_text:
        return []

    # #{변수명} 패턴으로 변수 추출
    pattern = r'#\{([^}]+)\}'
    variables = re.findall(pattern, template_text)

    # 중복 제거하고 정렬
    return sorted(list(set(variables)))

async def extract_fields_node(state: TemplateGenerationState) -> Dict[str, Any]: # 👈 반환 타입을 Dict로 변경
    """신규 노드: 메시지에서 변수 필드 추출"""
    logger.info("=" * 60)
    logger.info("✨ 추가 단계: 변수 필드 추출 시작")
    logger.info("=" * 60)

    try:
        # 다른 노드의 분석 결과를 힌트로 사용
        hint_content = f"""
            [참고 정보]
            - 메시지 유형: {state['message_type_result'].get('type')}
            - 서브 카테고리: {state['category_result'].get('category_sub')}
            - 참고 템플릿 유사도: {state['max_similarity']:.3f}
            
            위 정보를 바탕으로 원본 메시지에서 변수화할 필드를 더 정확하게 식별하세요.
            '김철수님'과 같은 이름은 반드시 'customer_name' 변수로 추출해야 합니다.
            """

        prompt_builder = FieldsPromptBuilder(state["user_text"])
        prompt_builder.add_hint("분석 컨텍스트", hint_content)
        messages = prompt_builder.build()

        response = await state["openai_service"].chat_completion(messages)
        result = json.loads(response)
        # 👇 변경된 값만 dict로 반환
        # --- 👇 날짜 후처리 로직 추가 ---
        processed_fields = result.copy()
        for key, value in processed_fields.items():
            # 만약 값이 'YYYY-MM-DD' 형식이 아니면, 오늘 날짜 기준으로 재계산 시도
            if 'date' in key and not re.match(r'\d{4}-\d{2}-\d{2}', str(value)):
                today = datetime.now()
                if '내일' in str(value) or 'tomorrow' in str(value).lower():
                    processed_fields[key] = (today + timedelta(days=1)).strftime('%Y-%m-%d')
                    logger.info(f"✅ 날짜 후처리: '{value}' -> '{processed_fields[key]}'")
                elif '오늘' in str(value) or 'today' in str(value).lower():
                    processed_fields[key] = today.strftime('%Y-%m-%d')
                    logger.info(f"✅ 날짜 후처리: '{value}' -> '{processed_fields[key]}'")

        logger.info(f"✅ 추출 및 정제된 변수 필드 ({len(processed_fields)}개): {processed_fields}")
        return {"extracted_fields": result}

        # state["extracted_fields"] = result
        logger.info(f"✅ 추출된 변수 필드 ({len(result)}개): {result}")

    except Exception as e:
        logger.error(f"❌ 변수 필드 추출 실패: {e}")
        state["extracted_fields"] = {} # 실패 시 빈 객체로 초기화
        # 👇 변경된 값만 dict로 반환
        return {"extracted_fields": {}}

    return state
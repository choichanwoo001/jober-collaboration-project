# template_engine/pipeline.py

import logging
from typing import Dict, List
from langgraph.graph import StateGraph, END

from .state import TemplateGenerationState
from .nodes import (
    classify_message_type_node,
    parallel_title_category_node,
    search_templates_node,
    extract_fields_node,
    decide_generation_method,
    generate_with_reference_node,
    search_public_and_generate_node,
    finalize_result_node
)
from services.openai_service import OpenAIService
from services.chromadb_service import ChromaDBService

logger = logging.getLogger(__name__)

async def create_pipeline() -> StateGraph:
    workflow = StateGraph(TemplateGenerationState)
    workflow.add_node("classify_type", classify_message_type_node)
    workflow.add_node("title_category_parallel", parallel_title_category_node)
    workflow.add_node("search_templates", search_templates_node)
    workflow.add_node("extract_fields", extract_fields_node)
    workflow.add_node("generate_with_reference", generate_with_reference_node)
    workflow.add_node("search_public_and_generate", search_public_and_generate_node)
    workflow.add_node("finalize_result", finalize_result_node)

    workflow.set_entry_point("classify_type")
    workflow.add_edge("classify_type", "title_category_parallel")
    workflow.add_edge("title_category_parallel", "search_templates")
    workflow.add_edge("search_templates", "extract_fields")
    workflow.add_conditional_edges(
        "extract_fields",
        decide_generation_method,
        {
            "with_reference": "generate_with_reference",
            "search_public": "search_public_and_generate"
        }
    )
    workflow.add_edge("generate_with_reference", "finalize_result")
    workflow.add_edge("search_public_and_generate", "finalize_result")
    workflow.add_edge("finalize_result", END)

    return workflow.compile()

async def run_template_generation_pipeline(
        user_text: str,
        category_sub_list: List[str],
        openai_service: OpenAIService,
        chromadb_service: ChromaDBService
) -> Dict:
    try:
        app = await create_pipeline()
        initial_state = {
            "user_text": user_text,
            "category_sub_list": category_sub_list,
            "openai_service": openai_service,
            "chromadb_service": chromadb_service,
        }
        final_state = await app.ainvoke(initial_state)
        return final_state.get("final_result", {})
    except Exception as e:
        logger.error(f"❌ 파이프라인 전체 실행 실패: {e}", exc_info=True)
        return {
            "pipeline_success": False,
            "error_message": f"파이프라인 실행 중 오류 발생: {str(e)}",
            "template_text": "", "template_title": "생성 실패", "variables": [],
            "generation_method": "error", "message_type": None, "category_sub": None,
            "category_analysis": None, "similarity_score": 0.0,
            "reference_templates": [], "public_templates": [],
        }

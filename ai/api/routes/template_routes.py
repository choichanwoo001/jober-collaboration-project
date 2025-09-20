# api/routes/template_routes.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from core.constants import APPROVED_SUB_CATEGORIES
from services.dependencies import get_openai_service, get_chromadb_service
from services.openai_service import OpenAIService
from services.chromadb_service import ChromaDBService
from templateEngine.pipeline import run_template_generation_pipeline

router = APIRouter(prefix="/template", tags=["Template Generation"])

# --- Pydantic 모델 ---
class GenerationRequest(BaseModel):
    userMessage: str

class GenerationResponse(BaseModel):
    pipeline_success: bool
    error_message: Optional[str] = None
    template_text: str
    template_title: str
    variables: List[str]
    generation_method: str
    message_type: Optional[str]
    category_sub: Optional[str]
    category_analysis: Optional[Dict]
    similarity_score: float
    reference_templates: List[Dict]
    pulblic_templates: List[Dict]

# --- 최종 API 엔드포인트 ---
@router.post("/generate", response_model=GenerationResponse)
async def generate_template_endpoint(
        request: GenerationRequest,
        openai_service: OpenAIService = Depends(get_openai_service),
        chromadb_service: ChromaDBService = Depends(get_chromadb_service)
):
    """
    LangGraph 기반의 지능형 템플릿 생성 파이프라인을 실행합니다.
    """
    try:
        result = await run_template_generation_pipeline(
            userMessage=request.userMessage,
            category_sub_list=APPROVED_SUB_CATEGORIES,
            openai_service=openai_service,
            chromadb_service=chromadb_service
        )
        return GenerationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API 엔드포인트 오류: {str(e)}")



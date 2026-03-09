# api/routes/template_routes.py

import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from core.database import get_db
from sqlalchemy.orm import Session
from core.database import get_db
import logging

from services.dependencies import get_openai_service, get_chromadb_service
from services.openai_service import OpenAIService
from services.category_service import CategoryService
from services.chromadb_service import ChromaDBService
from templateEngine.pipeline import run_template_generation_pipeline
from core.database import SessionLocal
from templateEngine.prompts.message_analyzer_prompts import PromptDefense, UnsuitableMessageError
from templateEngine.prompts.builders import SuitabilityCheckPromptBuilder

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

# --- 최종 API 엔드포인트 ---
@router.post("/generate", response_model=GenerationResponse)
async def generate_template_endpoint(
        request: GenerationRequest,
        db_session: Session = Depends(get_db), # db 세션 Depends로 주입
        openai_service: OpenAIService = Depends(get_openai_service),
        chromadb_service: ChromaDBService = Depends(get_chromadb_service)
):
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

    try:
        sanitize_userMessage = PromptDefense.sanitize_user_input(request.userMessage)

        # 적합성 검사 수행
        suitability_builder = SuitabilityCheckPromptBuilder(sanitize_userMessage)
        suitability_messages = suitability_builder.build()
        suitability_result = await openai_service.chat_completion(suitability_messages)
        
        # JSON 파싱하여 적합성 확인
        import json
        try:
            suitability_data = json.loads(suitability_result)
            if not suitability_data.get("is_suitable", True):
                # 부적합한 메시지인 경우 사용자 친화적인 에러 메시지 반환
                reason = suitability_data.get("reason", "메시지가 알림톡 템플릿 생성에 적합하지 않습니다.")
                
                # 사용자 친화적인 메시지로 변환
                if "욕설" in reason or "부적절한 언어" in reason:
                    user_message = "입력하신 내용에 부적절한 표현이 포함되어 있습니다. 다시 작성해 주세요."
                elif "무관한 내용" in reason:
                    user_message = "알림톡 템플릿과 관련 없는 내용입니다. 서비스 안내나 고객 소통 관련 내용으로 다시 작성해 주세요."
                else:
                    user_message = "입력하신 내용을 알림톡 템플릿으로 생성할 수 없습니다. 다시 작성해 주세요."
                
                raise HTTPException(status_code=400, detail=user_message)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 로그만 남기고 계속 진행
            logger.warning(f"적합성 검사 응답 파싱 실패: {suitability_result}")

        result = await run_template_generation_pipeline(
            userMessage=sanitize_userMessage,
            openai_service=openai_service,
            chromadb_service=chromadb_service,
            db_session=db_session  # <--- db_session을 전달합니다.
        )


        if not result.get("pipeline_success", False):
            # 파이프라인 내부에서 정상적으로 종료되었지만 실패한 경우
            raise HTTPException(status_code=400, detail=result.get("error_message", "템플릿 생성에 실패했습니다."))

        # 프론트엔드 형식에 맞게 변환
        response_data = {
            "template_content": result.get("template_text", ""),
            "variables": [
                {"name": var, "type": "string", "description": f"변수: {var}"}
                for var in result.get("variables", [])
            ],
            "category": result.get("category_sub") or "기타",
            "model": "gpt-4o-mini",
            "template_title": result.get("template_title", ""),
            "generation_method": result.get("generation_method", ""),
            "similarity_score": result.get("similarity_score", 0.0)
        }

        return GenerationResponse(**response_data)
    
    except UnsuitableMessageError as e:
        # 적합성 검사 실패 시, 400 에러와 함께 명확한 메시지 반환
        raise HTTPException(status_code=400, detail=str(e))
 
    except Exception as e:
        import traceback
        traceback.print_exc()
        # 사용자 친화적인 오류 메시지로 변경
        raise HTTPException(status_code=500, detail="템플릿 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")



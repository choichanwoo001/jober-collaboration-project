"""
알림톡 템플릿 검증 서비스
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from .chromadb_service import ChromaDBService

try:
    from .openai_service import OpenAIService
    HAS_OPENAI_SERVICE = True
except ImportError:
    HAS_OPENAI_SERVICE = False
    print("Warning: OpenAI 서비스를 로드할 수 없습니다. Mock 모드로 실행됩니다.")
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.alimtalk_models import (
    ValidationRequest, ValidationResponse, ValidationResult, SystemStats, ProblemArea
)
from validators.validator_pipeline import ValidationPipeline


class AlimtalkValidationService:
    """알림톡 검증 서비스"""
    
    def __init__(self):
        self.chromadb_service = ChromaDBService()
        self.openai_service = OpenAIService()  # AI 서비스 무조건 사용
        self.validation_pipeline = None
        self.is_initialized = False
        
    async def initialize(self):
        """
        알림톡 검증 서비스 초기화
        
        지연 초기화(Lazy Initialization) 패턴을 사용하여 서버 시작 시간을 단축하고,
        실제 검증 작업이 필요할 때만 무거운 초기화 작업을 수행합니다.
        
        초기화 과정:
        1. ChromaDB 서비스 초기화 - 벡터 데이터베이스 연결 및 컬렉션 준비
        2. 검증 파이프라인 구성 - 1차(제약) → 2차(의미적) 검증 순서 제어
        3. 의존성 주입 - 각 컴포넌트들을 연결하여 검증 워크플로우 구성
        
        중복 초기화 방지를 위해 is_initialized 플래그로 상태를 관리합니다.
        """
        if self.is_initialized:
            return
            
        # ChromaDB 초기화 - 정책 문서 및 승인된 템플릿 데이터 로드
        await self.chromadb_service.initialize()
        
        # 검증 파이프라인 초기화 - LLM 기반 제약 검증기와 의미적 검증기 연결
        from validators.constraint_validator import ConstraintValidator
        constraint_validator = ConstraintValidator()
        self.validation_pipeline = ValidationPipeline(
            chromadb_service=self.chromadb_service,
            constraint_validator=constraint_validator
        )
        
        self.is_initialized = True
        print(">>service<<")
        print("✅ 알림톡 검증 서비스 초기화 완료")
    
    async def validate_template(self, request: ValidationRequest) -> ValidationResponse:
        """템플릿 검증 실행"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 검증 실행
            template_data = request.template.dict()
            result = self.validation_pipeline.validate(template_data)
            
            # 응답 생성
            if result['final_result'].is_valid:
                final_message = "✅ 모든 검증을 통과했습니다. 발송 가능합니다."
                success = True
            else:
                error_count = len(result['final_result'].errors)
                warning_count = len(result['final_result'].warnings)
                final_message = f"❌ 검증 실패: {error_count}개 오류, {warning_count}개 경고"
                success = False
            
            # 결과 필터링 (None이 아닌 것만)
            validation_results = []
            if result.get('constraint_result'):
                validation_results.append(result['constraint_result'])
            if result.get('semantic_result'):
                validation_results.append(result['semantic_result'])
            if result.get('final_result'):
                validation_results.append(result['final_result'])
            
            # 문제 영역 생성
            problem_areas = []
            
            for result in validation_results:
                for error in result.errors:
                    # 문제 영역 생성
                    problem_area = await self._create_problem_area(
                        error, result.stage, request.template.template_content or ""
                    )
                    problem_areas.append(problem_area)
            
            # 오류 및 경고 개수 계산
            total_errors = sum(1 for area in problem_areas if area.severity == "error")
            total_warnings = sum(1 for area in problem_areas if area.severity == "warning")
            
            response = ValidationResponse(
                success=success,
                message=final_message,
                problem_areas=problem_areas,
                validation_stage=validation_results[0].stage if validation_results else "1차 검증",
                total_errors=total_errors,
                total_warnings=total_warnings
            )
            
            return response
            
        except Exception as e:
            return ValidationResponse(
                success=False,
                message=f"검증 중 오류가 발생했습니다: {str(e)}",
                problem_areas=[],
                validation_stage="오류",
                total_errors=0,
                total_warnings=0
            )
    
    async def _create_problem_area(self, error: str, stage: str, template_content: str) -> ProblemArea:
        """오류를 문제 영역으로 변환"""
        # 오류에서 문제 텍스트와 위치 추출
        problem_info = self._extract_problem_info(error, template_content)
        
        # 대안 생성
        alternatives = await self._generate_alternatives_for_error(error, stage, template_content)
        
        # 문제 영역 생성
        area_id = f"{stage}_{len(template_content)}_{hash(error) % 10000}"
        
        return ProblemArea(
            area_id=area_id,
            area_type=problem_info["area_type"],
            location=problem_info["location"],
            problem_text=problem_info["problem_text"],
            start_position=problem_info.get("start_position"),
            end_position=problem_info.get("end_position"),
            error_type=self._get_error_type_from_stage(stage),
            severity=self._get_severity_from_error(error),
            reason=error,
            suggestion="AI에서 생성된 수정 제안을 참고해주세요",
            alternatives=alternatives
        )
    
    def _extract_problem_info(self, error: str, template_content: str) -> Dict[str, Any]:
        """오류에서 문제 정보 추출"""
        # 기본값 설정
        problem_info = {
            "area_type": "entire_template",
            "location": "전체",
            "problem_text": template_content[:100] + "..." if len(template_content) > 100 else template_content
        }
        
        # 오류 내용에서 문제 텍스트 추출 시도
        if "전기세를 아끼고 효율을 극대화하세요" in error:
            problem_info.update({
                "area_type": "specific_text",
                "location": "전기세 절감 문구",
                "problem_text": "전기세를 아끼고 효율을 극대화하세요"
            })
        elif "고객님께서 사전에 고장 체크를 해보시고" in error:
            problem_info.update({
                "area_type": "paragraph",
                "location": "A/S 권장 문단",
                "problem_text": "고객님께서 사전에 고장 체크를 해보시고, 이상이 있을 경우 미리 서비스를 받아 불편함이 없도록 하시기 바랍니다"
            })
        elif "겨울철 장수돌침대 사용량 증가" in error:
            problem_info.update({
                "area_type": "paragraph",
                "location": "겨울철 안내 문단",
                "problem_text": "겨울철 장수돌침대 사용량 증가로 A/S 및 사전점검 일정을 미리 준비하여"
            })
        elif "변수가 사용되지 않음" in error:
            problem_info.update({
                "area_type": "entire_template",
                "location": "전체 템플릿",
                "problem_text": "변수가 전혀 사용되지 않음"
            })
        elif "미리보기 메시지" in error:
            problem_info.update({
                "area_type": "entire_template",
                "location": "미리보기 영역",
                "problem_text": "미리보기 메시지 누락"
            })
        
        return problem_info
    
    def _get_error_type_from_stage(self, stage: str) -> str:
        """검증 단계에서 오류 타입 추출"""
        if "constraint" in stage:
            return "constraint_validation"
        elif "semantic" in stage:
            return "semantic_validation"
        else:
            return "general_validation"
    
    def _get_severity_from_error(self, error: str) -> str:
        """오류에서 심각도 추출"""
        if "❌" in error or "오류" in error:
            return "error"
        elif "⚠️" in error or "경고" in error:
            return "warning"
        else:
            return "error"  # 기본값
    
    async def _generate_alternatives_for_error(self, error: str, stage: str, template_content: str = "") -> List[str]:
        """AI를 활용한 오류별 동적 대안 생성"""
        # 프롬프트 파일에서 대안 생성 프롬프트 가져오기
        from validators.prompts import get_alternative_generation_prompt
        
        prompt = get_alternative_generation_prompt(stage, error, template_content)
        response = await self.openai_service.generate_response(prompt)
        
        # 응답에서 대안 추출
        alternatives = self._extract_alternatives_from_response(response)
        
        # 대안이 3개 미만이면 기본 대안으로 보완
        if len(alternatives) < 3:
            default_alternatives = self._get_default_alternatives(error, stage)
            alternatives.extend(default_alternatives[:3-len(alternatives)])
        
        return alternatives[:3]  # 최대 3개까지만 반환
    
    def _extract_alternatives_from_response(self, response: str) -> List[str]:
        """AI 응답에서 대안 추출"""
        alternatives = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('대안') and ':' in line:
                alternative = line.split(':', 1)[1].strip()
                if alternative and len(alternative) > 10:  # 너무 짧은 대안 제외
                    alternatives.append(alternative)
        
        return alternatives
    
    def _get_default_alternatives(self, error: str, stage: str) -> List[str]:
        """기본 대안 생성 (AI 실패 시 사용)"""
        if "정보성 메시지" in error:
            return [
                "광고성 표현을 제거하고 순수 정보 전달 형태로 수정",
                "객관적이고 중립적인 톤으로 템플릿 재작성",
                "특정 행위 유도 문구를 안내성 표현으로 변경"
            ]
        elif "정형화된 템플릿" in error:
            return [
                "표준 알림톡 구조로 템플릿 재구성",
                "일관된 패턴의 정형화된 템플릿으로 수정",
                "계절/상황별 표현을 일반적 표현으로 변경"
            ]
        elif "변수 사용" in error:
            return [
                "개인화 변수를 포함한 템플릿으로 재작성",
                "동적 변수 활용한 맞춤형 메시지로 변경",
                "변수 규칙에 맞는 표준 템플릿으로 수정"
            ]
        elif "템플릿 작성" in error:
            return [
                "미리보기 메시지가 포함된 완전한 템플릿으로 재작성",
                "서비스 광고 문구 제거한 순수 안내 템플릿으로 변경",
                "알림톡 작성 가이드라인 준수 템플릿으로 수정"
            ]
        else:
            return [
                "알림톡 승인 기준에 맞는 완전한 템플릿으로 재작성",
                "검증 통과 가능한 표준 템플릿으로 전면 수정",
                "카카오 알림톡 가이드라인 준수 템플릿으로 변경"
            ]




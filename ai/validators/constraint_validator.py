"""
1차 검증: 제약 검증 (알림톡 승인 규칙 기반)
LLM을 활용한 동적 규칙 검증 시스템

이 모듈은 템플릿 검증 파이프라인의 첫 번째 단계로, 다음과 같은 검증을 수행합니다:
1. 정보성 메시지 요건 검증
2. 변수 사용 규칙 검증
3. 기타 템플릿 작성 규칙 검증
"""
import re
from typing import Dict, Any, List
import json
import logging

# 상대 임포트 시도 (패키지 내부에서 실행될 때) / main.py
try:
    from ..models.alimtalk_models import ValidationResult
    from ..services.openai_service import OpenAIService
    from .prompts.informational_message_prompt import get_informational_message_validation_prompt
    from .prompts.variable_usage_prompt import get_variable_usage_validation_prompt
    from .prompts.template_writing_prompt import get_template_writing_validation_prompt
except ImportError:
    # 절대 임포트 (단독 실행될 때) / validators/constraint_validator.py
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.alimtalk_models import ValidationResult
    from services.openai_service import OpenAIService
    from validators.prompts.informational_message_prompt import get_informational_message_validation_prompt
    from validators.prompts.variable_usage_prompt import get_variable_usage_validation_prompt
    from validators.prompts.template_writing_prompt import get_template_writing_validation_prompt

logger = logging.getLogger(__name__)

class ConstraintValidator:
    """
    템플릿 제약사항 검증을 담당하는 클래스
    
    알림톡 승인 규칙을 기반으로 LLM을 활용한 동적 검증을 수행합니다.
    """
    
    def __init__(self):
        """
        ConstraintValidator 초기화
        """
        try:
            self.openai_service = OpenAIService()
            logger.info("✅ ConstraintValidator 초기화 완료 (LLM 기반)")
        except Exception as e:
            logger.exception("❌ ConstraintValidator 초기화 실패")
            raise

    def validate(self, template_data: Dict[str, Any]) -> ValidationResult:
        """
        1차 검증: 알림톡 승인 규칙 기반 검증 (내부 검증 단계는 비동기 병렬 처리)
        
        검증 규칙:
        1. 정보성 메시지 요건
        2. 변수 사용 규칙
        3. 기타 템플릿 작성 규칙
        
        Args:
            template_data: 검증할 템플릿 데이터
                - template_content: 템플릿 텍스트 내용
                - template_title: 템플릿 제목
                - variables: 변수 정의 리스트 (List[Dict[str, str]])
                - category: 템플릿 카테고리
                - detected_variables: 이미 추출된 변수 리스트
                - model: 사용된 모델명
        
        Returns:
            ValidationResult: 검증 결과 객체
        """
        logger.info("🔍 1차 검증 시작: 알림톡 승인 규칙 검증 (병렬 처리)")
        logger.debug(f"입력 데이터 keys: {list(template_data.keys())}")

        try:
            # 3개 검증 단계를 비동기로 병렬 실행
            import asyncio
            
            # 현재 이벤트 루프가 실행 중인지 확인
            try:
                loop = asyncio.get_running_loop()
                # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
                import concurrent.futures
                
                def run_in_thread():
                    return asyncio.run(self._run_async_validations(template_data))
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    results = future.result()
            except RuntimeError:
                # 실행 중인 루프가 없으면 새 루프 생성
                results = asyncio.run(self._run_async_validations(template_data))
            
            # 결과 처리
            errors = []
            warnings = []
            rejected_variables = []
            validation_details = []
            
            # 각 검증 결과를 순서대로 처리
            step_names = ["정보성 메시지", "변수 사용 규칙", "기타 템플릿 작성"]
            
            for i, (step_name, result) in enumerate(zip(step_names, results), 1):
                if isinstance(result, Exception):
                    # 오류 발생 시
                    error_msg = f"{step_name} 검증 중 오류가 발생했습니다."
                    warnings.append(error_msg)
                    logger.warning(f"[{i}단계] {step_name} 검증 실패: {str(result)}")
                    print(f"⚠️ [{i}단계] {step_name} 경고 1개:")
                    print(f"   1. {error_msg}")
                else:
                    # 정상 결과
                    step_errors, step_warnings, step_details = result[:3]
                    errors.extend(step_errors)
                    warnings.extend(step_warnings)
                    validation_details.extend(step_details)
                    
                    # 변수 검증 결과인 경우 반려된 변수도 추가
                    if len(result) > 3:
                        rejected_variables.extend(result[3])
                    
                    # 단계별 결과 로그
                    if step_errors:
                        print(f"❌ [{i}단계] {step_name} 오류 {len(step_errors)}개:")
                        for j, error in enumerate(step_errors, 1):
                            print(f"   {j}. {error}")
                    if step_warnings:
                        print(f"⚠️ [{i}단계] {step_name} 경고 {len(step_warnings)}개:")
                        for j, warning in enumerate(step_warnings, 1):
                            print(f"   {j}. {warning}")
                    if len(result) > 3 and result[3]:  # 반려된 변수가 있는 경우
                        print(f"🚫 [{i}단계] 반려된 변수 {len(result[3])}개: {result[3]}")
                    if not step_errors and not step_warnings:
                        print(f"✅ [{i}단계] {step_name} 검증 통과")

            # 최종 결과
            is_valid = len(errors) == 0
            print(f"\n📋 1차 검증 최종 결과:")
            print(f"   ✅ 통과 여부: {'통과' if is_valid else '실패'}")
            print(f"   ❌ 총 오류: {len(errors)}개")
            print(f"   ⚠️ 총 경고: {len(warnings)}개")
            print(f"   🚫 반려된 변수: {len(rejected_variables)}개")
            
            logger.info(f"✅ 1차 검증 완료 → valid={is_valid}, 총 오류={len(errors)}, 총 경고={len(warnings)}")

            return ValidationResult(
                is_valid=is_valid,
                stage="constraint",
                errors=errors,
                warnings=warnings,
                details={
                    "validation_type": "alimtalk_approval_rules_parallel",
                    "total_errors": len(errors),
                    "total_warnings": len(warnings),
                    "rejected_variables": rejected_variables,
                    "validation_details": validation_details,
                    "rules_checked": [
                        "informational_message_requirements",
                        "variable_usage_rules",
                        "other_template_rules"
                    ]
                }
            )

        except Exception as e:
            logger.exception("❌ 1차 검증 중 예외 발생")
            return ValidationResult(
                is_valid=False,
                stage="constraint",
                errors=[f"1차 검증 중 오류 발생: {str(e)}"],
                warnings=[],
                details={"exception": str(e)}
            )

    async def _run_async_validations(self, template_data: Dict[str, Any]) -> List:
        """
        4개 검증 단계를 비동기로 병렬 실행
        
        Args:
            template_data: 검증할 템플릿 데이터
            
        Returns:
            List: 각 검증 단계의 결과 리스트
        """
        import asyncio
        
        # 3개 검증을 병렬로 실행
        tasks = [
            self._check_informational_message_requirements_async(template_data),
            self._check_variable_usage_rules_async(template_data),
            self._check_other_template_rules_async(template_data)
        ]
        
        # 모든 검증을 병렬로 실행 (오류가 발생해도 다른 검증은 계속 진행)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def _check_informational_message_requirements_async(self, template_data: Dict[str, Any]) -> tuple[List[str], List[str], List[Dict[str, Any]]]:
        """정보성 메시지 요건 검증 (비동기 버전)"""
        errors, warnings, details = [], [], []
        
        # 검증 대상 데이터 추출 (카테고리, 제목, 내용)
        templateContent = template_data.get('template_content', '')
        templateTitle = template_data.get('template_title', '')
        category = template_data.get('category', '')
        
        try:
            prompt = get_informational_message_validation_prompt(category, templateTitle, templateContent)
            
            # 비동기 함수 호출
            response = await self.openai_service.chat_completion([
                {"role": "system", "content": """알림톡 템플릿 정보성 메시지 요건 검증 전문가입니다.

🔍 **검증 원칙**:
1. 규칙을 정확히 이해하고 적용하세요
2. 모호한 부분은 허용하는 방향으로 판단하세요
3. 명확한 위반 사항만 오류로 분류하세요
4. 광고성 메시지와 정보성 메시지를 정확히 구분하세요

⚠️ **중요**: 
- 서비스 이용에 필요한 안내는 허용됩니다
- 일반적인 인사말과 정중한 표현은 허용됩니다
- 쿠폰 발급이 서비스 이용 과정의 일부라면 허용될 수 있습니다
- **제품 관리 조언이나 서비스 이용 안내는 허용됩니다** (예: "정기적인 유지보수와 관리로 제품의 수명과 효율을 극대화하세요")
- **"혜택 암시"는 문제가 되지 않습니다** - 구체적인 혜택 제공만 금지됩니다

JSON 형식으로만 응답하세요."""},
                {"role": "user", "content": prompt}
            ])
            
            try:
                result = json.loads(response)
                if not result.get('is_valid', True):
                    for violation in result.get('violations', []):
                        message = f"정보성 메시지 요건 위반: {violation.get('reason', '알 수 없는 사유')}"
                        if violation.get('severity') == 'error':
                            errors.append(message)
                        else:
                            warnings.append(message)
                        details.append({
                            "rule_type": "informational_message",
                            "rule": violation.get('rule', '알 수 없는 규칙'),
                            "reason": violation.get('reason', '알 수 없는 사유'),
                            "suggestion": violation.get('suggestion', '수정이 필요합니다'),
                            "severity": violation.get('severity', 'error')
                        })
            except json.JSONDecodeError:
                warnings.append("정보성 메시지 검증 응답 파싱 중 오류가 발생했습니다.")
                
        except Exception as e:
            # 시스템 오류는 로그에만 기록하고 사용자에게는 일반적인 메시지만 표시
            logger.warning(f"정보성 메시지 검증 중 예외 발생: {str(e)}")
            warnings.append("정보성 메시지 검증 중 오류가 발생했습니다.")
        
        return errors, warnings, details


    async def _check_variable_usage_rules_async(self, template_data: Dict[str, Any]) -> tuple[List[str], List[str], List[Dict[str, Any]], List[str]]:
        """변수 사용 규칙 검증 (비동기 버전)"""
        errors, warnings, details = [], [], []
        rejected_variables = []
        
        templateContent = template_data.get('template_content', '')
        variables = template_data.get('variables', [])
        detected_variables = template_data.get('detected_variables', [])
        
        # variables에서 변수명만 추출 (List[Dict[str, str]] 형태)
        if variables and isinstance(variables[0], dict):
            variable_names = [var.get("name", "") for var in variables if isinstance(var, dict)]
        else:
            variable_names = variables
        
        try:
            prompt = get_variable_usage_validation_prompt(templateContent, detected_variables, variable_names)
            
            # 비동기 함수 호출
            response = await self.openai_service.chat_completion([
                {"role": "system", "content": """알림톡 템플릿 변수 사용 규칙 검증 전문가입니다.

🔍 **검증 원칙**:
1. 변수 사용 규칙을 정확히 이해하고 적용하세요
2. 템플릿 본문의 변수 사용은 정상입니다
3. 버튼명과 미리보기 메시지만 변수 사용 불가입니다
4. 모호한 부분은 허용하는 방향으로 판단하세요

⚠️ **중요 구분**:
- ✅ 템플릿 본문: 변수 사용 가능 (예: "안녕하세요, {{고객명}}님")
- ❌ 버튼명: 변수 사용 불가 (예: "{{쿠폰명}} 확인하기")
- ❌ 미리보기: 변수 사용 불가 (예: "{{고객명}}님을 위한 혜택")

**현재 템플릿**: 버튼명이나 미리보기 메시지가 없으므로 버튼/미리보기 변수 사용 검증은 적용하지 마세요!

🎯 **정확한 판단 기준**:
- 변수 개수가 40개 초과 시에만 오류
- 템플릿이 변수로만 구성된 경우에만 오류 (일반 텍스트가 전혀 없는 경우)
- 버튼명/미리보기에 변수가 있는 경우에만 오류

**중요**: "안녕하세요, #{{회원님}}님. #{{올워크}}에서..."와 같이 일반 텍스트와 변수가 혼합된 템플릿은 정상입니다!

JSON 형식으로만 응답하세요."""},
                {"role": "user", "content": prompt}
            ])
            
            try:
                result = json.loads(response)
                if not result.get('is_valid', True):
                    for violation in result.get('violations', []):
                        message = f"변수 사용 규칙 위반: {violation.get('reason', '알 수 없는 사유')}"
                        if violation.get('severity') == 'error':
                            errors.append(message)
                        else:
                            warnings.append(message)
                        
                        # 변수 관련 오류인 경우 반려 변수 목록에 추가
                        if violation.get('variable_name'):
                            rejected_variables.append(violation.get('variable_name'))
                        
                        details.append({
                            "rule_type": "variable_usage",
                            "rule": violation.get('rule', '알 수 없는 규칙'),
                            "reason": violation.get('reason', '알 수 없는 사유'),
                            "suggestion": violation.get('suggestion', '수정이 필요합니다'),
                            "severity": violation.get('severity', 'error'),
                            "variable_name": violation.get('variable_name')
                        })
            except json.JSONDecodeError:
                warnings.append("변수 사용 규칙 검증 응답 파싱 중 오류가 발생했습니다.")
                
        except Exception as e:
            # 시스템 오류는 로그에만 기록하고 사용자에게는 일반적인 메시지만 표시
            logger.warning(f"변수 사용 규칙 검증 중 예외 발생: {str(e)}")
            warnings.append("변수 사용 규칙 검증 중 오류가 발생했습니다.")
        
        return errors, warnings, details, rejected_variables

    async def _check_other_template_rules_async(self, template_data: Dict[str, Any]) -> tuple[List[str], List[str], List[Dict[str, Any]]]:
        """기타 템플릿 작성 규칙 검증 (비동기 버전)"""
        errors, warnings, details = [], [], []
        
        # 검증 대상 데이터 추출 (제목, 내용)
        templateContent = template_data.get('template_content', '')
        templateTitle = template_data.get('template_title', '')
        
        try:
            prompt = get_template_writing_validation_prompt(templateTitle, templateContent)
            
            # 비동기 함수 호출
            response = await self.openai_service.chat_completion([
                {"role": "system", "content": """알림톡 템플릿 작성 규칙 검증 전문가입니다.

🔍 **검증 원칙**:
1. 템플릿 작성 규칙을 정확히 이해하고 적용하세요
2. 일반적인 인사말과 정중한 표현은 허용됩니다
3. 강한 광고성 표현만 금지 대상입니다
4. 모호한 부분은 허용하는 방향으로 판단하세요

⚠️ **허용되는 표현**:
- "많은 이용 부탁드립니다", "감사합니다" (일반적인 인사말)
- "서비스 이용 안내드립니다" (내용과 관련된 안내)
- 정중하고 적절한 서비스 안내 문구

❌ **금지되는 표현**:
- "지금 바로", "특별 할인", "무료 체험" (강한 광고성)
- 템플릿 내용과 전혀 무관한 문구

🎯 **연령인증 관련**:
- 템플릿에 "연령인증", "성인인증", "19세 이상" 등의 표현이 **있을 때만** 검토
- 해당 표현이 **없으면** 이 규칙은 적용하지 마세요
- 연령인증 관련 표현이 없는 템플릿에서 "연령인증 관련 표현이 포함되어 있지 않음" 오류를 발생시키지 마세요

JSON 형식으로만 응답하세요."""},
                {"role": "user", "content": prompt}
            ])
            
            try:
                result = json.loads(response)
                if not result.get('is_valid', True):
                    for violation in result.get('violations', []):
                        message = f"템플릿 작성 규칙 위반: {violation.get('reason', '알 수 없는 사유')}"
                        if violation.get('severity') == 'error':
                            errors.append(message)
                        else:
                            warnings.append(message)
                        details.append({
                            "rule_type": "template_writing",
                            "rule": violation.get('rule', '알 수 없는 규칙'),
                            "reason": violation.get('reason', '알 수 없는 사유'),
                            "suggestion": violation.get('suggestion', '수정이 필요합니다'),
                            "severity": violation.get('severity', 'error')
                        })
            except json.JSONDecodeError:
                warnings.append("기타 템플릿 작성 규칙 검증 응답 파싱 중 오류가 발생했습니다.")
                
        except Exception as e:
            # 시스템 오류는 로그에만 기록하고 사용자에게는 일반적인 메시지만 표시
            logger.warning(f"기타 템플릿 작성 규칙 검증 중 예외 발생: {str(e)}")
            warnings.append("기타 템플릿 작성 규칙 검증 중 오류가 발생했습니다.")
        
        return errors, warnings, details


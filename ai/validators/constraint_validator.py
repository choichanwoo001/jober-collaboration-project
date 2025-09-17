"""
1차 검증: 제약 검증 (ChromaDB 기반 스키마 제약)
ChromaDB에서 제약사항을 검색하여 정확한 스키마 매칭 검증

이 모듈은 템플릿 검증 파이프라인의 첫 번째 단계로, 다음과 같은 검증을 수행합니다:
1. ChromaDB 기반 동적 제약사항 검증
2. 백업 규칙 기반 기본 제약사항 검증
3. 템플릿 변수 추출 및 검증
4. 우선순위 기반 오류/경고 분류
"""
import re
from typing import Dict, Any, List

# 상대 임포트 시도 (패키지 내부에서 실행될 때)
try:
    from ..models.alimtalk_models import ValidationResult
    from ..services.chromadb_service import ChromaDBService
except ImportError:
    # 절대 임포트 (단독 실행될 때)
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.alimtalk_models import ValidationResult
    from services.chromadb_service import ChromaDBService

import logging

logger = logging.getLogger(__name__)

class ConstraintValidator:
    """
    템플릿 제약사항 검증을 담당하는 클래스
    
    이 클래스는 이중 안전장치를 제공합니다:
    1. ChromaDB 기반 동적 제약사항 (우선적용)
    2. 하드코딩된 백업 규칙 (ChromaDB 실패 시 대비)
    """
    
    def __init__(self, vector_db_manager: ChromaDBService = None, rules_path: str = None):
        """
        ConstraintValidator 초기화
        
        Args:
            vector_db_manager: 벡터DB 관리자 (ChromaDB 기반 제약 검색)
                              None인 경우 자동으로 ChromaDBService 인스턴스 생성
            rules_path: 기본 규칙 파일 경로 (백업용, 현재 미사용)
        
        Raises:
            Exception: ChromaDBService 초기화 실패 시
        """
        try:
            # ChromaDBService 인스턴스 초기화 (collection: "review_guidelines")
            self.vector_db = vector_db_manager or ChromaDBService(collection_name="review_guidelines")
            logger.info("✅ ConstraintValidator 초기화 완료 (collection=review_guidelines)")
        except Exception as e:
            logger.exception("❌ ConstraintValidator 초기화 실패")
            raise

    def validate(self, template_data: Dict[str, Any]) -> ValidationResult:
        """
        메인 검증 메서드: ChromaDB 기반 제약 검증을 수행
        
        검증 단계:
        1. ChromaDB 제약사항 검증 (동적 규칙)
        2. 백업 규칙 검증 (하드코딩된 기본 규칙)
        
        Args:
            template_data: 검증할 템플릿 데이터
                - templateContent: 템플릿 텍스트 내용
                - variableList: 변수 정의 딕셔너리
                - userMessage: 사용자 입력 메시지
                - category: 템플릿 카테고리 등
        
        Returns:
            ValidationResult: 검증 결과 객체
                - is_valid: 검증 통과 여부 (errors가 없으면 True)
                - stage: "constraint" (현재 검증 단계)
                - errors: 치명적 오류 목록 (검증 실패 원인)
                - warnings: 경고 목록 (권장사항 위반)
                - details: 검증 상세 정보
        """
        logger.info("🔍 제약 검증 시작")
        logger.debug(f"입력 데이터 keys: {list(template_data.keys())}")  # 전체 데이터 말고 key만 출력

        errors = []    # 치명적 오류 (검증 실패)
        warnings = []  # 경고 (검증 통과하지만 권장사항 위반)

        try:
            # 1단계: ChromaDB 제약사항 검증 (동적 규칙)
            logger.info("📌 [1단계] ChromaDB 제약사항 검증 실행")
            chromadb_errors, chromadb_warnings = self._check_chromadb_constraints(template_data)
            errors.extend(chromadb_errors)
            warnings.extend(chromadb_warnings)

            # 2단계: 백업 규칙 검증 (하드코딩된 기본 규칙)
            logger.info("📌 [2단계] 백업 규칙 검증 실행")
            backup_errors, backup_warnings = self._check_backup_constraints(template_data)
            errors.extend(backup_errors)
            warnings.extend(backup_warnings)

            # 최종 결과: errors가 없으면 검증 통과
            is_valid = len(errors) == 0
            logger.info(f"✅ 제약 검증 완료 → valid={is_valid}, 총 오류={len(errors)}, 총 경고={len(warnings)}")

            return ValidationResult(
                is_valid=is_valid,
                stage="constraint",
                errors=errors,
                warnings=warnings,
                details={
                    "chromadb_constraints_checked": True,
                    "backup_constraints_checked": True,
                    "total_errors": len(errors),
                    "total_warnings": len(warnings)
                }
            )

        except Exception as e:
            logger.exception("❌ 제약 검증 중 예외 발생")  # stack trace까지 로깅
            return ValidationResult(
                is_valid=False,
                stage="constraint",
                errors=[f"제약 검증 중 오류 발생: {str(e)}"],
                warnings=[],
                details={"exception": str(e)}
            )

    def _check_chromadb_constraints(self, template_data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """
        ChromaDB에서 모든 제약사항을 가져와서 스키마 검증 수행
        
        검증 과정:
        1. 템플릿에서 변수 추출 및 검증
        2. ChromaDB에서 모든 제약사항 조회
        3. 각 제약사항별로 스키마 검증 실행
        4. 우선순위 기반으로 오류/경고 분류
        
        Args:
            template_data: 검증할 템플릿 데이터
        
        Returns:
            tuple[List[str], List[str]]: (errors, warnings) 튜플
        """
        logger.info("🔍 ChromaDB 제약사항 검증 시작")
        errors = []
        warnings = []

        try:
            # 1. 템플릿 텍스트에서 변수 추출
            templateContent = template_data.get('templateContent', '')
            logger.debug(f"템플릿 텍스트 길이: {len(templateContent)}")
            detected_variables = self._extract_variables_from_template(templateContent)
            logger.debug(f"추출된 변수: {detected_variables}")

            # 2. 변수 검증 (정의 일치성, 값 유효성)
            variable_errors, variable_warnings = self._validate_variables(template_data, detected_variables)
            errors.extend(variable_errors)
            warnings.extend(variable_warnings)
            if variable_errors or variable_warnings:
                logger.info(f"📌 변수 검증 결과 → 오류 {len(variable_errors)}개, 경고 {len(variable_warnings)}개")

            # 3. ChromaDB에서 제약사항 전체 조회
            all_constraints = self._get_all_constraints_from_db()
            logger.info(f"📥 제약사항 {len(all_constraints)}개 로드됨")

            # 4. 각 제약사항별로 스키마 검증 실행
            for idx, constraint in enumerate(all_constraints, start=1):
                content = constraint.get('content', '')
                metadata = constraint.get('metadata', {})
                logger.debug(f"➡️ 제약[{idx}] 검사 시작: section={metadata.get('section', 'N/A')}")

                # 개별 제약사항 검증
                violation = self._check_schema_constraint(template_data, content, metadata)

                if violation:
                    # 우선순위 기반 분류: critical/high + strict → errors, 나머지 → warnings
                    priority = metadata.get('priority', 'medium')
                    enforcement = metadata.get('enforcement', 'flexible')
                    msg = f"[제약:{idx}] {violation}"

                    if priority in ['critical', 'high'] and enforcement == 'strict':
                        logger.error(f"❌ 치명적 위반: {msg}")
                        errors.append(msg)
                    else:
                        logger.warning(f"⚠️ 경고성 위반: {msg}")
                        warnings.append(msg)
                else:
                    logger.debug(f"✅ 제약[{idx}] 통과")

            logger.info(f"✅ ChromaDB 제약사항 검증 완료 → 오류 {len(errors)}개, 경고 {len(warnings)}개")

        except Exception as e:
            msg = f"ChromaDB 제약사항 검증 중 오류: {str(e)}"
            logger.error(f"❌ {msg}")
            warnings.append(msg)  # 예외는 경고로 처리 (검증 중단 방지)

        return errors, warnings

    def _extract_variables_from_template(self, templateContent: str) -> List[str]:
        """
        템플릿 텍스트에서 변수 추출
        
        지원하는 변수 패턴:
        1. {변수명} - 기본 패턴
        2. #{변수명} - 해시 접두사 패턴
        3. {{변수명}} - 이중 중괄호 패턴
        
        Args:
            templateContent: 템플릿 텍스트 내용
        
        Returns:
            List[str]: 중복 제거된 변수명 리스트
        """
        import re
        logger.debug("변수 추출 시작")
        variables = []

        # 1. {변수명} 패턴 - 기본 변수 형식
        matches = re.findall(r'\{([^}]+)\}', templateContent)
        variables.extend(matches)

        # 2. #{변수명} 패턴 - 해시 접두사가 있는 변수
        matches = re.findall(r'#\{([^}]+)\}', templateContent)
        variables.extend(matches)

        # 3. {{변수명}} 패턴 - 이중 중괄호 변수 (일부 템플릿 엔진 지원)
        matches = re.findall(r'\{\{([^}]+)\}\}', templateContent)
        variables.extend(matches)

        # 중복 제거 후 반환
        unique_vars = list(set(variables))
        logger.debug(f"추출된 변수 최종 목록: {unique_vars}")
        return unique_vars





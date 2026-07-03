"""
문제 영역 추출을 위한 프롬프트
"""

def get_problem_extraction_prompt(template_content: str, error_text: str) -> str:
    """
    AI를 사용해서 문제 영역을 추출하기 위한 프롬프트 생성
    
    Args:
        template_content: 검증 대상 템플릿 내용
        error_text: 오류 메시지
        
    Returns:
        AI에게 전달할 프롬프트 문자열
    """
    return f"""
알림톡 템플릿 검증 오류를 분석해주세요.

템플릿 내용:
{template_content}

오류 메시지:
{error_text}

다음 JSON 형식으로 응답해주세요:
{{
    "area_type": "specific_text" | "paragraph" | "entire_template",
    "location": "사용자 친화적인 위치 설명",
    "problem_text": "문제가 된 실제 텍스트 (템플릿에서 찾아서)",
    "search_methods": {{
        "exact_text": "정확히 일치하는 텍스트",
        "context_before": "문제 텍스트 앞의 문맥 (10-20자)",
        "context_after": "문제 텍스트 뒤의 문맥 (10-20자)",
        "regex_pattern": "정규표현식 패턴 (필요시)",
        "approximate_position": 대략적인_위치_숫자
    }}
}}

area_type 가이드:
- specific_text: 특정 문구나 단어 문제
- paragraph: 문단 전체 문제  
- entire_template: 전체 템플릿 문제

location은 사용자가 이해하기 쉬운 한국어로 설명해주세요.
problem_text는 템플릿에서 실제로 문제가 되는 부분을 정확히 찾아서 복사해주세요.

search_methods는 문제 텍스트를 정확히 찾기 위한 여러 방법을 제공합니다:
- exact_text: 문제가 되는 정확한 텍스트 (필수)
- context_before: 문제 텍스트 바로 앞의 문맥 (10-20자 정도)
- context_after: 문제 텍스트 바로 뒤의 문맥 (10-20자 정도)  
- regex_pattern: 복잡한 패턴이 필요한 경우 정규표현식
- approximate_position: 대략적인 위치 (참고용, 0부터 시작)

전체 템플릿 문제인 경우:
- exact_text: "전체 템플릿"
- context_before: null
- context_after: null
- approximate_position: 0

예시:
- area_type: "specific_text", location: "제품명 부분", problem_text: "장수돌침대", 
  search_methods: {{"exact_text": "장수돌침대", "context_before": "안녕하세요, ", "context_after": "입니다.", "approximate_position": 15}}
- area_type: "paragraph", location: "A/S 안내 문단", problem_text: "고객님께서 사전에...", 
  search_methods: {{"exact_text": "고객님께서 사전에...", "context_before": "문의사항이 있으시면", "context_after": "연락주세요", "approximate_position": 50}}
- area_type: "entire_template", location: "전체 템플릿", problem_text: "변수가 전혀 사용되지 않음", 
  search_methods: {{"exact_text": "전체 템플릿", "context_before": null, "context_after": null, "approximate_position": 0}}
"""

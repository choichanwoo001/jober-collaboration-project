// 템플릿 검증 관련 상수 정의

// ============================================
// 동작 기반 패턴 정의 (카테고리 독립적)
// ============================================

// 제거 동작을 나타내는 일반 패턴
export const REMOVAL_ACTION_PATTERNS = [
  // "X는/은/를/을 삭제/제거" 형태
  /(.+?)[는은를을이가]\s*(삭제|제거|없애|빼)/i,
  // "X 삭제/제거" 형태
  /(.+?)\s*(삭제|제거|없애|빼)/i,
  // "구체적인 X는/은 언급하지 않는다" 형태
  /구체적인\s*(.+?)[는은]\s*(언급|말)하지\s*않/i,
  // "X는/은 언급하지 않는다" 형태
  /(.+?)[는은]\s*(언급|말)하지\s*않/i,
  // "X 부분 삭제/제거" 형태
  /(.+?)\s*부분\s*(삭제|제거)/i,
  // "X가 없어야 한다" 형태
  /(.+?)[가이]\s*없어야\s*한/i,
  // "X를 없앤다" 형태
  /(.+?)[를을]\s*(없앤|제거한|삭제한)/i
]

// 추가/수정 동작을 나타내는 일반 패턴
export const MODIFICATION_ACTION_PATTERNS = [
  // "X를/을 추가" 형태
  /(.+?)[를을]\s*추가/i,
  // "X 추가" 형태
  /(.+?)\s*추가/i,
  // "X를/을 강조" 형태
  /(.+?)[를을]\s*강조/i,
  // "X 강조" 형태
  /(.+?)\s*강조/i,
  // "X를/을 변경/수정" 형태
  /(.+?)[를을]\s*(변경|수정|교체)/i,
  // "X로 변경/수정" 형태
  /(.+?)로\s*(변경|수정|교체)/i
]

// 일반적인 주제 키워드 추출 패턴
export const SUBJECT_EXTRACTION_PATTERN = /(.+?)[는은를을이가]\s/

/**
 * 주어진 텍스트에서 제거 동작과 대상 주제를 추출
 * @param text - 분석할 텍스트
 * @returns { action: 'remove', subject: string } | null
 */
export function extractRemovalAction(text: string): { action: 'remove', subject: string } | null {
  for (const pattern of REMOVAL_ACTION_PATTERNS) {
    const match = text.match(pattern)
    if (match && match[1]) {
      // 주제 정제 (불필요한 수식어 제거)
      const subject = match[1]
        .trim()
        .replace(/^(구체적인|특정|상세한|자세한)\s*/, '')
        .replace(/\s*(부분|내용|항목)$/, '')
      return { action: 'remove', subject }
    }
  }
  return null
}

/**
 * 주어진 텍스트에서 추가/수정 동작과 대상 주제를 추출
 * @param text - 분석할 텍스트
 * @returns { action: 'modify', subject: string } | null
 */
export function extractModificationAction(text: string): { action: 'modify', subject: string } | null {
  for (const pattern of MODIFICATION_ACTION_PATTERNS) {
    const match = text.match(pattern)
    if (match && match[1]) {
      const subject = match[1]
        .trim()
        .replace(/^(구체적인|특정|상세한|자세한)\s*/, '')
      return { action: 'modify', subject }
    }
  }
  return null
}

/**
 * 동적으로 패턴 생성 - 특정 주제에 대한 제거 패턴들을 생성
 * @param subject - 대상 주제 (예: "할인율", "문의", "가격" 등)
 * @returns RegExp[] - 생성된 정규식 패턴 배열
 */
export function generateRemovalPatterns(subject: string): RegExp[] {
  const escapedSubject = subject.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return [
    new RegExp(`구체적인\\s*${escapedSubject}[는은]\\s*(언급|말)하지\\s*않`, 'i'),
    new RegExp(`${escapedSubject}[는은]\\s*(언급|말)하지\\s*않`, 'i'),
    new RegExp(`${escapedSubject}\\s*(제거|삭제)`, 'i'),
    new RegExp(`${escapedSubject}\\s*부분\\s*(삭제|제거)`, 'i'),
    new RegExp(`${escapedSubject}.*?(삭제|제거)`, 'i'),
    new RegExp(`${escapedSubject}[가이]\\s*없어야\\s*한`, 'i')
  ]
}

/**
 * 동적으로 패턴 생성 - 특정 주제에 대한 수정 패턴들을 생성
 * @param subject - 대상 주제 (예: "할인율", "문의", "가격" 등)
 * @returns RegExp[] - 생성된 정규식 패턴 배열
 */
export function generateModificationPatterns(subject: string): RegExp[] {
  const escapedSubject = subject.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return [
    new RegExp(`${escapedSubject}[를을]\\s*강조`, 'i'),
    new RegExp(`${escapedSubject}\\s*강조`, 'i'),
    new RegExp(`${escapedSubject}[를을]\\s*추가`, 'i'),
    new RegExp(`${escapedSubject}\\s*추가`, 'i'),
    new RegExp(`${escapedSubject}[를을]\\s*(변경|수정)`, 'i')
  ]
}

// ============================================
// 레거시 호환용: 자주 사용되는 주제 미리 정의
// (필요시 확장 가능하지만, 위 함수들로 동적 처리 가능)
// ============================================
export const COMMON_SUBJECTS = [
  '할인율', '할인', '가격', '금액',
  '문의', '연락처', '전화', '번호', '이메일',
  '장소', '위치', '지점', '매장', '주소',
  '기간', '일정', '날짜', '시간', '기한',
  '테마', '주제', '이벤트', '행사',
  '상품', '제품', '서비스',
  '혜택', '쿠폰', '포인트',
  '조건', '대상', '자격'
] as const

// ============================================
// 내부 메시지/지시사항 감지 패턴 (범용)
// ============================================

/**
 * 내부 지시사항 키워드들 - 이런 표현들이 들어가면 고객용 메시지가 아닌 내부 지시사항
 */
export const INTERNAL_INSTRUCTION_KEYWORDS = [
  '언급하지', '말하지', '강조하되', '주의하되', '기억하되',
  '고객이', '고객들에게', '고객한테', '사용자가', '사용자에게',
  '보이면', '보여지면', '노출되면', '표시되면',
  '안되는', '안되니', '하지말고', '하지마',
  '메시지가', '메시지는', '텍스트가', '텍스트는',
  '미리보기에', '미리보기는', '화면에', '화면은',
  '잘하자', '주의하자', '기억하자', '명심하자',
  '참고:', '주의:', '메모:', '노트:',
  '~는 제외', '~는 빼고', '~는 말고'
] as const

/**
 * 내부 메시지 제거용 정규식 패턴 (동적 생성 가능)
 * 일반적인 패턴들 - 특정 키워드에 의존하지 않음
 */
export const INTERNAL_MESSAGE_PATTERNS = [
  // "X[콜론/공백]...문장" 형태로 내부 지시사항처럼 보이는 패턴
  /[가-힣]+[:\s]+~[^.]*\./g,
  
  // 지시/조언 표현
  /[^.]*하되[^.]*\./g,
  /[^.]*되[^.]*\./g,
  /[^.]*하지\s*말[^.]*\./g,
  /[^.]*언급하지\s*않[^.]*\./g,
  
  // 메타 언급 (메시지 자체에 대한 언급)
  /[^.]*메시지[가는를을이][^.]*\./g,
  /[^.]*텍스트[가는를을이][^.]*\./g,
  /[^.]*내용[가는를을이][^.]*\./g,
  
  // 대상자 언급 (고객/사용자를 3자로 언급)
  /[^.]*고객[이가에게한테][^.]*\./g,
  /[^.]*사용자[가이에게한테][^.]*\./g,
  
  // 조건/상황 설명
  /[^.]*보이면[^.]*\./g,
  /[^.]*보여지면[^.]*\./g,
  /[^.]*노출되면[^.]*\./g,
  /[^.]*표시되면[^.]*\./g,
  
  // 금지/제외 표현
  /[^.]*안\s*되[^.]*\./g,
  /[^.]*제외[^.]*\./g,
  /[^.]*빼고[^.]*\./g,
  /[^.]*말고[^.]*\./g,
  
  // 메타 지시어
  /[^.]*미리보기[에는를][^.]*\./g,
  /[^.]*화면[에는를][^.]*\./g,
  
  // 자기 독려/메모
  /잘하자\s*/g,
  /주의하자\s*/g,
  /기억하자\s*/g,
  /명심하자\s*/g,
  
  // 라벨 형태의 메모
  /참고:\s*[^.]*\./g,
  /주의:\s*[^.]*\./g,
  /메모:\s*[^.]*\./g,
  /노트:\s*[^.]*\./g
]

/**
 * 텍스트가 내부 지시사항인지 판별
 * @param text - 검사할 텍스트
 * @returns boolean - 내부 지시사항이면 true
 */
export function isInternalInstruction(text: string): boolean {
  // 키워드 기반 체크
  for (const keyword of INTERNAL_INSTRUCTION_KEYWORDS) {
    if (text.includes(keyword)) {
      return true
    }
  }
  
  // 패턴 기반 체크
  for (const pattern of INTERNAL_MESSAGE_PATTERNS) {
    if (pattern.test(text)) {
      return true
    }
  }
  
  return false
}

// ============================================
// 설명형/메타 텍스트 감지 패턴 (범용)
// ============================================

/**
 * 작업 동사 - 이런 동사가 명령형으로 나오면 설명/지시사항
 */
export const ACTION_VERBS = [
  '삭제', '제거', '변경', '수정', '교체', '대체', '없애', '빼',
  '추가', '넣어', '포함', '삽입',
  '바꾸', '변환', '전환',
  '확인', '체크', '검토'
] as const

/**
 * 메타 표현 키워드 - 콘텐츠 자체가 아닌 콘텐츠에 대한 언급
 */
export const META_KEYWORDS = [
  // 대상 지칭
  '문구', '내용', '텍스트', '표현', '문장', '단어', '부분', '항목',
  // 프로세스 지칭
  '과정', '단계', '절차', '작업', '처리',
  // 인터페이스 지칭
  '태그', '마크업', '코드', '미리보기', '화면', '페이지', '뷰',
  // 대상자 3인칭 지칭
  '고객', '사용자', '방문자', '수신자',
  // 광고/마케팅 메타 용어
  '광고성', '홍보', '마케팅', '프로모션'
] as const

/**
 * 설명형 접속사/부사 - 설명을 이어가는 표현들
 */
export const EXPLANATORY_CONNECTIVES = [
  '먼저', '그다음', '그리고', '또한', '추가로', '더불어', '아울러',
  '따라서', '그러므로', '결과적으로', '최종적으로',
  '예를 들어', '예시로', '예컨대',
  '만약', '만약에', '경우에', '상황에',
  '원래', '기존의', '이전의', '과거의', '새로운', '다른'
] as const

/**
 * 설명형 텍스트 제거용 정규식 패턴
 * 범용 패턴으로 구성 - 특정 내용에 의존하지 않음
 */
export const EXPLANATORY_TEXT_PATTERNS = [
  // === 작업 지시 패턴 ===
  // "X를 [동사]하고", "X를 [동사]합니다" 형태
  /[^.]*[를을]\s*(?:삭제|제거|변경|수정|교체|대체|추가|넣어)(?:하고|합니다|해야|하세요)[^.]*\.\s*/g,
  // "X로 [동사]합니다" 형태
  /[^.]*로\s*(?:변경|수정|교체|대체)(?:합니다|해야|하세요)[^.]*\.\s*/g,
  
  // === 과정/절차 설명 패턴 ===
  /(?:변경|수정|삭제|추가)(?:될|되어야\s*할|해야\s*할)\s*부분[^.]*\.\s*/g,
  /실제\s*적용되어야\s*할[^.]*\.\s*/g,
  
  // === 메타 언급 패턴 ===
  // "A라는 [메타키워드]" 형태
  /[^.]*라는\s*(?:문구|내용|텍스트|표현|문장)[^.]*\.\s*/g,
  // "[메타키워드]가/는 ..." 형태
  /(?:문구|내용|텍스트|표현|문장|부분)[가는이]\s*[^.]*\.\s*/g,
  
  // === 명령형 패턴 ===
  // "X를 Y로 바꾸세요/변경하세요/수정하세요" 형태
  /[^.]*[를을]\s*[^.]*로\s*(?:바꾸|변경|수정|교체)(?:세요|하세요|해주세요)[^.]*\.\s*/g,
  
  // === 프로세스/인터페이스 언급 패턴 ===
  /[^.]*(?:미리보기|화면|페이지|뷰)[에는를][^.]*\.\s*/g,
  /[^.]*(?:과정|단계|절차|작업)[이가을를][^.]*\.\s*/g,
  /[^.]*(?:태그|마크업|코드)[나를을][^.]*\.\s*/g,
  
  // === 대상자 3인칭 언급 패턴 ===
  /(?:고객|사용자|방문자|수신자)[이가]\s*(?:보는|보이는|받는|확인하는)[^.]*\.\s*/g,
  /(?:고객|사용자|방문자|수신자)[에게한테]\s*(?:보이는|전달되는|노출되는)[^.]*\.\s*/g,
  
  // === 광고/마케팅 메타 언급 패턴 ===
  /[^.]*(?:광고성|홍보|마케팅|프로모션)[^.]*\.\s*/g,
  
  // === 지시사항/메모 패턴 ===
  /(?:잘하자|주의하자|기억하자|명심하자)\s*/g,
  /(?:참고|주의|메모|노트):\s*[^.]*\.\s*/g,
  
  // === 설명형 접속사로 시작하는 문장 패턴 ===
  /(?:먼저|그다음|그리고|또한|추가로|더불어)[^.]*\.\s*/g,
  /(?:따라서|그러므로|결과적으로|최종적으로)[^.]*\.\s*/g,
  /예를\s*들어[^.]*\.\s*/g,
  /(?:만약|만약에)[^.]*\.\s*/g,
  
  // === 비교/대조 설명 패턴 ===
  /(?:기존의|원래의|이전의|과거의|새로운|다른)[^.]*\.\s*/g,
  
  // === 지시대명사로 시작하는 설명 패턴 ===
  /(?:이것은|저것은|그것은|이런|저런|그런)[^.]*\.\s*/g,
  /(?:이\s*(?:내용|부분|텍스트|문장)|저\s*(?:내용|부분)|그\s*(?:내용|부분))[이가][^.]*\.\s*/g
]

/**
 * 텍스트가 설명형/메타 텍스트인지 판별
 * @param text - 검사할 텍스트
 * @returns boolean - 설명형 텍스트면 true
 */
export function isExplanatoryText(text: string): boolean {
  // 작업 동사 + 명령형 체크
  for (const verb of ACTION_VERBS) {
    if (text.match(new RegExp(`${verb}(?:하고|합니다|해야|하세요|세요)`))) {
      return true
    }
  }
  
  // 메타 키워드 체크
  for (const keyword of META_KEYWORDS) {
    const metaPattern = new RegExp(`(?:${keyword})[가는이를]|라는\\s*${keyword}`)
    if (metaPattern.test(text)) {
      return true
    }
  }
  
  // 설명형 접속사로 시작하는지 체크
  for (const connective of EXPLANATORY_CONNECTIVES) {
    if (text.trim().startsWith(connective)) {
      return true
    }
  }
  
  // 패턴 기반 체크
  for (const pattern of EXPLANATORY_TEXT_PATTERNS) {
    if (pattern.test(text)) {
      return true
    }
  }
  
  return false
}

// ============================================
// 실제 콘텐츠 감지 패턴 (완전 범용)
// ============================================

/**
 * 언어 구조 기반 콘텐츠 판별 패턴
 * 특정 도메인이나 키워드에 의존하지 않음
 */

/**
 * 존댓말/경어 패턴 (도메인 무관)
 */
export const POLITE_LANGUAGE_PATTERNS = [
  // 존댓말 어미
  /습니다$/,
  /십니다$/,
  /세요$/,
  /셨습니까$/,
  /하십시오$/,
  /하시기\s*바랍니다$/,
  /[가-힣]+니다$/,
  // 존칭 표현
  /님/,
  /귀하/,
  /[가-힣]+분께서/,
  /[가-힣]+분들/,
  // 정중한 표현
  /감사(?:합니다|드립니다|인사)/,
  /안녕하세요/,
  /부탁드립니다/,
  /문의(?:해\s*)?주[시세]/
]

/**
 * 2인칭 직접 호칭 패턴 (고객 대면 언어)
 */
export const DIRECT_ADDRESS_PATTERNS = [
  /(?:여러분|당신)/,
  /주[시세](?:면|기를|오|고)/,  // "주시면", "주세요", "주시고"
  /[가-힣]+해\s*주[시세]/,      // "이용해 주세요", "방문해 주십시오"
  /[가-힣]+하시(?:면|기를|오|고)/,
  /받으시/,
  /이용하시/,
  /선택하시/
]

/**
 * 구체적 정보 패턴 (숫자, 날짜, 시간 등)
 */
export const CONCRETE_INFO_PATTERNS = [
  /\d+[%원달러유로엔]/,        // 숫자 + 단위
  /\d{4}[-./년]\d{1,2}[-./월]\d{1,2}일?/, // 날짜
  /\d{1,2}:\d{2}/,              // 시간
  /\d{2,4}[-\s]\d{3,4}[-\s]\d{4}/, // 전화번호
  /[가-힣]+(?:\d+)?(?:점|지점|매장|호점|층|호)/, // 장소
  /\d+(?:개|명|회|일|시간|분|초|건|번|차)/, // 수량 단위
]

/**
 * 3인칭/메타 언급 패턴 (내부 지시사항 특징)
 */
export const THIRD_PERSON_META_PATTERNS = [
  /(?:고객|사용자|수신자|방문자)[이가을를]/,
  /(?:메시지|텍스트|내용|문구|표현)[이가을를은는]/,
  /(?:템플릿|화면|페이지|미리보기)[에서는을를]/,
  /(?:이|저|그)\s*(?:부분|내용|텍스트|메시지)/
]

/**
 * 명령형/지시형 패턴 (내부 작업 지시 특징)
 */
export const IMPERATIVE_INSTRUCTION_PATTERNS = [
  /[가-힣]+[를을]\s*(?:삭제|제거|변경|수정|교체|대체)(?:하고|합니다|해야|하세요)/,
  /[가-힣]+로\s*(?:변경|수정|교체)(?:합니다|해야|하세요)/,
  /(?:다음|아래|위)와\s*같이/,
  /(?:예를\s*들어|예시로|예컨대)/,
  /(?:먼저|그다음|마지막으로|최종적으로)/
]

/**
 * 실제 콘텐츠 패턴 통합 배열
 */
export const CONTENT_PATTERNS = [
  ...POLITE_LANGUAGE_PATTERNS,
  ...DIRECT_ADDRESS_PATTERNS,
  ...CONCRETE_INFO_PATTERNS
]

/**
 * 텍스트가 실제 고객용 콘텐츠인지 판별 (완전 범용)
 * @param text - 검사할 텍스트
 * @returns boolean - 실제 콘텐츠면 true
 */
export function isActualContent(text: string): boolean {
  // 텍스트가 너무 짧으면 판별 불가
  if (!text || text.trim().length < 3) {
    return false
  }
  
  let contentScore = 0
  let nonContentScore = 0
  
  // 1. 존댓말/경어 체크 (고객 대면 언어)
  const hasPoliteLanguage = POLITE_LANGUAGE_PATTERNS.some(pattern => pattern.test(text))
  if (hasPoliteLanguage) contentScore += 2
  
  // 2. 2인칭 직접 호칭 체크 (고객에게 직접 말하기)
  const hasDirectAddress = DIRECT_ADDRESS_PATTERNS.some(pattern => pattern.test(text))
  if (hasDirectAddress) contentScore += 2
  
  // 3. 구체적 정보 체크 (실제 정보 제공)
  const hasConcreteInfo = CONCRETE_INFO_PATTERNS.some(pattern => pattern.test(text))
  if (hasConcreteInfo) contentScore += 1
  
  // 4. 3인칭/메타 언급 체크 (내부 지시사항 특징)
  const hasThirdPersonMeta = THIRD_PERSON_META_PATTERNS.some(pattern => pattern.test(text))
  if (hasThirdPersonMeta) nonContentScore += 2
  
  // 5. 명령형/지시형 체크 (내부 작업 지시)
  const hasImperativeInstruction = IMPERATIVE_INSTRUCTION_PATTERNS.some(pattern => pattern.test(text))
  if (hasImperativeInstruction) nonContentScore += 2
  
  // 6. 내부 지시사항이나 설명형 텍스트 체크
  if (isInternalInstruction(text)) nonContentScore += 3
  if (isExplanatoryText(text)) nonContentScore += 2
  
  // 7. 문장 길이 체크 (너무 짧으면 내부 지시일 가능성)
  const sentenceLength = text.length
  if (sentenceLength < 10) {
    nonContentScore += 1
  } else if (sentenceLength > 20) {
    contentScore += 1
  }
  
  // 8. 문장 부호 체크 (완결된 문장인지)
  const hasProperEnding = /[.!?。]$/.test(text.trim())
  if (hasProperEnding) contentScore += 1
  
  console.log(`콘텐츠 판별: "${text.substring(0, 30)}..." - 콘텐츠 점수: ${contentScore}, 비콘텐츠 점수: ${nonContentScore}`)
  
  // 최종 판별: 콘텐츠 점수가 비콘텐츠 점수보다 높으면 실제 콘텐츠
  return contentScore > nonContentScore
}

// ============================================
// 통합 유틸리티 함수
// ============================================

/**
 * 텍스트 분류 - 내부지시/설명/콘텐츠 중 어디에 해당하는지 판별
 * @param text - 분류할 텍스트
 * @returns 'internal' | 'explanatory' | 'content'
 */
export function classifyText(text: string): 'internal' | 'explanatory' | 'content' {
  if (isInternalInstruction(text)) return 'internal'
  if (isExplanatoryText(text)) return 'explanatory'
  return 'content'
}

/**
 * 불릿 포인트 동작 추출 - 제거/수정 동작을 통합 추출
 * @param text - 분석할 텍스트
 * @returns 동작 정보 또는 null
 */
export function extractBulletPointAction(text: string): 
  { action: 'remove' | 'modify', subject: string } | null {
  
  const removal = extractRemovalAction(text)
  if (removal) return removal
  
  const modification = extractModificationAction(text)
  if (modification) return modification
  
  return null
}

// ============================================
// 불릿 포인트 범용 처리 (완전 동적)
// ============================================

/**
 * 불릿 포인트 관련 작업 추출 및 처리
 * 특정 주제에 국한되지 않고 모든 불릿 포인트를 동적으로 처리
 */

/**
 * 텍스트에서 불릿 포인트 관련 키워드 추출
 * @param text - 분석할 텍스트
 * @returns 추출된 키워드 배열
 */
export function extractBulletKeywords(text: string): string[] {
  const keywords: string[] = []
  
  // "• 키워드:" 형태 추출
  const bulletPattern = /•\s*([^:：\n]+)[：:]/g
  let match
  while ((match = bulletPattern.exec(text)) !== null) {
    if (match[1]) {
      keywords.push(match[1].trim())
    }
  }
  
  // 일반적인 주제 키워드 추출 (동작 동사와 함께 나오는 경우)
  const subjectPattern = /([가-힣]+)[를을이가는은]\s*(?:삭제|제거|변경|수정|추가|강조)/g
  while ((match = subjectPattern.exec(text)) !== null) {
    if (match[1] && match[1].length >= 2) {
      keywords.push(match[1].trim())
    }
  }
  
  // COMMON_SUBJECTS에서 매칭되는 것 추가
  for (const subject of COMMON_SUBJECTS) {
    if (text.includes(subject)) {
      keywords.push(subject)
    }
  }
  
  // 중복 제거
  return Array.from(new Set(keywords))
}

/**
 * 통합 설명형 키워드 배열 (레거시 호환)
 */
export const EXPLANATORY_KEYWORDS = [
  // 내부 지시사항 키워드
  ...INTERNAL_INSTRUCTION_KEYWORDS,
  // 작업 동사
  ...ACTION_VERBS,
  // 메타 키워드
  ...META_KEYWORDS,
  // 설명형 접속사
  ...EXPLANATORY_CONNECTIVES
] as const


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
// 실제 콘텐츠 감지 패턴 (범용)
// ============================================

/**
 * 실제 고객용 콘텐츠에 나타나는 특징들
 * 특정 내용이 아닌 "유형"을 정의
 */
export const CONTENT_CHARACTERISTICS = {
  // 고객 대면 호칭 (2인칭)
  customerAddressing: [
    /(?:고객|회원)님/,
    /안녕하세요/,
    /감사합니다/,
    /방문해\s*주셔서/,
    /이용해\s*주셔서/
  ],
  
  // 상품/서비스 설명
  productDescription: [
    /(?:상품|제품|서비스|브랜드)/,
    /(?:할인|쿠폰|포인트|혜택)/,
    /(?:행사|이벤트|프로모션)/,
    /(?:신상품|신제품|신규)/,
    /(?:인기|베스트|추천)/
  ],
  
  // 설명/형용 표현 (일반적 마케팅 용어)
  descriptive: [
    /(?:특별한|다양한|풍부한|새로운)/,
    /(?:최고의|최상의|프리미엄|고급)/,
    /(?:합리적|저렴한|경제적)/,
    /(?:편리한|간편한|쉬운)/
  ],
  
  // 행동 유도 (CTA)
  callToAction: [
    /지금\s*(?:확인|신청|구매|예약)/,
    /(?:클릭|방문|문의)해\s*주세요/,
    /서둘러\s*주세요/,
    /놓치지\s*마세요/
  ],
  
  // 구체적 정보 제공
  specificInfo: [
    /\d+%/,                    // 퍼센트 (할인율 등)
    /\d+원/,                   // 가격
    /\d+월\s*\d+일/,          // 날짜
    /\d+:\d+/,                 // 시간
    /[\d-]+/,                  // 전화번호 패턴
    /[가-힣]+(?:점|지점|매장)/ // 장소
  ]
} as const

/**
 * 실제 콘텐츠 패턴 통합 배열
 */
export const CONTENT_PATTERNS = [
  ...CONTENT_CHARACTERISTICS.customerAddressing,
  ...CONTENT_CHARACTERISTICS.productDescription,
  ...CONTENT_CHARACTERISTICS.descriptive,
  ...CONTENT_CHARACTERISTICS.callToAction,
  ...CONTENT_CHARACTERISTICS.specificInfo
]

/**
 * 텍스트가 실제 고객용 콘텐츠인지 판별
 * @param text - 검사할 텍스트
 * @returns boolean - 실제 콘텐츠면 true
 */
export function isActualContent(text: string): boolean {
  let matchCount = 0
  
  // 여러 카테고리에서 매치되면 콘텐츠일 가능성 높음
  for (const patterns of Object.values(CONTENT_CHARACTERISTICS)) {
    for (const pattern of patterns) {
      if (pattern.test(text)) {
        matchCount++
        if (matchCount >= 2) return true // 2개 이상 매치되면 콘텐츠로 판단
      }
    }
  }
  
  // 내부 지시사항이나 설명형 텍스트가 아니면서 어느 정도 길이가 있으면 콘텐츠
  if (!isInternalInstruction(text) && !isExplanatoryText(text) && text.length > 10) {
    return true
  }
  
  return false
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


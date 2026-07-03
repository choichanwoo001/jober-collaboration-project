// UI 마커 관련 상수 정의

// 마커 문자 정의
export const MARKER_CHARS = {
  START_OPEN: '⟦',
  START_CLOSE: '⟧',
  END_OPEN: '⟦/',
  END_CLOSE: '⟧'
} as const

// 마커 생성 유틸리티 함수
export const createMarker = (id: string, content: string): string => {
  return `${MARKER_CHARS.START_OPEN}${id}${MARKER_CHARS.START_CLOSE}${content}${MARKER_CHARS.END_OPEN}${id}${MARKER_CHARS.END_CLOSE}`
}

// 마커 시작 태그 생성
export const createMarkerStart = (id: string): string => {
  return `${MARKER_CHARS.START_OPEN}${id}${MARKER_CHARS.START_CLOSE}`
}

// 마커 종료 태그 생성
export const createMarkerEnd = (id: string): string => {
  return `${MARKER_CHARS.END_OPEN}${id}${MARKER_CHARS.END_CLOSE}`
}

// 마커 패턴 정규식 생성
export const createMarkerPattern = (id: string): RegExp => {
  return new RegExp(`⟦${id}⟧([^⟦]*)⟦/${id}⟧`, 'g')
}

// 모든 마커 제거 패턴
export const ALL_MARKERS_PATTERN = /⟦([^⟦]+)⟧([^⟦]*)⟦\/\1⟧/g


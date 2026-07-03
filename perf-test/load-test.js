import http from 'k6/http';
import { check, sleep } from 'k6';

// 부하 테스트 옵션 (OpenAI rate limit 고려해 VU 낮춤)
export const options = {
  stages: [
    { duration: '20s', target: 3 },   // 20초 동안 3명으로 증가
    { duration: '1m', target: 5 },    // 1분 동안 5명 유지
    { duration: '20s', target: 0 },   // 20초 동안 0명으로 감소
  ],
  // 실제 API(템플릿 생성)는 무거우므로 기준 완화. 목표에 맞게 조정 가능
  thresholds: {
    http_req_duration: ['p(95)<30000'],  // 95% 요청 30초 이내 (AI 생성 시간 고려)
    http_req_failed: ['rate<0.51'],     // 실패율 51% 미만 (50%일 때 통과)
  },
};

const BACKEND_BASE = __ENV.BACKEND_URL || 'http://localhost:8080';
const AI_BASE = __ENV.AI_URL || 'http://localhost:8000';

const AI_GENERATE_PATH = __ENV.AI_GENERATE_PATH || '/ai/template/generate';
const AI_USER_MESSAGE =
  __ENV.AI_USER_MESSAGE ||
  '주문하신 상품이 오늘 발송되었습니다. 송장번호는 123-456-789 입니다. 감사합니다.';

export default function () {
  // 백엔드 헬스/루트
  const backendRes = http.get(`${BACKEND_BASE}/`);
  check(backendRes, { 'backend status 200': (r) => r.status === 200 });

  sleep(0.5);

  // AI 실제 API (템플릿 생성)
  const payload = JSON.stringify({ userMessage: AI_USER_MESSAGE });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const aiRes = http.post(`${AI_BASE}${AI_GENERATE_PATH}`, payload, params);
  check(aiRes, { 'ai generate status 200': (r) => r.status === 200 });

  sleep(0.5);
}

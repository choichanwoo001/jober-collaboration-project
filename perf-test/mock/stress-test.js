import http from 'k6/http';
import { check, sleep } from 'k6';

// [Mock 전용] 스트레스 테스트: VU 100 → … → 1000 (서버 한계점 탐색, OpenAI 호출 없음)
// 실행 전: AI 서버를 MOCK_OPENAI=1 로 띄울 것
export const options = {
  stages: [
    { duration: '30s', target: 100 },
    { duration: '1m', target: 100 },
    { duration: '30s', target: 200 },
    { duration: '1m', target: 200 },
    { duration: '30s', target: 300 },
    { duration: '1m', target: 300 },
    { duration: '30s', target: 500 },
    { duration: '1m', target: 500 },
    { duration: '30s', target: 700 },
    { duration: '1m', target: 700 },
    { duration: '30s', target: 1000 },
    { duration: '1m', target: 1000 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.51'],
  },
};

const BACKEND_BASE = __ENV.BACKEND_URL || 'http://localhost:8080';
const AI_BASE = __ENV.AI_URL || 'http://localhost:8000';
const AI_GENERATE_PATH = __ENV.AI_GENERATE_PATH || '/ai/template/generate';
const AI_USER_MESSAGE =
  __ENV.AI_USER_MESSAGE ||
  '주문하신 상품이 오늘 발송되었습니다. 송장번호는 123-456-789 입니다. 감사합니다.';

export default function () {
  const backendRes = http.get(`${BACKEND_BASE}/`);
  check(backendRes, { 'backend status 200': (r) => r.status === 200 });
  sleep(0.5);

  const payload = JSON.stringify({ userMessage: AI_USER_MESSAGE });
  const aiRes = http.post(`${AI_BASE}${AI_GENERATE_PATH}`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });
  check(aiRes, { 'ai generate status 200': (r) => r.status === 200 });
  sleep(0.5);
}

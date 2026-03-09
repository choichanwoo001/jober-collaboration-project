import http from 'k6/http';
import { check, sleep } from 'k6';

// 임계점 테스트 (OpenAI rate limit 고려해 VU 낮춤): 2 → 5 → 8 → 10
// 실행 후 터미널 요약에서 http_req_duration의 p(95) 확인
// 고정 VU 비교: ./run-threshold-vus.sh
export const options = {
  stages: [
    { duration: '1m', target: 2 },
    { duration: '1m', target: 5 },
    { duration: '1m', target: 8 },
    { duration: '1m', target: 10 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.51'],  // 실패율 51% 미만
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
  const params = { headers: { 'Content-Type': 'application/json' } };
  const aiRes = http.post(`${AI_BASE}${AI_GENERATE_PATH}`, payload, params);
  check(aiRes, { 'ai generate status 200': (r) => r.status === 200 });

  sleep(0.5);
}

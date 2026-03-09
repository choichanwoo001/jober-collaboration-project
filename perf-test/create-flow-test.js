import http from 'k6/http';
import { check, sleep } from 'k6';

/**
 * 생성(create) 전용 부하 테스트
 * - login 1회 (setup)
 * - POST /api/template/create 반복 (1차 저장만, AI 호출 없음)
 */

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '1m', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<300'],
  },
};

const BACKEND_BASE = __ENV.BACKEND_URL || 'http://localhost:8080';
const API_BASE = `${BACKEND_BASE}/api`;

const TEST_EMAIL = __ENV.TEST_USER_EMAIL || __ENV.TEST_EMAIL;
const TEST_PASSWORD = __ENV.TEST_USER_PASSWORD || __ENV.TEST_PASSWORD;

const DUMMY_TEMPLATE = {
  templateContent: '[k6 생성 테스트] 주문하신 상품이 발송되었습니다. {{고객명}}님 감사합니다.',
  templateTitle: 'k6 생성 테스트 템플릿',
  category: '기타',
  userMessage: '부하테스트용',
  variableList: [{ name: '고객명', type: 'string', description: '변수: 고객명' }],
};

export function setup() {
  if (!TEST_EMAIL || !TEST_PASSWORD) {
    throw new Error('TEST_USER_EMAIL, TEST_USER_PASSWORD 환경변수를 설정하세요.');
  }

  const res = http.post(
    `${API_BASE}/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  if (res.status !== 200) {
    throw new Error(`Login 실패: status=${res.status} body=${res.body}`);
  }

  const body = res.json();
  const token = body.accessToken || body.access_token;

  if (!token) {
    throw new Error(`Login 성공했지만 토큰 없음: ${res.body}`);
  }

  return { token };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.token}`,
  };

  const res = http.post(
    `${API_BASE}/template/create`,
    JSON.stringify(DUMMY_TEMPLATE),
    { headers }
  );

  check(res, { 'create 200': (r) => r.status === 200 });

  if (res.status >= 500) {
    console.log(`[SERVER ERROR] status=${res.status} body=${(res.body || '').slice(0, 300)}`);
  }
  if (res.status === 409) {
    console.log(`[CONFLICT] ${res.body}`);
  }

  sleep(0.1);
}

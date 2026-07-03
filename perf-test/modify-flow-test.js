import http from 'k6/http';
import { check, sleep } from 'k6';

/**
 * 수정(modify) 전용 부하 테스트
 * - setup: login 1회 + 템플릿 1개 생성(create) → templateId 확보
 * - default: POST /api/template/modify (AI) → POST /api/template/save 반복
 * - AI 서버 사용. 반복 실행 시 MOCK_OPENAI=1 권장.
 */

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: '1m', target: 15 },
    { duration: '1m', target: 30 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<15000'],
  },
};

const BACKEND_BASE = __ENV.BACKEND_URL || 'http://localhost:8080';
const API_BASE = `${BACKEND_BASE}/api`;

const TEST_EMAIL = __ENV.TEST_USER_EMAIL || __ENV.TEST_EMAIL;
const TEST_PASSWORD = __ENV.TEST_USER_PASSWORD || __ENV.TEST_PASSWORD;

const INITIAL_TEMPLATE = {
  templateContent: '[k6 수정 테스트] 안녕하세요 {{고객명}}님, 주문이 접수되었습니다.',
  templateTitle: 'k6 수정용 템플릿',
  category: '기타',
  userMessage: '수정 테스트',
  variableList: [{ name: '고객명', type: 'string', description: '고객명' }],
};

const MODIFY_BODY = {
  templateContent: INITIAL_TEMPLATE.templateContent,
  templateTitle: INITIAL_TEMPLATE.templateTitle,
  userMessage: '문구를 조금 더 친절하게 바꿔줘',
  chatHistory: [],
  variableList: [{ variableKey: '고객명', variableValue: '' }],
};

export function setup() {
  if (!TEST_EMAIL || !TEST_PASSWORD) {
    throw new Error('TEST_USER_EMAIL, TEST_USER_PASSWORD 환경변수를 설정하세요.');
  }

  const loginRes = http.post(
    `${API_BASE}/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  if (loginRes.status !== 200) {
    throw new Error(`Login 실패: status=${loginRes.status} body=${loginRes.body}`);
  }

  const loginBody = loginRes.json();
  const token = loginBody.accessToken || loginBody.access_token;
  if (!token) {
    throw new Error(`Login 성공했지만 토큰 없음: ${loginRes.body}`);
  }

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const createRes = http.post(
    `${API_BASE}/template/create`,
    JSON.stringify(INITIAL_TEMPLATE),
    { headers }
  );

  if (createRes.status !== 200) {
    throw new Error(`Create 실패 (수정용 템플릿): status=${createRes.status} body=${createRes.body}`);
  }

  const createBody = createRes.json();
  const templateId = createBody.templateId;
  if (!templateId) {
    throw new Error(`Create 성공했지만 templateId 없음: ${createRes.body}`);
  }

  return {
    token,
    templateId,
    templateContent: INITIAL_TEMPLATE.templateContent,
    templateTitle: INITIAL_TEMPLATE.templateTitle,
    category: INITIAL_TEMPLATE.category,
    variableList: INITIAL_TEMPLATE.variableList,
  };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.token}`,
  };

  const modifyRes = http.post(
    `${API_BASE}/template/modify`,
    JSON.stringify(MODIFY_BODY),
    { headers }
  );

  const modifyOk = check(modifyRes, { 'modify 200': (r) => r.status === 200 });
  if (!modifyOk) {
    if (modifyRes.status >= 500) {
      console.log(`[MODIFY ERROR] status=${modifyRes.status} body=${(modifyRes.body || '').slice(0, 200)}`);
    }
    sleep(0.5);
    return;
  }

  let modifiedContent = MODIFY_BODY.templateContent;
  let modifiedTitle = MODIFY_BODY.templateTitle;
  try {
    const parsed = modifyRes.json();
    modifiedContent = parsed.template_text ?? parsed.templateContent ?? modifiedContent;
    modifiedTitle = parsed.template_title ?? parsed.templateTitle ?? modifiedTitle;
  } catch (_) {}

  const saveBody = {
    templateId: Number(data.templateId),
    templateContent: modifiedContent,
    templateTitle: modifiedTitle,
    category: data.category,
    variableList: data.variableList,
  };

  const saveRes = http.post(
    `${API_BASE}/template/save`,
    JSON.stringify(saveBody),
    { headers }
  );

  check(saveRes, { 'save 200': (r) => r.status === 200 });
  if (saveRes.status >= 500) {
    console.log(`[SAVE ERROR] status=${saveRes.status} body=${(saveRes.body || '').slice(0, 200)}`);
  }

  sleep(0.3);
}

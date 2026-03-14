/**
 * k6 부하 테스트: 템플릿 생성 전체 플로우
 *
 * Front 기준 플로우를 그대로 밟습니다.
 *  1) 백엔드 로그인 (/api/auth/login) → accessToken 획득
 *  2) AI 서버에 생성 요청 (/ai/template/generate) → task_id 수신
 *  3) AI 서버에 폴링 (/ai/template/generate/task/{taskId}) → template_content 등 결과 수신
 *  4) 백엔드에 1차 저장 요청 (/api/template/create) → templateId 생성
 *
 * 환경 변수:
 *  - BACK_BASE_URL (기본: http://localhost:8080)
 *  - AI_BASE_URL   (기본: http://localhost:8000)
 *  - TEST_EMAIL    (로그인용 계정 이메일)
 *  - TEST_PASSWORD (로그인용 계정 비밀번호)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

const BACK_BASE = __ENV.BACK_BASE_URL || 'http://localhost:8080';
const AI_BASE = __ENV.AI_BASE_URL || 'http://localhost:8000';

export const options = {
  scenarios: {
    // executor: 'ramping-vus' -> 'constant-arrival-rate'로 변경
    // 초당 5개의 요청을 꾸준히 보내 Celery 큐의 처리 능력을 테스트합니다.
    ai_generation_arrival_rate: {
      executor: 'constant-arrival-rate',
      rate: 2, // 초당 요청 수 (Worker 처리량에 맞춰 조절)
      timeUnit: '1s', // rate의 시간 단위
      duration: '2m', // 2분 동안 테스트
      preAllocatedVUs: 100, // 시작 시 할당할 VU 수 (rate * 평균 응답 시간보다 커야 함)
      maxVUs: 200, // 최대 VU 수 (안전장치)
      gracefulStop: '90s'
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.1'],
  },
};

// Front에서 쓰는 것과 유사한 userMessage 샘플
const SAMPLE_MESSAGES = [
  '회원가입 완료 알림 템플릿 만들어줘. 가입일시, 아이디 포함.',
  '주문 접수 완료 알림톡 만들어줘. 주문번호, 상품명, 결제금액 변수로.',
  '배송 출발 안내 템플릿. 운송장번호, 예상 도착일 포함해줘.',
  '예약 확정 알림. 예약일시, 장소, 문의처 넣어줘.',
  '이벤트 당첨 안내 템플릿. 당첨 내용, 수령 방법 포함.',
];

// 템플릿 내용에서 {{변수}} 이름 추출 (프론트와 동일한 방식)
function extractVariablesFromTemplate(template) {
  const doubleBracePattern = /\{\{([^}]+)\}\}/g;
  const found = new Set();
  let m;
  while ((m = doubleBracePattern.exec(template)) !== null) {
    const name = (m[1] || '').trim();
    if (name) {
      found.add(name);
    }
  }
  return Array.from(found);
}

// 최초 1회: 로그인해서 accessToken 확보
export function setup() {
  const email = __ENV.TEST_EMAIL || 'asd123@a.com';
  const password = __ENV.TEST_PASSWORD || 'asd123';

  const loginRes = http.post(
    `${BACK_BASE}/api/auth/login`,
    JSON.stringify({ email, password }),
    {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s',
    },
  );

  check(loginRes, {
    'login status is 200': (r) => r.status === 200,
  });

  let tokens;
  try {
    tokens = JSON.parse(loginRes.body);
  } catch (e) {
    throw new Error(`로그인 응답 JSON 파싱 실패: ${loginRes.body}`);
  }

  const accessToken = tokens.accessToken;
  if (!accessToken) {
    throw new Error(`accessToken 없음: ${loginRes.body}`);
  }

  return { accessToken };
}

export default function (data) {
  const accessToken = data.accessToken;
  const userMessage = SAMPLE_MESSAGES[__VU % SAMPLE_MESSAGES.length];

  // 1) AI 서버에 SSE 연결 (Redis Pub/Sub 기반)
  // 폴링 없이 연결을 유지하며 Celery 작업 완료 이벤트를 기다립니다.
  const sseRes = http.get(
    `${AI_BASE}/ai/template/generate/stream?userMessage=${encodeURIComponent(userMessage)}`,
    {
      // Celery 작업 시간을 고려하여 타임아웃을 넉넉히 설정 (예: 90초)
      timeout: '90s',
    },
  );

  check(sseRes, {
    'sse status is 200': (r) => r.status === 200,
  });

  if (sseRes.status !== 200) {
    console.warn(`[VU ${__VU}] SSE 요청 실패: ${sseRes.status} ${sseRes.body}`);
    return;
  }

  let finalResult = null;
  try {
    // SSE 응답은 "data: {...}\n\n" 형태가 여러 번 올 수 있습니다.
    // "SUCCESS" 상태를 가진 마지막 메시지를 찾습니다.
    const lines = sseRes.body.split('\n\n');
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const jsonStr = line.substring(6).trim();
        const obj = JSON.parse(jsonStr);
        if (obj.status === 'SUCCESS') {
          finalResult = obj;
          break;
        }
      }
    }
  } catch (e) {
    console.warn(`[VU ${__VU}] SSE 응답 파싱 실패`);
  }

  if (!finalResult || !finalResult.template_content) {
    console.warn(`[VU ${__VU}] 결과 수신 실패 (타임아웃 또는 에러)`);
    return;
  }

  const templateContent = finalResult.template_content || '';
  const templateTitle = finalResult.template_title || '';
  const category = finalResult.category || '기타';

  const variableNames = extractVariablesFromTemplate(templateContent);

  // 2) 백엔드에 1차 저장 요청 (/api/template/create)
  const variableList = variableNames.map((name) => ({
    variableKey: name,
  }));

  const saveBody = {
    templateContent,
    templateTitle,
    variableList,
    category,
    buttonText: null,
    userMessage,
  };

  const saveRes = http.post(
    `${BACK_BASE}/api/template/create`,
    JSON.stringify(saveBody),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      timeout: '10s',
    },
  );

  check(saveRes, {
    'save status is 200 or 400': (r) => r.status === 200 || r.status === 400,
  });

  if (saveRes.status !== 200) {
    console.warn(
      `[VU ${__VU}] save 실패 status=${saveRes.status} body=${saveRes.body?.slice(
        0,
        200,
      )}`,
    );
  }

  sleep(1);
}

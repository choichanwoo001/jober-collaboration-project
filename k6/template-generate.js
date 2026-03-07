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
  stages: [
    { duration: '20s', target: 40 },
    { duration: '40s', target: 80 },
    { duration: '20s', target: 0 },
  ],
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

  // 1) AI 서버에 템플릿 생성 작업 큐잉
  const queueRes = http.post(
    `${AI_BASE}/ai/template/generate`,
    JSON.stringify({ userMessage }),
    {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s',
    },
  );

  check(queueRes, {
    'queue status is 202': (r) => r.status === 202,
  });

  let taskId;
  try {
    const body = JSON.parse(queueRes.body);
    taskId = body.task_id;
  } catch (e) {
    console.warn(`queue 응답 파싱 실패: ${queueRes.body}`);
  }

  if (!taskId) {
    console.warn(`[VU ${__VU}] task_id 없음, 종료`);
    return;
  }

  // 2) AI 서버에 폴링해서 실제 템플릿 생성 결과 받기
  let finalResult = null;
  const maxPolls = 30; // 최대 30번 * 2초 = 60초
  for (let i = 0; i < maxPolls; i++) {
    const pollRes = http.get(`${AI_BASE}/ai/template/generate/task/${taskId}`, {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s',
    });

    if (pollRes.status !== 200) {
      console.warn(`[VU ${__VU}] 폴링 응답 코드 이상: ${pollRes.status}`);
      sleep(2);
      continue;
    }

    let j;
    try {
      j = JSON.parse(pollRes.body);
    } catch (e) {
      console.warn(`[VU ${__VU}] 폴링 응답 JSON 파싱 실패: ${pollRes.body}`);
      sleep(2);
      continue;
    }

    // Front 로직과 동일: status가 없고 template_content가 있으면 완료
    if (typeof j.status === 'undefined' && typeof j.template_content !== 'undefined') {
      finalResult = j;
      break;
    }

    // 아직 진행 중이면 대기
    sleep(2);
  }

  if (!finalResult) {
    console.warn(`[VU ${__VU}] 폴링 타임아웃, 결과 없음`);
    return;
  }

  const templateContent = finalResult.template_content || '';
  const templateTitle = finalResult.template_title || '';
  const category = finalResult.category || '기타';

  const variableNames = extractVariablesFromTemplate(templateContent);

  // 3) 백엔드에 1차 저장 요청 (/api/template/create)
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

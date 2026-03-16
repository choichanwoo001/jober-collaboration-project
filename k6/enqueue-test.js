import http from 'k6/http';
import { check, sleep } from 'k6';

const AI_BASE = __ENV.AI_BASE_URL || 'http://localhost:8000';

export const options = {
  // Enqueue는 처리 속도가 빠르므로 더 높은 부하를 주어 웹 서버의 한계를 테스트합니다.
  scenarios: {
    enqueue_stress: {
      executor: 'ramping-arrival-rate', // RPS를 점진적으로 올려봅니다.
      startRate: 5,
      timeUnit: '1s',
      preAllocatedVUs: 20,
      maxVUs: 50,
      stages: [
        { target: 15, duration: '30s' },  // 초당 50개 요청까지 증가
        { target: 30, duration: '30s' }, // 초당 100개 요청까지 증가
        { target: 0, duration: '30s' },
      ],
    },
  },
};

const SAMPLE_MESSAGES = [
  '회원가입 완료 알림 템플릿 만들어줘.',
  '주문 접수 완료 알림톡 만들어줘.',
  '배송 출발 안내 템플릿.',
];

export default function () {
  const userMessage = SAMPLE_MESSAGES[Math.floor(Math.random() * SAMPLE_MESSAGES.length)];

  // SSE 연결 없이, 단순히 작업 등록(Enqueue)만 요청합니다.
  const payload = JSON.stringify({ userMessage: userMessage });
  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  // POST /generate 엔드포인트 사용 (SSE 아님)
  const res = http.post(`${AI_BASE}/ai/template/generate`, payload, params);

  check(res, {
    'status is 202': (r) => r.status === 202, // 202 Accepted 확인
  });
}

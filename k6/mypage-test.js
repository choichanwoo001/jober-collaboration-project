import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  vus: 50,          // 동시 사용자 수
  duration: '30s',  // 테스트 시간
};

const BASE_URL = 'http://localhost:8080';

// 1. setup 함수: 테스트 시작 전 딱 한 번 실행되어 토큰을 발급받습니다.
export function setup() {
  const loginPayload = JSON.stringify({
    email: "asd123@a.com",  // 실제 DB에 존재하는 테스트용 계정 이메일
    password: "asd123" // 해당 계정의 비밀번호
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  // 로그인 API 호출 (경로는 프로젝트의 AuthController 설정에 따라 다를 수 있음, 예: /api/auth/login)
  const res = http.post(`${BASE_URL}/api/auth/login`, loginPayload, params);

  check(res, {
    'login successful': (r) => r.status === 200,
  });

  const accessToken = res.json('accessToken');

  // 캐시 웜업 (Cache Warmup)
  // 실제 테스트 전에 API를 몇 번 호출하여 JVM 워밍업, DB 커넥션 풀 초기화 등을 유도합니다.
  const warmupParams = {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  };

  for (let i = 0; i < 5; i++) {
    http.get(`${BASE_URL}/api/mypage`, warmupParams);
  }

  return { token: accessToken };
}

// 2. default 함수: setup에서 반환한 data(토큰)를 받아 사용합니다.
export default function (data) {
  const res = http.get(`${BASE_URL}/api/mypage`, {
    headers: {
      Authorization: `Bearer ${data.token}`,
    },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(0.2); // 요청 간 간격
}

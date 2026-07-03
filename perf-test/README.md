# k6 부하/스트레스 테스트

백엔드 + AI API(`/ai/template/generate`) 연결해서 테스트합니다.

---

## 필요한 실행 환경 (테스트별)

| 테스트 | 스프링(백엔드) | Redis | AI 서버 |
|--------|----------------|-------|---------|
| **생성만** (`create-flow-test.js`, `save-flow-test.js`) | ✅ | ✅ | ❌ |
| **수정만** (`modify-flow-test.js`) | ✅ | ✅ | ✅ (Mock 권장) |
| **스트레스/부하** (`stress-test.js`, `load-test.js`, `threshold-test.js`) | ✅ | ❌ | ✅ |

- **스프링 + Redis만** 켜면 되는 건 **생성 전용** 테스트뿐입니다. (로그인 때문에 Redis 필요.)
- 수정 테스트는 백엔드가 AI 서버를 부르므로 **AI 서버도** 띄워야 합니다.
- stress/load/threshold는 로그인을 쓰지 않아서 Redis는 필요 없습니다.

```bash
# 생성 테스트만 할 때 (스프링 + Redis만 있으면 됨)
cd back && ./gradlew bootRun
# Redis: brew services start redis  또는  docker run -p 6379:6379 redis

cd perf-test
TEST_USER_EMAIL=... TEST_USER_PASSWORD=... k6 run create-flow-test.js
```

---

## 1. Mock 전용 (OpenAI 호출 없음, 권장)

API 한도 소진 없이 **서버 한계점·안정성**만 보고 싶을 때 사용합니다.

- **위치**: `perf-test/mock/`
- **실행 전**: AI 서버를 `MOCK_OPENAI=1` 로 띄우기
- **스크립트**: 고 VU (100→…→1000 등)

```bash
# AI 서버 Mock 모드
cd ai && MOCK_OPENAI=1 uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 테스트
cd perf-test/mock
k6 run stress-test.js
k6 run load-test.js
k6 run threshold-test.js
```

자세한 내용: [mock/README.md](mock/README.md)

---

## 2. 루트 스크립트 (perf-test/*.js)

`perf-test/` 루트의 `stress-test.js`, `load-test.js`, `threshold-test.js`를 사용합니다.

- **Mock 모드**로 AI 서버 띄우면: 고 VU 스트레스도 한도 없이 반복 가능 (stress-test 100~1000 VU).
- **일반 모드**(MOCK_OPENAI 없이)로 띄우면: 실제 OpenAI 호출, API 한도 소진. load-test(3→5 VU), threshold-test(2~10 VU)는 낮은 부하로 실제 AI 흐름 검증용.

```bash
# AI 서버 (Mock이면 한도 없음, 아니면 실제 API 사용)
cd ai && uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Mock: MOCK_OPENAI=1 uvicorn ...

# 테스트
cd perf-test
k6 run stress-test.js
k6 run load-test.js
k6 run threshold-test.js
```

| 파일 | 용도 |
|------|------|
| `stress-test.js` | VU 단계별 스트레스 (100→…→1000). Mock 권장. |
| `load-test.js` | 일정 부하(3→5 VU). p95 30초 이내 등. |
| `threshold-test.js` | 2→5→8→10 VU, 실패율·p95 확인. |
| `save-flow-test.js` | **1차 저장(create)** 반복 테스트 (AI 호출 없음, DB 부하). |
| `create-flow-test.js` | **생성 전용**: login → `POST /api/template/create` 반복 (AI 없음). |
| `modify-flow-test.js` | **수정 전용**: setup에서 템플릿 1개 생성 후, `modify`(AI) → `save` 반복. AI 서버 사용 시 `MOCK_OPENAI=1` 권장. |

---

## 3. 생성 / 수정 나눠서 테스트

생성(create)과 수정(modify) 플로우를 **각각 따로** 부하 테스트할 수 있습니다.

| 구분 | 스크립트 | 내용 |
|------|----------|------|
| **생성** | `create-flow-test.js` | login → `POST /api/template/create` 반복. AI 호출 없음. |
| **수정** | `modify-flow-test.js` | setup에서 템플릿 1개 생성 후, `POST /api/template/modify`(AI) → `POST /api/template/save` 반복. |

- **필요**: 백엔드 실행, AI 서버(수정 테스트 시), **테스트용 계정** (`TEST_USER_EMAIL`, `TEST_USER_PASSWORD`)

### 수정 테스트 + Mock 사용 (권장)

수정 플로우는 백엔드가 **AI 서버**의 `/ai/template/modify`를 호출합니다. 실제 OpenAI를 쓰면 한도 소진되므로, 부하/반복 테스트할 때는 **Mock 모드**로 AI 서버를 띄우는 것을 권장합니다.

**Mock이란?**  
AI 서버를 `MOCK_OPENAI=1`로 실행하면, **generate**와 **modify** API가 OpenAI를 호출하지 않고 더미 응답만 반환합니다. k6로 수정 테스트를 반복해도 API 한도를 쓰지 않습니다.

1. **AI 서버를 Mock 모드로 실행**  
   `MOCK_OPENAI=1`(또는 `true`, `yes`)로 띄우면 `/ai/template/generate`, `/ai/template/modify` 모두 더미 응답을 반환합니다.

2. **그 다음 수정 전용 k6 실행**

```bash
# 생성만 테스트 (AI 불필요)
TEST_USER_EMAIL=test@test.com TEST_USER_PASSWORD=asdfqwer k6 run create-flow-test.js

# 수정만 테스트 — Mock으로 하기 (OpenAI 한도 소진 없음)
# 1) 터미널 하나에서 AI 서버 Mock 모드로 실행
cd ai && MOCK_OPENAI=1 uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2) 다른 터미널에서 수정 테스트 실행
cd perf-test
TEST_USER_EMAIL=test@test.com TEST_USER_PASSWORD=asdfqwer k6 run modify-flow-test.js
```

- Mock 없이 **실제 AI**로 수정 테스트를 돌리려면: AI 서버를 `MOCK_OPENAI` 없이 띄운 뒤 같은 식으로 `modify-flow-test.js`를 실행하면 됩니다. (API 한도 주의)

---

## 4. 템플릿 저장 플로우만 테스트 (AI 없음, DB 포함)

**1차 저장**(`/api/template/create`)만 반복하는 부하 테스트는 `save-flow-test.js` 또는 `create-flow-test.js`를 사용합니다.

- **필요**: 백엔드 실행, **테스트용 계정**
- **환경변수**: `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`

```bash
# 백엔드 실행
cd back && ./gradlew bootRun

# 테스트 (계정 설정 후)
cd perf-test
TEST_USER_EMAIL=test@test.com TEST_USER_PASSWORD=asdfqwer k6 run save-flow-test.js
# 또는 생성 전용
TEST_USER_EMAIL=test@test.com TEST_USER_PASSWORD=asdfqwer k6 run create-flow-test.js
```

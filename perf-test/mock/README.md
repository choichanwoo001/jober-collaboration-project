# Mock 전용 부하 테스트 (OpenAI 호출 없음)

AI 서버를 **MOCK_OPENAI=1** 로 띄운 뒤 실행합니다. API 한도 소진 없이 서버 한계점·안정성을 확인할 수 있습니다.

## 1. AI 서버 Mock 모드 실행

```bash
cd ai
MOCK_OPENAI=1 uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 2. 테스트 실행

```bash
cd perf-test/mock
k6 run stress-test.js   # 100 → 1000 VU 단계별
k6 run load-test.js     # 20 → 50 VU 부하
k6 run threshold-test.js # 50 → 100 → 200 VU, p95 등 확인
```

| 파일 | 용도 |
|------|------|
| `stress-test.js` | 고 VU 스트레스, 서버 한계점 탐색 |
| `load-test.js` | 일정 부하 안정성 |
| `threshold-test.js` | 구간별 응답 시간·실패율 threshold 검증 |

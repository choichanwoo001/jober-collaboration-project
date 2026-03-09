#!/usr/bin/env bash
# 고정 VU(3, 5, 8)로 각각 1분씩 돌려서 p95 비교 (OpenAI rate limit 고려)
# 사용법: ./run-threshold-vus.sh  (perf-test 폴더에서 실행)

cd "$(dirname "$0")"

for VU in 3 5 8; do
  echo ""
  echo "=============================================="
  echo "  VU=$VU, duration=1m"
  echo "=============================================="
  k6 run --vus "$VU" --duration 1m threshold-test.js 2>&1 | tee "/tmp/k6-vu-$VU.txt"
  echo ""
  echo ">>> p95 요약 (위 출력에서 http_req_duration p(95) 확인)"
  grep -E 'p\(95\)=' "/tmp/k6-vu-$VU.txt" | head -1 || true
done

echo ""
echo "=============================================="
echo "  세 구간 p95 비교"
echo "=============================================="
for VU in 3 5 8; do
  p95=$(grep -oE 'p\(95\)=[0-9.]+[a-z]*' "/tmp/k6-vu-$VU.txt" 2>/dev/null | head -1)
  echo "  VU $VU: $p95"
done

import json
from pathlib import Path

# 현재 스크립트가 있는 폴더를 기준으로 파일 경로 잡기
BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR/"approved.jsonl"
open_path = BASE_DIR/"approved_fixed.jsonl"

with open(file_path, "r", encoding="utf-8") as f:
    # 현재는 쉼표로 이어진 객체들일 수 있으므로 대괄호로 감싸 파싱
    text = "[" + f.read().strip().rstrip(",") + "]"
    data = json.loads(text)

with open(open_path, "w", encoding="utf-8") as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("✅ approved_fixed.jsonl 생성 완료!")
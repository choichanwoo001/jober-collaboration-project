# main.py
# uvicorn main:app --reload 로 실행

# from fastapi import FastAPI
# from api.routes import template_routes # 👈 경로가 올바른지 확인
#
# app = FastAPI(title="AI Template Generation API")
# # 라우터를 앱에 포함시킴.
# app.include_router(template_routes.router)
#
# @app.get("/")
# def read_root():
#     return {"message": "AI Template Generation API is running."}

# main.py

from fastapi import FastAPI, Request  # 👈 Request를 추가로 import 합니다.
from api.routes import template_routes

app = FastAPI(title="AI Template Generation API")

# =================================================================
# 👇 --- 디버깅을 위한 임시 코드 --- 👇
# =================================================================
@app.post("/debug-what-i-received")
async def debug_what_i_received(request: Request):
    """
    클라이언트가 보낸 요청 본문(body)을 그대로 출력하고 반환하는
    디버깅 전용 엔드포인트입니다.
    """
    print("\n" + "="*50)
    print("🕵️‍♂️ /debug-what-i-received 엔드포인트 호출됨 🕵️‍♂️")

    try:
        body_json = await request.json()
        print("✅ 수신된 JSON 데이터:")
        print(body_json)
        print("="*50 + "\n")
        return {"status": "JSON 수신 성공", "received_data": body_json}
    except Exception as e:
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        print("❌ JSON 파싱 실패! 수신된 원시 데이터:")
        print(body_str)
        print(f"파싱 실패 원인: {e}")
        print("="*50 + "\n")
        return {"status": "JSON 파싱 실패", "raw_data": body_str}
# =================================================================

# 기존 코드는 그대로 둡니다.
app.include_router(template_routes.router)

@app.get("/")
def read_root():
    return {"message": "AI Template Generation API is running."}

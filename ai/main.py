# main.py
# uvicorn main:app --reload 로 실행

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from exceptions import validation_exception_handler
from dotenv import load_dotenv # 👈 1. dotenv import

load_dotenv()
from api.routes import template_routes

app = FastAPI(title="AI Template Generation API")
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# template_routes 라우터의 모든 경로는 /ai 로 시작하도록 설정.
app.include_router(template_routes.router, prefix="/ai")

@app.get("/")
def read_root():
    # 올바른 main.py를 실행.
    return {
        "message": "✅ SUCCESS! This is the CORRECT `main.py` file running!",
        "included_router_prefix": "/ai",
        "router_file_location": "api/routes/template_routes.py"
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "message": "Template Generator API is running"}
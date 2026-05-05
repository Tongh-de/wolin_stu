import os
import time
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.responses import HTMLResponse

# 加载环境变量
load_dotenv()

# 检查必要的环境变量
def check_required_env():
    required = ["DASHSCOPE_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"错误: 缺少必要的环境变量: {', '.join(missing)}")
        print("请在 .env 文件中设置以下变量:")
        for k in missing:
            print(f"  {k}=your-api-key-here")
        return False
    return True

if not check_required_env():
    exit(1)

from database import engine, Base
from controllers import (
    student_router,
    class_router,
    teacher_router,
    exam_router,
    employment_router,
    statistics_router,
    query_router,
    auth_router
)
from controllers.rag_router import router as rag_router
from controllers.agent_router import router as agent_router
from utils.logger import app_logger

# Lifespan 事件处理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    app_logger.info("🚀 应用服务已启动")
    app_logger.info("📚 Swagger文档: http://127.0.0.1:8082/docs")
    app_logger.info("🌐 前端界面: http://127.0.0.1:8082/static/index.html")
    yield
    # 关闭时
    app_logger.info("🛑 应用服务正在关闭...")
    app_logger.info("=" * 50)


# 创建 FastAPI 应用
app = FastAPI(
    title="沃林学生管理系统",
    description="FastAPI + MySQL 学生信息/成绩/就业/统计管理",
    version="1.0.0",
    lifespan=lifespan
)


# 请求拦截器 - 记录请求日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path

    # 记录请求
    app_logger.info(f"➡️  请求: {method} {path}")

    # 处理请求
    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # 记录成功响应
        app_logger.info(
            f"⬅️  响应: {method} {path} | 状态: {response.status_code} | 耗时: {duration:.3f}s"
        )
        return response
    except Exception as e:
        duration = time.time() - start_time
        app_logger.error(
            f"❌ 异常: {method} {path} | 错误: {str(e)} | 耗时: {duration:.3f}s"
        )
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"服务器内部错误: {str(e)}"}
        )

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# 注册路由
app.include_router(student_router)
app.include_router(class_router)
app.include_router(teacher_router)
app.include_router(exam_router)
app.include_router(employment_router)
app.include_router(statistics_router)
app.include_router(query_router)
app.include_router(auth_router)
app.include_router(rag_router)
app.include_router(agent_router)

# 创建所有表
Base.metadata.create_all(bind=engine)
app_logger.info("=" * 50)
app_logger.info("沃林学生管理系统启动")
app_logger.info("=" * 50)


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>学生管理系统运行成功！</h1>
        <p><a href="/docs" target="_blank">Swagger 文档</a></p>
        <p><a href="/static/index.html" target="_blank">前端界面</a></p>
    </body>
    </html>
    """



if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8099)

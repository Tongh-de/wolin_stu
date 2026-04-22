import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

from database import engine, Base
from controllers import (
    student_router,
    class_router,
    teacher_router,
    exam_router,
    employment_router,
    statistics_router,
    query_router,
    auth_router,
    text2sql_router
)
from knowledge_base import build_knowledge_base

# 创建所有表
Base.metadata.create_all(bind=engine)

# 构建知识库
build_knowledge_base()

app = FastAPI(
    title="沃林学生管理系统",
    description="FastAPI + MySQL 学生信息/成绩/就业/统计管理",
    version="1.0.0"
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
app.include_router(text2sql_router)


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
    uvicorn.run(app, host='127.0.0.1', port=8082)

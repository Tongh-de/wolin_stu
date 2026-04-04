import uvicorn
from fastapi import FastAPI
from database import engine, Base
from api import (
    student_api,
    class_api,
    teacher_api,
    exam_api,
    employment_api,
    statistics_api
)

# 创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="沃林学生管理系统",
    description="FastAPI + MySQL 学生信息/成绩/就业/统计管理",
    version="1.0.0"
)

# 注册所有路由
app.include_router(student_api.router)
app.include_router(class_api.router)
app.include_router(teacher_api.router)
app.include_router(exam_api.router_exam)
app.include_router(employment_api.router)
app.include_router(statistics_api.router)

# 首页
@app.get("/")
def root():
    return {"message": "学生管理系统运行成功！访问 /docs 查看接口"}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8080)

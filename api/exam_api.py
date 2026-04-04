from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from dao import exam_dao
from schemas import response, exam_request
from typing import Optional


router_exam = APIRouter(prefix="/exam", tags=["学生成绩管理"])


# 提交考试成绩
@router_exam.post("/", response_model=response.ResponseBase, description="提交考试成绩")
async def exam_submit(
        exam_data: exam_request.ExamData,
        db: Session = Depends(get_db)
):
    _return = exam_dao.submit_grade(exam_data, db)
    return response.ResponseBase(data=_return)


# 修改考试成绩
# @router_exam.put("/{stu_id}")
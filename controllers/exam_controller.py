from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from services import ExamService
from schemas import exam_request, ResponseBase
from typing import Optional

router_exam = APIRouter(prefix="/exam", tags=["学生成绩管理"])


@router_exam.post("/", response_model=ResponseBase, description="提交考试成绩")
async def exam_submit(
        exam_data: exam_request.NewExamData,
        db: Session = Depends(get_db)
):
    _return = ExamService.exam_submit(exam_data, db)
    if _return["message"] == "success":
        return ResponseBase(data=_return)
    raise HTTPException(status_code=400, detail=_return)


@router_exam.put("/", response_model=ResponseBase, description="修改考试成绩")
async def exam_update(
        exam_data: exam_request.UpdateExamData,
        stu_id: int = Query(description="学生编号"),
        seq_no: int = Query(description="考核序次"),
        db: Session = Depends(get_db)
):
    _return = ExamService.exam_update(stu_id, seq_no, exam_data, db)
    if _return.endswith('updated'):
        return ResponseBase(data=_return)
    raise HTTPException(status_code=400, detail=_return)


@router_exam.delete("/{stu_id}", response_model=ResponseBase, description="删除考试成绩")
async def exam_delete(
        stu_id: int,
        seq_no: Optional[int] = None,
        db: Session = Depends(get_db)
):
    _return = ExamService.exam_delete(stu_id, seq_no, db)
    if _return.endswith('deleted'):
        return ResponseBase(data=_return)
    raise HTTPException(status_code=400, detail=_return)


@router_exam.get("/", response_model=ResponseBase, description="查询考试成绩")
async def exam_get(
        stu_id: int,
        seq_no: Optional[int] = None,
        db: Session = Depends(get_db)
):
    _return = ExamService.exam_get(stu_id, seq_no, db)
    if _return["msg"] == "success":
        return ResponseBase(data=_return)
    raise HTTPException(status_code=400, detail=_return)

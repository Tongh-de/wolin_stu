from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from services import ExamService
from schemas import exam_request, ResponseBase
from model.exam_model import StuExamRecord
from model.student import StuBasicInfo
from model.class_model import Class
from typing import Optional

router_exam = APIRouter(prefix="/exam", tags=["学生成绩管理"])


@router_exam.get("/records", response_model=ResponseBase, description="获取所有成绩记录列表（带学生姓名和班级）")
async def get_all_exam_records(db: Session = Depends(get_db)):
    """获取所有成绩记录，关联学生姓名和班级名称"""
    records = db.query(
        StuExamRecord.stu_id,
        StuExamRecord.seq_no,
        StuExamRecord.grade,
        StuExamRecord.exam_date,
        StuBasicInfo.stu_name,
        StuBasicInfo.class_id,
        Class.class_name
    ).join(
        StuBasicInfo, StuExamRecord.stu_id == StuBasicInfo.stu_id
    ).outerjoin(
        Class, StuBasicInfo.class_id == Class.class_id
    ).filter(
        StuExamRecord.is_deleted == 0,
        StuBasicInfo.is_deleted == False
    ).all()

    data = [{
        "stu_id": r.stu_id,
        "stu_name": r.stu_name,
        "class_id": r.class_id,
        "class_name": r.class_name,
        "seq_no": r.seq_no,
        "grade": r.grade,
        "exam_date": r.exam_date.isoformat() if r.exam_date else None
    } for r in records]

    return ResponseBase(code=200, message="查询成功", data=data)


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

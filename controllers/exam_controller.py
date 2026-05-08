from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from services import ExamService
from schemas import exam_request, ResponseBase, ListResponse
from model.exam_model import StuExamRecord
from model.student import StuBasicInfo
from model.class_model import Class
from typing import Optional
from utils.logger import get_logger
from utils.auth_deps import get_current_user, require_admin, require_teacher_or_admin
from model.user import User

logger = get_logger("exam")
router_exam = APIRouter(prefix="/exam", tags=["学生成绩管理"])


@router_exam.get("/records", description="获取所有成绩记录列表（带学生姓名和班级）")
async def get_all_exam_records(
        page: int = Query(1, description="页码", ge=1),
        page_size: int = Query(10, description="每页条数", ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_teacher_or_admin)  # 教师或管理员
):
    """获取所有成绩记录，关联学生姓名和班级名称，支持分页"""
    logger.info(f"查询成绩记录: page={page}, page_size={page_size}, 操作者: {current_user.username}")

    # 构建基础查询
    base_query = db.query(
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
    )

    # 获取总数
    total = base_query.count()

    # 分页查询
    offset = (page - 1) * page_size
    records = base_query.order_by(StuExamRecord.stu_id, StuExamRecord.seq_no).offset(offset).limit(page_size).all()

    data = [{
        "stu_id": r.stu_id,
        "stu_name": r.stu_name,
        "class_id": r.class_id,
        "class_name": r.class_name,
        "seq_no": r.seq_no,
        "grade": r.grade,
        "exam_date": r.exam_date.isoformat() if r.exam_date else None
    } for r in records]

    logger.info(f"查询成功: total={total}, 返回{len(data)}条记录")
    return {
        "code": 200,
        "message": "查询成功",
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
    }


@router_exam.post("/", response_model=ResponseBase, description="提交考试成绩")
async def exam_submit(
        exam_data: exam_request.NewExamData,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    logger.info(f"新增成绩: stu_id={exam_data.stu_id}, seq_no={exam_data.seq_no}, grade={exam_data.grade}, 操作者: {current_user.username}")
    _return = ExamService.exam_submit(exam_data, db)
    if _return["message"] == "success":
        logger.info(f"新增成功: {_return}")
        return ResponseBase(data=_return)
    logger.warning(f"新增失败: {_return}")
    raise HTTPException(status_code=400, detail=_return)


@router_exam.put("/", response_model=ResponseBase, description="修改考试成绩")
async def exam_update(
        exam_data: exam_request.UpdateExamData,
        stu_id: int = Query(description="学生编号"),
        seq_no: int = Query(description="考核序次"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    logger.info(f"修改成绩: stu_id={stu_id}, seq_no={seq_no}, grade={exam_data.grade}, 操作者: {current_user.username}")
    _return = ExamService.exam_update(stu_id, seq_no, exam_data, db)
    if _return.endswith('updated'):
        logger.info(f"修改成功: {_return}")
        return ResponseBase(data=_return)
    logger.warning(f"修改失败: {_return}")
    raise HTTPException(status_code=400, detail=_return)


@router_exam.delete("/{stu_id}", response_model=ResponseBase, description="删除考试成绩")
async def exam_delete(
        stu_id: int,
        seq_no: Optional[int] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员可删除
):
    logger.info(f"删除成绩: stu_id={stu_id}, seq_no={seq_no}, 操作者: {current_user.username}")
    _return = ExamService.exam_delete(stu_id, seq_no, db)
    if _return.endswith('deleted'):
        logger.info(f"删除成功: {_return}")
        return ResponseBase(data=_return)
    logger.warning(f"删除失败: {_return}")
    raise HTTPException(status_code=400, detail=_return)


@router_exam.get("/", response_model=ResponseBase, description="查询考试成绩")
async def exam_get(
        stu_id: int,
        seq_no: Optional[int] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # 登录用户可查
):
    logger.info(f"查询成绩: stu_id={stu_id}, seq_no={seq_no}, 操作者: {current_user.username}")
    
    # 学生只能查自己的成绩
    if current_user.role == 'student' and current_user.student_id != stu_id:
        raise HTTPException(status_code=403, detail="只能查询自己的成绩")
    
    _return = ExamService.exam_get(stu_id, seq_no, db)
    if _return["msg"] == "success":
        logger.info(f"查询成功")
        return ResponseBase(data=_return)
    logger.warning(f"查询失败: {_return}")
    raise HTTPException(status_code=400, detail=_return)

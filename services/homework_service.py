"""
学生作业服务
"""
import os
import uuid
import io
import zipfile
import xml.etree.ElementTree as ET
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db
from model.student_homework import StudentHomework
from model.user import User
from utils.auth_deps import get_current_user
from sqlalchemy.orm import Session
from PyPDF2 import PdfReader

router = APIRouter(prefix="/homework", tags=["作业管理"])

# 上传文件保存目录
UPLOAD_DIR = "uploads/homework"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 支持的文件格式
SUPPORTED_EXTENSIONS = ['txt', 'pdf', 'docx']


# ============================================
# 文件解析函数
# ============================================
def parse_file_content(file_bytes: bytes, filename: str) -> str:
    """解析不同格式的文件内容"""
    ext = filename.lower().split('.')[-1]
    
    if ext == 'txt':
        return file_bytes.decode('utf-8')
    elif ext == 'pdf':
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            return '\n'.join([page.extract_text() or '' for page in reader.pages])
        except Exception as e:
            raise ValueError(f"PDF解析失败: {str(e)}")
    elif ext == 'docx':
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                with z.open('word/document.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    paragraphs = root.findall('.//w:p', ns)
                    texts = []
                    for p in paragraphs:
                        texts_in_p = []
                        for t in p.findall('.//w:t', ns):
                            if t.text:
                                texts_in_p.append(t.text)
                        if texts_in_p:
                            texts.append(''.join(texts_in_p))
                    return '\n'.join(texts)
        except Exception as e:
            raise ValueError(f"DOCX解析失败: {str(e)}")
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


# ============================================
# Pydantic Schemas
# ============================================
class HomeworkSubmit(BaseModel):
    title: Optional[str] = None
    content: str
    homework_type: str = "composition"


class HomeworkReview(BaseModel):
    review_comment: str
    homework_id: int


class HomeworkResponse(BaseModel):
    id: int
    student_id: str
    title: Optional[str]
    content: str
    homework_type: str
    status: str
    review_comment: Optional[str]
    reviewed_at: Optional[str]
    created_at: Optional[str]


# ============================================
# 学生接口
# ============================================
@router.post("/submit")
async def submit_homework(
    homework: HomeworkSubmit,
    current_user: User = Depends(get_current_user)
):
    """学生提交作业/作文"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="只有学生可以提交作业")
    
    db = next(get_db())
    try:
        record = StudentHomework(
            student_id=current_user.student_id or str(current_user.id),
            title=homework.title,
            content=homework.content,
            homework_type=homework.homework_type,
            status="pending"
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "code": 200,
            "message": "提交成功",
            "data": record.to_dict()
        }
    finally:
        db.close()


@router.post("/upload")
async def upload_homework_file(
    file: UploadFile = File(...),
    title: str = Form(default=""),
    homework_type: str = Form(default="composition"),
    current_user: User = Depends(get_current_user)
):
    """上传作业文件（支持 txt, pdf, docx）"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="只有学生可以提交作业")
    
    # 检查文件类型
    ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式，仅支持: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    # 读取文件内容
    file_bytes = await file.read()
    
    # 解析文件内容
    try:
        content = parse_file_content(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 生成唯一文件名保存
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    with open(file_path, 'wb') as f:
        f.write(file_bytes)
    
    # 保存到数据库
    db = next(get_db())
    try:
        record = StudentHomework(
            student_id=current_user.student_id or str(current_user.id),
            title=title or None,
            content=content,
            homework_type=homework_type,
            status="pending",
            file_path=file_path,
            original_filename=file.filename
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return {
            "code": 200,
            "message": "上传成功",
            "data": record.to_dict()
        }
    finally:
        db.close()


@router.get("/my")
async def get_my_homework(
    current_user: User = Depends(get_current_user)
):
    """获取我的作业列表"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="只有学生可以查看作业")
    
    db = next(get_db())
    try:
        records = db.query(StudentHomework).filter(
            StudentHomework.student_id == (current_user.student_id or str(current_user.id))
        ).order_by(StudentHomework.created_at.desc()).all()
        return {
            "code": 200,
            "message": "获取成功",
            "data": [r.to_dict() for r in records]
        }
    finally:
        db.close()


# ============================================
# 教师/管理员接口
# ============================================
@router.get("/list")
async def get_homework_list(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user)
):
    """获取作业列表（教师/管理员）"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="只有教师或管理员可以查看")
    
    db = next(get_db())
    try:
        query = db.query(StudentHomework)
        if status:
            query = query.filter(StudentHomework.status == status)
        
        total = query.count()
        records = query.order_by(StudentHomework.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "list": [r.to_dict() for r in records]
            }
        }
    finally:
        db.close()


@router.post("/review/{homework_id}")
async def review_homework(
    homework_id: int,
    review: HomeworkReview,
    current_user: User = Depends(get_current_user)
):
    """点评作业"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="只有教师或管理员可以点评")
    
    db = next(get_db())
    try:
        record = db.query(StudentHomework).filter(
            StudentHomework.id == homework_id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="作业不存在")
        
        record.status = "reviewed"
        record.review_comment = review.review_comment
        record.reviewed_at = datetime.now()
        db.commit()
        
        return {
            "code": 200,
            "message": "点评成功",
            "data": record.to_dict()
        }
    finally:
        db.close()


@router.delete("/{homework_id}")
async def delete_homework(
    homework_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除作业"""
    db = next(get_db())
    try:
        record = db.query(StudentHomework).filter(
            StudentHomework.id == homework_id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="作业不存在")
        
        # 学生只能删除自己的，教师/管理员可以删除任何
        if current_user.role == "student" and record.student_id != (current_user.student_id or str(current_user.id)):
            raise HTTPException(status_code=403, detail="无权删除此作业")
        
        db.delete(record)
        db.commit()
        
        return {"code": 200, "message": "删除成功"}
    finally:
        db.close()

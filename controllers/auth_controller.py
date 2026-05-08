from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from model.user import User
from services.auth_service import verify_password, get_password_hash, authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from utils.security import InputValidator
from utils.auth_deps import get_current_user
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["认证"])


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "student"  # 角色：admin, teacher, student
    student_id: Optional[int] = None  # 学生ID（学生用户绑定）
    teacher_id: Optional[int] = None  # 教师ID（教师用户绑定）


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 安全修复：禁止公开注册管理员和教师账号
    if user.role in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="禁止公开注册管理员或教师账号，请联系系统管理员"
        )

    # 验证用户名
    try:
        InputValidator.validate_username(user.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 验证密码强度
    try:
        InputValidator.validate_password(user.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 验证角色（学生注册只能是student）
    if user.role != "student":
        raise HTTPException(status_code=400, detail="注册角色只能是学生")

    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户（默认为学生，禁用状态，需要管理员审核）
    hashed = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        hashed_password=hashed,
        role="student",
        student_id=user.student_id,
        teacher_id=None,
        is_active=False  # 新注册用户默认禁用
    )
    db.add(new_user)
    db.commit()
    return {"code": 200, "message": "注册成功，请等待管理员审核后登录"}


@router.post("/login")
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "code": 200,
        "message": "登录成功",
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "student_id": user.student_id,
        "teacher_id": user.teacher_id
    }


@router.post("/logout")
def logout():
    """退出登录（前端删除token即可，这里记录日志）"""
    return {"code": 200, "message": "退出成功"}


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "code": 200,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "student_id": current_user.student_id,
            "teacher_id": current_user.teacher_id
        }
    }

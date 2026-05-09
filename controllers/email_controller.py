"""
邮件控制器
提供邮件发送相关的 API 接口

权限说明：
- 管理员(admin)：可发送所有类型邮件
- 教师(teacher)：可发送邮件给学生和教师
- 学生(student)：无邮件发送权限，仅可接收邮件
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List
import re
import logging

logger = logging.getLogger(__name__)

from services.email_service import (
    send_email,
    send_verification_code,
    send_notification,
    generate_email_content_with_ai,
    email_service
)
from utils.auth_deps import require_teacher_or_admin, get_current_user
from model.user import User

router = APIRouter(prefix="/email", tags=["邮件服务"])


def validate_email(email: str) -> str:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f'无效的邮箱格式: {email}')
    return email.lower().strip()


class SendEmailRequest(BaseModel):
    """发送邮件请求"""
    to_emails: List[str]  # 收件人邮箱列表
    subject: str  # 邮件主题
    html_content: str  # HTML 内容
    text_content: Optional[str] = None  # 纯文本内容（可选）

    @field_validator('to_emails', mode='before')
    @classmethod
    def validate_emails(cls, v):
        if isinstance(v, list):
            return [validate_email(email) if isinstance(email, str) else email for email in v]
        return v

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('邮件主题不能为空')
        if len(v) > 200:
            raise ValueError('邮件主题不能超过200个字符')
        return v.strip()

    @field_validator('html_content')
    @classmethod
    def validate_html_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('邮件内容不能为空')
        return v


class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求"""
    to_email: str  # 收件人邮箱
    expire_minutes: Optional[int] = 5  # 有效期（分钟），默认5分钟

    @field_validator('to_email', mode='before')
    @classmethod
    def validate_email(cls, v):
        if isinstance(v, str):
            return validate_email(v)
        return v

    @field_validator('expire_minutes')
    @classmethod
    def validate_expire_minutes(cls, v):
        if v and (v < 1 or v > 60):
            raise ValueError('有效期必须在1-60分钟之间')
        return v or 5


class SendNotificationRequest(BaseModel):
    """发送通知请求"""
    to_emails: List[str]  # 收件人邮箱列表
    title: str  # 通知标题
    content: str  # 通知内容（HTML格式）
    notification_type: Optional[str] = "general"  # 通知类型

    @field_validator('to_emails', mode='before')
    @classmethod
    def validate_emails(cls, v):
        if isinstance(v, list):
            return [validate_email(email) if isinstance(email, str) else email for email in v]
        return v

    @field_validator('notification_type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ["general", "exam", "homework", "employment"]
        if v not in valid_types:
            raise ValueError(f'通知类型必须是: {", ".join(valid_types)}')
        return v


class TestEmailRequest(BaseModel):
    """测试邮件请求"""
    to_email: Optional[str] = None  # 可选，指定测试邮箱

    @field_validator('to_email', mode='before')
    @classmethod
    def validate_email(cls, v):
        if v:
            return validate_email(v)
        return v


class GenerateEmailRequest(BaseModel):
    """AI生成邮件内容请求"""
    purpose: str  # 邮件目的
    recipient_type: str = "student"  # 收件人类型
    specific_info: Optional[str] = None  # 额外信息
    tone: str = "professional"  # 语气风格

    @field_validator('recipient_type')
    @classmethod
    def validate_recipient_type(cls, v):
        valid_types = ["student", "parent", "teacher", "all"]
        if v not in valid_types:
            raise ValueError(f'收件人类型必须是: {", ".join(valid_types)}')
        return v

    @field_validator('tone')
    @classmethod
    def validate_tone(cls, v):
        valid_tones = ["professional", "formal", "friendly", "gentle"]
        if v not in valid_tones:
            raise ValueError(f'语气风格必须是: {", ".join(valid_tones)}')
        return v


class GenerateAndSendRequest(BaseModel):
    """AI生成并发送邮件请求"""
    purpose: str  # 邮件目的
    recipient_type: str = "student"
    specific_info: Optional[str] = None
    tone: str = "professional"
    to_emails: List[str]  # 收件人邮箱列表

    @field_validator('to_emails', mode='before')
    @classmethod
    def validate_emails(cls, v):
        if isinstance(v, list):
            return [validate_email(email) if isinstance(email, str) else email for email in v]
        return v

    @field_validator('recipient_type')
    @classmethod
    def validate_recipient_type(cls, v):
        valid_types = ["student", "parent", "teacher", "all"]
        if v not in valid_types:
            raise ValueError(f'收件人类型必须是: {", ".join(valid_types)}')
        return v

    @field_validator('tone')
    @classmethod
    def validate_tone(cls, v):
        valid_tones = ["professional", "formal", "friendly", "gentle"]
        if v not in valid_tones:
            raise ValueError(f'语气风格必须是: {", ".join(valid_tones)}')
        return v


class EmailConfigResponse(BaseModel):
    """邮件配置响应"""
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from_name: str
    configured: bool


@router.get("/config", response_model=EmailConfigResponse)
async def get_email_config(current_user: User = Depends(get_current_user)):
    """
    获取邮件服务配置信息

    返回邮件服务的配置状态（不包含密码）
    """
    return EmailConfigResponse(
        smtp_host=email_service.smtp_host,
        smtp_port=email_service.smtp_port,
        smtp_user=email_service.smtp_user,
        smtp_from_name=email_service.smtp_from_name,
        configured=bool(email_service.smtp_user and email_service.smtp_password)
    )


@router.post("/send")
async def api_send_email(
    request: SendEmailRequest,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    发送邮件

    **权限要求**：仅管理员和教师可使用

    - **to_emails**: 收件人邮箱列表
    - **subject**: 邮件主题
    - **html_content**: HTML 格式的邮件内容
    - **text_content**: 纯文本内容（可选）
    """
    result = await send_email(
        to_emails=request.to_emails,
        subject=request.subject,
        html_content=request.html_content,
        text_content=request.text_content
    )

    if result["success"]:
        return {
            "code": 200,
            "message": result["message"],
            "data": {
                "recipients": request.to_emails,
                "subject": request.subject
            }
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])


@router.post("/verification-code")
async def api_send_verification_code(
    request: SendVerificationCodeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    发送验证码邮件

    **所有登录用户均可使用**

    - **to_email**: 收件人邮箱
    - **expire_minutes**: 有效期（分钟），默认5分钟
    """
    # 生成6位数字验证码
    import random
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

    result = await send_verification_code(
        to_email=request.to_email,
        code=code,
        expire_minutes=request.expire_minutes
    )

    if result["success"]:
        # 注意：生产环境中不应该返回验证码，这里仅用于调试
        return {
            "code": 200,
            "message": f"验证码已发送到 {request.to_email}",
            "data": {
                "email": request.to_email,
                "expire_minutes": request.expire_minutes
            }
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])


@router.post("/notification")
async def api_send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    发送通知邮件

    **权限要求**：仅管理员和教师可使用

    - **to_emails**: 收件人邮箱列表
    - **title**: 通知标题
    - **content**: 通知内容（HTML格式）
    - **notification_type**: 通知类型 (general/exam/homework/employment)
    """
    result = await send_notification(
        to_emails=request.to_emails,
        title=request.title,
        content=request.content,
        notification_type=request.notification_type
    )

    if result["success"]:
        return {
            "code": 200,
            "message": result["message"],
            "data": {
                "recipients": request.to_emails,
                "title": request.title,
                "type": request.notification_type
            }
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])


@router.post("/test")
async def test_email_connection(
    request: TestEmailRequest = TestEmailRequest(),
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    测试邮件服务连接

    **权限要求**：仅管理员和教师可使用
    
    - **to_email**: 可选，指定测试邮箱，不填则使用当前用户邮箱
    """
    # 如果没有指定邮箱，使用当前用户的用户名构造邮箱
    to_email = request.to_email
    if not to_email:
        to_email = f"{current_user.username}@163.com"
    
    result = await send_notification(
        to_emails=[to_email],
        title="邮件服务测试",
        content=f"""
            <p>这是一封来自学生管理系统的测试邮件。</p>
            <p>如果您收到这封邮件，说明邮件服务配置正常。</p>
            <p>发送时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """,
        notification_type="general"
    )

    if result["success"]:
        return {
            "code": 200,
            "message": f"测试邮件已发送到 {to_email}",
            "data": {"email": to_email}
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])


# ============================================
# AI 生成邮件内容
# ============================================


@router.post("/generate")
async def api_generate_email_content(
    request: GenerateEmailRequest,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    使用 AI 生成邮件内容

    **权限要求**：仅管理员和教师可使用

    - **purpose**: 邮件目的 (notice/reminder/invitation/warning/congratulation)
    - **recipient_type**: 收件人类型 (student/parent/teacher/all)
    - **specific_info**: 额外特定信息（如具体内容、时间、地点等）
    - **tone**: 语气风格 (professional/formal/friendly/gentle)
    """
    try:
        result = await generate_email_content_with_ai(
            purpose=request.purpose,
            recipient_type=request.recipient_type,
            specific_info=request.specific_info,
            tone=request.tone
        )

        if result["success"] and result.get("data"):
            return {
                "code": 200,
                "message": "邮件内容生成成功",
                "data": {
                    "subject": result["data"].get("subject", "通知"),
                    "html_content": result["data"].get("html_content", ""),
                    "text_content": result["data"].get("text_content", "")
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "生成邮件失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成邮件API异常: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"生成邮件失败: {str(e)}")


@router.post("/generate-and-send")
async def api_generate_and_send_email(
    request: GenerateAndSendRequest,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    使用 AI 生成邮件内容并直接发送

    **权限要求**：仅管理员和教师可使用

    - **purpose**: 邮件目的 (notice/reminder/invitation/warning/congratulation)
    - **recipient_type**: 收件人类型 (student/parent/teacher/all)
    - **specific_info**: 额外特定信息
    - **tone**: 语气风格 (professional/formal/friendly/gentle)
    - **to_emails**: 收件人邮箱列表
    """
    try:
        # 1. 使用 AI 生成内容
        result = await generate_email_content_with_ai(
            purpose=request.purpose,
            recipient_type=request.recipient_type,
            specific_info=request.specific_info,
            tone=request.tone
        )

        if not result["success"] or not result.get("data"):
            raise HTTPException(status_code=400, detail=result.get("message", "生成邮件失败"))

        # 2. 发送邮件
        email_result = await send_email(
            to_emails=request.to_emails,
            subject=result["data"].get("subject", "通知"),
            html_content=result["data"].get("html_content", ""),
            text_content=result["data"].get("text_content", "")
        )

        if email_result["success"]:
            return {
                "code": 200,
                "message": f"邮件生成并发送成功，已发送到 {len(request.to_emails)} 个收件人",
                "data": {
                    "subject": result["data"].get("subject", "通知"),
                    "recipients": request.to_emails,
                    "html_content": result["data"].get("html_content", ""),
                    "text_content": result["data"].get("text_content", "")
                }
            }
        else:
            raise HTTPException(status_code=400, detail=email_result["message"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成并发送邮件API异常: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"生成并发送邮件失败: {str(e)}")

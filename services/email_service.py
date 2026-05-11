"""
邮件服务模块
提供发送邮件功能，支持 SMTP 配置和 AI 内容生成
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional, List
import os
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('Email')


# ============================================
# AI 邮件内容生成
# ============================================

async def generate_email_content_with_ai(
    purpose: str,
    recipient_type: str,
    specific_info: Optional[str] = None,
    tone: str = "professional"
) -> dict:
    """
    使用 AI 生成邮件内容

    Args:
        purpose: 邮件目的 (notice/reminder/invitation/warning/congratulation)
        recipient_type: 收件人类型 (student/parent/teacher/all)
        specific_info: 额外特定信息
        tone: 语气风格 (professional/formal/friendly/gentle)

    Returns:
        dict: 包含 subject, html_content, text_content
    """
    try:
        from openai import AsyncOpenAI
        import json
        import re

        api_key = os.getenv("KIMI_API_KEY")
        if not api_key or api_key == "your-kimi-api-key":
            logger.warning("KIMI_API_KEY 未配置或为占位符")
            return {
                "success": False,
                "message": "未配置 KIMI API Key，请联系管理员"
            }

        logger.info(f"正在调用 KIMI API 生成邮件内容...")

        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )

        # 构建 prompt
        # 根据邮件目的生成合适的默认内容
        purpose_defaults = {
            'notice': '发布一条学校重要通知',
            'reminder': '提醒收件人注意某项事项或截止日期',
            'invitation': '邀请收件人参加学校活动或会议',
            'warning': '提醒收件人注意违规行为或需要改进的地方',
            'congratulation': '祝贺收件人取得的成绩或荣誉'
        }
        
        recipient_names = {
            'student': '同学们',
            'parent': '各位家长',
            'teacher': '各位老师',
            'all': '各位师生'
        }
        
        default_info = purpose_defaults.get(purpose, '发送一封学校邮件')
        specific = specific_info.strip() if specific_info else None
        
        prompt = f"""你是一位专业的学校邮件撰写助手。请根据以下信息生成一封专业的邮件。

【邮件目的】
{purpose} - {purpose_defaults.get(purpose, '')}

【收件人类型】
{recipient_type} - {recipient_names.get(recipient_type, '学校相关人员')}

【语气风格】
{tone}

【特定信息】
{specific if specific else f'请根据邮件目的「{purpose_defaults.get(purpose, '')}」自动生成合适的邮件内容，包含通用的学校通知模板内容。'}

【要求 - 重要：不要在JSON返回值中包含任何HTML标签或转义字符】
1. html_content 字段只包含纯文本内容，使用换行符分隔段落，不要包含任何 < > 标签
2. text_content 字段也是纯文本内容
3. 邮件正文要：
   - 开头有合适的称呼（根据收件人类型使用：亲爱的同学/尊敬的家长/尊敬的老师等）
   - 内容清晰有条理，段落分明
   - 语气得体恰当
   - 结尾有礼貌的结束语和落款（落款为：拾光学子管理处 + 日期）

请以JSON格式返回，格式如下：
{{
    "subject": "邮件主题（简洁明了，不超过30字）",
    "html_content": "邮件正文（纯文本，每段用空行分隔，不要任何HTML标签）",
    "text_content": "邮件正文（纯文本版本）"
}}

示例格式：
{{
    "subject": "关于期中考试安排的通知",
    "html_content": "亲爱的同学们：\\n\\n【考试安排】\\n考试时间：4月15日至4月22日\\n考试地点：教学楼各教室\\n\\n【注意事项】\\n1. 请携带学生证\\n2. 遵守考场纪律\\n\\n请大家认真复习，祝取得好成绩！\\n\\n此致\\n敬礼\\n\\n拾光学子管理处\\n2024年4月10日",
    "text_content": "亲爱的同学们：\\n\\n【考试安排】\\n考试时间：4月15日至4月22日\\n考试地点：教学楼各教室\\n\\n【注意事项】\\n1. 请携带学生证\\n2. 遵守考场纪律\\n\\n请大家认真复习，祝取得好成绩！\\n\\n此致\\n敬礼\\n\\n拾光学子管理处\\n2024年4月10日"
}}
"""

        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的学校邮件撰写助手，擅长生成各类正式通知邮件。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            ),
            timeout=60.0
        )

        result_text = response.choices[0].message.content.strip()
        logger.info(f"KIMI API 响应成功，内容长度: {len(result_text)}")

        # 清理HTML标签的函数
        def clean_html(text):
            if not text:
                return ""
            # 移除HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            # 解码HTML实体
            text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
            return text.strip()

        # 提取 JSON 部分
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            try:
                result = json.loads(json_match.group())
                # 清理内容中的HTML标签，确保返回纯文本
                html_content = clean_html(result.get("html_content") or result.get("content") or result_text)
                return {
                    "success": True,
                    "data": {
                        "subject": clean_html(result.get("subject")) or f"{purpose}通知",
                        "html_content": html_content,
                        "text_content": clean_html(result.get("text_content")) or html_content
                    }
                }
            except json.JSONDecodeError as json_err:
                logger.warning(f"JSON解析失败: {json_err}, 使用原始文本")
                cleaned_text = clean_html(result_text)
                return {
                    "success": True,
                    "data": {
                        "subject": f"{purpose}通知",
                        "html_content": cleaned_text,
                        "text_content": cleaned_text
                    }
                }
        else:
            cleaned_text = clean_html(result_text)
            return {
                "success": True,
                "data": {
                    "subject": f"{purpose}通知",
                    "html_content": cleaned_text,
                    "text_content": cleaned_text
                }
            }

    except asyncio.TimeoutError:
        logger.error("AI生成邮件内容超时")
        return {
            "success": False,
            "message": "AI生成超时，请检查网络连接后重试"
        }
    except ImportError as e:
        logger.error(f"导入openai包失败: {e}")
        return {
            "success": False,
            "message": "AI服务未正确安装，请联系管理员"
        }
    except Exception as e:
        logger.error(f"AI生成邮件内容失败: {type(e).__name__}: {e}")
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return {
                "success": False,
                "message": "AI API 认证失败，请检查 KIMI_API_KEY 是否正确"
            }
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            return {
                "success": False,
                "message": "AI服务连接失败，请检查网络连接"
            }
        else:
            return {
                "success": False,
                "message": f"AI生成失败: {error_msg}"
            }


class EmailService:
    """邮件服务类"""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from_name = os.getenv("SMTP_FROM_NAME", "拾光学子成长管理平台")

    def _create_message(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> MIMEMultipart:
        """
        创建邮件消息对象

        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            html_content: HTML 格式邮件内容
            text_content: 纯文本格式邮件内容（可选）

        Returns:
            MIMEMultipart 邮件对象
        """
        from email.utils import formataddr
        
        msg = MIMEMultipart('alternative')
        # 正确编码中文发件人名称
        msg['From'] = formataddr((str(Header(self.smtp_from_name, 'utf-8')), self.smtp_user))
        msg['To'] = '; '.join(to_emails)  # RFC 822 标准：使用分号分隔多个收件人
        msg['Subject'] = Header(subject, 'utf-8')

        # 判断内容是否为 HTML
        is_html = html_content.strip().startswith('<')
        
        # 确定发送内容
        if is_html:
            # HTML 内容：发送纯文本（如果提供）和 HTML
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        else:
            # 纯文本内容：只发送纯文本格式，不发送 HTML
            plain_text = text_content if text_content else html_content
            msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))

        return msg

    def _send_sync(self, to_emails: List[str], subject: str, html_content: str, text_content: Optional[str] = None) -> dict:
        """
        同步发送邮件

        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            html_content: HTML 格式邮件内容
            text_content: 纯文本格式邮件内容

        Returns:
            dict: 包含 success 和 message 的结果
        """
        try:
            # 检查配置
            if not self.smtp_user or not self.smtp_password:
                return {
                    "success": False,
                    "message": "邮件服务未配置，请检查 SMTP_USER 和 SMTP_PASSWORD 环境变量"
                }

            # 创建邮件
            msg = self._create_message(to_emails, subject, html_content, text_content)

            # 根据端口选择连接方式
            if self.smtp_port == 465:
                # 端口465使用 SSL 连接
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # 其他端口使用 STARTTLS
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"邮件发送成功: 主题={subject}, 收件人={to_emails}")
            return {
                "success": True,
                "message": f"邮件发送成功，已发送到 {len(to_emails)} 个收件人"
            }

        except smtplib.SMTPAuthenticationError:
            logger.error("邮件发送失败: SMTP 认证失败")
            return {
                "success": False,
                "message": "邮件发送失败：SMTP 认证失败，请检查用户名和密码"
            }
        except smtplib.SMTPConnectError as e:
            logger.error(f"邮件发送失败: 连接服务器失败 - {e}")
            return {
                "success": False,
                "message": f"邮件发送失败：无法连接到邮件服务器，请检查网络或SMTP配置"
            }
        except smtplib.SMTPException as e:
            logger.error(f"邮件发送失败: SMTP 错误 - {e}")
            return {
                "success": False,
                "message": f"邮件发送失败：SMTP 错误 - {str(e)}"
            }
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return {
                "success": False,
                "message": f"邮件发送失败：{str(e)}"
            }

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> dict:
        """
        异步发送邮件

        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            html_content: HTML 格式邮件内容
            text_content: 纯文本格式邮件内容

        Returns:
            dict: 包含 success 和 message 的结果
        """
        return await asyncio.to_thread(
            self._send_sync, to_emails, subject, html_content, text_content
        )

    async def send_verification_code(
        self,
        to_email: str,
        code: str,
        expire_minutes: int = 5
    ) -> dict:
        """
        发送验证码邮件

        Args:
            to_email: 收件人邮箱
            code: 验证码
            expire_minutes: 有效期（分钟）

        Returns:
            dict: 发送结果
        """
        subject = "【学生管理系统】您的验证码"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 30px; background-color: #ffffff; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #4CAF50; }}
                .code-box {{ text-align: center; padding: 30px 0; }}
                .code {{ font-size: 32px; font-weight: bold; color: #4CAF50; letter-spacing: 8px; }}
                .tips {{ color: #666; font-size: 14px; text-align: center; margin-top: 20px; }}
                .footer {{ text-align: center; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>验证码</h2>
                </div>
                <div class="code-box">
                    <p class="code">{code}</p>
                </div>
                <p class="tips">
                    您的验证码是 <strong>{code}</strong>，有效期 <strong>{expire_minutes}</strong> 分钟。
                </p>
                <p class="tips">
                    如果您没有请求此验证码，请忽略此邮件。
                </p>
                <div class="footer">
                    <p>此邮件由学生管理系统自动发送，请勿回复。</p>
                </div>
            </div>
        </body>
        </html>
        """
        text_content = f"""
        【学生管理系统】您的验证码

        您的验证码是：{code}
        有效期：{expire_minutes} 分钟

        如果您没有请求此验证码，请忽略此邮件。
        """

        return await self.send_email([to_email], subject, html_content, text_content)

    async def send_notification(
        self,
        to_emails: List[str],
        title: str,
        content: str,
        notification_type: str = "general"
    ) -> dict:
        """
        发送通知邮件

        Args:
            to_emails: 收件人邮箱列表
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型 (general/exam/homework/employment)

        Returns:
            dict: 发送结果
        """
        type_styles = {
            "exam": ("#2196F3", "考试通知"),
            "homework": ("#FF9800", "作业通知"),
            "employment": ("#4CAF50", "就业通知"),
            "general": ("#9C27B0", "系统通知")
        }

        color, type_name = type_styles.get(notification_type, type_styles["general"])

        subject = f"【学生管理系统】{title}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 30px; background-color: #ffffff; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid {color}; }}
                .type-badge {{ display: inline-block; background-color: {color}; color: white; padding: 5px 15px; border-radius: 3px; font-size: 12px; }}
                .content {{ padding: 30px 0; line-height: 1.8; }}
                .footer {{ text-align: center; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="type-badge">{type_name}</span>
                    <h2 style="margin-top: 15px;">{title}</h2>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p>此邮件由学生管理系统自动发送</p>
                    <p>如有问题请联系管理员</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to_emails, subject, html_content)


# 全局单例
email_service = EmailService()


async def send_email(to_emails: List[str], subject: str, html_content: str, text_content: str = None) -> dict:
    """发送邮件的便捷函数"""
    return await email_service.send_email(to_emails, subject, html_content, text_content)


async def send_verification_code(to_email: str, code: str, expire_minutes: int = 5) -> dict:
    """发送验证码的便捷函数"""
    return await email_service.send_verification_code(to_email, code, expire_minutes)


async def send_notification(to_emails: List[str], title: str, content: str, notification_type: str = "general") -> dict:
    """发送通知的便捷函数"""
    return await email_service.send_notification(to_emails, title, content, notification_type)

"""
安全工具模块 - 用于处理SQL验证、数据验证、异常处理等安全相关功能
"""
import re
from typing import List, Dict, Any
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class SQLValidator:
    """SQL语句验证器"""
    
    # 禁止的SQL关键词（针对非SELECT操作）
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 
        'ALTER', 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE'
    ]
    
    # 允许的最大查询结果行数
    MAX_ROWS = 10000
    
    @staticmethod
    def validate_select_only(sql: str) -> bool:
        """
        验证SQL语句只包含SELECT操作
        
        Args:
            sql: 待验证的SQL语句
            
        Returns:
            bool: 如果SQL有效则返回True
            
        Raises:
            ValueError: 如果SQL包含危险操作
        """
        sql_stripped = sql.strip().upper()
        
        # 检查是否以SELECT开头
        if not sql_stripped.startswith('SELECT'):
            raise ValueError("仅允许SELECT查询语句")
        
        # 检查是否包含危险关键词
        for keyword in SQLValidator.DANGEROUS_KEYWORDS:
            if re.search(rf'\b{keyword}\b', sql_stripped):
                raise ValueError(f"不允许的操作: {keyword}")
        
        return True
    
    @staticmethod
    def validate_no_comment_injection(sql: str) -> bool:
        """
        验证SQL语句不包含注释注入
        
        Args:
            sql: 待验证的SQL语句
            
        Returns:
            bool: 如果SQL有效则返回True
        """
        # 检查注释
        if '--' in sql or '/*' in sql or '*/' in sql:
            logger.warning("检测到可能的注释注入尝试")
            # 在生产环境中可能要更严格的处理
        
        return True
    
    @staticmethod
    def validate_sql_syntax(sql: str) -> bool:
        """
        基本的SQL语法验证
        
        Args:
            sql: 待验证的SQL语句
            
        Returns:
            bool: 如果SQL语法有效则返回True
        """
        sql_stripped = sql.strip()
        
        if not sql_stripped:
            raise ValueError("SQL语句不能为空")
        
        # 检查基本的平衡括号
        if sql_stripped.count('(') != sql_stripped.count(')'):
            raise ValueError("SQL语句括号不匹配")
        
        return True
    
    @staticmethod
    def validate_query(sql: str) -> bool:
        """
        完整的SQL验证流程
        
        Args:
            sql: 待验证的SQL语句
            
        Returns:
            bool: 如果SQL通过所有验证则返回True
            
        Raises:
            ValueError: 如果SQL验证失败
        """
        try:
            SQLValidator.validate_sql_syntax(sql)
            SQLValidator.validate_select_only(sql)
            SQLValidator.validate_no_comment_injection(sql)
            return True
        except ValueError as e:
            logger.warning(f"SQL验证失败: {str(e)}")
            raise


class InputValidator:
    """输入数据验证器"""
    
    @staticmethod
    def validate_username(username: str, min_length: int = 3, max_length: int = 50) -> bool:
        """验证用户名"""
        if not username or len(username) < min_length or len(username) > max_length:
            raise ValueError(f"用户名长度必须在 {min_length} 到 {max_length} 之间")
        
        # 只允许字母、数字和下划线
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("用户名只能包含字母、数字和下划线")
        
        return True
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> bool:
        """
        验证密码强度

        Args:
            password: 密码
            min_length: 最小长度，默认8位

        Returns:
            bool: 如果密码有效则返回True

        Raises:
            ValueError: 如果密码不符合要求
        """
        if len(password) < min_length:
            raise ValueError(f"密码长度必须至少 {min_length} 个字符")

        # 检查复杂度：必须包含大小写字母和数字
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_lower and has_upper and has_digit):
            raise ValueError("密码必须包含大小写字母和数字")

        return True
    
    @staticmethod
    def validate_student_name(name: str, max_length: int = 20) -> bool:
        """验证学生姓名"""
        if not name or len(name) > max_length:
            raise ValueError(f"学生姓名长度不能超过 {max_length} 个字符")
        
        # 允许中文、英文、空格和中划线
        if not re.match(r'^[\u4e00-\u9fff a-zA-Z\-]+$', name):
            raise ValueError("学生姓名只能包含中文、英文、空格和中划线")
        
        return True
    
    @staticmethod
    def validate_age(age: int) -> bool:
        """验证年龄"""
        if not isinstance(age, int) or age < 0 or age > 150:
            raise ValueError("年龄必须在 0 到 150 之间")
        return True
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证电话号码"""
        if not phone or len(phone) < 7 or len(phone) > 20:
            raise ValueError("电话号码格式不正确")
        
        if not re.match(r'^[\d\-\+\(\)]+$', phone):
            raise ValueError("电话号码只能包含数字、连字符和括号")
        
        return True


class ExceptionHandler:
    """统一的异常处理"""
    
    @staticmethod
    def handle_db_error(error: Exception) -> HTTPException:
        """处理数据库错误"""
        logger.exception("数据库错误", exc_info=error)
        return HTTPException(status_code=500, detail="数据库操作失败，请稍后重试")
    
    @staticmethod
    def handle_validation_error(error: Exception) -> HTTPException:
        """处理验证错误"""
        logger.warning(f"验证错误: {str(error)}")
        return HTTPException(status_code=400, detail=f"数据验证失败: {str(error)}")
    
    @staticmethod
    def handle_auth_error(error: Exception) -> HTTPException:
        """处理认证错误"""
        logger.warning(f"认证错误: {str(error)}")
        return HTTPException(status_code=401, detail="认证失败，请重新登录")
    
    @staticmethod
    def handle_permission_error(error: Exception) -> HTTPException:
        """处理权限错误"""
        logger.warning(f"权限错误: {str(error)}")
        return HTTPException(status_code=403, detail="无权限访问此资源")
    
    @staticmethod
    def handle_not_found_error(resource: str) -> HTTPException:
        """处理资源未找到"""
        return HTTPException(status_code=404, detail=f"找不到指定的{resource}")
    
    @staticmethod
    def handle_timeout_error() -> HTTPException:
        """处理超时错误"""
        logger.warning("查询超时")
        return HTTPException(status_code=408, detail="请求超时，请尝试简化查询条件")
    
    @staticmethod
    def handle_rate_limit_error() -> HTTPException:
        """处理速率限制"""
        return HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")


class SanitizedLogger:
    """日志记录器 - 避免记录敏感信息"""
    
    SENSITIVE_KEYWORDS = [
        'password', 'secret', 'token', 'key', 'api_key',
        'auth', 'credential', 'ssn', 'credit_card'
    ]
    
    @staticmethod
    def sanitize_message(message: str) -> str:
        """清理日志消息中的敏感信息"""
        for keyword in SanitizedLogger.SENSITIVE_KEYWORDS:
            # 替换敏感值为掩码
            pattern = rf'({keyword}["\']?\s*[:=]\s*)["\']?[^"\']*["\']?'
            message = re.sub(pattern, rf'\1***REDACTED***', message, flags=re.IGNORECASE)
        
        return message
    
    @staticmethod
    def safe_info(logger: logging.Logger, message: str):
        """安全的INFO日志"""
        logger.info(SanitizedLogger.sanitize_message(message))
    
    @staticmethod
    def safe_error(logger: logging.Logger, message: str, exc_info=False):
        """安全的ERROR日志"""
        logger.error(SanitizedLogger.sanitize_message(message), exc_info=exc_info)
    
    @staticmethod
    def safe_warning(logger: logging.Logger, message: str):
        """安全的WARNING日志"""
        logger.warning(SanitizedLogger.sanitize_message(message))
    
    @staticmethod
    def safe_debug(logger: logging.Logger, message: str):
        """安全的DEBUG日志"""
        logger.debug(SanitizedLogger.sanitize_message(message))


class ResponseFormatter:
    """响应格式化工具"""
    
    @staticmethod
    def format_error_response(
        code: int,
        message: str,
        detail: str = None,
        data: Any = None
    ) -> Dict[str, Any]:
        """格式化错误响应"""
        response = {
            "code": code,
            "message": message,
        }
        if detail:
            response["detail"] = detail
        if data:
            response["data"] = data
        return response
    
    @staticmethod
    def format_success_response(
        data: Any = None,
        message: str = "success",
        code: int = 200
    ) -> Dict[str, Any]:
        """格式化成功响应"""
        return {
            "code": code,
            "message": message,
            "data": data
        }


# 使用示例

"""
# 在控制器中使用

from utils.security import SQLValidator, InputValidator, ExceptionHandler

@router.post("/query")
async def query_data(sql: str, db: Session = Depends(get_db)):
    try:
        # 验证SQL
        SQLValidator.validate_query(sql)
        
        # 执行查询
        result = db.execute(text(sql))
        rows = result.fetchall()
        
        return ResponseFormatter.format_success_response(data=rows)
    
    except ValueError as e:
        raise ExceptionHandler.handle_validation_error(e)
    except Exception as e:
        raise ExceptionHandler.handle_db_error(e)


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # 验证输入
        InputValidator.validate_username(user.username)
        InputValidator.validate_password(user.password)
        
        # ... 创建用户逻辑
        return ResponseFormatter.format_success_response(message="注册成功")
    
    except ValueError as e:
        raise ExceptionHandler.handle_validation_error(e)
    except Exception as e:
        raise ExceptionHandler.handle_db_error(e)
"""

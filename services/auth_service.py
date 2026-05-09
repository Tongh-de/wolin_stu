import os
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from model.user import User

# 从环境变量读取配置
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 安全检查：禁止使用弱密钥
if not SECRET_KEY or SECRET_KEY == "fallback-secret-key-change-in-production":
    raise ValueError(
        "安全错误: SECRET_KEY 未设置或使用了默认密钥！"
        "请在 .env 文件中设置强密钥: SECRET_KEY=your-strong-secret-key-at-least-32-chars"
    )

if len(SECRET_KEY) < 32:
    raise ValueError("安全错误: SECRET_KEY 长度必须至少 32 个字符")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> User:
    """
    验证用户登录

    Args:
        db: 数据库会话
        username: 用户名
        password: 明文密码

    Returns:
        User对象或False
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 要编码的数据 (如 {"sub": username})
        expires_delta: 过期时间 delta

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    expire = datetime.now().replace(tzinfo=None) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    解码JWT令牌

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload dict，失败返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None

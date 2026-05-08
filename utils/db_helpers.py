"""
数据库会话上下文管理器
解决 get_db() 调用方式不一致的问题
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from database import get_db


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    数据库会话上下文管理器
    使用方式:
        with db_session() as db:
            students = db.query(Student).all()
    
    替代原来的:
        db = next(get_db())
        try:
            ...
        finally:
            db.close()
    """
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI依赖注入版本的数据库会话
    使用方式:
        @router.get("/students")
        async def get_students(db: Session = Depends(get_db_session)):
            ...
    """
    yield from get_db()

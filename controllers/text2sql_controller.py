import os
import re
import uuid
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import AsyncOpenAI
from pydantic import BaseModel

from database import get_db
from schemas.text2sql import (
    Text2SQLRequest, Text2SQLResponse,
    SQLExplainRequest, SQLExplainResponse,
    SQLValidateRequest, SQLValidateResponse
)

router = APIRouter(prefix="/text2sql", tags=["Text2SQL"])

# 千问API配置
client = AsyncOpenAI(
    api_key="sk-950da4fd8b9a4f3680b5ec8467afafab",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
MODEL_NAME = "qwen-plus"

# 学生管理系统数据库表结构
SCHEMA_CONTEXT = """
学生管理系统数据库表结构：

1. teacher (教师表)
   - teacher_id: int, 主键
   - teacher_name: varchar(20), 教师姓名
   - gender: varchar(2), 性别
   - phone: varchar(20), 电话
   - role: varchar(20), 角色
   - is_deleted: bool, 是否删除

2. class (班级表)
   - class_id: int, 主键
   - class_name: varchar(50), 班级名称
   - start_time: datetime, 开课时间
   - head_teacher_id: int, 班主任ID(外键->teacher)
   - is_deleted: bool, 是否删除

3. stu_basic_info (学生基本信息表)
   - stu_id: int, 主键
   - stu_name: varchar(20), 学生姓名
   - native_place: varchar(50), 籍贯
   - graduated_school: varchar(50), 毕业学校
   - major: varchar(50), 专业
   - admission_date: datetime, 入学日期
   - graduation_date: datetime, 毕业日期
   - education: varchar(20), 学历
   - age: int, 年龄
   - gender: varchar(2), 性别
   - advisor_id: int, 导师ID(外键->teacher)
   - class_id: int, 班级ID(外键->class)
   - is_deleted: bool, 是否删除

4. stu_exam_record (学生成绩表)
   - stu_id: int, 学生ID(外键->stu_basic_info, 主键之一)
   - seq_no: int, 考核序次(主键之一)
   - grade: int, 成绩
   - exam_date: date, 考核日期
   - is_deleted: int, 是否删除

5. employment (就业信息表)
   - emp_id: int, 主键
   - stu_id: int, 学生ID(外键->stu_basic_info)
   - stu_name: varchar(20), 学生姓名
   - class_id: int, 班级ID(外键->class)
   - open_time: date, 就业开放时间
   - offer_time: date, offer下发时间
   - company: varchar(50), 就业公司
   - salary: float, 薪资
   - is_deleted: bool, 是否删除

重要提示：
- 所有表的主键使用 is_deleted 字段做逻辑删除，查询时必须添加 WHERE is_deleted = 0 或 is_deleted = False
- 日期字段比较时使用 DATE() 函数
- 关联查询时使用 JOIN
"""

SYSTEM_PROMPT = """你是一个MySQL专家，专门将自然语言问题转换为SQL查询语句。

规则：
1. 只生成 SELECT 查询语句，禁止生成 INSERT、UPDATE、DELETE 等操作
2. 必须添加 WHERE is_deleted = 0 条件过滤已删除数据
3. 表名和字段名必须与提供的表结构一致
4. 如果涉及日期比较，使用 DATE() 函数
5. 如果需要关联查询，使用 JOIN
6. 只输出SQL语句，不要输出其他内容

示例：
问题：有多少学生？
SQL：SELECT COUNT(*) as count FROM stu_basic_info WHERE is_deleted = 0

问题：查询2024年入学的学生
SQL：SELECT * FROM stu_basic_info WHERE YEAR(admission_date) = 2024 AND is_deleted = 0

问题：每个班有多少学生？
SQL：SELECT c.class_name, COUNT(s.stu_id) as student_count FROM class c LEFT JOIN stu_basic_info s ON c.class_id = s.class_id AND s.is_deleted = 0 WHERE c.is_deleted = 0 GROUP BY c.class_id, c.class_name
"""


def fix_table_names(sql: str) -> str:
    """修正表名"""
    sql = re.sub(r'\bteachers\b', 'teacher', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bstudents\b', 'stu_basic_info', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bcourses\b', 'class', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bclasss\b', 'class', sql, flags=re.IGNORECASE)
    return sql


async def generate_sql(question: str) -> str:
    """调用LLM生成SQL"""
    user_prompt = f"表结构：\n{SCHEMA_CONTEXT}\n\n问题：{question}\n\n只输出SQL语句："
    
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )
    
    sql = response.choices[0].message.content.strip()
    # 移除可能的 markdown 代码块
    sql = re.sub(r'^```sql\s*', '', sql)
    sql = re.sub(r'^```\s*', '', sql)
    sql = re.sub(r'\s*```$', '', sql)
    
    return fix_table_names(sql)


async def explain_sql(sql: str) -> str:
    """解释SQL语句"""
    prompt = f"""请解释以下SQL语句的功能，用中文回答：

{sql}

回答格式：
- 查询目的：
- 涉及表：
- 查询条件：
- 返回结果：
"""
    
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300
    )
    
    return response.choices[0].message.content.strip()


def validate_sql(sql: str) -> tuple[bool, str]:
    """验证SQL是否安全（仅SELECT）"""
    sql_stripped = sql.strip().upper()
    
    if not sql_stripped.startswith('SELECT'):
        return False, "只允许 SELECT 查询语句"
    
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in sql_stripped:
            return False, f"检测到危险关键字: {keyword}"
    
    return True, "SQL验证通过"


@router.post("/", response_model=Text2SQLResponse)
async def text_to_sql(request: Text2SQLRequest, db: Session = Depends(get_db)):
    """
    自然语言转SQL查询
    
    将用户的自然语言问题转换为SQL并执行返回结果
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # 生成SQL
        sql = await generate_sql(request.question)
        
        # 安全验证
        valid, msg = validate_sql(sql)
        if not valid:
            raise HTTPException(status_code=400, detail=f"SQL验证失败: {msg}")
        
        # 执行SQL
        result = db.execute(text(sql))
        rows = result.fetchall()
        
        if not rows:
            return Text2SQLResponse(
                sql=sql,
                data=[],
                count=0,
                message="查询成功，无数据",
                session_id=session_id
            )
        
        # 转换为字典
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]
        
        # 限制结果数量
        limit = request.limit or 100
        data = data[:limit]
        count = len(data)
        
        return Text2SQLResponse(
            sql=sql,
            data=data,
            count=count,
            message=f"查询成功，返回 {count} 条数据",
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.post("/explain", response_model=SQLExplainResponse)
async def sql_explain(request: SQLExplainRequest):
    """
    SQL语句解释
    
    解释生成的SQL语句含义
    """
    try:
        explanation = await explain_sql(request.sql)
        return SQLExplainResponse(
            sql=request.sql,
            explanation=explanation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解释失败: {str(e)}")


@router.post("/validate", response_model=SQLValidateResponse)
async def sql_validate(request: SQLValidateRequest):
    """
    SQL语句验证
    
    验证SQL语句是否安全合法
    """
    valid, message = validate_sql(request.sql)
    return SQLValidateResponse(
        valid=valid,
        message=message,
        sql=request.sql
    )


@router.get("/schema")
async def get_schema():
    """
    获取数据库表结构
    
    返回学生管理系统的完整表结构信息
    """
    return {
        "schema": SCHEMA_CONTEXT,
        "tables": [
            {"name": "teacher", "description": "教师表"},
            {"name": "class", "description": "班级表"},
            {"name": "stu_basic_info", "description": "学生基本信息表"},
            {"name": "stu_exam_record", "description": "学生成绩表"},
            {"name": "employment", "description": "就业信息表"}
        ]
    }

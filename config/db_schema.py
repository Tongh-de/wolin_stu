"""
数据库表结构配置
统一管理数据库表结构信息，支持动态扩展
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TableField:
    """表字段定义"""
    name: str           # 字段名
    type: str           # 字段类型
    description: str    # 字段描述
    nullable: bool = True      # 是否可为空
    primary_key: bool = False  # 是否主键
    foreign_key: Optional[str] = None  # 外键关联


@dataclass
class TableSchema:
    """表结构定义"""
    name: str                    # 表名
    description: str             # 表描述
    fields: List[TableField]      # 字段列表
    alias: List[str] = field(default_factory=list)  # 常用别名


# ============================================
# 数据库表结构定义
# ============================================

DATABASE_SCHEMA = {
    "teacher": TableSchema(
        name="teacher",
        description="教师信息表",
        alias=["teachers", "老师", "教师"],
        fields=[
            TableField("teacher_id", "INT", "教师ID", primary_key=True),
            TableField("teacher_name", "VARCHAR", "教师姓名"),
            TableField("gender", "VARCHAR", "性别"),
            TableField("phone", "VARCHAR", "联系电话"),
            TableField("role", "VARCHAR", "角色/职务"),
            TableField("is_deleted", "TINYINT", "是否删除"),
        ]
    ),

    "class": TableSchema(
        name="class",
        description="班级信息表",
        alias=["classes", "班级"],
        fields=[
            TableField("class_id", "INT", "班级ID", primary_key=True),
            TableField("class_name", "VARCHAR", "班级名称"),
            TableField("start_time", "DATETIME", "开班时间"),
            TableField("head_teacher_id", "INT", "班主任ID", foreign_key="teacher.teacher_id"),
            TableField("is_deleted", "TINYINT", "是否删除"),
        ]
    ),

    "stu_basic_info": TableSchema(
        name="stu_basic_info",
        description="学生基本信息表",
        alias=["students", "学生", "stu_info"],
        fields=[
            TableField("stu_id", "INT", "学生ID", primary_key=True),
            TableField("stu_name", "VARCHAR", "学生姓名"),
            TableField("native_place", "VARCHAR", "籍贯"),
            TableField("graduated_school", "VARCHAR", "毕业学校"),
            TableField("major", "VARCHAR", "专业"),
            TableField("admission_date", "DATE", "入学日期"),
            TableField("graduation_date", "DATE", "毕业日期"),
            TableField("education", "VARCHAR", "学历"),
            TableField("age", "INT", "年龄"),
            TableField("gender", "VARCHAR", "性别"),
            TableField("advisor_id", "INT", "导师ID", foreign_key="teacher.teacher_id"),
            TableField("class_id", "INT", "班级ID", foreign_key="class.class_id"),
            TableField("is_deleted", "TINYINT", "是否删除"),
        ]
    ),

    "stu_exam_record": TableSchema(
        name="stu_exam_record",
        description="学生成绩记录表",
        alias=["exam_records", "成绩", "exam", "scores"],
        fields=[
            TableField("id", "INT", "记录ID", primary_key=True),
            TableField("stu_id", "INT", "学生ID", foreign_key="stu_basic_info.stu_id"),
            TableField("seq_no", "INT", "序号/学期"),
            TableField("grade", "FLOAT", "成绩分数"),
            TableField("exam_date", "DATE", "考试日期"),
            TableField("is_deleted", "TINYINT", "是否删除"),
        ]
    ),

    "employment": TableSchema(
        name="employment",
        description="学生就业信息表",
        alias=["employments", "就业", "jobs"],
        fields=[
            TableField("emp_id", "INT", "就业记录ID", primary_key=True),
            TableField("stu_id", "INT", "学生ID", foreign_key="stu_basic_info.stu_id"),
            TableField("stu_name", "VARCHAR", "学生姓名"),
            TableField("class_id", "INT", "班级ID", foreign_key="class.class_id"),
            TableField("open_time", "DATETIME", "开始时间"),
            TableField("offer_time", "DATETIME", "收到offer时间"),
            TableField("company", "VARCHAR", "就业公司"),
            TableField("salary", "VARCHAR", "薪资"),
            TableField("is_deleted", "TINYINT", "是否删除"),
        ]
    ),
}


def generate_schema_text(include_deleted_filter: bool = True) -> str:
    """
    生成用于 NL2SQL 的表结构文本

    Args:
        include_deleted_filter: 是否包含 is_deleted 过滤说明

    Returns:
        格式化的表结构描述文本
    """
    lines = ["数据库表结构："]

    for table_name, schema in DATABASE_SCHEMA.items():
        lines.append(f"- {schema.name}: {schema.description}")
        field_names = [f.name for f in schema.fields]
        lines.append(f"  字段: {', '.join(field_names)}")

    lines.append("")
    if include_deleted_filter:
        lines.append("重要规则：所有查询必须添加 WHERE is_deleted = 0 过滤已删除数据")
        lines.append("学生表(stu_basic_info)和成绩表(stu_exam_record)通过 stu_id 关联")

    return "\n".join(lines)


def get_table_by_alias(alias: str) -> Optional[TableSchema]:
    """根据别名查找表结构"""
    alias_lower = alias.lower()
    for schema in DATABASE_SCHEMA.values():
        if schema.name.lower() == alias_lower:
            return schema
        for a in schema.alias:
            if a.lower() == alias_lower:
                return schema
    return None


def get_all_table_names() -> List[str]:
    """获取所有表名"""
    return list(DATABASE_SCHEMA.keys())


def get_table_relationships() -> Dict[str, List[str]]:
    """获取表关系（外键）"""
    relationships = {}
    for table_name, schema in DATABASE_SCHEMA.items():
        fks = []
        for field in schema.fields:
            if field.foreign_key:
                fks.append(f"{field.name} -> {field.foreign_key}")
        if fks:
            relationships[table_name] = fks
    return relationships


# 导出兼容旧代码的常量
FALLBACK_SCHEMA = generate_schema_text()

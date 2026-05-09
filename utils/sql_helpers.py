"""
SQL工具函数
"""


def fix_table_names(sql: str) -> str:
    """
    将表别名转换为实际表名
    支持的别名：学生, 班级, 教师, 成绩, 考试, 就业, 老师
    """
    replacements = {
        '学生': 'stu_basic_info',
        '学生信息': 'stu_basic_info',
        '班级': 'class_info',
        '班级信息': 'class_info',
        '教师': 'teacher_info',
        '老师': 'teacher_info',
        '教师信息': 'teacher_info',
        '成绩': 'stu_exam_record',
        '考试': 'stu_exam_record',
        '考试记录': 'stu_exam_record',
        '就业': 'employment_info',
        '就业信息': 'employment_info',
        '学生成绩': 'stu_exam_record',
    }
    
    result = sql
    for alias, table in replacements.items():
        result = result.replace(alias, table)
    
    return result


def validate_sql_safe(sql: str) -> bool:
    """
    验证SQL是否安全（只允许SELECT）
    """
    sql_upper = sql.strip().upper()
    dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    return True

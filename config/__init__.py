"""
配置模块初始化
"""
from .agent_prompts import SYSTEM_PROMPTS, get_nl2sql_system_prompt, get_analysis_system_prompt
from .db_schema import (
    DATABASE_SCHEMA,
    TableSchema,
    TableField,
    generate_schema_text,
    get_table_by_alias,
    get_all_table_names,
    get_table_relationships,
    FALLBACK_SCHEMA
)

__all__ = [
    # Agent 提示词
    "SYSTEM_PROMPTS",
    "get_nl2sql_system_prompt",
    "get_analysis_system_prompt",
    # 数据库结构
    "DATABASE_SCHEMA",
    "TableSchema",
    "TableField",
    "generate_schema_text",
    "get_table_by_alias",
    "get_all_table_names",
    "get_table_relationships",
    "FALLBACK_SCHEMA",
]

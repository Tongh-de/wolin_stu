"""
智能路由 Agent
功能：根据用户请求类型动态选择合适的模型处理
支持 Tool Calling（工具调用）：天气查询、时间查询等

改进点：
1. 统一管理 system prompts（通过 config 模块）
2. 改进错误处理和日志
3. 消除代码重复
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Callable
import os
import asyncio
import json
import re
import time
import uuid
import httpx
from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from model.agent_memory import AgentMemory
from model.user import User
from utils.auth_deps import get_current_user

# 导入配置
from config import (
    SYSTEM_PROMPTS,
    get_nl2sql_system_prompt,
    get_analysis_system_prompt,
    FALLBACK_SCHEMA,
    generate_schema_text
)


# ============================================
# 常量定义
# ============================================

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

router = APIRouter(prefix="/agent", tags=["智能Agent"])

# 需要使用工具的意图
TOOL_INTENTS = ["weather", "time", "lindaidai", "nl2sql", "analysis", "rag"]

# Persona 到 intent 的映射
PERSONA_TO_INTENT = {
    "lindaidai": "lindaidai",
    "xueshuzhuoyou": "xueshuzhuoyou",
    "psychology": "psychology_student",
    "psychology_student": "psychology_student",
    "psychology_teacher": "psychology_teacher",
}


# ============================================
# 工具函数
# ============================================

def fix_table_names(sql: str) -> str:
    """修正表名"""
    sql = re.sub(r'\bteachers\b', 'teacher', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bstudents\b', 'stu_basic_info', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bcourses\b', 'class', sql, flags=re.IGNORECASE)
    return sql


def resolve_intent(persona: Optional[str], detected_intent: str) -> tuple[str, str]:
    """
    解析意图，处理 persona 覆盖

    Returns: (intent, reason)
    """
    if persona and persona in PERSONA_TO_INTENT:
        return PERSONA_TO_INTENT[persona], f"用户启用了 {persona} 人格"
    return detected_intent, "默认意图分类"


def get_system_prompt(intent: str, intent_type: str = "default") -> str:
    """
    获取系统提示词

    Args:
        intent: 意图类型
        intent_type: 提示词类型（default/nl2sql/analysis）

    Returns:
        系统提示词字符串
    """
    if intent_type == "nl2sql":
        return get_nl2sql_system_prompt(generate_schema_text())
    elif intent_type == "analysis":
        return get_analysis_system_prompt()
    elif intent_type == "agent":
        return SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["general"])
    else:
        return SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["general"])


# ============================================
# NL2SQL 客户端
# ============================================

_nl2sql_client = None


def get_nl2sql_client():
    """获取 NL2SQL 专用客户端（Kimi）"""
    global _nl2sql_client
    if _nl2sql_client is None:
        api_key = os.getenv("KIMI_API_KEY")
        if not api_key:
            raise ValueError("未设置 KIMI_API_KEY")
        _nl2sql_client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
            timeout=60.0
        )
    return _nl2sql_client


async def generate_sql(question: str) -> str:
    """根据问题生成 SQL"""
    client = get_nl2sql_client()
    system_prompt = get_system_prompt("", "nl2sql")

    user_prompt = f"""数据库结构：
{FALLBACK_SCHEMA}

问题：{question}

输出SQL（只输出SQL语句，不要其他内容）："""

    resp = await client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )

    sql = resp.choices[0].message.content.strip()
    sql = re.sub(r'^```sql\s*', '', sql)
    sql = re.sub(r'\s*```$', '', sql)
    return fix_table_names(sql)


async def execute_sql_to_dict(db: Session, sql: str) -> List[dict]:
    """执行 SQL 并返回字典列表"""
    def _sync():
        result = db.execute(text(sql))
        rows = result.fetchall()
        if not rows:
            return []
        return [dict(zip(result.keys(), row)) for row in rows]
    return await asyncio.to_thread(_sync)


# ============================================
# 模型配置
# ============================================

class ModelConfig:
    """可用模型配置"""

    # Kimi (NL2SQL / 闲聊)
    KIMI = {
        "name": "moonshot-v1-8k",
        "provider": "moonshot",
        "api_key": os.getenv("KIMI_API_KEY"),
        "base_url": "https://api.moonshot.cn/v1",
        "strengths": ["中文NL2SQL", "闲聊", "数据分析解释"],
        "cost": "medium"
    }

    # DeepSeek (代码 / 数学)
    DEEPSEEK = {
        "name": "deepseek-chat",
        "provider": "deepseek",
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com/v1",
        "strengths": ["代码生成", "数学计算", "复杂推理"],
        "cost": "low"
    }

    # GPT-4 (复杂推理)
    GPT4 = {
        "name": "gpt-4",
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": "https://api.openai.com/v1",
        "strengths": ["复杂推理", "多步骤任务", "高精度"],
        "cost": "high"
    }

    # Qwen (综合)
    QWEN = {
        "name": "qwen-turbo",
        "provider": "dashscope",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "strengths": ["综合问答", "知识库问答", "快速响应"],
        "cost": "low"
    }


# ============================================
# 请求/响应模型
# ============================================

class AgentRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    force_model: Optional[str] = None
    context: Optional[List[dict]] = None
    persona: Optional[str] = None
    user_id: Optional[int] = None


class AgentResponse(BaseModel):
    answer: str
    model_used: str
    provider: str
    reasoning: str
    session_id: str
    latency_ms: float
    tools_used: bool = False


class ModelInfo(BaseModel):
    name: str
    provider: str
    strengths: List[str]
    cost: str


# ============================================
# Tools 工具定义
# ============================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的实时天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称或拼音，例如：北京、上海、beijing"
                    },
                    "lang": {
                        "type": "string",
                        "description": "返回语言，zh_CN=中文，en=英文",
                        "default": "zh_CN"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前时间信息（北京时间）",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "时间格式：full=完整日期时间，date=仅日期，time=仅时间",
                        "default": "full"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_student_data",
            "description": """查询学生管理系统数据库，获取学生信息、成绩记录、就业情况、班级信息、教师信息等。
当用户询问以下类型问题时必须使用此工具：
- 查询学生信息（有多少学生、某个学生信息等）
- 查询成绩（成绩排名、最高分、最低分、平均分、某学生成绩等）
- 查询班级信息（班级列表、班级人数等）
- 查询教师信息（老师名单、某个老师信息等）
- 查询就业信息（就业率、就业公司等）
- 任何涉及数据库数据的统计和分析问题

输入自然语言问题，返回查询结果。""",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "用户的自然语言查询问题，例如：'查询所有学生的成绩'、'有多少男生'、'平均分是多少'"
                    }
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_knowledge_base",
            "description": "查询知识库中与问题相关的内容。当你需要回答关于文档、政策、指南等知识库相关问题时，必须使用此工具获取准确信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "用户的查询问题，例如：'毕业条件是什么'、'课程设置有哪些'、'升学指南的内容'"
                    }
                },
                "required": ["question"]
            }
        }
    }
]


# ============================================
# 工具实现函数
# ============================================

async def query_knowledge_base(question: str) -> str:
    """查询知识库获取相关内容"""
    try:
        from services.rag_complete import retrieve_relevant_chunks

        results = await asyncio.to_thread(retrieve_relevant_chunks, question, top_k=5)

        print(f"[知识库检索] 问题: {question}, 结果数量: {len(results) if results else 0}")

        if not results:
            return "【知识库检索结果为空】当前知识库中没有找到与该问题相关的内容。"

        relevant_results = [r for r in results if r.get("score", 999) < 1.5]

        print(f"[知识库检索] 过滤后相关结果: {len(relevant_results)} 条（阈值: distance < 1.5）")

        if not relevant_results:
            return "【知识库检索结果】知识库中确实没有与您问题相关的内容。我无法根据现有知识库回答这个问题。"

        formatted_results = []
        for i, chunk in enumerate(relevant_results, 1):
            content = chunk.get("content", "")
            filename = chunk.get("metadata", {}).get("filename", "未知文档")
            print(f"[知识库检索] 来源{i}: {filename}, 距离: {chunk.get('score', 0):.2f}")
            formatted_results.append(f"【来源{i}: {filename}】\n{content}")

        return "【知识库检索结果】\n" + "\n\n".join(formatted_results)
    except Exception as e:
        print(f"[知识库检索错误] {str(e)}")
        return f"【知识库查询失败】无法访问知识库，错误信息: {str(e)}。"


async def get_weather(city: str, lang: str = "zh_CN") -> str:
    """获取实时天气"""
    try:
        url = f"https://wttr.in/{city}?format=j1&lang={lang}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"获取天气失败，状态码: {resp.status_code}"

            data = resp.json()
            current = data.get("current_condition", [{}])[0]

            return json.dumps({
                "city": city,
                "temperature": f"{current.get('temp_C', '未知')}°C",
                "feels_like": f"{current.get('FeelsLikeC', '未知')}°C",
                "humidity": f"{current.get('humidity', '未知')}%",
                "weather": current.get("weatherDesc", [{}])[0].get("value", "未知"),
                "wind": f"{current.get('windspeedKmph', '未知')}km/h {current.get('winddir16Point', '未知')}"
            }, ensure_ascii=False)
    except Exception as e:
        return f"获取天气失败: {str(e)}"


async def get_current_time(format: str = "full") -> str:
    """获取当前时间（北京时间）"""
    now = datetime.now(BEIJING_TZ)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_cn = weekdays[now.weekday()]

    if format == "full":
        return now.strftime(f"%Y年%m月%d日 %H:%M:%S {weekday_cn}")
    elif format == "date":
        return now.strftime(f"%Y年%m月%d日 {weekday_cn}")
    elif format == "time":
        return now.strftime("%H:%M:%S")
    else:
        return now.strftime("%Y-%m-%d %H:%M:%S")


async def query_student_data(question: str) -> str:
    """查询学生管理系统数据库"""
    db = next(get_db())
    try:
        sql = await generate_sql(question)
        print(f"[DEBUG] 生成的SQL: {sql}")

        if not sql.strip().lower().startswith("select"):
            return "错误：只支持查询操作（SELECT）"

        data = await execute_sql_to_dict(db, sql)
        print(f"[DEBUG] 查询结果: {len(data)} 条记录")
        row_count = len(data)

        if row_count == 0:
            return "查询结果为空，没有找到匹配的数据。"

        max_sample = 10
        sample = data[:max_sample]

        if row_count <= max_sample:
            return f"查询成功，共 {row_count} 条记录：\n{json.dumps(sample, ensure_ascii=False, default=str, indent=2)}"
        else:
            return f"查询成功，共 {row_count} 条记录（显示前 {max_sample} 条）：\n{json.dumps(sample, ensure_ascii=False, default=str, indent=2)}\n\n如需查看完整数据，请缩小查询范围。"

    except Exception as e:
        error_msg = str(e)
        if "Unknown column" in error_msg or "doesn't exist" in error_msg:
            return f"查询失败：字段或表名错误，请重新描述问题。错误信息：{error_msg}"
        elif "syntax" in error_msg.lower():
            return f"查询失败：SQL语法错误，请重新描述问题。"
        else:
            return f"查询失败：{error_msg}"
    finally:
        db.close()


# 工具注册表
TOOL_FUNCTIONS: dict[str, Callable] = {
    "get_weather": get_weather,
    "get_current_time": get_current_time,
    "query_student_data": query_student_data,
    "query_knowledge_base": query_knowledge_base
}


# ============================================
# Agent 记忆功能
# ============================================

def save_agent_memory(session_id: str, user_id: int, role: str, content: str, intent: str = None, model_used: str = None):
    """保存单条对话记忆到数据库"""
    try:
        db = next(get_db())
        try:
            max_turn = db.query(AgentMemory).filter(
                AgentMemory.session_id == session_id
            ).count()

            memory = AgentMemory(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                intent=intent,
                model_used=model_used
            )
            db.add(memory)
            db.commit()
            print(f"[记忆保存] session={session_id}, user_id={user_id}, role={role}, turn={max_turn + 1}")
        finally:
            db.close()
    except Exception as e:
        print(f"[记忆保存失败] {str(e)}")


def load_agent_memory(session_id: str, user_id: int, limit: int = 10) -> List[dict]:
    """加载会话记忆（仅返回属于该用户的记忆）"""
    try:
        db = next(get_db())
        try:
            records = db.query(AgentMemory).filter(
                AgentMemory.session_id == session_id,
                AgentMemory.user_id == user_id
            ).order_by(AgentMemory.created_at.desc()).limit(limit * 2).all()

            records = list(reversed(records))
            messages = [r.to_dict() for r in records]
            print(f"[记忆加载] session={session_id}, user_id={user_id}, 加载 {len(messages)} 条消息")
            return messages
        finally:
            db.close()
    except Exception as e:
        print(f"[记忆加载失败] {str(e)}")
        return []


def clear_agent_memory(session_id: str, user_id: int) -> bool:
    """清除会话记忆（仅清除属于该用户的记忆）"""
    try:
        db = next(get_db())
        try:
            db.query(AgentMemory).filter(
                AgentMemory.session_id == session_id,
                AgentMemory.user_id == user_id
            ).delete()
            db.commit()
            print(f"[记忆清除] session={session_id}, user_id={user_id}")
            return True
        finally:
            db.close()
    except Exception as e:
        print(f"[记忆清除失败] {str(e)}")
        return False


def get_memory_count(session_id: str, user_id: int) -> int:
    """获取会话记忆条数"""
    try:
        db = next(get_db())
        try:
            return db.query(AgentMemory).filter(
                AgentMemory.session_id == session_id,
                AgentMemory.user_id == user_id
            ).count()
        finally:
            db.close()
    except:
        return 0


# ============================================
# 意图分类
# ============================================
_clients = {}


def get_client(provider: str, config: dict) -> AsyncOpenAI:
    """获取或创建模型客户端"""
    if provider not in _clients:
        if not config["api_key"]:
            raise ValueError(f"未设置 {provider} 的 API Key")
        _clients[provider] = AsyncOpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
    return _clients[provider]


async def classify_intent(question: str) -> tuple[str, str]:
    """
    分类用户意图，返回 (intent_type, reasoning)

    意图类型:
    - nl2sql: 自然语言转SQL查询
    - code: 代码生成/分析
    - math: 数学计算
    - chat: 闲聊问答
    - rag: RAG知识库问答
    - analysis: 数据分析
    - general: 通用问答
    """
    question_lower = question.lower()
    print(f"[意图识别] 原始问题: {question}")

    question_clean = re.sub(r'[!！.?。,，、\s]', '', question_lower)

    rules = [
        # 林黛玉角色扮演（优先级最高）
        (["林黛玉", "黛玉", "红楼梦"],
         "lindaidai", "林黛玉角色扮演"),

        # NL2SQL（查询数据库）
        (["有多少", "几个", "查询", "统计", "排名", "最高", "最低", "平均",
          "学生", "班级", "老师", "成绩", "就业", "人数", "列表", "所有人"],
         "nl2sql", "包含数据库查询关键词"),

        # 代码
        (["写代码", "代码", "python", "javascript", "函数", "class", "def"],
         "code", "包含代码相关关键词"),

        # 数学
        (["计算", "数学", "+", "-", "*", "/", "等于", "求解"],
         "math", "包含数学计算关键词"),

        # RAG/知识库
        (["知识库", "文档", "上传", "入库", "检索", "查找文档", "毕业", "升学", "课程", "政策", "指南", "规定", "条件",
          "金陵十二钗", "红楼梦", "薛宝钗", "林黛玉", "贾宝玉", "王熙凤", "史湘云", "介绍", "讲解", "是什么", "有哪些", "说说", "告诉我"],
         "rag", "知识库问答请求"),

        # 数据分析
        (["分析", "为什么", "原因", "趋势", "比较", "对比"],
         "analysis", "数据分析请求"),

        # 天气查询
        (["天气", "气温", "下雨", "下雪", "冷", "热", "温度", "晴", "阴", "多云"],
         "weather", "天气相关查询"),

        # 时间查询
        (["现在几点", "时间", "几点", "今天几号", "星期几", "几月几号", "日期", "什么时候"],
         "time", "时间相关查询"),

        # 闲聊
        (["你好", "hi", "hello", "你是谁", "帮忙"],
         "chat", "闲聊/问候"),
    ]

    for keywords, intent, reason in rules:
        for kw in keywords:
            if kw in question_clean or kw in question_lower:
                print(f"[意图识别] 匹配到: intent={intent}, reason={reason}, keyword={kw}")
                return intent, reason

    print(f"[意图识别] 未匹配，返回: general")
    return "general", "通用问答请求"


# ============================================
# 模型选择策略
# ============================================

def select_model(intent: str, force_model: Optional[str] = None) -> tuple[dict, str]:
    """根据意图选择最合适的模型"""
    if force_model:
        for name, config in ModelConfig.__dict__.items():
            if not name.startswith("_") and isinstance(config, dict):
                if name.lower() == force_model.lower():
                    return config, f"强制使用模型: {name}"
        raise ValueError(f"未知模型: {force_model}")

    strategy = {
        "nl2sql": (ModelConfig.KIMI, "Kimi擅长中文NL2SQL任务"),
        "code": (ModelConfig.DEEPSEEK, "DeepSeek代码能力优秀"),
        "math": (ModelConfig.DEEPSEEK, "DeepSeek数学推理能力强"),
        "rag": (ModelConfig.QWEN, "通义千问适合RAG场景"),
        "analysis": (ModelConfig.KIMI, "Kimi擅长数据分析解释"),
        "weather": (ModelConfig.KIMI, "Kimi擅长工具调用任务"),
        "time": (ModelConfig.KIMI, "Kimi擅长工具调用任务"),
        "chat": (ModelConfig.KIMI, "Kimi闲聊体验好"),
        "lindaidai": (ModelConfig.KIMI, "林黛玉角色扮演模式"),
        "xueshuzhuoyou": (ModelConfig.KIMI, "学业卓友诗词鉴赏模式"),
        "psychology": (ModelConfig.KIMI, "心理疏导需要温暖共情的对话模式"),
        "psychology_student": (ModelConfig.KIMI, "学生心理疏导模式"),
        "psychology_teacher": (ModelConfig.KIMI, "教师心理工作辅助模式"),
        "general": (ModelConfig.QWEN, "通义千问综合能力强、性价比高"),
    }

    model, reason = strategy.get(intent, (ModelConfig.QWEN, "默认使用通义千问"))
    return model, reason


# ============================================
# LLM 调用
# ============================================

async def call_llm(client: AsyncOpenAI, model: str, messages: list,
                   temperature: float = 0.7, max_tokens: int = 2000,
                   tools: Optional[List[dict]] = None) -> dict:
    """调用 LLM，支持 Function Calling"""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools if tools else None,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            return {
                "type": "tool_call",
                "tool": tool_call.function.name,
                "arguments": json.loads(tool_call.function.arguments)
            }

        return {
            "type": "text",
            "content": message.content or ""
        }
    except Exception as e:
        print(f"[LLM调用错误] {str(e)}")
        raise


async def call_llm_with_tools(client: AsyncOpenAI, model: str, messages: list,
                               temperature: float = 0.7, max_tokens: int = 2000,
                               max_turns: int = 3) -> str:
    """支持多轮工具调用的 LLM 调用"""
    tools = TOOLS_SCHEMA

    for turn in range(max_turns):
        result = await call_llm(client, model, messages, temperature, max_tokens, tools)

        if result["type"] == "text":
            return result["content"]

        if result["type"] == "tool_call":
            tool_name = result["tool"]
            args = result["arguments"]
            print(f"[工具调用] 工具名称: {tool_name}, 参数: {args}")

            if tool_name in TOOL_FUNCTIONS:
                tool_func = TOOL_FUNCTIONS[tool_name]
                tool_result = await tool_func(**args)
                print(f"[工具调用] 返回结果长度: {len(tool_result)} 字符")

                assistant_msg = messages[-1]["content"] if messages else ""
                tool_result_msg = f"[{tool_name} 结果]: {tool_result}"

                messages.append({
                    "role": "assistant",
                    "content": assistant_msg,
                    "tool_calls": [{
                        "id": f"call_{turn}",
                        "type": "function",
                        "function": {"name": tool_name, "arguments": json.dumps(args)}
                    }]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": f"call_{turn}",
                    "content": tool_result
                })
            else:
                return f"未知工具: {tool_name}"

    return "工具调用超时，请重试"


# ============================================
# Agent 核心逻辑
# ============================================

async def run_agent_core(
    question: str,
    intent: str,
    intent_reason: str,
    persona: Optional[str],
    user_id: int = None,
    context: Optional[List[dict]] = None,
    session_id: Optional[str] = None
) -> dict:
    """
    Agent 核心处理逻辑（供 run_agent 和 agent_chat_stream 共用）

    Args:
        question: 用户问题
        intent: 意图类型
        intent_reason: 意图识别原因
        persona: 角色人格
        user_id: 用户ID
        context: 上下文
        session_id: 会话ID

    Returns:
        包含 answer, model_used, provider 等的字典
    """
    start_time = time.time()

    # 解析最终意图
    final_intent, intent_reason = resolve_intent(persona, intent)

    # 模型选择
    model_config, model_reason = select_model(final_intent)

    # 获取系统提示词
    system_prompt = get_system_prompt(final_intent, "agent")

    # 构建消息
    messages = [{"role": "system", "content": system_prompt}]

    # 添加上下文/记忆
    if context:
        for c in context:
            role = c.get("role", "user")
            content = c.get("content", "")
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})
    elif session_id and user_id:
        memory_messages = load_agent_memory(session_id, user_id)
        messages.extend(memory_messages)

    messages.append({"role": "user", "content": question})

    # 调用 LLM
    use_tools = final_intent in TOOL_INTENTS
    model_name = model_config["name"]

    try:
        client = get_client(model_config["provider"], model_config)
        if use_tools:
            answer = await call_llm_with_tools(
                client, model_config["name"], messages,
                temperature=0.7, max_tokens=2000
            )
        else:
            result = await call_llm(client, model_config["name"], messages)
            answer = result["content"] if result["type"] == "text" else str(result)
    except Exception as e:
        # 降级处理
        if model_config["provider"] != "moonshot":
            try:
                client = get_client("moonshot", ModelConfig.KIMI)
                if use_tools:
                    answer = await call_llm_with_tools(
                        client, ModelConfig.KIMI["name"], messages
                    )
                else:
                    result = await call_llm(client, ModelConfig.KIMI["name"], messages)
                    answer = result["content"] if result["type"] == "text" else str(result)
                model_config = ModelConfig.KIMI
                model_reason = "原模型失败，降级到Kimi"
                model_name = ModelConfig.KIMI["name"]
            except Exception as e2:
                raise HTTPException(500, f"LLM调用失败: {str(e2)}")
        else:
            raise HTTPException(500, f"LLM调用失败: {str(e)}")

    latency = (time.time() - start_time) * 1000

    # 保存记忆
    if session_id and user_id:
        save_agent_memory(session_id, user_id, "user", question, final_intent, model_name)
        save_agent_memory(session_id, user_id, "assistant", answer, final_intent, model_name)

    return {
        "answer": answer,
        "model_used": model_name,
        "provider": model_config["provider"],
        "reasoning": f"意图:{intent_reason} | 模型:{model_reason}",
        "latency_ms": round(latency, 2),
        "tools_used": use_tools,
        "session_id": session_id or str(uuid.uuid4()),
        "intent": final_intent,
        "intent_reason": intent_reason
    }


# ============================================
# Agent 主逻辑（非流式）
# ============================================

async def run_agent(
    question: str,
    user_id: int = None,
    context: Optional[List[dict]] = None,
    persona: Optional[str] = None,
    session_id: Optional[str] = None
) -> dict:
    """运行 Agent 处理请求"""
    session_id = session_id or str(uuid.uuid4())

    # 意图分类
    intent, intent_reason = await classify_intent(question)

    return await run_agent_core(
        question=question,
        intent=intent,
        intent_reason=intent_reason,
        persona=persona,
        user_id=user_id,
        context=context,
        session_id=session_id
    )


# ============================================
# API 路由
# ============================================

@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """列出所有可用模型"""
    models = []
    for name, config in ModelConfig.__dict__.items():
        if not name.startswith("_") and isinstance(config, dict):
            models.append(ModelInfo(
                name=name.lower(),
                provider=config["provider"],
                strengths=config["strengths"],
                cost=config["cost"]
            ))
    return models


@router.get("/route")
async def explain_route(question: str):
    """解释为什么选择某个模型"""
    intent, intent_reason = await classify_intent(question)
    model_config, model_reason = select_model(intent)

    return {
        "question": question,
        "intent": intent,
        "intent_reason": intent_reason,
        "recommended_model": model_config["name"],
        "provider": model_config["provider"],
        "model_reason": model_reason,
        "strengths": model_config["strengths"],
        "uses_tools": intent in TOOL_INTENTS
    }


@router.get("/tools")
async def list_tools():
    """列出所有可用工具"""
    tools_info = []
    for tool in TOOLS_SCHEMA:
        func = tool["function"]
        tools_info.append({
            "name": func["name"],
            "description": func["description"],
            "parameters": func["parameters"]
        })
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "tools": tools_info,
            "tool_count": len(tools_info)
        }
    }


@router.post("/tools/test")
async def test_tool(tool_name: str, params: dict = {}):
    """测试单个工具"""
    if tool_name not in TOOL_FUNCTIONS:
        return {
            "code": 400,
            "message": f"未知工具: {tool_name}",
            "available_tools": list(TOOL_FUNCTIONS.keys())
        }

    try:
        result = await TOOL_FUNCTIONS[tool_name](**params)
        return {
            "code": 200,
            "message": "调用成功",
            "data": {
                "tool": tool_name,
                "params": params,
                "result": result
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"工具调用失败: {str(e)}"
        }


# ============================================
# Agent 记忆管理 API
# ============================================

@router.get("/memory")
async def get_memory(
    session_id: str,
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """获取会话记忆（仅返回当前用户的记忆）"""
    memories = load_agent_memory(session_id, current_user.id, limit)
    count = get_memory_count(session_id, current_user.id)
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "session_id": session_id,
            "user_id": current_user.id,
            "count": count,
            "messages": memories
        }
    }


@router.delete("/memory")
async def delete_memory(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """清除会话记忆"""
    success = clear_agent_memory(session_id, current_user.id)
    return {
        "code": 200 if success else 500,
        "message": "清除成功" if success else "清除失败",
        "data": {"session_id": session_id, "user_id": current_user.id}
    }


# ============================================
# 流式对话 API
# ============================================

@router.post("/chat")
async def agent_chat_stream(
    request: AgentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    智能对话接口 - 流式输出
    """
    session_id = request.session_id or str(uuid.uuid4())
    user_id = current_user.id
    start_time = time.time()
    model_name = ""

    async def stream_generate():
        try:
            # 意图分类
            intent, intent_reason = await classify_intent(request.question)

            # 使用共享核心逻辑
            result = await run_agent_core(
                question=request.question,
                intent=intent,
                intent_reason=intent_reason,
                persona=request.persona,
                user_id=user_id,
                context=request.context,
                session_id=session_id
            )

            # 发送元数据
            latency = (time.time() - start_time) * 1000
            yield f"data: {json.dumps({
                'type': 'meta',
                'session_id': result['session_id'],
                'model_used': result['model_used'],
                'provider': result['provider'],
                'intent': result['intent'],
                'intent_reason': result['intent_reason'],
                'model_reason': result['reasoning'],
                'tools_used': result['tools_used'],
                'start_time_ms': round(latency, 2)
            }, ensure_ascii=False)}\n\n"

            # 发送答案
            yield f"data: {json.dumps({
                'type': 'answer',
                'content': result['answer']
            }, ensure_ascii=False)}\n\n"

            # 发送完成标记
            total_time = (time.time() - start_time) * 1000
            yield f"data: {json.dumps({
                'type': 'done',
                'total_time_ms': round(total_time, 2)
            }, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({
                'type': 'error',
                'content': f"处理失败: {str(e)}"
            }, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        stream_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

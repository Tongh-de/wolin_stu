"""
智能路由 Agent
功能：根据用户请求类型动态选择合适的模型处理
支持 Tool Calling（工具调用）：天气查询、时间查询等
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Literal, Callable, Any
import os
import asyncio
import json
import httpx
from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI
from dotenv import load_dotenv


# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

load_dotenv()

router = APIRouter(prefix="/agent", tags=["智能Agent"])

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
    force_model: Optional[str] = None  # 强制使用指定模型
    context: Optional[List[dict]] = None  # 上下文
    persona: Optional[str] = None  # 角色人格：lindaidai=林黛玉


class AgentResponse(BaseModel):
    answer: str
    model_used: str
    provider: str
    reasoning: str  # 为什么选择这个模型
    session_id: str
    latency_ms: float
    tools_used: bool = False  # 是否使用了工具


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
    }
]


async def get_weather(city: str, lang: str = "zh_CN") -> str:
    """
    获取实时天气
    使用 wttr.in 免费天气 API
    """
    try:
        url = f"https://wttr.in/{city}?format=j1&lang={lang}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"获取天气失败，状态码: {resp.status_code}"
            
            data = resp.json()
            current = data.get("current_condition", [{}])[0]
            
            temp_C = current.get("temp_C", "未知")
            feelsLike_C = current.get("FeelsLikeC", "未知")
            humidity = current.get("humidity", "未知")
            desc = current.get("weatherDesc", [{}])[0].get("value", "未知")
            wind_Kmph = current.get("windspeedKmph", "未知")
            wind_dir = current.get("winddir16Point", "未知")
            
            return json.dumps({
                "city": city,
                "temperature": f"{temp_C}°C",
                "feels_like": f"{feelsLike_C}°C",
                "humidity": f"{humidity}%",
                "weather": desc,
                "wind": f"{wind_Kmph}km/h {wind_dir}"
            }, ensure_ascii=False)
    except Exception as e:
        return f"获取天气失败: {str(e)}"


async def get_current_time(format: str = "full") -> str:
    """
    获取当前时间（北京时间）
    """
    # 使用北京时间 (UTC+8)
    now = datetime.now(BEIJING_TZ)

    # 星期几的中文映射
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


# 工具注册表
TOOL_FUNCTIONS: dict[str, Callable] = {
    "get_weather": get_weather,
    "get_current_time": get_current_time
}


# ============================================
# 模型客户端管理
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


# ============================================
# 意图分类
# ============================================
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
    
    # 移除常见标点和空白
    import re
    question_clean = re.sub(r'[!！.?。,，、\s]', '', question_lower)
    
    # 关键词规则
    rules = [
        # 林黛玉角色扮演（优先级最高）
        (["林黛玉", "黛玉", "红楼梦"],
         "lindaidai", "林黛玉角色扮演"),

        # NL2SQL
        (["有多少", "几个", "查询", "统计", "排名", "最高", "最低", "平均",
          "学生", "班级", "老师", "成绩", "就业"], "nl2sql", "包含数据库查询关键词"),

        # 代码
        (["写代码", "代码", "python", "javascript", "函数", "class", "def"],
         "code", "包含代码相关关键词"),

        # 数学
        (["计算", "数学", "+", "-", "*", "/", "等于", "求解"],
         "math", "包含数学计算关键词"),

        # RAG/知识库
        (["知识库", "文档", "上传", "入库", "检索", "查找文档"],
         "rag", "知识库操作请求"),

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
    
    # 优先用清理后的文本匹配林黛玉
    for keywords, intent, reason in rules:
        for kw in keywords:
            if kw in question_clean or kw in question_lower:
                return intent, reason
    
    return "general", "通用问答请求"


# ============================================
# 模型选择策略
# ============================================

# 需要使用工具的意图
TOOL_INTENTS = ["weather", "time", "lindaidai"]


def select_model(intent: str, force_model: Optional[str] = None) -> tuple[dict, str]:
    """
    根据意图选择最合适的模型

    返回: (model_config, reasoning)
    """
    if force_model:
        # 强制使用指定模型
        for name, config in ModelConfig.__dict__.items():
            if not name.startswith("_") and isinstance(config, dict):
                if name.lower() == force_model.lower():
                    return config, f"强制使用模型: {name}"
        raise ValueError(f"未知模型: {force_model}")

    # 意图匹配策略
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
    """
    调用 LLM
    支持 Function Calling
    返回: {"type": "text", "content": "..."} 或 {"type": "tool_call", "tool": "xxx", "args": {...}}
    """
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools if tools else None,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # 检查是否有工具调用
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


async def call_llm_with_tools(client: AsyncOpenAI, model: str, messages: list,
                               temperature: float = 0.7, max_tokens: int = 2000,
                               max_turns: int = 3) -> str:
    """
    支持多轮工具调用的 LLM 调用
    """
    tools = TOOLS_SCHEMA

    for turn in range(max_turns):
        result = await call_llm(client, model, messages, temperature, max_tokens, tools)

        if result["type"] == "text":
            return result["content"]

        if result["type"] == "tool_call":
            tool_name = result["tool"]
            args = result["arguments"]

            # 查找工具函数
            if tool_name in TOOL_FUNCTIONS:
                tool_func = TOOL_FUNCTIONS[tool_name]
                tool_result = await tool_func(**args)

                # 添加助手消息和工具结果
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
# Agent 主逻辑
# ============================================
async def run_agent(question: str, context: Optional[List[dict]] = None, persona: Optional[str] = None) -> dict:
    """运行 Agent 处理请求"""
    import time
    start_time = time.time()

    # 1. 意图分类
    intent, intent_reason = await classify_intent(question)

    # 如果启用了角色人格，强制使用该角色
    if persona == "lindaidai":
        intent = "lindaidai"
        intent_reason = "用户启用了林黛玉人格"
    elif persona:
        intent = persona
        intent_reason = f"用户启用了 {persona} 人格"

    # 2. 模型选择
    model_config, model_reason = select_model(intent)

    # 3. 构建消息
    system_prompts = {
        "nl2sql": """你是一个MySQL专家，根据用户问题生成SQL查询。
规则：
1. 只生成 SELECT 语句
2. 必须添加 WHERE is_deleted = 0
3. 表名使用单数形式""",

        "code": """你是一个专业程序员，根据用户需求生成代码。
规则：
1. 代码简洁规范
2. 添加必要注释
3. 考虑边界情况""",

        "math": """你是一个数学专家，精确计算并给出答案。
规则：
1. 列出计算步骤
2. 最终给出精确答案""",

        "rag": """你是一个知识库问答助手，根据提供的内容回答问题。""",

        "analysis": """你是一个数据分析专家，解释数据趋势和原因。""",

        "weather": """你是一个天气助手，当用户询问天气时，使用 get_weather 工具获取实时天气信息。
用户询问天气时，必须调用工具获取最新数据，不要编造天气信息。""",

        "time": """你是一个时间助手，当用户询问时间时，使用 get_current_time 工具获取准确时间。
用户询问时间时，必须调用工具获取当前时间。""",

        "chat": """你是一个友好的AI助手，简洁回答用户问题。""",

        "lindaidai": """【角色设定】你是林黛玉，来自《红楼梦》，才情横溢、多愁善感、体弱多病、言语犀利但内心善良。

【性格特点】
1. 说话常带诗意，善用典故
2. 敏感细腻，容易感伤
3. 言语中带点刻薄但不失温柔
4. 常常自怜"风刀霜剑严相逼"
5. 对宝玉有深厚感情但口是心非

【语言风格】
- 常用"那也未可知""偏又""大约""竟"等语气词
- 说话带点讽刺但不失礼貌
- 时常叹息、流泪、自怜
- 用典雅的语言表达情感

【行为规范】
1. 回答时体现林黛玉的性格特点
2. 可以适当引用《红楼梦》中的典故
3. 遇到宝玉相关话题会特别敏感
4. 谈论花草、诗词、月亮等话题时更有感触
5. 可以调用get_current_time获取时间，但要以黛玉的口吻回应""",

        "general": """你是一个智能助手，准确回答用户问题。
当用户询问天气或时间时，可以使用相应工具获取准确信息。"""
    }

    system_prompt = system_prompts.get(intent, system_prompts["general"])

    messages = [{"role": "system", "content": system_prompt}]

    # 添加对话历史作为上下文
    if context:
        for c in context:
            role = c.get("role", "user")
            content = c.get("content", "")
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})

    # 添加当前问题
    messages.append({"role": "user", "content": question})

    # 4. 调用 LLM（根据意图决定是否使用工具）
    use_tools = intent in TOOL_INTENTS

    try:
        client = get_client(model_config["provider"], model_config)
        if use_tools:
            answer = await call_llm_with_tools(client, model_config["name"], messages)
        else:
            result = await call_llm(client, model_config["name"], messages)
            answer = result["content"] if result["type"] == "text" else str(result)
    except Exception as e:
        # 如果首选模型失败，尝试降级到 Kimi
        if model_config["provider"] != "moonshot":
            try:
                client = get_client("moonshot", ModelConfig.KIMI)
                if use_tools:
                    answer = await call_llm_with_tools(client, ModelConfig.KIMI["name"], messages)
                else:
                    result = await call_llm(client, ModelConfig.KIMI["name"], messages)
                    answer = result["content"] if result["type"] == "text" else str(result)
                model_config = ModelConfig.KIMI
                model_reason = "原模型失败，降级到Kimi"
            except Exception as e2:
                raise HTTPException(500, f"LLM调用失败: {str(e2)}")
        else:
            raise HTTPException(500, f"LLM调用失败: {str(e)}")

    latency = (time.time() - start_time) * 1000

    return {
        "answer": answer,
        "model_used": model_config["name"],
        "provider": model_config["provider"],
        "reasoning": f"意图:{intent_reason} | 模型:{model_reason}",
        "latency_ms": round(latency, 2),
        "tools_used": use_tools
    }


# ============================================
# API 路由
# ============================================
@router.post("/chat", response_model=AgentResponse)
async def agent_chat(request: AgentRequest):
    """
    智能对话接口
    根据问题类型自动选择最合适的模型
    """
    import uuid
    
    session_id = request.session_id or str(uuid.uuid4())
    
    result = await run_agent(request.question, request.context, request.persona)
    result["session_id"] = session_id
    
    return result


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
    """
    解释为什么选择某个模型（不实际调用）
    用于调试和理解路由逻辑
    """
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

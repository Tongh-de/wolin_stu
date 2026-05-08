"""
Agent 核心功能测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestIntentClassification:
    """意图分类测试"""

    @pytest.fixture
    def classify_intent(self):
        """导入意图分类函数"""
        from services.agent_service import classify_intent
        return classify_intent

    @pytest.mark.asyncio
    async def test_nl2sql_intent(self, classify_intent):
        """测试数据库查询意图识别"""
        test_cases = [
            "查询有多少学生",
            "班级列表是什么",
            "成绩排名前十",
            "平均分是多少",
            "老师信息有哪些"
        ]
        for question in test_cases:
            intent, reason = await classify_intent(question)
            assert intent == "nl2sql", f"问题 '{question}' 应该识别为 nl2sql，实际: {intent}"

    @pytest.mark.asyncio
    async def test_weather_intent(self, classify_intent):
        """测试天气查询意图识别"""
        test_cases = [
            "今天天气怎么样",
            "北京气温多少",
            "会下雨吗"
        ]
        for question in test_cases:
            intent, reason = await classify_intent(question)
            assert intent == "weather", f"问题 '{question}' 应该识别为 weather"

    @pytest.mark.asyncio
    async def test_time_intent(self, classify_intent):
        """测试时间查询意图识别"""
        test_cases = [
            "现在几点",
            "今天几号",
            "星期几了"
        ]
        for question in test_cases:
            intent, reason = await classify_intent(question)
            assert intent == "time", f"问题 '{question}' 应该识别为 time"

    @pytest.mark.asyncio
    async def test_rag_intent(self, classify_intent):
        """测试知识库问答意图识别"""
        test_cases = [
            "毕业条件是什么",
            "课程设置有哪些",
            "升学指南的内容"
        ]
        for question in test_cases:
            intent, reason = await classify_intent(question)
            assert intent == "rag", f"问题 '{question}' 应该识别为 rag"

    @pytest.mark.asyncio
    async def test_code_intent(self, classify_intent):
        """测试代码生成意图识别"""
        test_cases = [
            "帮我写一段Python代码",
            "用javascript实现这个功能",
            "写一个函数处理数据"
        ]
        for question in test_cases:
            intent, reason = await classify_intent(question)
            assert intent == "code", f"问题 '{question}' 应该识别为 code"

    @pytest.mark.asyncio
    async def test_lindaidai_intent(self, classify_intent):
        """测试林黛玉角色意图识别"""
        test_cases = [
            "林黛玉性格如何",
            "和黛玉对话",
            "红楼梦中的黛玉"
        ]
        for question in test_cases:
            intent, reason = await classify_intent(question)
            assert intent == "lindaidai", f"问题 '{question}' 应该识别为 lindaidai"

    @pytest.mark.asyncio
    async def test_general_intent(self, classify_intent):
        """测试通用问答意图识别"""
        intent, reason = await classify_intent("随便聊聊")
        assert intent == "general", f"无法识别的问题应该返回 general，实际: {intent}"


class TestModelSelection:
    """模型选择测试"""

    @pytest.fixture
    def select_model(self):
        """导入模型选择函数"""
        from services.agent_service import select_model
        return select_model

    def test_nl2sql_uses_kimi(self, select_model):
        """NL2SQL 应该使用 Kimi"""
        model, reason = select_model("nl2sql")
        assert model["provider"] == "moonshot"

    def test_code_uses_deepseek(self, select_model):
        """代码生成应该使用 DeepSeek"""
        model, reason = select_model("code")
        assert model["provider"] == "deepseek"

    def test_rag_uses_qwen(self, select_model):
        """RAG 应该使用 Qwen"""
        model, reason = select_model("rag")
        assert model["provider"] == "dashscope"

    def test_general_uses_qwen(self, select_model):
        """通用问答默认使用 Qwen"""
        model, reason = select_model("general")
        assert model["provider"] == "dashscope"

    def test_weather_uses_kimi(self, select_model):
        """天气查询使用 Kimi"""
        model, reason = select_model("weather")
        assert model["provider"] == "moonshot"

    def test_force_model(self, select_model):
        """测试强制模型选择"""
        with patch.dict('os.environ', {"DEEPSEEK_API_KEY": "test-key"}):
            model, reason = select_model("general", force_model="deepseek")
            assert model["provider"] == "deepseek"
            assert "强制使用" in reason


class TestSystemPrompts:
    """系统提示词测试"""

    def test_all_intents_have_prompts(self):
        """验证所有意图都有对应的提示词"""
        from config.agent_prompts import SYSTEM_PROMPTS

        required_intents = [
            "nl2sql", "code", "math", "rag", "analysis",
            "weather", "time", "chat", "general",
            "lindaidai", "xueshuzhuoyou", "psychology",
            "psychology_student", "psychology_teacher"
        ]

        for intent in required_intents:
            assert intent in SYSTEM_PROMPTS, f"缺少意图 '{intent}' 的提示词"
            assert len(SYSTEM_PROMPTS[intent]) > 0, f"意图 '{intent}' 的提示词为空"

    def test_lindaidai_prompt_contains_key_elements(self):
        """验证林黛玉提示词包含关键要素"""
        from config.agent_prompts import SYSTEM_PROMPTS

        prompt = SYSTEM_PROMPTS["lindaidai"]
        assert "林黛玉" in prompt
        assert "红楼梦" in prompt
        assert "诗意" in prompt

    def test_psychology_teacher_prompt_structure(self):
        """验证心理教师提示词结构"""
        from config.agent_prompts import SYSTEM_PROMPTS

        prompt = SYSTEM_PROMPTS["psychology_teacher"]
        assert "共情" in prompt
        assert "沟通" in prompt or "话术" in prompt
        assert "教师" in prompt


class TestDatabaseSchema:
    """数据库表结构测试"""

    def test_schema_generation(self):
        """测试表结构生成"""
        from config.db_schema import generate_schema_text

        schema_text = generate_schema_text()
        assert "teacher" in schema_text
        assert "stu_basic_info" in schema_text
        assert "stu_exam_record" in schema_text
        assert "employment" in schema_text

    def test_table_by_alias(self):
        """测试通过别名查找表"""
        from config.db_schema import get_table_by_alias

        # 测试常见别名
        assert get_table_by_alias("学生") is not None
        assert get_table_by_alias("students") is not None
        assert get_table_by_alias("成绩") is not None

    def test_table_relationships(self):
        """测试表关系获取"""
        from config.db_schema import get_table_relationships

        relationships = get_table_relationships()
        assert "stu_basic_info" in relationships
        assert "stu_exam_record" in relationships

    def test_fallback_schema_constant(self):
        """测试兼容性别名"""
        from config.db_schema import FALLBACK_SCHEMA

        assert FALLBACK_SCHEMA is not None
        assert len(FALLBACK_SCHEMA) > 0


class TestToolFunctions:
    """工具函数测试"""

    @pytest.mark.asyncio
    async def test_get_current_time(self):
        """测试获取当前时间"""
        from services.agent_service import get_current_time

        result = await get_current_time("full")
        assert "年" in result
        assert "月" in result
        assert "日" in result

        result_date = await get_current_time("date")
        assert "年" in result_date

        result_time = await get_current_time("time")
        assert ":" in result_time

    @pytest.mark.asyncio
    async def test_get_weather_invalid_city(self):
        """测试无效城市天气查询"""
        from services.agent_service import get_weather

        result = await get_weather("invalid_city_xyz_12345")
        # 应该返回错误信息而不是抛出异常
        assert result is not None


class TestIntentResolution:
    """意图解析测试"""

    @pytest.fixture
    def resolve_intent(self):
        """导入意图解析函数"""
        from services.agent_service import resolve_intent
        return resolve_intent

    def test_psychology_persona(self, resolve_intent):
        """测试心理疏导 persona"""
        intent, reason = resolve_intent("psychology", "general")
        assert intent == "psychology_student"
        assert "启用了" in reason

    def test_psychology_teacher_persona(self, resolve_intent):
        """测试教师心理疏导 persona"""
        intent, reason = resolve_intent("psychology_teacher", "general")
        assert intent == "psychology_teacher"

    def test_lindaidai_persona(self, resolve_intent):
        """测试林黛玉 persona"""
        intent, reason = resolve_intent("lindaidai", "nl2sql")
        assert intent == "lindaidai"

    def test_no_persona_uses_detected(self, resolve_intent):
        """无 persona 时使用检测到的意图"""
        intent, reason = resolve_intent(None, "code")
        assert intent == "code"


# ============================================
# pytest 配置
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

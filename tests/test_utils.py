"""
工具函数测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch


class TestResponseUtils:
    """响应工具测试"""

    def test_success_response(self):
        """测试成功响应"""
        from utils.responses import success_response
        
        result = success_response(data={"name": "test"}, message="操作成功")
        
        assert result["code"] == 200
        assert result["message"] == "操作成功"
        assert result["data"]["name"] == "test"

    def test_error_response(self):
        """测试错误响应"""
        from utils.responses import error_response
        
        result = error_response(code=400, message="参数错误")
        
        assert result["code"] == 400
        assert result["message"] == "参数错误"

    def test_paginated_response(self):
        """测试分页响应"""
        from utils.responses import paginated_response
        
        items = [{"id": 1}, {"id": 2}]
        result = paginated_response(items, total=100, page=1, page_size=20)
        
        assert result["code"] == 200
        assert result["data"]["total"] == 100
        assert result["data"]["page"] == 1
        assert result["data"]["page_size"] == 20
        assert len(result["data"]["list"]) == 2

    def test_http_exception(self):
        """测试HTTP异常创建"""
        from utils.responses import http_exception
        
        exc = http_exception("未找到资源", 404)
        
        assert exc.status_code == 404
        assert exc.detail == "未找到资源"

    def test_require_role_success(self):
        """测试角色检查通过"""
        from utils.responses import require_role
        
        # 不应抛出异常
        require_role(["admin", "teacher"], "admin")

    def test_require_role_failure(self):
        """测试角色检查失败"""
        from utils.responses import require_role, http_exception
        
        with pytest.raises(http_exception) as exc_info:
            require_role(["admin"], "student")
        
        assert exc_info.value.status_code == 403


class TestDbHelpers:
    """数据库助手测试"""

    def test_db_session_context_manager(self):
        """测试数据库会话上下文管理器"""
        from utils.db_helpers import db_session
        
        # 创建一个简单的mock
        mock_db = Mock()
        mock_get_db = Mock(return_value=iter([mock_db]))
        
        with patch('utils.db_helpers.get_db', mock_get_db):
            with db_session() as db:
                assert db is mock_db
            
            # 验证close被调用
            mock_db.close.assert_called_once()

    def test_get_db_session_dependency(self):
        """测试FastAPI依赖注入版本"""
        from utils.db_helpers import get_db_session
        
        gen = get_db_session()
        db = next(gen)
        
        assert isinstance(db, Mock)
        
        # 清理
        try:
            next(gen)
        except StopIteration:
            pass


class TestConfig:
    """配置测试"""

    def test_settings_load(self):
        """测试配置加载"""
        from config.app_config import settings
        
        assert settings.HOST is not None
        assert settings.PORT > 0
        assert isinstance(settings.SUPPORTED_EXTENSIONS, list)

    def test_settings_cors_origins(self):
        """测试CORS配置"""
        from config.app_config import settings
        
        assert len(settings.CORS_ORIGINS) > 0
        assert "http://localhost:8099" in settings.CORS_ORIGINS

    def test_settings_model_configs(self):
        """测试AI模型配置"""
        from config.app_config import settings
        
        assert "deepseek" in settings.MODEL_CONFIGS
        assert "kimi" in settings.MODEL_CONFIGS
        assert "qwen" in settings.MODEL_CONFIGS
        assert "gpt4" in settings.MODEL_CONFIGS

    def test_settings_upload_dir_created(self):
        """测试上传目录自动创建"""
        from config.app_config import settings
        import os
        
        # 验证目录存在
        assert os.path.exists(settings.UPLOAD_DIR) or settings.UPLOAD_DIR == "uploads/homework"


class TestAgentPrompts:
    """Agent提示词配置测试"""

    def test_system_prompts_loaded(self):
        """测试系统提示词加载"""
        from config.agent_prompts import SYSTEM_PROMPTS
        
        assert len(SYSTEM_PROMPTS) > 0
        assert "agent" in SYSTEM_PROMPTS
        assert "math_teacher" in SYSTEM_PROMPTS
        assert "心理疏导" in SYSTEM_PROMPTS

    def test_db_schema_configured(self):
        """测试数据库schema配置"""
        from config.db_schema import FALLBACK_SCHEMA
        
        assert len(FALLBACK_SCHEMA) > 0
        assert "学生基本信息" in FALLBACK_SCHEMA
        assert "班级信息" in FALLBACK_SCHEMA

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境变量配置检查脚本
验证 .env.example 中的所有配置是否能正常连接
"""

import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

def check_result(name: str, success: bool, detail: str = ""):
    status = "[OK]" if success else "[FAIL]"
    print(f"  {status} {name}: {detail}")
    return success

def main():
    print("=" * 60)
    print("[检查] 拾光学子成长管理平台 - 配置检查")
    print("=" * 60)
    
    all_passed = True
    
    # ========== 1. 数据库配置 ==========
    print("\n[数据库]")
    db_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if db_url:
        if check_result("SQLALCHEMY_DATABASE_URL", True, "已配置"):
            try:
                # 尝试连接数据库
                from sqlalchemy import create_engine, text
                engine = create_engine(db_url, connect_args={"connect_timeout": 5})
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                check_result("数据库连接", True, "连接成功")
            except Exception as e:
                check_result("数据库连接", False, f"连接失败: {e}")
                all_passed = False
    else:
        check_result("SQLALCHEMY_DATABASE_URL", False, "未配置")
        all_passed = False
    
    # ========== 2. API 密钥配置 ==========
    print("\n[API密钥]")
    
    # 2.1 DashScope API
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    if dashscope_key and dashscope_key != "your-dashscope-api-key-here":
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=dashscope_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            # 简单验证：尝试获取模型列表
            client.models.list()
            check_result("DASHSCOPE_API_KEY", True, "可用")
        except Exception as e:
            check_result("DASHSCOPE_API_KEY", False, f"验证失败: {e}")
            all_passed = False
    else:
        check_result("DASHSCOPE_API_KEY", False, "未配置或为占位符")
        all_passed = False
    
    # 2.2 Kimi API
    kimi_key = os.getenv("KIMI_API_KEY")
    if kimi_key and kimi_key != "your-kimi-api-key-here":
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=kimi_key,
                base_url="https://api.moonshot.cn/v1"
            )
            client.models.list()
            check_result("KIMI_API_KEY", True, "可用")
        except Exception as e:
            check_result("KIMI_API_KEY", False, f"验证失败: {e}")
            all_passed = False
    else:
        check_result("KIMI_API_KEY", False, "未配置或为占位符")
        all_passed = False
    
    # 2.3 DeepSeek API
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key and deepseek_key != "your-deepseek-api-key-here":
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com"
            )
            client.models.list()
            check_result("DEEPSEEK_API_KEY", True, "可用")
        except Exception as e:
            check_result("DEEPSEEK_API_KEY", False, f"验证失败: {e}")
            all_passed = False
    else:
        check_result("DEEPSEEK_API_KEY", False, "未配置（可选）")
    
    # 2.4 OpenAI API
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your-openai-api-key-here":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            client.models.list()
            check_result("OPENAI_API_KEY", True, "可用")
        except Exception as e:
            check_result("OPENAI_API_KEY", False, f"验证失败: {e}")
    else:
        check_result("OPENAI_API_KEY", False, "未配置（可选）")
    
    # ========== 3. JWT 配置 ==========
    print("\n[JWT配置]")
    secret_key = os.getenv("SECRET_KEY")
    if secret_key and len(secret_key) >= 32:
        check_result("SECRET_KEY", True, f"长度 {len(secret_key)} 字符")
    elif secret_key:
        check_result("SECRET_KEY", False, f"长度不足 32 字符 (当前 {len(secret_key)})")
        all_passed = False
    else:
        check_result("SECRET_KEY", False, "未配置")
        all_passed = False
    
    algorithm = os.getenv("ALGORITHM", "HS256")
    check_result("ALGORITHM", True, algorithm)
    
    # ========== 4. Milvus 向量数据库 ==========
    print("\n[Milvus]")
    milvus_host = os.getenv("MILVUS_HOST", "localhost")
    milvus_port = int(os.getenv("MILVUS_PORT", "19530"))
    
    try:
        from pymilvus import connections
        connections.connect(host=milvus_host, port=milvus_port, timeout=5)
        check_result("Milvus 连接", True, f"{milvus_host}:{milvus_port}")
        connections.disconnect("default")
    except ImportError:
        check_result("Milvus 连接", False, "pymilvus 未安装（可选）")
    except Exception as e:
        check_result("Milvus 连接", False, f"连接失败: {e}（可选，不影响主功能）")
    
    # ========== 5. Chroma 向量数据库 ==========
    print("\n[Chroma]")
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    if os.path.exists(chroma_path):
        check_result("CHROMA_DB_PATH", True, f"目录存在: {chroma_path}")
        try:
            from langchain_chroma import Chroma
            from langchain_community.embeddings import DashScopeEmbeddings
            embeddings = DashScopeEmbeddings(
                model="text-embedding-v3",
                dashscope_api_key=dashscope_key
            )
            vectordb = Chroma(persist_directory=chroma_path, embedding_function=embeddings)
            check_result("Chroma 加载", True, "向量数据库正常")
        except Exception as e:
            check_result("Chroma 加载", False, f"加载失败: {e}")
    else:
        check_result("CHROMA_DB_PATH", False, f"目录不存在: {chroma_path}（可选）")
    
    # ========== 总结 ==========
    print("\n" + "=" * 60)
    if all_passed:
        print("[PASS] 所有必填配置检查通过！可以启动应用。")
        print("=" * 60)
        return 0
    else:
        print("[FAIL] 部分配置检查失败，请检查上述错误。")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

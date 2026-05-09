"""
RAG 智能问答服务
功能：
1. 文档上传 -> 滑动窗口切分 -> 向量化 -> 存入 Milvus
2. 用户提问 -> 检索相关片段 -> LLM 生成答案
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import uuid
import io
import os
import zipfile
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import logging

# 日志配置
rag_logger = logging.getLogger('RAG')

# 加载环境变量
load_dotenv()

router = APIRouter(
    prefix="/rag",
    tags=["RAG智能问答"])

# ============================================
# 配置 (从环境变量读取)
# ============================================
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))  # 必须是整数
COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "rag_knowledge")

# LLM 配置 (Moonshot Kimi)
LLM_API_KEY = os.getenv("KIMI_API_KEY")
LLM_BASE_URL = "https://api.moonshot.cn/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "moonshot-v1-8k")

# ============================================
# 懒加载变量
# ============================================
_embeddings = None
_vectorstore = None
_llm_client = None


def get_embeddings():
    """懒加载嵌入模型（使用本地 HuggingFace 模型）"""
    global _embeddings
    if _embeddings is None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceBgeEmbeddings as HuggingFaceEmbeddings
        rag_logger.info("正在加载本地嵌入模型 BAAI/bge-m3...")
        _embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        rag_logger.info("嵌入模型加载完成: BAAI/bge-m3 (本地)")
    return _embeddings


def get_vectorstore():
    """获取 Milvus 向量数据库连接"""
    global _vectorstore
    if _vectorstore is None:
        from langchain_milvus import Milvus
        rag_logger.info(f"正在连接 Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
        _vectorstore = Milvus(
            embedding_function=get_embeddings(),
            connection_args={
                "host": MILVUS_HOST,
                "port": MILVUS_PORT,
            },
            collection_name=COLLECTION_NAME,
        )
        rag_logger.info("Milvus 向量库初始化成功")
    return _vectorstore


def get_llm_client():
    """懒加载 LLM 客户端"""
    global _llm_client
    if _llm_client is None:
        from openai import AsyncOpenAI
        api_key = os.getenv("KIMI_API_KEY")
        if not api_key:
            raise ValueError("错误: 未找到 KIMI_API_KEY，请在 .env 文件中设置")
        _llm_client = AsyncOpenAI(
            api_key=api_key,
            base_url=LLM_BASE_URL
        )
        rag_logger.info(f"LLM 客户端加载完成: {LLM_MODEL}")
    return _llm_client


# ============================================
# 文档解析
# ============================================
def parse_file_content(file_bytes: bytes, filename: str) -> str:
    """解析不同格式的文件内容"""
    ext = filename.lower().split('.')[-1]

    if ext == 'txt':
        return file_bytes.decode('utf-8')
    elif ext == 'pdf':
        reader = PdfReader(io.BytesIO(file_bytes))
        return '\n'.join([page.extract_text() or '' for page in reader.pages])
    elif ext == 'docx':
        return parse_docx(file_bytes)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def parse_docx(file_bytes: bytes) -> str:
    """使用 zipfile 解析 docx 文件"""
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            with z.open('word/document.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                paragraphs = root.findall('.//w:p', ns)
                return '\n'.join([''.join(t.text or '' for t in p.findall('.//w:t', ns)) for p in paragraphs])
    except Exception as e:
        raise RuntimeError(f"解析 docx 文件失败: {e}")


# ============================================
# 滑动窗口文本切分
# ============================================
def sliding_window_split(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    使用滑动窗口切分文本

    Args:
        text: 原始文本
        chunk_size: 每个块的大小（字符数）
        overlap: 相邻块之间的重叠字符数

    Returns:
        切分后的文本块列表
    """
    if not text or len(text.strip()) == 0:
        return []

    # 清理文本
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        # 如果不是最后一块，尽量在句号、换行或逗号处断开
        if end < text_len:
            # 向前查找最近的断点
            break_point = end
            for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                if text[i] in '。.!？\n，,':
                    break_point = i + 1
                    break

            chunk = text[start:break_point].strip()
        else:
            chunk = text[start:].strip()

        if chunk:
            chunks.append(chunk)

        # 滑动窗口：下次从 (end - overlap) 开始
        start = end - overlap
        if start >= text_len:
            break

    return chunks


# ============================================
# 文档入库
# ============================================
def add_document_to_vectorstore(doc_id: str, text: str, filename: str, category: str):
    """将文档添加到 Milvus 向量库（同步函数）"""
    # 使用滑动窗口切分
    chunks = sliding_window_split(text, chunk_size=500, overlap=50)

    if not chunks:
        raise ValueError("文档内容为空，无法入库")

    rag_logger.info(f"文档 '{filename}' 切分为 {len(chunks)} 个块")

    # 准备元数据
    metadatas = [{
        "doc_id": doc_id,
        "filename": filename,
        "category": category,
        "chunk_index": i,
        "total_chunks": len(chunks)
    } for i in range(len(chunks))]

    rag_logger.info(f"开始向量化 {len(chunks)} 个文本块...")

    # 获取嵌入模型
    emb = get_embeddings()
    rag_logger.debug("嵌入模型获取成功")

    # 直接使用 pymilvus 操作
    from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
    import numpy as np

    rag_logger.info("连接 Milvus...")
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, timeout=60)
    rag_logger.info("Milvus 连接成功")

    # 检查 collection 是否存在
    if utility.has_collection(COLLECTION_NAME):
        rag_logger.info(f"Collection '{COLLECTION_NAME}' 已存在")
        collection = Collection(COLLECTION_NAME)
        
        # 检查是否缺少 text 字段（兼容旧 collection）
        schema = collection.schema
        field_names = [f.name for f in schema.fields]
        if "text" not in field_names:
            rag_logger.warning("检测到旧版 collection，缺少 text 字段，需要重建...")
            # 删除旧 collection
            collection.drop()
            utility.has_collection(COLLECTION_NAME)  # 刷新状态
            collection = None
    else:
        rag_logger.info(f"创建 Collection '{COLLECTION_NAME}'...")
        collection = None  # 标记需要创建新 collection
    
    if collection is None:
        # BGE-M3 生成 1024 维向量
        # 添加 text 字段存储原始文本内容
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),  # 存储文本内容
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="total_chunks", dtype=DataType.INT64),
        ]
        schema = CollectionSchema(fields=fields, description="RAG Knowledge Base")
        collection = Collection(name=COLLECTION_NAME, schema=schema)
        rag_logger.info("Collection 创建成功")
        
        # 创建索引（必须！）
        rag_logger.info("创建向量索引...")
        index_params = {"index_type": "IVF_FLAT", "params": {"nlist": 128}, "metric_type": "L2"}
        collection.create_index(field_name="vector", index_params=index_params)
        rag_logger.info("索引创建成功")

    # 加载 collection
    collection.load()
    rag_logger.info("Collection 已加载")

    # 生成向量 - 分批处理，每批 100 个
    rag_logger.info("正在生成向量...")
    batch_size = 100
    all_vectors = []
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_num = i // batch_size + 1
        rag_logger.info(f"  正在处理第 {batch_num}/{total_batches} 批 ({len(batch)} 个)...")
        batch_vectors = emb.embed_documents(batch)
        all_vectors.extend(batch_vectors)

    vectors = all_vectors
    rag_logger.info(f"向量生成完成，共 {len(vectors)} 个")

    # 准备插入数据（包含 text 字段）
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    vector_data = [vec.tolist() if hasattr(vec, 'tolist') else list(vec) for vec in vectors]
    texts = chunks  # 存储文本内容
    doc_ids = [m["doc_id"] for m in metadatas]
    filenames = [m["filename"] for m in metadatas]
    categories = [m["category"] for m in metadatas]
    chunk_indices = [m["chunk_index"] for m in metadatas]
    total_chunks = [m["total_chunks"] for m in metadatas]

    # 插入数据 - 分批插入
    rag_logger.info("正在插入数据到 Milvus...")
    insert_batch_size = 200
    for i in range(0, len(ids), insert_batch_size):
        end_idx = min(i + insert_batch_size, len(ids))
        rag_logger.info(f"  插入第 {i//insert_batch_size + 1} 批数据 ({i}-{end_idx})...")
        collection.insert([
            ids[i:end_idx],
            vector_data[i:end_idx],
            texts[i:end_idx],
            doc_ids[i:end_idx],
            filenames[i:end_idx],
            categories[i:end_idx],
            chunk_indices[i:end_idx],
            total_chunks[i:end_idx]
        ])
    collection.flush()
    rag_logger.info("数据插入完成!")

    # 关闭连接
    connections.disconnect(alias="default")

    rag_logger.info(f"文档 '{filename}' 已入库，共 {len(chunks)} 个向量")
    return len(chunks)


# ============================================
# 相似度检索
# ============================================
def retrieve_relevant_chunks(query: str, top_k: int = 5) -> List[dict]:
    """检索与查询最相关的文档片段"""
    from pymilvus import connections, Collection

    # 直接使用 pymilvus 检索
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, timeout=30)
    collection = Collection(COLLECTION_NAME)
    collection.load()

    # 获取嵌入模型并生成查询向量
    emb = get_embeddings()
    query_vector = emb.embed_query(query)

    # 执行搜索
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    results = collection.search(
        data=[query_vector],
        anns_field="vector",
        param=search_params,
        limit=top_k,
        output_fields=["filename", "category", "text", "doc_id", "chunk_index"]
    )

    # 整理结果
    chunks = []
    for hits in results:
        for hit in hits:
            chunks.append({
                "content": hit.entity.get("text", ""),
                "metadata": {
                    "filename": hit.entity.get("filename", ""),
                    "category": hit.entity.get("category", ""),
                    "doc_id": hit.entity.get("doc_id", ""),
                    "chunk_index": hit.entity.get("chunk_index", 0)
                },
                "score": hit.distance
            })

    connections.disconnect(alias="default")
    return chunks


# ============================================
# LLM 生成答案
# ============================================
async def generate_answer(question: str, context_chunks: List[dict]) -> str:
    """使用 LLM 基于检索到的上下文生成答案"""
    if not context_chunks:
        return "抱歉，知识库中没有找到与您问题相关的内容。"

    # 构造上下文
    context_text = "\n\n".join([
        f"【片段 {i+1}】(来源: {chunk['metadata'].get('filename', '未知')})\n{chunk['content']}"
        for i, chunk in enumerate(context_chunks)
    ])

    system_prompt = """你是一个专业的知识库问答助手。你的职责是根据提供的上下文内容，准确回答用户的问题。

回答规则：
1. 只根据提供的上下文内容回答，不要编造信息
2. 如果上下文中有相关信息，尽量完整地引用
3. 如果上下文不足以回答，可以说明"根据现有资料..."并给出可能的答案
4. 回答要简洁、有条理，突出关键信息
5. 如果确实无法从上下文找到答案，请坦诚告知用户"""

    user_prompt = f"""上下文内容：
{context_text}

用户问题：{question}

请根据以上上下文内容回答用户的问题："""

    try:
        client = get_llm_client()
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        answer = response.choices[0].message.content
        return answer
    except Exception as e:
        raise RuntimeError(f"LLM 生成答案失败: {str(e)}")


# ============================================
# API 接口
# ============================================

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    question: str


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(default="general"),
):
    """
    上传文档并入库

    - file: 文档文件 (支持 txt, pdf, docx)
    - category: 文档分类
    """
    try:
        rag_logger.info(f"收到上传请求: {file.filename}, category: {category}")

        # 读取文件
        file_bytes = await file.read()

        # 解析文档内容
        text = parse_file_content(file_bytes, file.filename)

        if not text.strip():
            return JSONResponse(
                status_code=400,
                content={"code": 400, "message": "文档内容为空"}
            )

        # 生成文档 ID
        doc_id = str(uuid.uuid4())

        # 在线程池中执行同步入库操作
        chunk_count = await asyncio.to_thread(
            add_document_to_vectorstore,
            doc_id, text, file.filename, category
        )

        return {
            "code": 200,
            "message": "文档入库成功",
            "data": {
                "doc_id": doc_id,
                "filename": file.filename,
                "category": category,
                "chunk_count": chunk_count,
                "char_count": len(text)
            }
        }

    except ValueError as e:
        return JSONResponse(status_code=400, content={"code": 400, "message": str(e)})
    except Exception as e:
        rag_logger.error(f"上传失败: {e}")
        return JSONResponse(status_code=500, content={"code": 500, "message": f"上传失败: {str(e)}"})


@router.post("/query")
async def query_knowledge(req: QueryRequest):
    """
    RAG 问答接口（流式输出）

    - question: 用户问题
    - top_k: 检索的文档块数量 (默认5)
    """
    from fastapi.responses import StreamingResponse
    import json

    async def stream_generate():
        try:
            rag_logger.info(f"收到问答请求: {req.question}")

            # 1. 检索相关文档块
            try:
                chunks = await asyncio.to_thread(retrieve_relevant_chunks, req.question, req.top_k)
                rag_logger.debug(f"检索到 {len(chunks)} 个相关片段")
            except Exception as retrieve_err:
                rag_logger.warning(f"检索失败（可能知识库为空或Milvus未启动）: {retrieve_err}")
                chunks = []

            # 2. 流式 LLM 生成答案
            if not chunks:
                yield f"data: {json.dumps({'type': 'answer', 'content': '抱歉，知识库中暂无相关内容。你可以上传相关文档后再提问。'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return

            # 构造上下文 - 限制长度避免超出token限制
            context_parts = []
            for i, chunk in enumerate(chunks):
                content = chunk['content'][:500]  # 限制每个片段长度
                source = chunk['metadata'].get('filename', '未知')
                context_parts.append(f"【{source} 内容{i+1}】{content}")
            
            context_text = "\n\n".join(context_parts)

            system_prompt = """你是一个专业的知识库问答助手。根据以下上下文内容，准确回答用户的问题。

重要规则：
1. 只根据提供的上下文内容回答，禁止编造信息
2. 如果上下文中包含相关信息，直接引用回答
3. 如果上下文不足以回答问题，请诚实说明"我没有在提供的资料中找到相关信息"
4. 回答要简洁明了，直接给出答案"""

            user_prompt = f"""【上下文】
{context_text}

【用户问题】
{req.question}

请根据上述上下文，直接回答用户的问题："""

            # 先发送 sources
            sources = [
                {
                    "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                    "filename": chunk["metadata"].get("filename", ""),
                    "category": chunk["metadata"].get("category", "")
                }
                for chunk in chunks
            ]
            yield f"data: {json.dumps({'type': 'sources', 'content': sources}, ensure_ascii=False)}\n\n"

            # 流式调用 LLM
            client = get_llm_client()
            stream = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'type': 'answer', 'content': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            rag_logger.error(f"流式问答失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'问答处理失败: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        stream_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/search")
async def search_documents(q: str, top_k: int = 5):
    """
    纯检索接口（不调用 LLM）

    - q: 搜索关键词
    - top_k: 返回结果数量
    """
    try:
        results = await asyncio.to_thread(retrieve_relevant_chunks, q, top_k)

        return {
            "code": 200,
            "message": "检索成功",
            "data": results
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "message": f"检索失败: {str(e)}"})


@router.get("/stats")
async def get_stats():
    """获取知识库统计信息"""
    try:
        # 先测试 Milvus 连接
        from pymilvus import connections, utility
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, timeout=5)
        connected = True
        connections.disconnect(alias="default")
    except Exception as e:
        rag_logger.warning(f"Milvus 连接测试失败: {e}")
        connected = False
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "connected": connected,
            "collection_name": COLLECTION_NAME,
            "milvus_host": MILVUS_HOST,
            "milvus_port": MILVUS_PORT,
            "embedding_model": "BAAI/bge-m3",
            "llm_model": LLM_MODEL
        }
    }


@router.delete("/clear")
async def clear_collection():
    """清空知识库（危险操作）"""
    try:
        from langchain_milvus import Milvus
        from pymilvus import connections, Collection

        connections.connect(host=MILVUS_HOST, port=int(MILVUS_PORT))
        collection = Collection(COLLECTION_NAME)
        collection.drop()

        global _vectorstore
        _vectorstore = None

        return {
            "code": 200,
            "message": f"知识库 '{COLLECTION_NAME}' 已清空"
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "message": f"清空失败: {str(e)}"})

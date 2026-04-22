import os
import re
import asyncio
import uuid
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import AsyncOpenAI
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from database import get_db
from services import ConversationService

load_dotenv()

router = APIRouter(prefix="/query", tags=["自然语言查询"])

# 使用千问（通义千问）API
client = AsyncOpenAI(
    api_key="sk-950da4fd8b9a4f3680b5ec8467afafab",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

vectordb = None
try:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("警告: 未设置 DASHSCOPE_API_KEY，知识库功能不可用")
    else:
        embeddings = DashScopeEmbeddings(model="text-embedding-v3", dashscope_api_key=api_key)
        if os.path.exists("./chroma_db") and os.path.isdir("./chroma_db"):
            vectordb = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
            print("向量知识库加载成功")
        else:
            print("知识库目录不存在")
except Exception as e:
    print(f"向量知识库加载失败: {e}")


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    include_history: bool = True


FALLBACK_SCHEMA = """
数据库表结构：
- teacher: teacher_id, teacher_name, gender, phone, role, is_deleted
- class: class_id, class_name, start_time, head_teacher_id, is_deleted
- stu_basic_info: stu_id, stu_name, native_place, graduated_school, major, admission_date, graduation_date, education, age, gender, advisor_id, class_id, is_deleted
- stu_exam_record: stu_id, seq_no, grade, exam_date, is_deleted
- employment: emp_id, stu_id, stu_name, class_id, open_time, offer_time, company, salary, is_deleted
"""


def fix_table_names(sql: str) -> str:
    sql = re.sub(r'\bteachers\b', 'teacher', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bstudents\b', 'stu_basic_info', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bcourses\b', 'class', sql, flags=re.IGNORECASE)
    return sql


async def similarity_search_async(vectordb, query: str, k: int = 3):
    def _sync():
        return vectordb.similarity_search(query, k=k)
    return await asyncio.to_thread(_sync)


async def retrieve_schema_context(vectordb) -> str:
    if vectordb is None:
        return FALLBACK_SCHEMA
    try:
        docs = await similarity_search_async(vectordb, "数据库表结构 字段定义 表名", k=2)
        if docs:
            return "\n\n".join([doc.page_content for doc in docs])[:4000]
    except Exception as e:
        print(f"检索表结构失败: {e}")
    return FALLBACK_SCHEMA


def summarize_result(data: List[dict], max_sample_rows: int = 3, full_save: bool = False) -> str:
    if not data:
        return json.dumps({"row_count": 0, "sample": []})
    if full_save:
        return json.dumps(data, ensure_ascii=False, default=str)
    else:
        row_count = len(data)
        sample = data[:max_sample_rows]
        stats = {}
        for key in data[0].keys():
            if isinstance(data[0].get(key), (int, float)):
                values = [row.get(key) for row in data if row.get(key) is not None]
                if values:
                    stats[key] = {"avg": sum(values)/len(values), "min": min(values), "max": max(values)}
        return json.dumps({"row_count": row_count, "sample": sample, "statistics": stats}, ensure_ascii=False, default=str)


INTENT_CLASSIFICATION_PROMPT = """
你是一个意图分类助手。根据用户问题，判断用户意图。
问题：{question}
意图选项：sql / analysis / chat

规则：
- 如果问题是关于数据查询（学生、班级、老师、成绩、就业人数、统计等），返回 sql
- 如果问题是要求解释分析数据或趋势原因，返回 analysis
- 如果是闲聊或问候，返回 chat

只输出一个单词（sql 或 analysis 或 chat）：
"""

async def classify_intent_llm(question: str, history_text: str = "") -> str:
    # 关键词优先匹配（更可靠）
    analysis_keywords = ["为什么", "原因", "怎么", "解释", "趋势", "分析一下"]
    sql_keywords = ["多少", "几个", "查询", "有多少", "统计", "排名", "最高", "最低", "平均", "所有", "找出", "看看"]
    
    question_lower = question.lower()
    
    if any(kw in question_lower for kw in sql_keywords):
        return "sql"
    if any(kw in question_lower for kw in analysis_keywords):
        return "analysis"
    
    # LLM 辅助分类
    try:
        prompt = INTENT_CLASSIFICATION_PROMPT.format(history=history_text, question=question)
        resp = await client.chat.completions.create(model="qwen-plus", messages=[{"role": "user", "content": prompt}], temperature=0, max_tokens=10)
        intent = resp.choices[0].message.content.strip().lower()
        if intent in ["sql", "analysis", "chat"]:
            return intent
    except Exception as e:
        print(f"LLM意图分类失败: {e}")
    
    return "sql"  # 默认按SQL处理


async def check_sql_reference(question: str, history_text: str) -> str:
    reference_keywords = ["刚才", "上一轮", "再查", "同样的", "也", "那个", "再次", "同样"]
    if any(kw in question for kw in reference_keywords):
        return "YES"
    return "NO"


async def generate_sql(question: str, retry: bool = False, previous_sql: Optional[str] = None) -> str:
    system = "你是一个MySQL专家，只输出SQL语句。表名都是单数。"
    if retry:
        system += " 上一次SQL执行失败，请修正。"
    schema = await retrieve_schema_context(vectordb)
    user = f"数据库结构：\n{schema}\n\n问题：{question}\n输出SQL："
    if previous_sql:
        user = f"上一轮SQL：\n{previous_sql}\n\n问题：{question}\n数据库结构：\n{schema}\n输出SQL："
    resp = await client.chat.completions.create(model="qwen-plus", messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.1)
    sql = resp.choices[0].message.content.strip()
    sql = re.sub(r'^```sql\s*', '', sql)
    sql = re.sub(r'\s*```$', '', sql)
    return fix_table_names(sql)


async def execute_sql_to_dict(db: Session, sql: str):
    def _sync():
        result = db.execute(text(sql))
        rows = result.fetchall()
        if not rows:
            return []
        return [dict(zip(result.keys(), row)) for row in rows]
    return await asyncio.to_thread(_sync)


@router.post("/natural")
async def natural_query(req: QueryRequest, db: Session = Depends(get_db)):
    question = req.question
    session_id = req.session_id or str(uuid.uuid4())
    include_history = req.include_history

    history_turns = ConversationService.get_recent_turns(db, session_id, limit=5) if include_history else []
    history_text = ""
    for turn in history_turns:
        summary = turn.result_summary[:200] if turn.result_summary else (turn.answer_text[:200] if turn.answer_text else "")
        history_text += f"用户: {turn.question}\n系统: {summary}\n"

    intent = await classify_intent_llm(question, history_text)
    turn_index = ConversationService.get_turn_count(db, session_id) + 1

    if intent == "sql":
        previous_sql_turn = None
        if history_turns:
            previous_sql_turn = ConversationService.get_previous_sql_turn(db, session_id)
        need_reference = await check_sql_reference(question, history_text) == "YES"

        try:
            if need_reference and previous_sql_turn and previous_sql_turn.sql_query:
                sql = await generate_sql(question, retry=False, previous_sql=previous_sql_turn.sql_query)
            else:
                sql = await generate_sql(question)
        except Exception as e:
            raise HTTPException(500, f"生成SQL失败: {e}")

        if not sql.strip().lower().startswith("select"):
            raise HTTPException(400, "只能生成SELECT语句")

        try:
            data = await execute_sql_to_dict(db, sql)
            row_count = len(data)
            full_save = (row_count <= 100) and (len(json.dumps(data, default=str)) <= 2000)
            result_summary = summarize_result(data, full_save=full_save)
            answer_text = f"查询成功，共{row_count}条记录。" if full_save else f"数据量较大（共{row_count}行），已存储。"
            ConversationService.save_turn(db, session_id, turn_index, question, sql_query=sql, result_summary=result_summary, answer_text=answer_text, full_data_saved=full_save)

            if full_save:
                return {"type": "sql", "session_id": session_id, "turn_index": turn_index, "sql": sql, "data": data, "count": row_count}
            else:
                return {"type": "sql", "session_id": session_id, "turn_index": turn_index, "sql": sql, "data_truncated": True, "sample_data": data[:10], "message": answer_text}
        except Exception as e:
            try:
                sql_corrected = await generate_sql(question, retry=True)
                data2 = await execute_sql_to_dict(db, sql_corrected)
                row_count2 = len(data2)
                full_save2 = (row_count2 <= 100) and (len(json.dumps(data2, default=str)) <= 2000)
                result_summary2 = summarize_result(data2, full_save=full_save2)
                answer_text2 = f"查询成功，共{row_count2}条记录。" if full_save2 else f"数据量较大"
                ConversationService.save_turn(db, session_id, turn_index, question, sql_query=sql_corrected, result_summary=result_summary2, answer_text=answer_text2, full_data_saved=full_save2)
                if full_save2:
                    return {"type": "sql", "session_id": session_id, "turn_index": turn_index, "sql": sql_corrected, "data": data2, "count": row_count2}
                else:
                    return {"type": "sql", "session_id": session_id, "turn_index": turn_index, "sql": sql_corrected, "data_truncated": True, "sample_data": data2[:10]}
            except Exception as e2:
                raise HTTPException(500, f"SQL执行失败: {str(e)}")

    elif intent == "analysis":
        latest_turn = ConversationService.get_latest_turn(db, session_id)
        data_context = ""
        if latest_turn and latest_turn.result_summary:
            try:
                if latest_turn.full_data_saved:
                    full_data = json.loads(latest_turn.result_summary)
                    data_context = f"上一轮数据（共{len(full_data)}条）：\n{json.dumps(full_data, ensure_ascii=False, indent=2)[:5000]}\n"
                else:
                    data_context = "上一轮数据量较大。\n"
            except:
                data_context = "读取数据失败。\n"

        analysis_prompt = f"你是一个数据分析专家。基于以下数据回答用户问题。\n\n数据：\n{data_context}\n\n问题：{question}\n"
        try:
            resp = await client.chat.completions.create(model="qwen-plus", messages=[{"role": "user", "content": analysis_prompt}], temperature=0.5)
            answer = resp.choices[0].message.content
            ConversationService.save_turn(db, session_id, turn_index, question, answer_text=answer)
            return {"type": "answer", "session_id": session_id, "turn_index": turn_index, "answer": answer}
        except Exception as e:
            raise HTTPException(500, f"分析失败: {str(e)}")

    else:
        chat_prompt = f"用户：{question}\n助手："
        try:
            resp = await client.chat.completions.create(model="qwen-plus", messages=[{"role": "user", "content": chat_prompt}], temperature=0.7)
            answer = resp.choices[0].message.content
            ConversationService.save_turn(db, session_id, turn_index, question, answer_text=answer)
            return {"type": "answer", "session_id": session_id, "turn_index": turn_index, "answer": answer}
        except Exception as e:
            raise HTTPException(500, f"闲聊失败: {str(e)}")

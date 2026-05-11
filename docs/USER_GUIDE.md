# 拾光学子成长管理平台 - 使用手册

## 目录

1. [系统简介](#1-系统简介)
2. [快速开始](#2-快速开始)
3. [账号与权限](#3-账号与权限)
4. [学生管理](#4-学生管理)
5. [班级管理](#5-班级管理)
6. [教师管理](#6-教师管理)
7. [考试管理](#7-考试管理)
8. [就业管理](#8-就业管理)
9. [统计分析](#9-统计分析)
10. [自然语言查询](#10-自然语言查询)
11. [智能助手](#11-智能助手)
12. [知识库问答](#12-知识库问答)
13. [常见问题](#13-常见问题)

---

## 1. 系统简介

拾光学子成长管理平台是一套面向教育机构的信息化管理平台，提供以下核心功能：

| 模块 | 功能描述 |
|------|----------|
| 学生管理 | 学生信息的增删改查，支持按学号、姓名、班级筛选 |
| 班级管理 | 班级创建、编辑、删除与恢复 |
| 教师管理 | 教师多角色管理（班主任/讲师/顾问） |
| 考试管理 | 成绩录入、修改、删除与分页查询 |
| 就业管理 | 学生就业信息跟踪记录 |
| 统计分析 | 年龄统计、班级比例、平均分排名等 |
| NL2SQL | 自然语言转 SQL 查询数据库 |
| AI 助手 | 智能对话、天气查询、角色扮演 |
| 知识库 | 文档上传与智能问答 |

### 系统入口

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8099 | 首页 |
| http://127.0.0.1:8099/docs | API 文档 (Swagger) |
| http://127.0.0.1:8099/static/index.html | 前端管理界面 |

---

## 2. 快速开始

### 2.1 环境要求

- Python 3.10+
- MySQL 5.7+
- Node.js (可选，前端开发)

### 2.2 安装步骤

**Step 1：克隆项目**

```bash
git clone <项目地址>
cd wolin-student
```

**Step 2：安装依赖**

```bash
pip install -r requirements.txt
```

**Step 3：配置环境变量**

创建 `.env` 文件，配置以下内容：

```env
# 数据库配置
SQLALCHEMY_DATABASE_URL=mysql+pymysql://用户名:密码@localhost:3306/wolin_student

# JWT 密钥 (至少32字符)
SECRET_KEY=your-strong-secret-key-at-least-32-characters

# AI API Keys
DASHSCOPE_API_KEY=your-dashscope-api-key
KIMI_API_KEY=your-kimi-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key

# 向量数据库 (可选)
MILVUS_HOST=192.168.184.128
MILVUS_PORT=19530
```

**Step 4：初始化数据库**

```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE wolin_student CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# 导入表结构
mysql -u root -p wolin_student < init_full.sql
```

**Step 5：启动服务**

```bash
python main.py
```

看到以下日志表示启动成功：

```
INFO:     Uvicorn running on http://127.0.0.1:8099
🚀 应用服务已启动
📚 Swagger文档: http://127.0.0.1:8099/docs
🌐 前端界面: http://127.0.0.1:8099/static/index.html
```

---

## 3. 账号与权限

### 3.1 角色说明

| 角色 | 说明 | 权限范围 |
|------|------|----------|
| admin | 管理员 | 全部功能，可管理所有数据 |
| teacher | 教师 | 查看和修改所管班级的数据 |
| student | 学生 | 仅可查看个人信息 |

### 3.2 注册账号

**接口：** `POST /auth/register`

```bash
curl -X POST "http://127.0.0.1:8099/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123456",
    "role": "admin"
  }'
```

**响应：**

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "username": "admin",
    "role": "admin"
  }
}
```

### 3.3 登录

**接口：** `POST /auth/login`

```bash
curl -X POST "http://127.0.0.1:8099/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123456"
  }'
```

**响应：**

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

> 保存返回的 `access_token`，后续请求需在 Header 中携带：
> ```
> Authorization: Bearer <access_token>
> ```

---

## 4. 学生管理

### 4.1 查询学生列表

**接口：** `GET /students/`

```bash
curl -X GET "http://127.0.0.1:8099/students/" \
  -H "Authorization: Bearer <token>"
```

**带条件查询：**

```bash
# 按学号查询
curl -X GET "http://127.0.0.1:8099/students/?stu_id=1" \
  -H "Authorization: Bearer <token>"

# 按姓名查询
curl -X GET "http://127.0.0.1:8099/students/?stu_name=张三" \
  -H "Authorization: Bearer <token>"

# 按班级查询
curl -X GET "http://127.0.0.1:8099/students/?class_id=1" \
  -H "Authorization: Bearer <token>"
```

### 4.2 新增学生

**接口：** `POST /students/`

> ⚠️ 仅管理员可操作

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| stu_name | string | ✅ | 学生姓名 |
| class_id | integer | ✅ | 班级ID |
| native_place | string | ✅ | 籍贯 |
| graduated_school | string | ✅ | 毕业院校 |
| major | string | ✅ | 专业 |
| admission_date | datetime | ✅ | 入学日期 |
| graduation_date | datetime | ✅ | 毕业日期 |
| education | string | ✅ | 学历 |
| advisor_id | integer | ❌ | 顾问教师ID |
| age | integer | ✅ | 年龄 |
| gender | string | ✅ | 性别 (男/女) |

**示例：**

```bash
curl -X POST "http://127.0.0.1:8099/students/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stu_name": "张三",
    "class_id": 1,
    "native_place": "北京市",
    "graduated_school": "清华大学",
    "major": "计算机科学与技术",
    "admission_date": "2024-09-01T00:00:00",
    "graduation_date": "2027-06-30T00:00:00",
    "education": "本科",
    "advisor_id": 1,
    "age": 22,
    "gender": "男"
  }'
```

### 4.3 更新学生信息

**接口：** `PUT /students/{stu_id}`

> ⚠️ 仅管理员可操作

```bash
curl -X PUT "http://127.0.0.1:8099/students/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "native_place": "上海市",
    "phone": "13800138000"
  }'
```

### 4.4 删除学生

**接口：** `DELETE /students/{stu_id}`

> ⚠️ 仅管理员可操作，执行逻辑删除

```bash
curl -X DELETE "http://127.0.0.1:8099/students/1" \
  -H "Authorization: Bearer <token>"
```

---

## 5. 班级管理

### 5.1 查询班级列表

**接口：** `GET /class/`

```bash
curl -X GET "http://127.0.0.1:8099/class/" \
  -H "Authorization: Bearer <token>"
```

### 5.2 新增班级

**接口：** `POST /class/`

> ⚠️ 仅管理员可操作

```bash
curl -X POST "http://127.0.0.1:8099/class/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "class_name": "Python开发班",
    "start_time": "2024-09-01",
    "head_teacher_id": 1
  }'
```

### 5.3 更新班级

**接口：** `PUT /class/{class_id}`

```bash
curl -X PUT "http://127.0.0.1:8099/class/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "class_name": "Python进阶班"
  }'
```

### 5.4 删除班级（逻辑删除）

**接口：** `DELETE /class/{class_id}`

```bash
curl -X DELETE "http://127.0.0.1:8099/class/1" \
  -H "Authorization: Bearer <token>"
```

### 5.5 恢复已删除班级

**接口：** `POST /class/{class_id}/restore`

```bash
curl -X POST "http://127.0.0.1:8099/class/1/restore" \
  -H "Authorization: Bearer <token>"
```

---

## 6. 教师管理

### 6.1 查询教师列表

**接口：** `GET /teachers/`

```bash
curl -X GET "http://127.0.0.1:8099/teachers/" \
  -H "Authorization: Bearer <token>"
```

### 6.2 新增教师

**接口：** `POST /teachers/`

> ⚠️ 仅管理员可操作

**教师角色说明：**

| role | 说明 |
|------|------|
| head_teacher | 班主任 |
| lecturer | 讲师 |
| counselor | 顾问 |

```bash
curl -X POST "http://127.0.0.1:8099/teachers/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_name": "李老师",
    "gender": "女",
    "phone": "13900139000",
    "role": "counselor"
  }'
```

### 6.3 更新教师

**接口：** `PUT /teachers/{teacher_id}`

```bash
curl -X PUT "http://127.0.0.1:8099/teachers/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "role": "head_teacher"
  }'
```

### 6.4 删除教师

**接口：** `DELETE /teachers/{teacher_id}`

```bash
curl -X DELETE "http://127.0.0.1:8099/teachers/1" \
  -H "Authorization: Bearer <token>"
```

---

## 7. 考试管理

### 7.1 提交成绩

**接口：** `POST /exam/`

```bash
curl -X POST "http://127.0.0.1:8099/exam/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stu_id": 1,
    "seq_no": 1,
    "grade": 95,
    "exam_date": "2024-12-01"
  }'
```

### 7.2 修改成绩

**接口：** `PUT /exam/`

```bash
curl -X PUT "http://127.0.0.1:8099/exam/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stu_id": 1,
    "seq_no": 1,
    "grade": 98
  }'
```

### 7.3 查询成绩列表

**接口：** `GET /exam/records`

```bash
# 基础查询
curl -X GET "http://127.0.0.1:8099/exam/records" \
  -H "Authorization: Bearer <token>"

# 带分页参数
curl -X GET "http://127.0.0.1:8099/exam/records?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"

# 按学号筛选
curl -X GET "http://127.0.0.1:8099/exam/records?stu_id=1" \
  -H "Authorization: Bearer <token>"
```

### 7.4 删除成绩

**接口：** `DELETE /exam/{stu_id}`

```bash
curl -X DELETE "http://127.0.0.1:8099/exam/1?seq_no=1" \
  -H "Authorization: Bearer <token>"
```

---

## 8. 就业管理

### 8.1 查询就业信息

**接口：** `GET /employment/`

```bash
curl -X GET "http://127.0.0.1:8099/employment/" \
  -H "Authorization: Bearer <token>"

# 按学生ID查询
curl -X GET "http://127.0.0.1:8099/employment/?stu_id=1" \
  -H "Authorization: Bearer <token>"
```

### 8.2 更新就业信息

**接口：** `PUT /employment/`

```bash
curl -X PUT "http://127.0.0.1:8099/employment/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stu_id": 1,
    "company": "腾讯科技",
    "salary": 25000,
    "offer_time": "2024-06-15"
  }'
```

### 8.3 就业信息字段说明

| 字段 | 说明 |
|------|------|
| stu_id | 学生ID |
| stu_name | 学生姓名 |
| class_id | 班级ID |
| open_time | 开班时间 |
| offer_time | offer时间 |
| company | 就业公司 |
| salary | 薪资 |

---

## 9. 统计分析

### 9.1 数据总览仪表盘

**接口：** `GET /statistics/dashboard/all`

```bash
curl -X GET "http://127.0.0.1:8099/statistics/dashboard/all" \
  -H "Authorization: Bearer <token>"
```

**返回数据包括：**

- 学生总数
- 班级数量
- 教师数量
- 就业率统计
- 平均成绩
- 年龄分布

### 9.2 班级平均分排名

**接口：** `GET /statistics/score/class-average`

```bash
curl -X GET "http://127.0.0.1:8099/statistics/score/class-average" \
  -H "Authorization: Bearer <token>"
```

### 9.3 班级男女比例

**接口：** `GET /statistics/student/class-gender`

```bash
curl -X GET "http://127.0.0.1:8099/statistics/student/class-gender" \
  -H "Authorization: Bearer <token>"
```

### 9.4 不及格学生名单

**接口：** `GET /statistics/score/fail-list`

```bash
curl -X GET "http://127.0.0.1:8099/statistics/score/fail-list" \
  -H "Authorization: Bearer <token>"
```

### 9.5 30岁以上学生统计

**接口：** `GET /statistics/student/age-stat`

```bash
curl -X GET "http://127.0.0.1:8099/statistics/student/age-stat" \
  -H "Authorization: Bearer <token>"
```

---

## 10. 自然语言查询

系统支持使用自然语言查询数据库数据。

### 10.1 发起查询

**接口：** `POST /query/natural`

```bash
curl -X POST "http://127.0.0.1:8099/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "统计每个班级的学生数量",
    "session_id": "user123_session1"
  }'
```

**支持的查询类型：**

| 示例问题 | 说明 |
|----------|------|
| 有多少学生？ | 统计学生总数 |
| Python班有多少人？ | 按班级统计人数 |
| 平均成绩最高的是哪个班？ | 班级平均分排名 |
| 不及格的学生有哪些？ | 筛选不及格学生 |
| 就业率是多少？ | 就业统计 |

### 10.2 查询上下文

系统支持对话上下文，可基于之前的对话继续追问：

```bash
# 首次查询
curl -X POST "http://127.0.0.1:8099/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Python班有多少学生？",
    "session_id": "my_session"
  }'

# 追问（使用相同 session_id）
curl -X POST "http://127.0.0.1:8099/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "他们的平均成绩是多少？",
    "session_id": "my_session",
    "include_history": true
  }'
```

---

## 11. 智能助手

AI 助手支持多种功能：闲聊、天气查询、时间查询、角色扮演等。

### 11.1 发起对话

**接口：** `POST /agent/chat`

```bash
curl -X POST "http://127.0.0.1:8099/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，今天天气怎么样？",
    "user_id": "user123"
  }'
```

### 11.2 功能示例

| 对话内容 | 系统行为 |
|----------|----------|
| 今天北京天气如何？ | 调用天气API返回北京天气 |
| 现在几点了？ | 返回当前时间 |
| 给我讲个笑话 | AI闲聊 |
| 你是什么角色？ | 角色扮演对话 |

### 11.3 指定角色

```bash
curl -X POST "http://127.0.0.1:8099/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何提高编程能力？",
    "user_id": "user123",
    "persona": "lindaidai"
  }'
```

**支持的角色：**

| persona | 说明 |
|---------|------|
| lindaidai | 林黛玉扮演 |
| xueshuzhuoyou | 学术好友 |
| psychology | 心理咨询 |

### 11.4 获取可用模型

**接口：** `GET /agent/models`

```bash
curl -X GET "http://127.0.0.1:8099/agent/models" \
  -H "Authorization: Bearer <token>"
```

### 11.5 列出可用工具

**接口：** `GET /agent/tools`

```bash
curl -X GET "http://127.0.0.1:8099/agent/tools" \
  -H "Authorization: Bearer <token>"
```

---

## 12. 知识库问答

RAG（检索增强生成）知识库支持上传文档并进行智能问答。

### 12.1 上传文档

**接口：** `POST /rag/upload`

> 支持格式：txt、pdf、docx

```bash
curl -X POST "http://127.0.0.1:8099/rag/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@./documents/faq.txt"
```

### 12.2 知识库问答

**接口：** `POST /rag/query`

```bash
curl -X POST "http://127.0.0.1:8099/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何申请休学？"
  }'
```

### 12.3 文档检索

**接口：** `GET /rag/search`

```bash
curl -X GET "http://127.0.0.1:8099/rag/search?query=考试安排" \
  -H "Authorization: Bearer <token>"
```

### 12.4 查看知识库统计

**接口：** `GET /rag/stats`

```bash
curl -X GET "http://127.0.0.1:8099/rag/stats" \
  -H "Authorization: Bearer <token>"
```

### 12.5 清空知识库

**接口：** `DELETE /rag/clear`

```bash
curl -X DELETE "http://127.0.0.1:8099/rag/clear" \
  -H "Authorization: Bearer <token>"
```

---

## 13. 常见问题

### Q1: 启动时报错 "缺少必要的环境变量"

**解决：** 检查 `.env` 文件，确保以下变量已配置：

```env
DASHSCOPE_API_KEY=your-key
KIMI_API_KEY=your-key
SECRET_KEY=your-key-at-least-32-chars
SQLALCHEMY_DATABASE_URL=your-database-url
```

### Q2: SECRET_KEY 长度不足

**错误信息：** `SECRET_KEY 长度必须至少 32 个字符`

**解决：** 修改 `.env` 中的 `SECRET_KEY`，确保长度 >= 32

```env
SECRET_KEY=a-very-long-secret-key-at-least-32-characters-here
```

### Q3: 数据库连接失败

**检查项：**

1. MySQL 服务是否启动
2. 数据库是否存在
3. 用户名密码是否正确
4. 端口是否正确（默认 3306）

### Q4: NL2SQL 查询返回错误

**可能原因：**

1. Kimi API Key 未配置或已过期
2. 问题表述不够清晰
3. 数据库中没有相关数据

**解决：** 检查 `.env` 中 `KIMI_API_KEY` 配置，尝试简化问题表述。

### Q5: 知识库功能不可用

**检查项：**

1. `DASHSCOPE_API_KEY` 是否配置
2. ChromaDB/Milvus 服务是否正常

### Q6: 前端页面样式异常

**解决：**

1. 确认访问地址：`http://127.0.0.1:8099/static/index.html`
2. 清除浏览器缓存
3. 检查 `static/` 目录是否完整

### Q7: 管理员密码忘记

**解决：** 直接在数据库中插入新管理员：

```sql
INSERT INTO user (username, password_hash, role) 
VALUES ('admin', '你的密码SHA256哈希', 'admin');
```

---

## 附录

### A. API 响应格式

系统统一使用以下响应格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {...}
}
```

**状态码说明：**

| code | 说明 |
|------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（未登录） |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### B. 日志文件

运行时日志保存在 `logs/` 目录：

```
logs/
├── app.log           # 应用全局日志
├── students.log      # 学生模块日志
├── classes.log       # 班级模块日志
├── teachers.log      # 教师模块日志
└── agent.log         # AI模块日志
```

### C. 联系方式

如有问题，请联系系统管理员或提交 Issue。

---

*文档版本：v1.0.0*
*最后更新：2024年*

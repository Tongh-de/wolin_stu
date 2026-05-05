# 沃林学生管理系统

基于 FastAPI + MySQL 构建的学生信息管理系统，提供学生、班级、教师、成绩、就业、统计等完整功能的 RESTful API，并配备可视化前端界面。

## 功能特性

- **学生管理** - 学生信息的增删改查，支持按学号、姓名、班级筛选
- **班级管理** - 班级管理，支持班主任关联、逻辑删除与恢复
- **教师管理** - 教师多角色管理（班主任/讲师/顾问）
- **考试管理** - 成绩录入与查询，支持分页展示
- **就业管理** - 学生就业信息跟踪
- **统计分析** - 年龄统计、班级男女比例、平均分排名、就业数据等
- **自然语言查询** - NL2SQL 自然语言转 SQL 查询，支持对话上下文
- **智能 Agent** - 多模型路由、意图分类、工具调用（天气/时间）、角色扮演
- **RAG 知识库** - 文档上传、向量检索、智能问答
- **用户认证** - JWT 认证系统
- **日志系统** - 完整的请求日志记录与异常追踪
- **安全验证** - SQL 验证、输入校验、敏感信息脱敏

## 技术栈

| 技术 | 说明 |
|------|------|
| Python 3.10+ | 编程语言 |
| FastAPI | Web 框架 |
| SQLAlchemy | ORM |
| MySQL | 数据库 |
| ChromaDB | 本地向量数据库 |
| Milvus | 分布式向量数据库 |
| LangChain | AI 应用框架 |
| Kimi (Moonshot) | NL2SQL / 闲聊 |
| DeepSeek | 代码生成 / 数学 |
| Qwen (通义千问) | 知识库问答 |
| Element Plus | 前端 UI |

## 项目结构

```
wolin-student/
├── controllers/           # API 控制器层
│   ├── student_controller.py    # 学生管理
│   ├── class_controller.py      # 班级管理
│   ├── teacher_controller.py     # 教师管理
│   ├── exam_controller.py       # 考试管理
│   ├── employment_controller.py  # 就业管理
│   ├── statistics_controller.py  # 统计分析
│   ├── query_controller.py       # NL2SQL 自然语言查询
│   ├── auth_controller.py        # 用户认证
│   ├── rag_router.py            # RAG 知识库路由
│   └── agent_router.py          # 智能 Agent 路由
├── services/              # 业务逻辑层
│   ├── agent_service.py          # 智能 Agent 服务（多模型路由）
│   ├── rag_complete.py           # RAG 问答服务（文档处理/向量检索）
│   ├── conversation_service.py   # 对话历史管理
│   └── ...
├── model/                 # 数据库模型
│   ├── user.py                  # 用户模型
│   └── conversation.py          # 对话记忆模型
├── schemas/               # Pydantic 数据模型
├── utils/                 # 工具模块
│   ├── logger.py               # 日志配置
│   └── security.py             # 安全工具（SQL验证/输入校验/脱敏）
├── static/
│   └── index.html         # 前端页面
├── chroma_db/             # Chroma 向量数据库
├── docs/                  # 项目文档
├── database.py            # 数据库配置
├── main.py                # 应用入口
└── requirements.txt      # 依赖列表
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

修改 `database.py` 中的数据库连接：

```python
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://用户名:密码@localhost/数据库名"
```

### 3. 初始化数据库

```bash
mysql -u root -p 数据库名 < database_init_test.sql
```

### 4. 启动服务

```bash
python main.py
```

### 5. 访问应用

- 后端 API：http://127.0.0.1:8082
- Swagger 文档：http://127.0.0.1:8082/docs
- 前端界面：http://127.0.0.1:8082/static/index.html

## API 概览

### 学生管理
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/students/` | 获取学生列表 |
| POST | `/students/` | 创建学生 |
| PUT | `/students/{stu_id}` | 更新学生 |
| DELETE | `/students/{stu_id}` | 删除学生 |

### 班级管理
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/class/` | 获取班级列表 |
| POST | `/class/` | 创建班级 |
| PUT | `/class/{class_id}` | 更新班级 |
| DELETE | `/class/{class_id}` | 删除班级 |
| POST | `/class/{class_id}/restore` | 恢复班级 |

### 考试管理
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/exam/` | 提交成绩 |
| PUT | `/exam/` | 修改成绩 |
| DELETE | `/exam/{stu_id}` | 删除成绩 |
| GET | `/exam/records` | 获取成绩列表（分页） |

### 统计分析
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/statistics/test` | 测试连通性 |
| GET | `/statistics/student/age-stat` | 30岁以上学生统计 |
| GET | `/statistics/student/class-gender` | 班级男女比例 |
| GET | `/statistics/score/class-average` | 班级平均分排名 |
| GET | `/statistics/score/fail-list` | 不及格学生名单 |
| GET | `/statistics/dashboard/all` | 数据总览仪表盘 |

### 自然语言查询 (NL2SQL)
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/query/natural` | 自然语言查询，支持意图分类和对话上下文 |

### RAG 知识库
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/rag/upload` | 上传文档到知识库（支持 txt/pdf/docx） |
| POST | `/rag/query` | RAG 问答（流式输出） |
| GET | `/rag/search` | 文档检索 |
| GET | `/rag/stats` | 知识库统计 |
| DELETE | `/rag/clear` | 清空知识库 |

### 智能 Agent
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/agent/chat` | 智能对话（多模型路由） |
| GET | `/agent/models` | 列出可用模型 |
| GET | `/agent/route` | 查看路由决策 |
| GET | `/agent/tools` | 列出可用工具 |
| POST | `/agent/tools/test` | 测试工具调用 |

### 用户认证
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/register` | 用户注册 |

## 数据库表结构

- **teacher** - 教师表（ID、姓名、性别、电话、角色）
- **class** - 班级表（ID、名称、开课时间、班主任）
- **stu_basic_info** - 学生表（学号、姓名、籍贯、院校、专业、学历等）
- **stu_exam_record** - 成绩表（学号、考核序次、成绩、日期）
- **employment** - 就业表（学生、公司、薪资、offer时间等）
- **class_teacher** - 班级教师关联表
- **user** - 用户表（用户名、密码哈希、角色）
- **conversation_memory** - 对话记忆表（会话ID、轮次、问题、SQL、结果）

## 日志说明

日志文件存放在 `logs/` 目录下，按模块分类：

- `app.log` - 应用全局日志
- `students.log` - 学生模块日志
- `classes.log` - 班级模块日志
- `teachers.log` - 教师模块日志
- `exams.log` - 考试模块日志
- `employment.log` - 就业模块日志

日志格式：`时间 | 级别 | 模块:函数:行号 | 消息`

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| LOG_LEVEL | INFO | 日志级别 |
| DASHSCOPE_API_KEY | - | 阿里云 DashScope API Key（知识库向量化） |
| KIMI_API_KEY | - | Moonshot Kimi API Key（NL2SQL/闲聊） |
| DEEPSEEK_API_KEY | - | DeepSeek API Key（代码/数学） |
| OPENAI_API_KEY | - | OpenAI API Key（复杂推理） |
| MILVUS_HOST | 192.168.184.128 | Milvus 向量数据库地址 |
| MILVUS_PORT | 19530 | Milvus 端口 |

## 安全特性

- **SQL 验证器** - 防止 SQL 注入，只允许 SELECT 查询
- **输入校验** - 用户名、密码、手机号等输入验证
- **敏感信息脱敏** - 日志中自动过滤敏感关键词
- **统一异常处理** - 标准化的错误响应格式

## 许可证

MIT License

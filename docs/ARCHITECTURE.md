# 拾光学子成长管理平台 - 系统架构设计文档

## 一、项目概述

本项目是一个基于 FastAPI + MySQL 的学生信息管理系统，采用分层架构设计，核心功能包括学生管理、班级管理、教师管理、考试管理、就业管理、统计分析、NL2SQL 自然语言查询、RAG 知识库问答和智能 Agent 对话。

## 二、技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (static/)                           │
│                  HTML + CSS + JavaScript (Element Plus)          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Web 框架                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Controllers │  │   Middleware │  │    请求拦截器           │ │
│  │  (路由层)    │  │  (CORS等)    │  │  (日志/异常处理)        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Services (业务逻辑层)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐│
│  │ Student  │ │  Class   │ │ Teacher  │ │   Exam   │ │Agent ││
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │ │Service││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Models (数据模型层)                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Student  │ │  Class   │ │ Teacher  │ │ Employment│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database (MySQL + SQLAlchemy)                │
└─────────────────────────────────────────────────────────────────┘
```

## 三、核心模块详解

### 3.1 数据库层 (database.py)

数据库配置采用 SQLAlchemy ORM，核心组件：

```python
# 1. 创建数据库引擎
engine = create_engine(url=os.getenv("SQLALCHEMY_DATABASE_URL"), 
                        pool_size=5, pool_recycle=3600)

# 2. 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 定义 ORM 基类
Base = declarative_base()

# 4. 依赖注入获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.2 数据模型层 (model/)

使用 SQLAlchemy 定义数据库表结构，采用 ORM 模式：

```python
class StuBasicInfo(Base):
    __tablename__ = "stu_basic_info"
    stu_id = Column(Integer, primary_key=True, autoincrement=True)
    stu_name = Column(String(20), nullable=False)
    native_place = Column(String(50), nullable=False)
    graduated_school = Column(String(50), nullable=False)
    major = Column(String(50), nullable=False)
    admission_date = Column(DateTime, nullable=False)
    graduation_date = Column(DateTime, nullable=False)
    education = Column(String(20), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(2), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # 外键关联
    advisor_id = Column(Integer, ForeignKey("teacher.teacher_id"))
    class_id = Column(Integer, ForeignKey("class.class_id"), nullable=False)
    
    # 关系定义
    class_ = relationship("Class", back_populates="students")
```

**数据模型一览：**

| 模型名 | 表名 | 主要字段 |
|--------|------|----------|
| Student | stu_basic_info | 学号、姓名、籍贯、院校、专业、学历、年龄、性别 |
| Class | class | 班级ID、名称、开课时间、班主任 |
| Teacher | teacher | 教师ID、姓名、性别、电话、角色 |
| Exam | stu_exam_record | 学号、考核序次、成绩、日期 |
| Employment | employment | 学生、公司、薪资、offer时间 |
| User | user | 用户名、密码哈希、角色 |

### 3.3 Schemas 层 (schemas/)

使用 Pydantic 定义请求/响应的数据验证模型：

```python
class StudentCreate(BaseModel):
    stu_name: str = Field(..., min_length=1, max_length=20)
    class_id: int = Field(..., gt=0)
    native_place: str = Field(..., max_length=50)
    graduated_school: str = Field(..., max_length=50)
    major: str = Field(..., max_length=50)
    admission_date: datetime
    graduation_date: datetime
    education: str = Field(..., max_length=20)
    advisor_id: Optional[int] = None
    age: int = Field(..., gt=0, lt=150)
    gender: str = Field(..., pattern="^(男|女)$")

class StudentUpdate(BaseModel):
    # 所有字段为可选，支持部分更新
    stu_name: Optional[str] = Field(None, max_length=20)
    class_id: Optional[int] = Field(None, gt=0)
    # ... 其他字段
```

### 3.4 控制器层 (controllers/)

API 路由层，处理 HTTP 请求和响应：

```python
router = APIRouter(prefix="/students", tags=["学生管理"])

@router.post("/", response_model=ResponseBase)
def create_student(
    new_student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # 权限验证
):
    logger.info(f"新增学生: {new_student_data.stu_name}")
    new_student = StudentService.create_student(new_student_data, db)
    # 级联创建就业信息
    EmploymentService.create_empty_employment(...)
    return ResponseBase(data=new_student)
```

**路由注册流程（main.py）：**

```python
# 注册所有路由
app.include_router(student_router)      # 学生管理
app.include_router(class_router)       # 班级管理
app.include_router(teacher_router)     # 教师管理
app.include_router(exam_router)        # 考试管理
app.include_router(employment_router)  # 就业管理
app.include_router(statistics_router)  # 统计分析
app.include_router(query_router)       # NL2SQL 查询
app.include_router(auth_router)         # 用户认证
app.include_router(email_router)        # 邮件服务
app.include_router(rag_router)          # RAG 知识库
app.include_router(agent_router)        # 智能 Agent
app.include_router(homework_router)     # 作业管理

# 创建所有表
Base.metadata.create_all(bind=engine)
```

### 3.5 业务逻辑层 (services/)

封装核心业务逻辑，与控制器分离：

```python
class StudentService:
    @staticmethod
    def create_student(new_student_data: StudentCreate, db: Session):
        # 1. 验证顾问ID是否存在且为 counselor 角色
        StudentService._is_teacher_counselor(new_student_data.advisor_id, db)
        # 2. 验证班级ID是否存在
        StudentService._is_classes_exist(new_student_data.class_id, db)
        # 3. 创建学生记录
        new_student = StuBasicInfo(...)
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        return StudentService._format_student_data(new_student)

    @staticmethod
    def get_students(db: Session, stu_id: int = None, stu_name: str = None, class_id: int = None):
        result = db.query(StuBasicInfo).filter(StuBasicInfo.is_deleted == False)
        # 动态添加过滤条件
        if stu_id is not None:
            result = result.filter(StuBasicInfo.stu_id == stu_id)
        if stu_name is not None:
            result = result.filter(StuBasicInfo.stu_name == stu_name)
        if class_id is not None:
            result = result.filter(StuBasicInfo.class_id == class_id)
        return StudentService._format_student_data(result.all())
```

## 四、智能模块详解

### 4.1 NL2SQL 自然语言查询 (query_controller.py)

将用户自然语言转换为 SQL 查询：

```
用户问题 → 意图识别 → SQL生成 → 数据库执行 → 结果返回
```

**核心流程：**

```python
# 1. 从知识库检索相关表结构上下文
async def retrieve_schema_context(vectordb) -> str:
    if vectordb:
        docs = await similarity_search_async(vectordb, query, k=3)
        # 从向量数据库获取相关文档
    return FALLBACK_SCHEMA  # 回退到默认表结构

# 2. 使用 Kimi 模型生成 SQL
response = await client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]
)
sql = response.choices[0].message.content

# 3. SQL 验证与修正
sql = fix_table_names(sql)  # 修正表名 teachers → teacher

# 4. 执行查询
result = db.execute(text(sql))
```

### 4.2 智能 Agent (agent_service.py)

多模型路由 + 意图识别 + 工具调用：

```
用户输入 → 意图识别 → 模型路由 → 响应生成 → 流式输出
              ↓
         工具调用
         (天气/时间)
```

**意图类型：**

| 意图 | 处理模型 | 功能 |
|------|----------|------|
| nl2sql | Kimi | 自然语言转 SQL 查询 |
| analysis | DeepSeek | 数据分析/代码生成 |
| rag | Qwen | RAG 知识库问答 |
| weather | DeepSeek | 天气查询 |
| time | DeepSeek | 时间查询 |
| lindaidai | DeepSeek | 角色扮演 |
| analysis | DeepSeek | 数学/推理 |

**工具调用示例：**

```python
# 天气查询工具
def get_weather(city: str) -> str:
    # 调用天气 API
    return weather_data

# 时间查询工具  
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

### 4.3 RAG 知识库 (rag_complete.py)

文档向量化 + 语义检索 + 问答生成：

```
文档上传 → 文本分割 → 向量化 → 存储到向量数据库
              ↓
用户问题 → 问题向量化 → 相似度检索 → 上下文构建 → LLM 生成答案
```

**向量数据库：** ChromaDB / Milvus

**嵌入模型：** DashScope text-embedding-v3

## 五、中间件与安全

### 5.1 CORS 配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8099", "http://localhost:8099"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 5.2 请求拦截器

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    # 记录请求
    app_logger.info(f"➡️  请求: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        # 记录响应
        app_logger.info(f"⬅️  响应: {response.status_code} | 耗时: {duration:.3f}s")
        return response
    except Exception as e:
        # 异常处理，隐藏内部错误
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误"}
        )
```

### 5.3 认证与授权

```python
# JWT Token 验证
def get_current_user(token: str = Depends(oauth2_scheme)):
    # 验证 token，获取当前用户
    
# 管理员权限验证
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
```

## 六、数据流向图

```
┌──────────────────────────────────────────────────────────────────┐
│                         HTTP 请求                                │
│                    POST /students/                               │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                      请求拦截器                                   │
│                   日志记录 + 异常处理                             │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    认证中间件                                     │
│                JWT Token 验证 + 权限检查                          │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Controller (控制器)                            │
│              student_controller.create_student()                 │
│                   参数验证 + 数据转换                             │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Service (服务层)                                │
│                StudentService.create_student()                  │
│              业务逻辑处理 + 数据验证                              │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Model (数据模型)                                │
│                  StuBasicInfo ORM 对象                           │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Database (数据库)                              │
│                  MySQL 数据库操作                                 │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                       响应返回                                    │
│              ResponseBase(data=student_data)                    │
└──────────────────────────────────────────────────────────────────┘
```

## 七、关键配置

### 7.1 环境变量

| 变量名 | 说明 |
|--------|------|
| SQLALCHEMY_DATABASE_URL | MySQL 数据库连接 |
| DASHSCOPE_API_KEY | 阿里云 DashScope (RAG 向量化) |
| KIMI_API_KEY | Kimi 大模型 (NL2SQL) |
| DEEPSEEK_API_KEY | DeepSeek 大模型 (代码/数学) |
| SECRET_KEY | JWT 密钥 (至少32字符) |

### 7.2 端口配置

- 后端服务：**127.0.0.1:8099**
- Swagger 文档：**http://127.0.0.1:8099/docs**
- 前端界面：**http://127.0.0.1:8099/static/index.html**

## 八、项目结构总览

```
wolin-student/
├── main.py                    # 应用入口，路由注册
├── database.py                 # 数据库配置
├── requirements.txt           # 依赖列表
│
├── controllers/                # API 控制器层
│   ├── student_controller.py   # 学生 CRUD
│   ├── class_controller.py    # 班级管理
│   ├── teacher_controller.py   # 教师管理
│   ├── exam_controller.py      # 考试管理
│   ├── employment_controller.py # 就业管理
│   ├── statistics_controller.py# 统计分析
│   ├── query_controller.py     # NL2SQL 查询
│   ├── auth_controller.py      # 用户认证
│   ├── email_controller.py     # 邮件服务
│   └── rag_router.py           # RAG 知识库
│
├── services/                   # 业务逻辑层
│   ├── student_service.py      # 学生业务逻辑
│   ├── agent_service.py        # AI Agent 路由
│   ├── rag_complete.py         # RAG 问答
│   └── homework_service.py     # 作业管理
│
├── model/                      # ORM 数据模型
│   ├── student.py             # 学生模型
│   ├── class_model.py          # 班级模型
│   └── ...
│
├── schemas/                    # Pydantic 模型
│   ├── student.py             # 学生请求/响应模型
│   └── ...
│
├── config/                     # 配置文件
│   ├── agent_prompts.py       # Agent 提示词配置
│   └── db_schema.py           # 数据库表结构
│
├── utils/                      # 工具模块
│   ├── logger.py              # 日志配置
│   ├── auth_deps.py          # 认证依赖
│   └── responses.py          # 统一响应格式
│
├── static/                     # 前端资源
│   ├── index.html             # 主页面
│   └── styles.css             # 样式文件
│
├── docs/                       # 项目文档
└── tests/                      # 单元测试
```

## 九、API 调用示例

### 创建学生

```bash
curl -X POST "http://127.0.0.1:8099/students/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stu_name": "张三",
    "class_id": 1,
    "native_place": "北京",
    "graduated_school": "清华大学",
    "major": "计算机科学",
    "admission_date": "2024-09-01",
    "graduation_date": "2027-06-30",
    "education": "本科",
    "advisor_id": 1,
    "age": 22,
    "gender": "男"
  }'
```

### 自然语言查询

```bash
curl -X POST "http://127.0.0.1:8099/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "统计每个班级的平均成绩",
    "session_id": "abc123"
  }'
```

### AI Agent 对话

```bash
curl -X POST "http://127.0.0.1:8099/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "北京今天天气怎么样？",
    "user_id": "user123"
  }'
```

## 十、启动流程

```python
# 1. 加载环境变量
load_dotenv()

# 2. 检查必要配置
check_required_env()

# 3. 创建 FastAPI 应用
app = FastAPI(title="拾光学子成长管理平台", version="1.0.0")

# 4. 配置中间件
app.add_middleware(CORSMiddleware, ...)
app.middleware("http")(log_requests)

# 5. 注册路由
app.include_router(student_router)
# ... 其他路由

# 6. 创建数据库表
Base.metadata.create_all(bind=engine)

# 7. 启动服务
uvicorn.run(app, host='127.0.0.1', port=8099)
```

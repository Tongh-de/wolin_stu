# 沃林学生管理系统

基于 FastAPI + MySQL 构建的学生信息管理系统，提供学生、班级、教师、成绩、就业、统计等完整功能的 RESTful API，并配备可视化前端界面。

## 功能特性

- **学生管理** - 学生信息的增删改查，支持按学号、姓名、班级筛选
- **班级管理** - 班级管理，支持班主任关联、逻辑删除与恢复
- **教师管理** - 教师多角色管理（班主任/讲师/顾问）
- **考试管理** - 成绩录入与查询，支持分页展示
- **就业管理** - 学生就业信息跟踪
- **统计分析** - 年龄统计、班级男女比例、平均分排名、就业数据等
- **智能问答** - 基于向量数据库的自然语言查询
- **日志系统** - 完整的请求日志记录与异常追踪

## 技术栈

| 技术 | 说明 |
|------|------|
| Python 3.10+ | 编程语言 |
| FastAPI | Web 框架 |
| SQLAlchemy | ORM |
| MySQL | 数据库 |
| ChromaDB | 向量数据库（知识库） |
| Element Plus | 前端 UI |

## 项目结构

```
wolin-student/
├── controllers/           # API 控制器层
│   ├── student_controller.py
│   ├── class_controller.py
│   ├── teacher_controller.py
│   ├── exam_controller.py
│   ├── employment_controller.py
│   ├── statistics_controller.py
│   ├── query_controller.py
│   ├── auth_controller.py
│   └── text2sql_controller.py
├── services/              # 业务逻辑层
├── model/                 # 数据库模型
├── schemas/               # Pydantic 数据模型
├── utils/                 # 工具模块
│   └── logger.py          # 日志配置
├── static/
│   └── index.html         # 前端页面
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

## 数据库表结构

- **teacher** - 教师表（ID、姓名、性别、电话、角色）
- **class** - 班级表（ID、名称、开课时间、班主任）
- **stu_basic_info** - 学生表（学号、姓名、籍贯、院校、专业、学历等）
- **stu_exam_record** - 成绩表（学号、考核序次、成绩、日期）
- **employment** - 就业表（学生、公司、薪资、offer时间等）
- **class_teacher** - 班级教师关联表

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

## 许可证

MIT License

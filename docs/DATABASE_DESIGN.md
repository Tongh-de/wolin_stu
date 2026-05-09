# Wolin 学生管理系统 - 数据库设计文档

## 一、数据库概览

| 项目 | 配置 |
|------|------|
| 数据库名 | `wolin_test1` |
| 字符集 | `utf8mb4` |
| 排序规则 | `utf8mb4_0900_ai_ci` |

---

## 二、ER关系图

```
┌─────────────┐     1:N      ┌─────────────┐     N:M      ┌─────────────────┐
│   teacher   │◄────────────│    class    │─────────────►│    class_teacher │
└─────────────┘             └─────────────┘              └─────────────────┘
      │                            │                              │
      │ 1:N                       │ 1:N                          │ N:1
      │ (advisor)                │                              │
      │                     ┌────┴────┐                         │
      │                     │         │                         │
      ▼                     ▼         ▼                         │
┌──────────────────┐   ┌──────────────────┐                     │
│  stu_basic_info  │   │    employment    │                     │
│     (学生表)      │   │    (就业表)      │                     │
└──────────────────┘   └──────────────────┘                     │
      │                                                         │
      │ 1:N                                                      │
      ▼                                                         │
┌──────────────────┐                                            │
│  stu_exam_record │◄───────────────────────────────────────────┘
│    (考核表)        │
└──────────────────┘

┌────────────────────┐
│       users        │──────────┬──────────┬──────────
│      (用户表)       │  1:1    │  1:1     │  N:1
└────────────────────┘  │        │          │
                   ┌────┴───┐   │    ┌────┴────┐
                   ▼        ▼   ▼    ▼         │
             ┌──────────┐ ┌─────────────────────────┐
             │ teacher  │ │      stu_basic_info      │
             └──────────┘ └─────────────────────────┘

┌────────────────────┐
│ conversation_memory │     (AI对话会话记录)
│    (会话记录表)      │
└────────────────────┘
```

---

## 三、表结构详情

### 3.1 teacher (教师表)

| 字段名 | 类型 | 可空 | 说明 |
|--------|------|------|------|
| teacher_id | INT | 否 | 主键，自增 |
| teacher_name | VARCHAR(30) | 是 | 姓名 |
| gender | VARCHAR(10) | 是 | 性别：男/女 |
| phone | VARCHAR(20) | 是 | 电话号码 |
| role | VARCHAR(20) | 是 | 角色：counselor(顾问)/headteacher(班主任)/lecturer(讲师) |
| is_deleted | TINYINT(1) | 是 | 逻辑删除：0-未删除，1-已删除 |

**索引**: PRIMARY KEY (teacher_id)

---

### 3.2 class (班级表)

| 字段名 | 类型 | 可空 | 说明 |
|--------|------|------|------|
| class_id | INT | 否 | 主键，自增 |
| class_name | VARCHAR(50) | 否 | 班级名称 |
| start_time | DATETIME | 否 | 开课时间 |
| is_deleted | TINYINT(1) | 否 | 是否删除：0-未删除，1-已删除 |
| head_teacher_id | INT | 是 | 班主任ID (外键→teacher.teacher_id) |

**索引**: PRIMARY KEY (class_id), INDEX (head_teacher_id)

---

### 3.3 class_teacher (班级教师关联表)

| 字段名 | 类型 | 可空 | 说明 |
|--------|------|------|------|
| class_id | INT | 否 | 班级ID (外键→class.class_id) |
| teacher_id | INT | 否 | 教师ID (外键→teacher.teacher_id) |

**索引**: PRIMARY KEY (class_id, teacher_id), INDEX (teacher_id)

---

### 3.4 stu_basic_info (学生基本信息表)

| 字段名 | 类型 | 可空 | 说明 |
|--------|------|------|------|
| stu_id | INT | 否 | 主键，自增 |
| stu_name | VARCHAR(20) | 否 | 学生姓名 |
| native_place | VARCHAR(50) | 否 | 籍贯 |
| graduated_school | VARCHAR(50) | 否 | 毕业学校 |
| major | VARCHAR(50) | 否 | 所学专业 |
| admission_date | DATETIME | 否 | 入学日期 |
| graduation_date | DATETIME | 否 | 毕业日期 |
| education | VARCHAR(20) | 否 | 学历 |
| age | INT | 否 | 年龄 |
| gender | VARCHAR(2) | 否 | 性别：男/女 |
| is_deleted | INT | 否 | 逻辑删除 |
| advisor_id | INT | 是 | 导师ID (外键→teacher.teacher_id) |
| class_id | INT | 否 | 班级ID (外键→class.class_id) |

**索引**: PRIMARY KEY (stu_id), INDEX (advisor_id), INDEX (class_id)

---

### 3.5 employment (就业信息表)

| 字段名 | 类型 | 可空 | 说明 |
|--------|------|------|------|
| emp_id | INT | 否 | 主键，自增 |
| stu_id | INT | 否 | 学生ID (外键→stu_basic_info.stu_id) |
| stu_name | VARCHAR(20) | 否 | 学生姓名 |
| class_id | INT | 否 | 班级ID |
| open_time | DATE | 是 | 就业开放时间 |
| offer_time | DATE | 是 | offer下发时间 |
| company | VARCHAR(50) | 是 | 就业公司 |
| salary | FLOAT | 是 | 薪资 |
| is_deleted | TINYINT(1) | 是 | 逻辑删除 |

**索引**: PRIMARY KEY (emp_id), INDEX (stu_id)

---

### 3.6 stu_exam_record (学生考核记录表)

| 字段名 | 类型 | 可空 | 说明 |
|--------|------|------|------|
| stu_id | INT | 否 | 学生ID (外键→stu_basic_info.stu_id) |
| seq_no | INT | 否 | 考核序次 |
| grade | INT | 是 | 考核成绩 |
| exam_date | DATE | 是 | 考核日期 |
| is_deleted | INT | 是 | 逻辑删除 |

**索引**: PRIMARY KEY (stu_id, seq_no)

---

### 3.7 users (用户表)

| 字段名 | 类型 | 可空 | 说明 |
|--------|------|------|------|
| id | INT | 否 | 主键，自增 |
| username | VARCHAR(50) | 否 | 用户名，唯一 |
| hashed_password | VARCHAR(255) | 否 | 密码哈希 |
| is_active | TINYINT(1) | 是 | 是否启用，默认1 |
| role | VARCHAR(20) | 否 | 角色：admin(管理员)/teacher(教师)/student(学生) |
| student_id | INT | 是 | 关联学生ID (外键→stu_basic_info.stu_id) |
| teacher_id | INT | 是 | 关联教师ID (外键→teacher.teacher_id) |

**索引**: PRIMARY KEY (id), UNIQUE (username), INDEX (role), INDEX (student_id), INDEX (teacher_id)

---

### 3.8 conversation_memory (会话记录表)

| 字段名 | 类型 | 可空 | 说明 |
|--------|------|------|------|
| id | INT | 否 | 主键，自增 |
| session_id | VARCHAR(64) | 否 | 会话ID |
| turn_index | INT | 否 | 轮次序号 |
| question | TEXT | 否 | 用户提问 |
| sql_query | TEXT | 是 | 生成的SQL语句 |
| result_summary | TEXT | 是 | 查询结果摘要 |
| answer_text | TEXT | 是 | 最终回答文本 |
| full_data_saved | TINYINT(1) | 是 | 是否完整保存 |
| aggregate_sql | TEXT | 是 | 聚合SQL |
| embedding_vector | JSON | 是 | 向量表示 |
| created_at | DATETIME | 是 | 创建时间，默认当前时间 |

**索引**: PRIMARY KEY (id), INDEX (session_id)

---

## 四、表关系总结

| 关系 | 说明 |
|------|------|
| teacher → class | 1:N (班主任管理班级) |
| teacher → stu_basic_info | 1:N (导师指导学生) |
| class → stu_basic_info | 1:N (班级包含学生) |
| stu_basic_info → employment | 1:1 (学生有一条就业记录) |
| stu_basic_info → stu_exam_record | 1:N (学生有多条考核记录) |
| class ↔ teacher | N:M (通过class_teacher关联) |
| users → teacher/student | 1:1 (用户关联教师或学生) |

---

## 五、物理模型图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    teacher      │     │     class       │     │  class_teacher  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ PK teacher_id   │1──N │ PK class_id     │N──M◄┤ PK class_id     │
│    teacher_name │     │    class_name   │     │ PK teacher_id   │
│    gender       │     │ FK head_teacher │     └─────────────────┘
│    phone        │     │    start_time   │
│    role         │     │    is_deleted   │
│    is_deleted   │     └────────┬────────┘
└─────────────────┘              │1:N
       │1:N                      │
       │                         │
       ▼                    ┌────▼────────┐     ┌─────────────────┐
┌──────────────┐            │ stu_basic   │     │   employment    │
│stu_exam_record│           │   _info     │     ├─────────────────┤
├──────────────┤            ├─────────────┤     │ PK emp_id       │
│PK stu_id     │◄──────────┤PK stu_id    │     │ FK stu_id    ───┘
│PK seq_no     │     1:N   │ stu_name     │
│    grade     │            │ FK advisor_id│     └─────────────────┘
│    exam_date │            │ FK class_id  │
│    is_deleted│            │    ...       │
└──────────────┘            └──────────────┘
                                  │
                                  │1:1
                                  ▼
                           ┌──────────────┐     ┌────────────────────┐
                           │    users     │     │conversation_memory │
                           ├──────────────┤     ├────────────────────┤
                           │ PK id        │     │ PK id              │
                           │ username(UQ) │     │ session_id         │
                           │ password     │     │ turn_index         │
                           │ FK student_id│     │ question           │
                           │ FK teacher_id│     │ sql_query          │
                           │ role         │     │ answer_text        │
                           └──────────────┘     └────────────────────┘
```

---

## 六、初始化脚本

**数据库初始化**:
```bash
mysql -u root -p123456 < init_full.sql
```

**初始账号** (密码均为: 123456):

| 用户名 | 角色 |
|--------|------|
| admin | 管理员 |
| teacher01 | 教师 |
| student01 | 学生 |

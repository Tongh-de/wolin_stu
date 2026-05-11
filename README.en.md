# Shiguang Student Growth Management Platform

A comprehensive education management system built on FastAPI and SQLAlchemy, providing RESTful API interfaces for core functionalities such as student, class, teacher, employment, exam management, and AI-powered features.

## Project Overview

Shiguang Student Growth Management Platform is an information management system designed for educational institutions, adopting a frontend-backend separation architecture. The backend is built using the Python FastAPI framework to deliver RESTful APIs, combined with SQLAlchemy for database operations. The system supports functionalities including student information management, class management, teacher management, employment tracking, exam score management, data analytics, NL2SQL natural language queries, RAG knowledge base, and intelligent Agent.

## Technology Stack

- **Web Framework**: FastAPI
- **Database ORM**: SQLAlchemy
- **Database**: MySQL
- **Vector Database**: ChromaDB (local), Milvus (distributed)
- **AI Framework**: LangChain
- **LLM Providers**: Kimi (Moonshot), DeepSeek, Qwen, GPT-4
- **Data Validation**: Pydantic
- **Python Version**: 3.10+

## Functional Modules

### 1. Student Management (Student API)
- Retrieve student list (supports filtering by student ID, name, class)
- Create new student
- Update student information
- Delete student

### 2. Class Management (Class API)
- Retrieve all classes
- Retrieve single class information
- Create class
- Update class information
- Delete class

### 3. Teacher Management (Teacher API)
- Retrieve teacher list
- Retrieve teacher information
- Create teacher
- Update teacher information
- Delete teacher
- Query classes taught by a teacher
- Query classes where a teacher serves as homeroom teacher
- Query students under a teacher's employment guidance

### 4. Employment Management (Employment API)
- Query employment records (supports multi-condition filtering)
- Update employment information
- Delete employment record

### 5. Exam Management (Exam API)
- Submit exam scores

### 6. Statistics & Analytics (Statistics API)
- Count of students over 30 years old
- Gender ratio by class
- Class average score ranking
- List of failing students
- Top 5 salary earners
- Employment count by company
- Comprehensive data dashboard

### 7. Natural Language Query (NL2SQL)
- Natural language to SQL conversion using Kimi
- Intent classification (SQL, analysis, chat)
- Conversation history management

### 8. RAG Knowledge Base
- Document upload (supports txt, pdf, docx)
- Sliding window text chunking
- Vector storage with Milvus
- RAG-based Q&A with streaming output

### 9. Intelligent Agent
- Multi-model routing (Kimi, DeepSeek, Qwen, GPT-4)
- Intent classification
- Tool calling (weather, time)
- Character role-play (e.g., Lin Daiyu from Dream of Red Chamber)

### 10. User Authentication
- JWT-based authentication
- User registration and login

### 11. Security Features
- SQL injection prevention
- Input validation
- Sensitive information redaction

## Project Structure

```
wolin-student/
├── controllers/           # API routing layer
│   ├── student_controller.py    # Student management
│   ├── class_controller.py      # Class management
│   ├── teacher_controller.py    # Teacher management
│   ├── exam_controller.py       # Exam management
│   ├── employment_controller.py  # Employment management
│   ├── statistics_controller.py  # Statistics
│   ├── query_controller.py       # NL2SQL query
│   ├── auth_controller.py        # Authentication
│   ├── rag_router.py            # RAG knowledge base
│   └── agent_router.py          # Intelligent Agent
├── services/              # Business logic layer
│   ├── agent_service.py          # Agent service (multi-model routing)
│   ├── rag_complete.py           # RAG service (document processing)
│   ├── conversation_service.py   # Conversation history
│   └── ...
├── model/                 # Database models
│   ├── user.py                  # User model
│   └── conversation.py          # Conversation memory model
├── schemas/               # Pydantic data models
├── utils/                 # Utilities
│   ├── logger.py               # Logging
│   └── security.py             # Security tools
├── chroma_db/             # Chroma vector database
├── database.py            # Database configuration
├── main.py                # Application entry point
└── requirements.txt       # Dependencies
```

## Quick Start

### Prerequisites

- Python 3.10+
- MySQL 5.7+
- API keys for LLM providers (KIMI_API_KEY, DASHSCOPE_API_KEY, etc.)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file with required API keys:

```bash
DASHSCOPE_API_KEY=your-dashscope-key
KIMI_API_KEY=your-kimi-key
DEEPSEEK_API_KEY=your-deepseek-key
```

### Configure Database

Modify the database connection settings in `database.py` according to your environment.

### Initialize Database

```bash
mysql -u root -p < database_init_test.sql
```

### Start the Application

```bash
python main.py
```

The API will be available at:
- Backend API: http://127.0.0.1:8082
- Swagger Docs: http://127.0.0.1:8082/docs
- Frontend: http://127.0.0.1:8082/static/index.html
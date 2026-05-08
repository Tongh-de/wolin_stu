/**
 * API 配置文件
 * 统一管理所有后端接口地址
 */

const API_CONFIG = {
    // 基础配置
    BASE_URL: '',
    
    // 认证相关
    AUTH: {
        LOGIN: '/auth/login',
        REGISTER: '/auth/register',
        LOGOUT: '/auth/logout'
    },
    
    // 学生管理
    STUDENTS: {
        LIST: '/students/',
        DETAIL: (id) => `/students/${id}`,
        CREATE: '/students/',
        UPDATE: (id) => `/students/${id}`,
        DELETE: (id) => `/students/${id}`
    },
    
    // 班级管理
    CLASS: {
        LIST: '/class/',
        DETAIL: (id) => `/class/${id}`,
        CREATE: '/class/',
        UPDATE: (id) => `/class/${id}`,
        DELETE: (id) => `/class/${id}`,
        RESTORE: (id) => `/class/${id}/restore`
    },
    
    // 教师管理
    TEACHERS: {
        LIST: '/teachers/',
        DETAIL: (id) => `/teacher/${id}`,
        CREATE: '/teachers/',
        UPDATE: (id) => `/teacher/${id}`,
        DELETE: (id) => `/teacher/${id}`
    },
    
    // 成绩管理
    EXAM: {
        RECORDS: '/exam/records',
        SUBMIT: '/exam/',
        UPDATE: '/exam/',
        DELETE: (stuId) => `/exam/${stuId}`
    },
    
    // 就业管理
    EMPLOYMENT: {
        LIST: '/employment/list',
        DETAIL: (id) => `/employment/${id}`,
        CREATE: '/employment/',
        UPDATE: '/employment/',
        DELETE: (id) => `/employment/delete/${id}`
    },
    
    // 统计分析
    STATS: {
        DASHBOARD: '/statistics/dashboard/all',
        AGE_STAT: '/statistics/student/age-stat',
        CLASS_GENDER: '/statistics/student/class-gender',
        CLASS_AVG: '/statistics/score/class-average',
        FAIL_LIST: '/statistics/score/fail-list'
    },
    
    // NL2SQL 查询
    QUERY: {
        NATURAL: '/query/natural'
    },
    
    // 智能 Agent
    AGENT: {
        CHAT: '/agent/chat',
        MODELS: '/agent/models',
        ROUTE: '/agent/route',
        TOOLS: '/agent/tools',
        TOOL_TEST: '/agent/tools/test',
        MEMORY: '/agent/memory'
    },
    
    // RAG 知识库
    RAG: {
        UPLOAD: '/rag/upload',
        QUERY: '/rag/query',
        SEARCH: '/rag/search',
        STATS: '/rag/stats',
        CLEAR: '/rag/clear'
    },
    
    // 作业管理
    HOMEWORK: {
        UPLOAD: '/homework/upload',
        LIST: '/homework/list',
        DOWNLOAD: (filename) => `/homework/download/${filename}`
    }
};

// 导出
window.API_CONFIG = API_CONFIG;

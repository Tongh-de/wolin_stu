/**
 * 数据服务模块
 * 处理学生管理系统的 CRUD 操作
 */

class DataService {
    // ============================================
    // 学生管理
    // ============================================
    
    async getStudents(params = {}) {
        const response = await axios.get(API_CONFIG.STUDENTS.LIST, { params });
        return response.data;
    }
    
    async getStudent(id) {
        const response = await axios.get(API_CONFIG.STUDENTS.DETAIL(id));
        return response.data;
    }
    
    async createStudent(data) {
        const response = await axios.post(API_CONFIG.STUDENTS.CREATE, data);
        return response.data;
    }
    
    async updateStudent(id, data) {
        const response = await axios.put(API_CONFIG.STUDENTS.UPDATE(id), data);
        return response.data;
    }
    
    async deleteStudent(id) {
        const response = await axios.delete(API_CONFIG.STUDENTS.DELETE(id));
        return response.data;
    }
    
    // ============================================
    // 班级管理
    // ============================================
    
    async getClasses(params = {}) {
        const response = await axios.get(API_CONFIG.CLASS.LIST, { params });
        return response.data;
    }
    
    async getClass(id) {
        const response = await axios.get(API_CONFIG.CLASS.DETAIL(id));
        return response.data;
    }
    
    async createClass(data) {
        const response = await axios.post(API_CONFIG.CLASS.CREATE, data);
        return response.data;
    }
    
    async updateClass(id, data) {
        const response = await axios.put(API_CONFIG.CLASS.UPDATE(id), data);
        return response.data;
    }
    
    async deleteClass(id) {
        const response = await axios.delete(API_CONFIG.CLASS.DELETE(id));
        return response.data;
    }
    
    async restoreClass(id) {
        const response = await axios.post(API_CONFIG.CLASS.RESTORE(id));
        return response.data;
    }
    
    // ============================================
    // 教师管理
    // ============================================
    
    async getTeachers(params = {}) {
        const response = await axios.get(API_CONFIG.TEACHERS.LIST, { params });
        return response.data;
    }
    
    async getTeacher(id) {
        const response = await axios.get(API_CONFIG.TEACHERS.DETAIL(id));
        return response.data;
    }
    
    async createTeacher(data) {
        const response = await axios.post(API_CONFIG.TEACHERS.CREATE, data);
        return response.data;
    }
    
    async updateTeacher(id, data) {
        const response = await axios.put(API_CONFIG.TEACHERS.UPDATE(id), data);
        return response.data;
    }
    
    async deleteTeacher(id) {
        const response = await axios.delete(API_CONFIG.TEACHERS.DELETE(id));
        return response.data;
    }
    
    // ============================================
    // 成绩管理
    // ============================================
    
    async getExamRecords(params = {}) {
        const response = await axios.get(API_CONFIG.EXAM.RECORDS, { params });
        return response.data;
    }
    
    async submitExam(data) {
        const response = await axios.post(API_CONFIG.EXAM.SUBMIT, data);
        return response.data;
    }
    
    async updateExam(data) {
        const response = await axios.put(API_CONFIG.EXAM.UPDATE, data);
        return response.data;
    }
    
    async deleteExam(stuId) {
        const response = await axios.delete(API_CONFIG.EXAM.DELETE(stuId));
        return response.data;
    }
    
    // ============================================
    // 就业管理
    // ============================================
    
    async getEmploymentList(params = {}) {
        const response = await axios.get(API_CONFIG.EMPLOYMENT.LIST, { params });
        return response.data;
    }
    
    async getEmployment(id) {
        const response = await axios.get(API_CONFIG.EMPLOYMENT.DETAIL(id));
        return response.data;
    }
    
    async createEmployment(data) {
        const response = await axios.post(API_CONFIG.EMPLOYMENT.CREATE, data);
        return response.data;
    }
    
    async updateEmployment(data) {
        const response = await axios.put(API_CONFIG.EMPLOYMENT.UPDATE, data);
        return response.data;
    }
    
    async deleteEmployment(id) {
        const response = await axios.delete(API_CONFIG.EMPLOYMENT.DELETE(id));
        return response.data;
    }
    
    // ============================================
    // 统计分析
    // ============================================
    
    async getDashboard() {
        const response = await axios.get(API_CONFIG.STATS.DASHBOARD);
        return response.data;
    }
    
    async getAgeStatistics() {
        const response = await axios.get(API_CONFIG.STATS.AGE_STAT);
        return response.data;
    }
    
    async getClassGenderStats() {
        const response = await axios.get(API_CONFIG.STATS.CLASS_GENDER);
        return response.data;
    }
    
    async getClassAverageScores() {
        const response = await axios.get(API_CONFIG.STATS.CLASS_AVG);
        return response.data;
    }
    
    async getFailList() {
        const response = await axios.get(API_CONFIG.STATS.FAIL_LIST);
        return response.data;
    }
    
    // ============================================
    // NL2SQL 查询
    // ============================================
    
    async queryNaturalLanguage(question) {
        const response = await axios.post(API_CONFIG.QUERY.NATURAL, { question });
        return response.data;
    }
}

// 导出
window.DataService = DataService;

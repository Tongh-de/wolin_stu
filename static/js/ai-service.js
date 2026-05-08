/**
 * AI 对话服务模块
 * 处理 RAG 问答和 Agent 对话
 */

class AIService {
    constructor() {
        this.sessionId = StorageUtils.get('ai_session_id') || this.generateSessionId();
        this.messageHistory = StorageUtils.get('ai_history') || [];
        this.currentModel = null;
        this.isStreaming = false;
        
        // 保存 sessionId
        StorageUtils.set('ai_session_id', this.sessionId);
    }
    
    generateSessionId() {
        return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * 发送消息到 Agent
     */
    async sendToAgent(message, persona = null) {
        const formData = new FormData();
        formData.append('question', message);
        formData.append('session_id', this.sessionId);
        if (persona) formData.append('persona', persona);
        
        try {
            const response = await fetch(API_CONFIG.AGENT.CHAT, {
                method: 'POST',
                body: formData
            });
            
            return await this.processStreamResponse(response);
        } catch (error) {
            console.error('Agent 请求失败:', error);
            throw error;
        }
    }
    
    /**
     * 发送消息到 RAG
     */
    async sendToRAG(message) {
        const formData = new FormData();
        formData.append('question', message);
        formData.append('session_id', this.sessionId);
        
        try {
            const response = await fetch(API_CONFIG.RAG.QUERY, {
                method: 'POST',
                body: formData
            });
            
            return await this.processStreamResponse(response);
        } catch (error) {
            console.error('RAG 请求失败:', error);
            throw error;
        }
    }
    
    /**
     * 处理流式响应
     */
    async processStreamResponse(response) {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let result = '';
        let meta = null;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'meta') {
                            meta = data;
                        } else if (data.type === 'answer') {
                            result += data.content;
                        } else if (data.type === 'error') {
                            throw new Error(data.content);
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }
                }
            }
        }
        
        return { content: result, meta };
    }
    
    /**
     * 获取知识库统计
     */
    async getKnowledgeStats() {
        try {
            const response = await axios.get(API_CONFIG.RAG.STATS);
            return response.data?.data || {};
        } catch (error) {
            console.error('获取知识库统计失败:', error);
            return {};
        }
    }
    
    /**
     * 上传文档到知识库
     */
    async uploadDocument(file, category = 'general', onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);
        
        try {
            const response = await axios.post(API_CONFIG.RAG.UPLOAD, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: onProgress
            });
            return response.data;
        } catch (error) {
            console.error('上传失败:', error);
            throw error;
        }
    }
    
    /**
     * 清空知识库
     */
    async clearKnowledgeBase() {
        try {
            const response = await axios.delete(API_CONFIG.RAG.CLEAR);
            return response.data;
        } catch (error) {
            console.error('清空知识库失败:', error);
            throw error;
        }
    }
    
    /**
     * 获取模型列表
     */
    async getModels() {
        try {
            const response = await axios.get(API_CONFIG.AGENT.MODELS);
            return response.data || [];
        } catch (error) {
            console.error('获取模型列表失败:', error);
            return [];
        }
    }
    
    /**
     * 添加消息到历史
     */
    addToHistory(role, content) {
        this.messageHistory.push({ role, content, timestamp: Date.now() });
        // 限制历史记录数量
        if (this.messageHistory.length > 50) {
            this.messageHistory = this.messageHistory.slice(-50);
        }
        StorageUtils.set('ai_history', this.messageHistory);
    }
    
    /**
     * 清空历史记录
     */
    clearHistory() {
        this.messageHistory = [];
        StorageUtils.set('ai_history', []);
        this.sessionId = this.generateSessionId();
        StorageUtils.set('ai_session_id', this.sessionId);
    }
}

// 导出
window.AIService = AIService;

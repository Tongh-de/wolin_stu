-- Agent 记忆表
-- 用于存储 agent 的会话对话历史

CREATE TABLE IF NOT EXISTS agent_memory (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    user_id INT COMMENT '用户ID，与users表关联',
    role VARCHAR(16) NOT NULL COMMENT '角色: user/assistant',
    content TEXT NOT NULL COMMENT '消息内容',
    intent VARCHAR(32) COMMENT '意图类型',
    model_used VARCHAR(64) COMMENT '使用的模型',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent会话记忆表';

-- 如果表已存在，添加 user_id 字段的 ALTER 语句
-- ALTER TABLE agent_memory ADD COLUMN user_id INT COMMENT '用户ID，与users表关联' AFTER session_id;
-- ALTER TABLE agent_memory ADD INDEX idx_user_id (user_id);

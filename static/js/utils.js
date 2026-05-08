/**
 * 工具函数模块
 */

// ============================================
// 格式化工具
// ============================================

const FormatUtils = {
    /**
     * 格式化日期
     * @param {string|Date} date - 日期
     * @param {string} format - 格式，默认 'YYYY-MM-DD'
     */
    formatDate(date, format = 'YYYY-MM-DD') {
        if (!date) return '-';
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day);
    },
    
    /**
     * 格式化日期时间
     */
    formatDateTime(date) {
        return this.formatDate(date, 'YYYY-MM-DD HH:mm:ss');
    },
    
    /**
     * 格式化数字（千分位）
     */
    formatNumber(num) {
        if (num === null || num === undefined) return '-';
        return Number(num).toLocaleString('zh-CN');
    },
    
    /**
     * 格式化货币
     */
    formatCurrency(amount) {
        if (!amount) return '-';
        return `¥${Number(amount).toLocaleString('zh-CN')}`;
    },
    
    /**
     * 截断文本
     */
    truncate(text, length = 50) {
        if (!text) return '';
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    }
};

// ============================================
// 验证工具
// ============================================

const ValidateUtils = {
    // 必填验证
    required(value) {
        return value !== null && value !== undefined && value !== '';
    },
    
    // 手机号验证
    phone(value) {
        return /^1[3-9]\d{9}$/.test(value);
    },
    
    // 邮箱验证
    email(value) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    },
    
    // 身份证号验证
    idCard(value) {
        return /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/.test(value);
    }
};

// ============================================
// DOM 工具
// ============================================

const DOMUtils = {
    /**
     * 显示元素
     */
    show(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) element.style.display = '';
    },
    
    /**
     * 隐藏元素
     */
    hide(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) element.style.display = 'none';
    },
    
    /**
     * 切换显示/隐藏
     */
    toggle(element, force) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            if (force !== undefined) {
                element.style.display = force ? '' : 'none';
            } else {
                element.style.display = element.style.display === 'none' ? '' : 'none';
            }
        }
    }
};

// ============================================
// 本地存储工具
// ============================================

const StorageUtils = {
    KEY_PREFIX: 'wolin_',
    
    set(key, value) {
        try {
            const data = JSON.stringify(value);
            localStorage.setItem(this.KEY_PREFIX + key, data);
            return true;
        } catch (e) {
            console.error('存储失败:', e);
            return false;
        }
    },
    
    get(key, defaultValue = null) {
        try {
            const data = localStorage.getItem(this.KEY_PREFIX + key);
            return data ? JSON.parse(data) : defaultValue;
        } catch (e) {
            console.error('读取失败:', e);
            return defaultValue;
        }
    },
    
    remove(key) {
        localStorage.removeItem(this.KEY_PREFIX + key);
    },
    
    clear() {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith(this.KEY_PREFIX)) {
                localStorage.removeItem(key);
            }
        });
    }
};

// ============================================
// 防抖/节流
// ============================================

const ThrottleUtils = {
    debounce(fn, delay = 300) {
        let timer = null;
        return function (...args) {
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },
    
    throttle(fn, delay = 300) {
        let last = 0;
        return function (...args) {
            const now = Date.now();
            if (now - last >= delay) {
                last = now;
                fn.apply(this, args);
            }
        };
    }
};

// ============================================
// 导出
// ============================================

window.FormatUtils = FormatUtils;
window.ValidateUtils = ValidateUtils;
window.DOMUtils = DOMUtils;
window.StorageUtils = StorageUtils;
window.ThrottleUtils = ThrottleUtils;

/**
 * 图表服务模块
 * 封装 ECharts 图表创建
 */

class ChartService {
    constructor() {
        this.charts = {};
    }
    
    /**
     * 创建柱状图
     */
    createBarChart(container, options = {}) {
        const chart = echarts.init(container);
        
        const defaultOptions = {
            grid: { left: '10%', right: '10%', bottom: '15%', top: '15%' },
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', axisLabel: { rotate: 30 } },
            yAxis: { type: 'value' },
            series: [{ type: 'bar', itemStyle: { borderRadius: { topLeft: 4, topRight: 4, bottomLeft: 0, bottomRight: 0 } } }]
        };
        
        chart.setOption({ ...defaultOptions, ...options });
        this.charts[container.id] = chart;
        return chart;
    }
    
    /**
     * 创建饼图
     */
    createPieChart(container, options = {}) {
        const chart = echarts.init(container);
        
        const defaultOptions = {
            tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
            legend: { bottom: '5%', left: 'center' },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
                label: { show: false },
                emphasis: { label: { show: true, fontSize: 14 } }
            }]
        };
        
        chart.setOption({ ...defaultOptions, ...options });
        this.charts[container.id] = chart;
        return chart;
    }
    
    /**
     * 创建折线图
     */
    createLineChart(container, options = {}) {
        const chart = echarts.init(container);
        
        const defaultOptions = {
            grid: { left: '10%', right: '10%', bottom: '15%', top: '15%' },
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', boundaryGap: false },
            yAxis: { type: 'value' },
            series: [{ type: 'line', smooth: true, areaStyle: {} }]
        };
        
        chart.setOption({ ...defaultOptions, ...options });
        this.charts[container.id] = chart;
        return chart;
    }
    
    /**
     * 班级平均分排名柱状图
     */
    renderClassRanking(container, data) {
        const chart = echarts.init(container);
        
        const sortedData = [...data].sort((a, b) => b.avg_score - a.avg_score);
        const names = sortedData.map(d => d.class_name || 'Class' + d.class_id);
        const scores = sortedData.map(d => parseFloat(d.avg_score || 0).toFixed(1));
        
        chart.setOption({
            grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
            tooltip: { trigger: 'axis', formatter: '{b}: {c}' },
            xAxis: { type: 'value', max: 100 },
            yAxis: { type: 'category', data: names, axisLabel: { fontSize: 11 } },
            series: [{
                type: 'bar',
                data: scores,
                itemStyle: {
                    color: function(params) {
                        var color;
                        if (params.value >= 90) color = '#10b981';
                        else if (params.value >= 75) color = '#3b82f6';
                        else if (params.value >= 60) color = '#f59e0b';
                        else color = '#ef4444';
                        return color;
                    },
                    borderRadius: [0, 4, 4, 0]
                },
                label: { show: true, position: 'right', formatter: '{c}' }
            }]
        });
        
        this.charts[container.id] = chart;
        return chart;
    }
    
    /**
     * 班级男女比例饼图
     */
    renderGenderPie(container, data) {
        const chart = echarts.init(container);
        
        var chartData = [
            { value: data.male_count || 0, name: 'Male' },
            { value: data.female_count || 0, name: 'Female' }
        ];
        
        chart.setOption({
            tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
            legend: { orient: 'vertical', right: '5%', top: 'center' },
            series: [{
                type: 'pie',
                radius: ['45%', '70%'],
                center: ['35%', '50%'],
                avoidLabelOverlap: false,
                itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
                label: { show: false },
                emphasis: {
                    label: { show: true, fontSize: 14, fontWeight: 'bold' }
                },
                data: chartData,
                color: ['#3b82f6', '#ec4899']
            }]
        });
        
        this.charts[container.id] = chart;
        return chart;
    }
    
    /**
     * 仪表盘
     */
    renderGauge(container, value, options) {
        var chart = echarts.init(container);
        options = options || {};
        
        var defaultOptions = {
            series: [{
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                center: ['50%', '75%'],
                radius: '90%',
                min: 0,
                max: 100,
                splitNumber: 8,
                axisLine: { lineStyle: { width: 6, color: [[0.3, '#ef4444'], [0.7, '#f59e0b'], [1, '#10b981']] } },
                pointer: { icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z', length: '12%', width: 20, offsetCenter: [0, '-60%'], itemStyle: { color: 'auto' } },
                axisTick: { length: 12, lineStyle: { color: 'auto', width: 2 } },
                splitLine: { length: 20, lineStyle: { color: 'auto', width: 5 } },
                axisLabel: { color: '#464646', fontSize: 12, distance: -60 },
                title: { offsetCenter: [0, '-10%'], fontSize: 14 },
                detail: { fontSize: 30, fontWeight: 'bold', offsetCenter: [0, '-35%'], color: '#333' },
                data: [{ value: value }]
            }]
        };
        
        chart.setOption(Object.assign({}, defaultOptions, options));
        this.charts[container.id] = chart;
        return chart;
    }
    
    /**
     * 成绩分布直方图
     */
    renderScoreDistribution(container, data) {
        var chart = echarts.init(container);
        data = data || [];
        
        var ranges = ['0-60', '60-70', '70-80', '80-90', '90-100'];
        var counts = [0, 0, 0, 0, 0];
        
        data.forEach(function(score) {
            var s = parseFloat(score) || 0;
            if (s < 60) counts[0]++;
            else if (s < 70) counts[1]++;
            else if (s < 80) counts[2]++;
            else if (s < 90) counts[3]++;
            else counts[4]++;
        });
        
        chart.setOption({
            tooltip: { trigger: 'axis' },
            grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
            xAxis: { type: 'category', data: ranges },
            yAxis: { type: 'value' },
            series: [{
                type: 'bar',
                data: counts,
                itemStyle: {
                    color: function(params) {
                        return ['#ef4444', '#f59e0b', '#eab308', '#84cc16', '#10b981'][params.dataIndex];
                    }
                },
                barWidth: '50%'
            }]
        });
        
        this.charts[container.id] = chart;
        return chart;
    }
    
    /**
     * 刷新图表
     */
    refresh(container, data, type) {
        if (!this.charts[container.id]) return;
        
        switch (type) {
            case 'classRanking':
                this.renderClassRanking(container, data);
                break;
            case 'genderPie':
                this.renderGenderPie(container, data);
                break;
            case 'scoreDist':
                this.renderScoreDistribution(container, data);
                break;
        }
    }
    
    /**
     * 响应式调整
     */
    resizeAll() {
        var self = this;
        Object.values(this.charts).forEach(function(chart) {
            if (chart) chart.resize();
        });
    }
    
    /**
     * 销毁所有图表
     */
    disposeAll() {
        Object.values(this.charts).forEach(function(chart) {
            if (chart) chart.dispose();
        });
        this.charts = {};
    }
}

// Export
window.ChartService = ChartService;

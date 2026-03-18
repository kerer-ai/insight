#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成GitCode社区数字化看板HTML页面和Markdown文件
"""

import json
import datetime
import os
import sys


def generate_dashboard(config_file=None):
    """生成更新后的仪表盘HTML页面"""
    # 读取配置文件
    if config_file is None:
        # 检查是否有命令行参数
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        else:
            # 默认使用第一个找到的配置文件
            config_files = [f for f in os.listdir('.') if f.startswith('config_') and f.endswith('.json')]
            if not config_files:
                print("错误: 找不到任何配置文件")
                return
            config_file = config_files[0]
    
    if not os.path.exists(config_file):
        print(f"错误: 找不到配置文件 {config_file}")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    owner = config.get("owner", "Community")
    
    # 读取JSON数据
    json_file = f"{owner}_community_stats_detailed.json"
    if not os.path.exists(json_file):
        print(f"错误: 找不到数据文件 {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建HTML内容
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>COMMUNITY_NAME社区数字化看板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            width: 100%;
            max-width: 100%;
            margin: 0 auto;
            padding: 15px;
            overflow-x: hidden;
        }
        
        h1 {
            text-align: center;
            color: #1a365d;
            margin-bottom: 25px;
            padding: 15px 0;
            border-bottom: 2px solid #e2e8f0;
            font-size: 28px;
        }
        
        .stats-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        /* 大屏幕适配 */
        @media (min-width: 1200px) {
            .container {
                max-width: 95%;
            }
            .stats-overview {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }
        }
        
        @media (min-width: 1600px) {
            .container {
                max-width: 90%;
            }
            .stats-overview {
                grid-template-columns: repeat(6, 1fr);
            }
        }
        
        @media (min-width: 2000px) {
            .container {
                max-width: 85%;
            }
            table {
                font-size: 15px;
            }
        }
        
        /* 小屏幕适配 */
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            h1 {
                font-size: 22px;
                margin-bottom: 15px;
                padding: 8px 0;
            }
            
            .stats-overview {
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 10px;
            }
            
            .stat-card {
                padding: 10px;
            }
            
            .stat-number {
                font-size: 22px;
            }
            
            .stat-title {
                font-size: 12px;
            }
            
            /* 表格适配 */
            table {
                min-width: 800px;
                font-size: 11px;
            }
            
            th, td {
                padding: 6px 4px;
            }
            
            /* 隐藏部分列以适配小屏幕 */
            th:nth-child(8), td:nth-child(8),
            th:nth-child(9), td:nth-child(9),
            th:nth-child(12), td:nth-child(12),
            th:nth-child(14), td:nth-child(14),
            th:nth-child(15), td:nth-child(15) {
                display: none;
            }
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 5px;
            }
            
            h1 {
                font-size: 20px;
                margin-bottom: 12px;
                padding: 6px 0;
            }
            
            .stats-overview {
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }
            
            .stat-card {
                padding: 8px;
            }
            
            .stat-title {
                font-size: 11px;
                margin-bottom: 5px;
            }
            
            .stat-number {
                font-size: 18px;
            }
            
            /* 进一步隐藏表格列 */
            th:nth-child(11), td:nth-child(11),
            th:nth-child(10), td:nth-child(10) {
                display: none;
            }
            
            .chart-container {
                height: 200px;
                padding: 10px;
            }
            
            .chart-title {
                font-size: 14px;
                margin-bottom: 10px;
            }
        }
        
        .stat-title {
            font-size: 14px;
            color: #64748b;
            margin-bottom: 10px;
        }
        
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #1e40af;
        }
        
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            height: 350px;
        }
        
        /* 响应式图表高度 */
        @media (max-width: 768px) {
            .chart-container {
                height: 250px;
            }
        }
        
        @media (max-width: 480px) {
            .chart-container {
                height: 200px;
            }
        }
        
        @media (min-width: 1600px) {
            .chart-container {
                height: 400px;
            }
        }
        
        .chart-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #1a365d;
        }
        
        .table-section {
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        /* 表格水平滚动容器 */
        .table-scroll-container {
            overflow-x: auto;
            width: 100%;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
            scrollbar-color: #cbd5e1 #f1f5f9;
        }
        
        /* 优化表格滚动体验 */
        .table-scroll-container::-webkit-scrollbar {
            height: 6px;
        }
        
        .table-scroll-container::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 3px;
        }
        
        .table-scroll-container::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
        
        .table-scroll-container::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
        
        table {
            width: 100%;
            min-width: 900px;
            border-collapse: collapse;
            font-size: 14px;
            touch-action: manipulation;
        }
        
        /* 排序表头样式 */
        th[onclick] {
            cursor: pointer;
            user-select: none;
            background-color: #f1f5f9;
        }
        
        th[onclick]:hover {
            background-color: #e2e8f0;
        }
        
        .sort-indicator {
            font-size: 0.8em;
            margin-left: 5px;
            color: #64748b;
        }
        
        /* 高亮样式 */
        .highlight-red {
            color: #dc3545;
            font-weight: bold;
        }
        
        th, td {
            padding: 8px 6px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            white-space: nowrap;
        }
        
        th {
            background-color: #f1f5f9;
            font-weight: 600;
            color: #475569;
        }
        
        tr:hover {
            background-color: #f8fafc;
        }
        
        a {
            color: #2563eb;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .footer {
            text-align: center;
            color: #64748b;
            padding: 15px 10px;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>COMMUNITY_NAME社区数字化看板</h1>
        
        <div class="stats-overview">
            <div class="stat-card">
                <div class="stat-title">仓库总数</div>
                <div class="stat-number">64</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">总贡献者数</div>
                <div class="stat-number">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">总PR数（100天内）</div>
                <div class="stat-number">3010</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">30天内PR数</div>
                <div class="stat-number">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">平均门禁时长(分钟)</div>
                <div class="stat-number">11.1</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">PR平均闭环时间(天)</div>
                <div class="stat-number">0.0</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">项目贡献者分布</div>
                <canvas id="contributorChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">项目PR数量分布（100天）</div>
                <canvas id="prCountChart"></canvas>
            </div>
        </div>
        
        <div class="table-section">
            <h2 style="margin-bottom: 15px; color: #1a365d;">项目详细统计</h2>
            <div class="table-scroll-container">
                <table id="project-stats-table">
                <thead>
                    <tr>
                        <th>序号</th>
                        <th>项目名称</th>
                        <th onclick="sortTable(2)">贡献者数量 <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(3)">一年贡献者 <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(4)">总PR（100天） <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(5)">近7天PR <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(6)">近30天PR <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(7)">单日创建PR峰值（30天） <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(8)">峰值PR日期</th>
                        <th onclick="sortTable(9)">门禁类型 <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(10)">平均门禁时长(分钟) <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(11)">最长门禁时长(分钟) <span class="sort-indicator"></span></th>
                        <th>最长门禁时长PR</th>
                        <th onclick="sortTable(13)">PR平均闭环时间(天) <span class="sort-indicator"></span></th>
                        <th onclick="sortTable(14)">PR最长闭环时间(天) <span class="sort-indicator"></span></th>
                        <th>最长闭环PR</th>
                    </tr>
                </thead>
                <tbody>
                </tbody>
            </table>
            </div>
            <script>
                // 排序状态，记录当前排序的列和方向
                let currentSortColumn = -1;
                let currentSortDirection = 1; // 1为升序，-1为降序
                
                function sortTable(columnIndex) {
                    const table = document.querySelector('.table-section table');
                    const tbody = table.getElementsByTagName('tbody')[0];
                    const rows = Array.from(tbody.getElementsByTagName('tr'));
                    
                    // 切换排序方向
                    if (columnIndex === currentSortColumn) {
                        currentSortDirection *= -1;
                    } else {
                        currentSortColumn = columnIndex;
                        currentSortDirection = 1;
                    }
                    
                    // 移除所有排序指示器
                    const indicators = table.querySelectorAll('.sort-indicator');
                    indicators.forEach(ind => ind.textContent = '');
                    
                    // 设置当前列的排序指示器
                    const currentIndicator = table.rows[0].cells[columnIndex].querySelector('.sort-indicator');
                    currentIndicator.textContent = currentSortDirection === 1 ? '↑' : '↓';
                    
                    // 排序行
                    rows.sort((a, b) => {
                        // 获取可见单元格的索引
                        const visibleColumns = [];
                        for (let i = 0; i < a.cells.length; i++) {
                            if (getComputedStyle(a.cells[i]).display !== 'none') {
                                visibleColumns.push(i);
                            }
                        }
                        
                        // 计算实际排序的可见列索引
                        const actualColumnIndex = visibleColumns.indexOf(columnIndex);
                        if (actualColumnIndex === -1) return 0;
                        
                        const aValue = a.cells[columnIndex].textContent;
                        const bValue = b.cells[columnIndex].textContent;
                        
                        // 尝试将值转换为数字进行比较
                        const aNum = parseFloat(aValue);
                        const bNum = parseFloat(bValue);
                        
                        if (!isNaN(aNum) && !isNaN(bNum)) {
                            return (aNum - bNum) * currentSortDirection;
                        } else {
                            // 字符串比较
                            return aValue.localeCompare(bValue) * currentSortDirection;
                        }
                    });
                    
                    // 重新插入排序后的行
                    rows.forEach(row => tbody.appendChild(row));
                    
                    // 更新序号
                    rows.forEach((row, index) => {
                        row.cells[0].textContent = index + 1;
                    });
                }
            </script>
        </div>
        
        <div class="footer">
            <p class="text-center">统计时间: 2025-11-28 01:24:52</p>
        </div>
    </div>
</body>
</html>'''
    
    # 更新统计概览部分
    total_repos = data["total_repos"]
    
    # 计算统计指标
    total_contributors = 0
    total_prs = 0
    prs_30_days = 0
    total_gatekeeper_duration = 0
    projects_with_gatekeeper = 0
    
    for project_data in data["project_stats"].values():
        stats = project_data["stats"]
        total_contributors += stats["contributor_count"]
        total_prs += stats["total_pr_count"]
        prs_30_days += stats["pr_count_30_days"]
        
        if stats["avg_gatekeeper_duration"] > 0:
            total_gatekeeper_duration += stats["avg_gatekeeper_duration"]
            projects_with_gatekeeper += 1
    
    # 计算平均门禁时长
    avg_gatekeeper_duration = 0.0
    if projects_with_gatekeeper > 0:
        avg_gatekeeper_duration = total_gatekeeper_duration / projects_with_gatekeeper
    avg_gatekeeper_duration = f"{avg_gatekeeper_duration:.2f}"
    
    # 计算平均PR闭环时间
    total_pr_close_duration = 0
    projects_with_pr_close = 0
    for project_data in data["project_stats"].values():
        stats = project_data["stats"]
        if stats["avg_pr_close_duration"] > 0:
            total_pr_close_duration += stats["avg_pr_close_duration"]
            projects_with_pr_close += 1
    
    avg_pr_close_duration = 0.0
    if projects_with_pr_close > 0:
        # 转换为天，保留2位小数
        avg_pr_close_duration = (total_pr_close_duration / projects_with_pr_close) / 1440
    avg_pr_close_duration = f"{avg_pr_close_duration:.2f}"
    
    # 更新统计概览卡片
    html_content = html_content.replace('<div class="stat-number">64</div>', f'<div class="stat-number">{total_repos}</div>')
    html_content = html_content.replace('<div class="stat-number">0</div>', f'<div class="stat-number">{total_contributors}</div>', 1)
    html_content = html_content.replace('<div class="stat-number">3010</div>', f'<div class="stat-number">{total_prs}</div>')
    html_content = html_content.replace('<div class="stat-number">0</div>', f'<div class="stat-number">{prs_30_days}</div>', 1)
    html_content = html_content.replace('<div class="stat-number">11.1</div>', f'<div class="stat-number">{avg_gatekeeper_duration}</div>')
    html_content = html_content.replace('<div class="stat-number">0.0</div>', f'<div class="stat-number">{avg_pr_close_duration}</div>', 1)
    html_content = html_content.replace('<div class="stat-number">0.00</div>', f'<div class="stat-number">{avg_pr_close_duration}</div>', 1)
    
    # 更新统计时间
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = html_content.replace('<p class="text-center">统计时间: 2025-11-28 01:24:52</p>', 
                                        f'<p class="text-center">统计时间: {current_time}</p>')
    
    # 准备图表数据
    # 1. 贡献者分布（前10个项目）
    sorted_projects_by_contributors = sorted(data["project_stats"].items(), 
                                             key=lambda x: x[1]["stats"]["contributor_count"], 
                                             reverse=True)[:10]
    
    # 2. PR数量分布（前10个项目）
    sorted_projects_by_prs = sorted(data["project_stats"].items(), 
                                    key=lambda x: x[1]["stats"]["total_pr_count"], 
                                    reverse=True)[:10]
    
    # 生成表格内容
    table_rows = ""
    # 按照PR平均闭环时间从大到小排序项目
    sorted_projects = sorted(data["project_stats"].items(), 
                            key=lambda x: x[1]["stats"]["avg_pr_close_duration"], 
                            reverse=True)
    for i, (project_name, project_data) in enumerate(sorted_projects, 1):
        project_info = project_data["project_info"]
        stats = project_data["stats"]
        
        # 生成表格行
        table_row = f"""
        <tr>
            <td>{i}</td>
            <td><a href="{project_info['url']}" target="_blank">{project_name}</a></td>
            <td>{stats['contributor_count']}</td>
            <td>{stats.get('contributor_count_year', 0)}</td>
            <td>{stats['total_pr_count']}</td>
            <td>{stats['pr_count_7_days']}</td>
            <td>{stats['pr_count_30_days']}</td>
            <td>{stats['max_pr_count_30_days']}</td>
            <td>{stats['max_pr_date_30_days']}</td>
            <td>{'黄区 and 蓝区' if stats['yellow_ci_flag'] and stats['blue_ci_flag'] else '黄区' if stats['yellow_ci_flag'] else '蓝区' if stats['blue_ci_flag'] else '无'}</td>
            <td{stats['avg_gatekeeper_duration'] > 30 and ' class="highlight-red"' or ''}>{stats['avg_gatekeeper_duration']:.2f}</td>
            <td>{stats['max_duration']:.2f}</td>
            <td>{f'<a href="{stats["max_duration_pr_url"]}" target="_blank">查看</a>' if stats['max_duration_pr_url'] else '-'}</td>
            <td>{(stats['avg_pr_close_duration'] / 1440):.2f}</td>
            <td>{(stats['max_pr_close_duration'] / 1440):.2f}</td>
            <td>{f'<a href="{stats["max_close_duration_pr_url"]}" target="_blank">查看</a>' if stats['max_close_duration_pr_url'] else '-'}</td>
        </tr>
        """
        table_rows += table_row
    
    # 替换表格内容
    table_start = "<tbody>"
    table_end = "</tbody>"
    tbody_start_index = html_content.find(table_start)
    tbody_end_index = html_content.find(table_end)
    
    if tbody_start_index != -1 and tbody_end_index != -1:
        new_html = html_content[:tbody_start_index + len(table_start)] + table_rows + html_content[tbody_end_index:]
        html_content = new_html
    
    # 更新图表数据
    # 1. 贡献者分布图表
    contributor_labels = json.dumps([project[0] for project in sorted_projects_by_contributors])
    contributor_data = json.dumps([project[1]["stats"]["contributor_count"] for project in sorted_projects_by_contributors])
    
    # 2. PR数量分布图表
    pr_labels = json.dumps([project[0] for project in sorted_projects_by_prs])
    pr_data = json.dumps([project[1]["stats"]["total_pr_count"] for project in sorted_projects_by_prs])
    
    # 生成图表脚本
    chart_script = """
    <script>
    // 确保DOM和Chart.js加载完成后执行图表渲染
    window.onload = function() {
        // 贡献者分布图表
        const contributorCtx = document.getElementById('contributorChart').getContext('2d');
        new Chart(contributorCtx, {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{
                    label: '贡献者数量',
                    data: %s,
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FFCD56', '#C9CBCF', '#3498DB', '#2ECC71']
                }]
            },
            options: {
                responsive: true, 
                maintainAspectRatio: false, 
                scales: {
                    y: {beginAtZero: true}
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: {
                                size: window.innerWidth < 480 ? 10 : 12
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            font: {
                                size: window.innerWidth < 480 ? 8 : (window.innerWidth < 768 ? 10 : 12)
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: window.innerWidth < 480 ? 8 : (window.innerWidth < 768 ? 10 : 12)
                            }
                        }
                    }
                },
                onResize: function(chart, size) {
                    // 动态调整标签字体大小，确保对象存在
                    if (chart.options && chart.options.scales) {
                        const fontSize = window.innerWidth < 480 ? 8 : (window.innerWidth < 768 ? 10 : 12);
                        
                        // 确保x轴相关对象存在
                        if (chart.options.scales.x && chart.options.scales.x.ticks) {
                            if (!chart.options.scales.x.ticks.font) {
                                chart.options.scales.x.ticks.font = {};
                            }
                            chart.options.scales.x.ticks.font.size = fontSize;
                        }
                        
                        // 确保y轴相关对象存在
                        if (chart.options.scales.y && chart.options.scales.y.ticks) {
                            if (!chart.options.scales.y.ticks.font) {
                                chart.options.scales.y.ticks.font = {};
                            }
                            chart.options.scales.y.ticks.font.size = fontSize;
                        }
                        
                        chart.update();
                    }
                }
            }
        });
        
        // PR数量分布图表
        const prCtx = document.getElementById('prCountChart').getContext('2d');
        new Chart(prCtx, {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{
                    label: 'PR数量',
                    data: %s,
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7', '#fa709a', '#fee140']
                }]
            },
            options: {
                responsive: true, 
                maintainAspectRatio: false, 
                scales: {
                    y: {beginAtZero: true}
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: {
                                size: window.innerWidth < 480 ? 10 : 12
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            font: {
                                size: window.innerWidth < 480 ? 8 : (window.innerWidth < 768 ? 10 : 12)
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: window.innerWidth < 480 ? 8 : (window.innerWidth < 768 ? 10 : 12)
                            }
                        }
                    }
                },
                onResize: function(chart, size) {
                    // 动态调整标签字体大小，确保对象存在
                    if (chart.options && chart.options.scales) {
                        const fontSize = window.innerWidth < 480 ? 8 : (window.innerWidth < 768 ? 10 : 12);
                        
                        // 确保x轴相关对象存在
                        if (chart.options.scales.x && chart.options.scales.x.ticks) {
                            if (!chart.options.scales.x.ticks.font) {
                                chart.options.scales.x.ticks.font = {};
                            }
                            chart.options.scales.x.ticks.font.size = fontSize;
                        }
                        
                        // 确保y轴相关对象存在
                        if (chart.options.scales.y && chart.options.scales.y.ticks) {
                            if (!chart.options.scales.y.ticks.font) {
                                chart.options.scales.y.ticks.font = {};
                            }
                            chart.options.scales.y.ticks.font.size = fontSize;
                        }
                        
                        chart.update();
                    }
                }
            }
        });
    };
    </script>
    """ % (contributor_labels, contributor_data, pr_labels, pr_data)
    
    # 找到最后一个</body>标签，在其前插入新脚本
    body_end_index = html_content.rfind("</body>")
    if body_end_index != -1:
        new_html = html_content[:body_end_index] + chart_script + html_content[body_end_index:]
        html_content = new_html
    
    # 替换HTML中的社区名称
    html_content = html_content.replace('COMMUNITY_NAME', owner)
    
    # 保存更新后的HTML文件
    output_file = f"{owner}_community_dashboard.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"成功生成更新后的仪表盘页面: {output_file}")
    
    # 生成Markdown文件
    generate_markdown_file(data, owner, current_time)


def generate_markdown_file(data, owner, current_time):
    """生成Markdown格式的社区数字化看板"""
    # 计算统计指标
    total_repos = data["total_repos"]
    total_contributors = 0
    total_prs = 0
    prs_30_days = 0
    total_gatekeeper_duration = 0
    projects_with_gatekeeper = 0
    
    for project_data in data["project_stats"].values():
        stats = project_data["stats"]
        total_contributors += stats["contributor_count"]
        total_prs += stats["total_pr_count"]
        prs_30_days += stats["pr_count_30_days"]
        
        if stats["avg_gatekeeper_duration"] > 0:
            total_gatekeeper_duration += stats["avg_gatekeeper_duration"]
            projects_with_gatekeeper += 1
    
    # 计算平均门禁时长
    avg_gatekeeper_duration = 0.0
    if projects_with_gatekeeper > 0:
        avg_gatekeeper_duration = total_gatekeeper_duration / projects_with_gatekeeper
    avg_gatekeeper_duration = f"{avg_gatekeeper_duration:.2f}"
    
    # 计算平均PR闭环时间
    total_pr_close_duration = 0
    projects_with_pr_close = 0
    for project_data in data["project_stats"].values():
        stats = project_data["stats"]
        if stats["avg_pr_close_duration"] > 0:
            total_pr_close_duration += stats["avg_pr_close_duration"]
            projects_with_pr_close += 1
    
    avg_pr_close_duration = 0.0
    if projects_with_pr_close > 0:
        # 转换为天，保留2位小数
        avg_pr_close_duration = (total_pr_close_duration / projects_with_pr_close) / 1440
    avg_pr_close_duration = f"{avg_pr_close_duration:.2f}"
    
    # 生成Markdown内容
    md_content = f"# {owner}社区数字化看板\n\n"
    md_content += f"**统计时间**: {current_time}\n\n"
    
    # 统计概览
    md_content += "## 统计概览\n\n"
    md_content += "| 指标 | 数值 |\n"
    md_content += "|------|------|\n"
    md_content += f"| 仓库总数 | {total_repos} |\n"
    md_content += f"| 总贡献者数 | {total_contributors} |\n"
    md_content += f"| 总PR数（100天内） | {total_prs} |\n"
    md_content += f"| 30天内PR数 | {prs_30_days} |\n"
    md_content += f"| 平均门禁时长(分钟) | {avg_gatekeeper_duration} |\n"
    md_content += f"| PR平均闭环时间(天) | {avg_pr_close_duration} |\n\n"
    
    # Top 5 贡献者最多的仓库
    md_content += "## Top 5 贡献者最多的仓库\n\n"
    md_content += "| 排名 | 项目名称 | 贡献者数量 | 一年贡献者 |\n"
    md_content += "|------|----------|------------|------------|\n"
    
    # 获取贡献者数量排名前5的项目
    sorted_projects_by_contributors = sorted(data["project_stats"].items(),
                                           key=lambda x: x[1]["stats"]["contributor_count"],
                                           reverse=True)[:5]
    
    for i, (project_name, project_data) in enumerate(sorted_projects_by_contributors, 1):
        project_info = project_data["project_info"]
        stats = project_data["stats"]
        md_content += f"| {i} | [{project_name}]({project_info['url']}) | {stats['contributor_count']} | {stats.get('contributor_count_year', 0)} |\n"
    
    md_content += "\n"
    
    # Top 5 PR数量最多的仓库
    md_content += "## Top 5 PR数量最多的仓库\n\n"
    md_content += "| 排名 | 项目名称 | 总PR数（100天） | 近7天PR | 近30天PR |\n"
    md_content += "|------|----------|---------------|---------|----------|\n"
    
    # 获取PR数量排名前5的项目
    sorted_projects_by_prs = sorted(data["project_stats"].items(),
                                  key=lambda x: x[1]["stats"]["total_pr_count"],
                                  reverse=True)[:5]
    
    for i, (project_name, project_data) in enumerate(sorted_projects_by_prs, 1):
        project_info = project_data["project_info"]
        stats = project_data["stats"]
        md_content += f"| {i} | [{project_name}]({project_info['url']}) | {stats['total_pr_count']} | {stats['pr_count_7_days']} | {stats['pr_count_30_days']} |\n"
    
    md_content += "\n"
    
    # 项目详细统计表格
    md_content += "## 项目详细统计\n\n"
    md_content += "| 序号 | 项目名称 | 贡献者数量 | 一年贡献者 | 总PR（100天） | 近7天PR | 近30天PR | 单日创建PR峰值（30天） | 峰值PR日期 | 门禁类型 | 平均门禁时长(分钟) | 最长门禁时长(分钟) | 平均闭环时间(天) | 最长闭环时间(天) |\n"
    md_content += "|------|----------|------------|------------|---------------|---------|----------|------------------------|------------|----------|--------------------|--------------------|------------------|--------------------|\n"
    
    # 按照PR平均闭环时间从大到小排序项目
    sorted_projects = sorted(data["project_stats"].items(), 
                            key=lambda x: x[1]["stats"]["avg_pr_close_duration"], 
                            reverse=True)
    
    for i, (project_name, project_data) in enumerate(sorted_projects, 1):
        project_info = project_data["project_info"]
        stats = project_data["stats"]
        
        # 生成表格行
        table_row = f"| {i} | [{project_name}]({project_info['url']}) | {stats['contributor_count']} | {stats.get('contributor_count_year', 0)} | {stats['total_pr_count']} | {stats['pr_count_7_days']} | {stats['pr_count_30_days']} | {stats['max_pr_count_30_days']} | {stats['max_pr_date_30_days']} | {stats['yellow_ci_flag'] and '黄区' or stats['blue_ci_flag'] and '蓝区' or '无'} | {stats['avg_gatekeeper_duration']:.2f} | {stats['max_duration']:.2f} | {(stats['avg_pr_close_duration'] / 1440):.2f} | {(stats['max_pr_close_duration'] / 1440):.2f} |\n"
        md_content += table_row
    
    # 保存Markdown文件
    output_file = f"{owner}_community_dashboard.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"成功生成Markdown文件: {output_file}")


if __name__ == "__main__":
    generate_dashboard()

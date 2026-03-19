# -*- coding: utf-8 -*-
"""
GitCode 社区看板生成模块
生成社区数字化看板 HTML 页面和 Markdown 文件
"""

import json
import datetime
import os


def generate_dashboard(config_file=None, output_dir=None):
    """生成更新后的仪表盘HTML页面"""
    # 设置默认配置文件路径
    if config_file is None:
        config_file = os.path.join(os.getcwd(), "config", "gitcode.json")

    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "output")

    if not os.path.exists(config_file):
        print(f"错误: 找不到配置文件 {config_file}")
        return

    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    owner = config.get("owner", "Community")

    # 读取JSON数据
    json_file = os.path.join(output_dir, f"{owner}_community_stats_detailed.json")
    if not os.path.exists(json_file):
        print(f"错误: 找不到数据文件 {json_file}")
        print("请先运行 gc-insight community 获取数据")
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f7fa; color: #333; line-height: 1.6; }
        .container { width: 100%; max-width: 100%; margin: 0 auto; padding: 15px; overflow-x: hidden; }
        h1 { text-align: center; color: #1a365d; margin-bottom: 25px; padding: 15px 0; border-bottom: 2px solid #e2e8f0; font-size: 28px; }
        .stats-overview { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background-color: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); text-align: center; }
        .stat-title { font-size: 14px; color: #64748b; margin-bottom: 10px; }
        .stat-number { font-size: 28px; font-weight: bold; color: #1e40af; }
        .charts-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .chart-container { background-color: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); height: 350px; }
        .chart-title { font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #1a365d; }
        .table-section { background-color: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); margin-bottom: 30px; overflow-x: auto; }
        .table-scroll-container { overflow-x: auto; width: 100%; }
        table { width: 100%; min-width: 900px; border-collapse: collapse; font-size: 14px; }
        th[onclick] { cursor: pointer; user-select: none; background-color: #f1f5f9; }
        th[onclick]:hover { background-color: #e2e8f0; }
        .sort-indicator { font-size: 0.8em; margin-left: 5px; color: #64748b; }
        .highlight-red { color: #dc3545; font-weight: bold; }
        th, td { padding: 8px 6px; text-align: left; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
        th { background-color: #f1f5f9; font-weight: 600; color: #475569; }
        tr:hover { background-color: #f8fafc; }
        a { color: #2563eb; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .footer { text-align: center; color: #64748b; padding: 15px 10px; border-top: 1px solid #e2e8f0; font-size: 12px; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>COMMUNITY_NAME社区数字化看板</h1>

        <div class="stats-overview">
            <div class="stat-card">
                <div class="stat-title">仓库总数</div>
                <div class="stat-number">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">总贡献者数</div>
                <div class="stat-number">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">总PR数（100天内）</div>
                <div class="stat-number">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">30天内PR数</div>
                <div class="stat-number">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">平均门禁时长(分钟)</div>
                <div class="stat-number">0.00</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">PR平均闭环时间(天)</div>
                <div class="stat-number">0.00</div>
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
                let currentSortColumn = -1;
                let currentSortDirection = 1;

                function sortTable(columnIndex) {
                    const table = document.querySelector('.table-section table');
                    const tbody = table.getElementsByTagName('tbody')[0];
                    const rows = Array.from(tbody.getElementsByTagName('tr'));

                    if (columnIndex === currentSortColumn) {
                        currentSortDirection *= -1;
                    } else {
                        currentSortColumn = columnIndex;
                        currentSortDirection = 1;
                    }

                    const indicators = table.querySelectorAll('.sort-indicator');
                    indicators.forEach(ind => ind.textContent = '');

                    const currentIndicator = table.rows[0].cells[columnIndex].querySelector('.sort-indicator');
                    currentIndicator.textContent = currentSortDirection === 1 ? '↑' : '↓';

                    rows.sort((a, b) => {
                        const aValue = a.cells[columnIndex].textContent;
                        const bValue = b.cells[columnIndex].textContent;
                        const aNum = parseFloat(aValue);
                        const bNum = parseFloat(bValue);

                        if (!isNaN(aNum) && !isNaN(bNum)) {
                            return (aNum - bNum) * currentSortDirection;
                        } else {
                            return aValue.localeCompare(bValue) * currentSortDirection;
                        }
                    });

                    rows.forEach(row => tbody.appendChild(row));
                    rows.forEach((row, index) => { row.cells[0].textContent = index + 1; });
                }
            </script>
        </div>

        <div class="footer">
            <p class="text-center">统计时间: </p>
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
        avg_pr_close_duration = (total_pr_close_duration / projects_with_pr_close) / 1440
    avg_pr_close_duration = f"{avg_pr_close_duration:.2f}"

    # 更新统计时间
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 替换统计数值
    html_content = html_content.replace('<div class="stat-number">0</div>', f'<div class="stat-number">{total_repos}</div>', 1)
    html_content = html_content.replace('<div class="stat-number">0</div>', f'<div class="stat-number">{total_contributors}</div>', 1)
    html_content = html_content.replace('<div class="stat-number">0</div>', f'<div class="stat-number">{total_prs}</div>', 1)
    html_content = html_content.replace('<div class="stat-number">0</div>', f'<div class="stat-number">{prs_30_days}</div>', 1)
    html_content = html_content.replace('<div class="stat-number">0.00</div>', f'<div class="stat-number">{avg_gatekeeper_duration}</div>', 1)
    html_content = html_content.replace('<div class="stat-number">0.00</div>', f'<div class="stat-number">{avg_pr_close_duration}</div>', 1)
    html_content = html_content.replace('<p class="text-center">统计时间: </p>',
                                        f'<p class="text-center">统计时间: {current_time}</p>')

    # 准备图表数据
    sorted_projects_by_contributors = sorted(data["project_stats"].items(),
                                             key=lambda x: x[1]["stats"]["contributor_count"],
                                             reverse=True)[:10]

    sorted_projects_by_prs = sorted(data["project_stats"].items(),
                                    key=lambda x: x[1]["stats"]["total_pr_count"],
                                    reverse=True)[:10]

    # 生成表格内容
    table_rows = ""
    sorted_projects = sorted(data["project_stats"].items(),
                            key=lambda x: x[1]["stats"]["avg_pr_close_duration"],
                            reverse=True)
    for i, (project_name, project_data) in enumerate(sorted_projects, 1):
        project_info = project_data["project_info"]
        stats = project_data["stats"]

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

    # 准备图表数据
    contributor_labels = json.dumps([project[0] for project in sorted_projects_by_contributors])
    contributor_data = json.dumps([project[1]["stats"]["contributor_count"] for project in sorted_projects_by_contributors])
    pr_labels = json.dumps([project[0] for project in sorted_projects_by_prs])
    pr_data = json.dumps([project[1]["stats"]["total_pr_count"] for project in sorted_projects_by_prs])

    # 生成图表脚本
    chart_script = f"""
    <script>
    window.onload = function() {{
        new Chart(document.getElementById('contributorChart').getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: {contributor_labels},
                datasets: [{{ label: '贡献者数量', data: {contributor_data}, backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FFCD56', '#C9CBCF', '#3498DB', '#2ECC71'] }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true }} }} }}
        }});

        new Chart(document.getElementById('prCountChart').getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: {pr_labels},
                datasets: [{{ label: 'PR数量', data: {pr_data}, backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7', '#fa709a', '#fee140'] }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true }} }} }}
        }});
    }};
    </script>
    """

    # 插入图表脚本
    body_end_index = html_content.rfind("</body>")
    if body_end_index != -1:
        new_html = html_content[:body_end_index] + chart_script + html_content[body_end_index:]
        html_content = new_html

    # 替换社区名称
    html_content = html_content.replace('COMMUNITY_NAME', owner)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 保存HTML文件
    output_file = os.path.join(output_dir, f"{owner}_community_dashboard.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"成功生成更新后的仪表盘页面: {output_file}")

    # 生成Markdown文件
    generate_markdown_file(data, owner, current_time, output_dir)


def generate_markdown_file(data, owner, current_time, output_dir=None):
    """生成Markdown格式的社区数字化看板"""
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "output")

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

    sorted_projects = sorted(data["project_stats"].items(),
                            key=lambda x: x[1]["stats"]["avg_pr_close_duration"],
                            reverse=True)

    for i, (project_name, project_data) in enumerate(sorted_projects, 1):
        project_info = project_data["project_info"]
        stats = project_data["stats"]

        table_row = f"| {i} | [{project_name}]({project_info['url']}) | {stats['contributor_count']} | {stats.get('contributor_count_year', 0)} | {stats['total_pr_count']} | {stats['pr_count_7_days']} | {stats['pr_count_30_days']} | {stats['max_pr_count_30_days']} | {stats['max_pr_date_30_days']} | {stats['yellow_ci_flag'] and '黄区' or stats['blue_ci_flag'] and '蓝区' or '无'} | {stats['avg_gatekeeper_duration']:.2f} | {stats['max_duration']:.2f} | {(stats['avg_pr_close_duration'] / 1440):.2f} | {(stats['max_pr_close_duration'] / 1440):.2f} |\n"
        md_content += table_row

    # 保存Markdown文件
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{owner}_community_dashboard.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"成功生成Markdown文件: {output_file}")
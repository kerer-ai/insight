# -*- coding: utf-8 -*-
"""
GitCode 仓库综合报告模块
整合 Issue、PR、仓库统计数据生成综合报告
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

from .issue import GitCodeIssueInsight
from .pr import GitCodePRInsight
from .repo_stats import GitCodeRepoStats


class GitCodeReport:
    """仓库综合报告生成器"""

    def __init__(self, repo: str, token: str, owner: str = None, days: int = 30, output_dir: str = None):
        """
        初始化

        Args:
            repo: 仓库名称（path）
            token: API 访问令牌
            owner: 组织名
            days: 统计天数
            output_dir: 输出目录
        """
        self.repo = repo
        self.token = token
        self.owner = owner or self._get_default_owner()
        self.days = days

        # 设置输出目录
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "output")
        self.output_dir = output_dir

    def _get_default_owner(self) -> str:
        """从配置文件获取默认 owner"""
        config_file = os.path.join(os.getcwd(), "config", "gitcode.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("owner", "")
        return ""

    def _collect_issue_data(self) -> Dict:
        """采集 Issue 数据"""
        print(f"\n采集 Issue 数据...")
        insight = GitCodeIssueInsight(
            repo=self.repo,
            token=self.token,
            owner=self.owner,
            days=self.days,
            output_dir=self.output_dir
        )
        # 直接获取数据，不保存文件
        return insight.run()

    def _collect_pr_data(self) -> Dict:
        """采集 PR 数据"""
        print(f"\n采集 PR 数据...")
        insight = GitCodePRInsight(
            repo=self.repo,
            token=self.token,
            owner=self.owner,
            days=self.days,
            output_dir=self.output_dir
        )
        # 直接获取数据，不保存文件
        return insight.run()

    def _collect_repo_stats_data(self) -> Dict:
        """采集仓库统计数据（包含下载、Fork、订阅用户、编程语言）"""
        print(f"\n采集仓库统计数据...")
        stats = GitCodeRepoStats(
            repo=self.repo,
            token=self.token,
            owner=self.owner,
            days=self.days,
            output_dir=self.output_dir
        )
        # 直接获取数据，不保存文件
        return stats.run()

    def collect_all_data(self) -> Dict:
        """采集所有模块数据"""
        print(f"\n{'='*60}")
        print(f"开始采集数据...")
        print(f"{'='*60}")

        # 采集仓库统计数据（包含订阅用户和编程语言）
        repo_stats_data = self._collect_repo_stats_data()

        # 从 repo_stats 数据中提取统计信息
        statistics = repo_stats_data.get("statistics", {})
        download_stats = statistics.get("download_stats", {})
        fork_stats = statistics.get("fork_stats", {})
        subscriber_stats = statistics.get("subscriber_stats", {})
        language_stats = statistics.get("language_stats", {})

        # 采集 Issue 和 PR 数据
        issue_data = self._collect_issue_data()
        pr_data = self._collect_pr_data()

        data = {
            "repo": f"{self.owner}/{self.repo}",
            "analysis_period": f"近 {self.days} 天",
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "issue": issue_data,
            "pr": pr_data,
            "repo_stats": {
                "download_stats": download_stats,
                "fork_stats": fork_stats
            },
            "subscribers": {
                "subscriber_stats": subscriber_stats
            },
            "languages": {
                "language_stats": language_stats
            }
        }

        return data

    def generate_html_report(self, data: Dict, output_file: str):
        """生成 HTML 综合报告"""
        # 提取各模块数据
        issue_data = data.get("issue", {})
        pr_data = data.get("pr", {})
        repo_stats_data = data.get("repo_stats", {})
        subscribers_data = data.get("subscribers", {})
        languages_data = data.get("languages", {})

        # Issue 摘要
        issue_summary = issue_data.get("summary", {})
        issue_efficiency = issue_data.get("efficiency", {})
        issue_trend = issue_data.get("daily_trend", {})

        # PR 摘要
        pr_summary = pr_data.get("summary", {})
        pr_efficiency = pr_data.get("efficiency", {})
        pr_quality = pr_data.get("quality", {})
        pr_trend = pr_data.get("daily_trend", {})

        # 仓库统计
        download_stats = repo_stats_data.get("download_stats", {})
        fork_stats = repo_stats_data.get("fork_stats", {})

        # 订阅用户
        subscriber_stats = subscribers_data.get("subscriber_stats", {})

        # 编程语言
        language_stats = languages_data.get("language_stats", {})

        # 准备图表数据
        issue_dates = list(issue_trend.keys()) if issue_trend else []
        issue_created = [issue_trend[d]["created"] for d in issue_dates] if issue_trend else []
        issue_closed = [issue_trend[d]["closed"] for d in issue_dates] if issue_trend else []

        pr_dates = list(pr_trend.keys()) if pr_trend else []
        pr_created_counts = [pr_trend[d]["created"] for d in pr_dates] if pr_trend else []
        pr_merged_counts = [pr_trend[d]["merged"] for d in pr_dates] if pr_trend else []

        lang_names = list(language_stats.get("languages", {}).keys())[:10]
        lang_values = list(language_stats.get("languages", {}).values())[:10]
        top_download_days = download_stats.get("top_days", [])
        top_fork_users = fork_stats.get("top_fork_users", [])

        top_download_rows = "".join(
            [
                f"<tr><td>{item.get('date', '-')}</td><td>{item.get('count', 0)}</td><td>{item.get('total', 0):,}</td></tr>"
                for item in top_download_days[:10]
            ]
        )
        top_fork_user_rows = "".join(
            [
                f"<tr><td>{item.get('owner', '-')}</td><td>{item.get('count', 0)}</td><td>{item.get('latest_created_at', '-')[:19]}</td></tr>"
                for item in top_fork_users[:10]
            ]
        )

        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>仓库综合报告 - {data["repo"]}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        h1 {{ text-align: center; color: #1a365d; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #e2e8f0; }}
        .overview {{ background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; border-radius: 12px; padding: 30px; margin-bottom: 25px; }}
        .overview h2 {{ margin-bottom: 20px; font-size: 24px; }}
        .overview-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 20px; }}
        .overview-item {{ text-align: center; }}
        .overview-value {{ font-size: 32px; font-weight: bold; }}
        .overview-label {{ font-size: 13px; opacity: 0.9; margin-top: 5px; }}
        .section {{ background: white; border-radius: 8px; padding: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 25px; }}
        .section-title {{ font-size: 18px; font-weight: bold; color: #1a365d; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: #f8fafc; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #e2e8f0; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #1e40af; }}
        .stat-label {{ color: #64748b; margin-top: 5px; font-size: 13px; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }}
        .chart-box {{ background: #f8fafc; border-radius: 8px; padding: 20px; border: 1px solid #e2e8f0; }}
        .chart-title {{ font-size: 14px; font-weight: bold; color: #1a365d; margin-bottom: 15px; }}
        .footer {{ text-align: center; color: #64748b; padding: 20px; font-size: 12px; }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }}
        @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>仓库综合报告 - {data["repo"]}</h1>

        <!-- 概览 -->
        <div class="overview">
            <h2>概览统计</h2>
            <div class="overview-grid">
                <div class="overview-item">
                    <div class="overview-value">{issue_summary.get("total_issues", 0)}</div>
                    <div class="overview-label">总 Issue 数</div>
                </div>
                <div class="overview-item">
                    <div class="overview-value">{pr_summary.get("total_prs", 0)}</div>
                    <div class="overview-label">总 PR 数</div>
                </div>
                <div class="overview-item">
                    <div class="overview-value">{issue_summary.get("close_rate", 0)}%</div>
                    <div class="overview-label">Issue 关闭率</div>
                </div>
                <div class="overview-item">
                    <div class="overview-value">{pr_summary.get("merge_rate", 0)}%</div>
                    <div class="overview-label">PR 合并率</div>
                </div>
                <div class="overview-item">
                    <div class="overview-value">{subscriber_stats.get("total", 0)}</div>
                    <div class="overview-label">订阅用户</div>
                </div>
                <div class="overview-item">
                    <div class="overview-value">{fork_stats.get("total", 0)}</div>
                    <div class="overview-label">Fork 数</div>
                </div>
            </div>
        </div>

        <!-- Issue 分析 -->
        <div class="section">
            <div class="section-title">Issue 分析</div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{issue_summary.get("total_issues", 0)}</div>
                    <div class="stat-label">总 Issue 数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{issue_summary.get("opened_issues", 0)}</div>
                    <div class="stat-label">未关闭</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{issue_summary.get("closed_issues", 0)}</div>
                    <div class="stat-label">已关闭</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{issue_efficiency.get("avg_first_response_time_minutes", 0):.1f}</div>
                    <div class="stat-label">平均响应(分钟)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{issue_efficiency.get("avg_close_duration_hours", 0):.1f}</div>
                    <div class="stat-label">平均关闭(小时)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{issue_efficiency.get("timely_response_rate", 0)}%</div>
                    <div class="stat-label">24h响应率</div>
                </div>
            </div>
            <div class="charts-grid">
                <div class="chart-box">
                    <div class="chart-title">Issue 每日趋势</div>
                    <canvas id="issueTrendChart"></canvas>
                </div>
            </div>
        </div>

        <!-- PR 分析 -->
        <div class="section">
            <div class="section-title">PR 分析</div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{pr_summary.get("total_prs", 0)}</div>
                    <div class="stat-label">总 PR 数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{pr_summary.get("merged_prs", 0)}</div>
                    <div class="stat-label">已合并</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{pr_summary.get("merge_rate", 0)}%</div>
                    <div class="stat-label">合并率</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{pr_efficiency.get("avg_first_review_time_minutes", 0):.1f}</div>
                    <div class="stat-label">平均评审(分钟)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{pr_efficiency.get("avg_merge_duration_hours", 0):.1f}</div>
                    <div class="stat-label">平均合并(小时)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{pr_quality.get("avg_change_lines", 0):.0f}</div>
                    <div class="stat-label">平均变更行</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{pr_quality.get("ci_success_rate", 0)}%</div>
                    <div class="stat-label">CI成功率</div>
                </div>
            </div>
            <div class="charts-grid">
                <div class="chart-box">
                    <div class="chart-title">PR 每日趋势</div>
                    <canvas id="prTrendChart"></canvas>
                </div>
            </div>
        </div>

        <!-- 仓库统计 & 社区活跃 -->
        <div class="two-col">
            <div class="section">
                <div class="section-title">仓库统计</div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{download_stats.get("period_total", 0)}</div>
                        <div class="stat-label">期间下载量</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{download_stats.get("history_total", 0):,}</div>
                        <div class="stat-label">历史总下载</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{download_stats.get("daily_average", 0):.1f}</div>
                        <div class="stat-label">日均下载</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{fork_stats.get("total", 0)}</div>
                        <div class="stat-label">Fork 总数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{fork_stats.get("new_in_period", 0)}</div>
                        <div class="stat-label">新增 Fork</div>
                    </div>
                </div>
                <div class="chart-box">
                    <div class="chart-title">下载峰值 Top 10</div>
                    <table style="width:100%; border-collapse: collapse; font-size: 13px;">
                        <thead>
                            <tr style="background:#eef2ff;">
                                <th style="padding:8px; border:1px solid #e2e8f0;">日期</th>
                                <th style="padding:8px; border:1px solid #e2e8f0;">当日下载</th>
                                <th style="padding:8px; border:1px solid #e2e8f0;">截止当日累计</th>
                            </tr>
                        </thead>
                        <tbody>{top_download_rows}</tbody>
                    </table>
                </div>
                <div class="chart-box" style="margin-top: 15px;">
                    <div class="chart-title">Fork 人员 Top 10</div>
                    <table style="width:100%; border-collapse: collapse; font-size: 13px;">
                        <thead>
                            <tr style="background:#eef2ff;">
                                <th style="padding:8px; border:1px solid #e2e8f0;">用户</th>
                                <th style="padding:8px; border:1px solid #e2e8f0;">Fork 数</th>
                                <th style="padding:8px; border:1px solid #e2e8f0;">最新 Fork 时间</th>
                            </tr>
                        </thead>
                        <tbody>{top_fork_user_rows}</tbody>
                    </table>
                </div>
            </div>

            <div class="section">
                <div class="section-title">社区活跃</div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{subscriber_stats.get("total", 0)}</div>
                        <div class="stat-label">订阅用户</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{subscriber_stats.get("new_in_period", 0)}</div>
                        <div class="stat-label">新增订阅</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{language_stats.get("total_languages", 0)}</div>
                        <div class="stat-label">语言种类</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{language_stats.get("primary_language", "-")}</div>
                        <div class="stat-label">主要语言</div>
                    </div>
                </div>
                <div class="chart-box" style="margin-top: 15px;">
                    <div class="chart-title">编程语言分布</div>
                    <canvas id="languageChart"></canvas>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>分析时间: {data["analysis_time"]} | 分析周期: {data["analysis_period"]}</p>
        </div>
    </div>

    <script>
    // Issue 趋势图
    new Chart(document.getElementById('issueTrendChart'), {{
        type: 'line',
        data: {{
            labels: {json.dumps(issue_dates)},
            datasets: [
                {{
                    label: '新增',
                    data: {json.dumps(issue_created)},
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true
                }},
                {{
                    label: '关闭',
                    data: {json.dumps(issue_closed)},
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true
                }}
            ]
        }},
        options: {{
            responsive: true,
            scales: {{ y: {{ beginAtZero: true }} }}
        }}
    }});

    // PR 趋势图
    new Chart(document.getElementById('prTrendChart'), {{
        type: 'line',
        data: {{
            labels: {json.dumps(pr_dates)},
            datasets: [
                {{
                    label: '创建',
                    data: {json.dumps(pr_created_counts)},
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true
                }},
                {{
                    label: '合并',
                    data: {json.dumps(pr_merged_counts)},
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true
                }}
            ]
        }},
        options: {{
            responsive: true,
            scales: {{ y: {{ beginAtZero: true }} }}
        }}
    }});

    // 语言分布图
    new Chart(document.getElementById('languageChart'), {{
        type: 'doughnut',
        data: {{
            labels: {json.dumps(lang_names)},
            datasets: [{{
                data: {json.dumps(lang_values)},
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1']
            }}]
        }},
        options: {{
            responsive: true,
            plugins: {{ legend: {{ position: 'right' }} }}
        }}
    }});
    </script>
</body>
</html>
'''

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"已生成 HTML 报告: {output_file}")

    def generate_markdown_report(self, data: Dict, output_file: str):
        """生成 Markdown 综合报告"""
        # 提取各模块数据
        issue_data = data.get("issue", {})
        pr_data = data.get("pr", {})
        repo_stats_data = data.get("repo_stats", {})
        subscribers_data = data.get("subscribers", {})
        languages_data = data.get("languages", {})

        # Issue 摘要
        issue_summary = issue_data.get("summary", {})
        issue_efficiency = issue_data.get("efficiency", {})

        # PR 摘要
        pr_summary = pr_data.get("summary", {})
        pr_efficiency = pr_data.get("efficiency", {})
        pr_quality = pr_data.get("quality", {})

        # 仓库统计
        download_stats = repo_stats_data.get("download_stats", {})
        fork_stats = repo_stats_data.get("fork_stats", {})

        # 订阅用户
        subscriber_stats = subscribers_data.get("subscriber_stats", {})

        # 编程语言
        language_stats = languages_data.get("language_stats", {})

        md_content = f'''# 仓库综合报告 - {data["repo"]}

> 分析时间: {data["analysis_time"]} | 分析周期: {data["analysis_period"]}

## 概览统计

| 指标 | 数值 |
|------|------|
| 总 Issue 数 | {issue_summary.get("total_issues", 0)} |
| 总 PR 数 | {pr_summary.get("total_prs", 0)} |
| Issue 关闭率 | {issue_summary.get("close_rate", 0)}% |
| PR 合并率 | {pr_summary.get("merge_rate", 0)}% |
| 订阅用户数 | {subscriber_stats.get("total", 0)} |
| Fork 数 | {fork_stats.get("total", 0)} |

## Issue 分析

### 效率指标

| 指标 | 数值 |
|------|------|
| 总 Issue 数 | {issue_summary.get("total_issues", 0)} |
| 未关闭 | {issue_summary.get("opened_issues", 0)} |
| 已关闭 | {issue_summary.get("closed_issues", 0)} |
| 关闭率 | {issue_summary.get("close_rate", 0)}% |
| 平均首次响应时间 | {issue_efficiency.get("avg_first_response_time_minutes", 0):.1f} 分钟 |
| 平均关闭耗时 | {issue_efficiency.get("avg_close_duration_hours", 0):.1f} 小时 |
| 24小时响应率 | {issue_efficiency.get("timely_response_rate", 0)}% |

## PR 分析

### 效率指标

| 指标 | 数值 |
|------|------|
| 总 PR 数 | {pr_summary.get("total_prs", 0)} |
| 已合并 | {pr_summary.get("merged_prs", 0)} |
| 合并率 | {pr_summary.get("merge_rate", 0)}% |
| 平均首次评审时间 | {pr_efficiency.get("avg_first_review_time_minutes", 0):.1f} 分钟 |
| 平均合并耗时 | {pr_efficiency.get("avg_merge_duration_hours", 0):.1f} 小时 |

### 质量指标

| 指标 | 数值 |
|------|------|
| 平均变更行数 | {pr_quality.get("avg_change_lines", 0):.0f} |
| 大 PR 数 (>500行) | {pr_quality.get("large_pr_count", 0)} |
| CI 成功率 | {pr_quality.get("ci_success_rate", 0)}% |

## 仓库统计

### 下载统计

| 指标 | 数值 |
|------|------|
| 期间下载量 | {download_stats.get("period_total", 0)} |
| 历史总下载 | {download_stats.get("history_total", 0):,} |
| 日均下载 | {download_stats.get("daily_average", 0):.1f} |
| 活跃下载天数 | {download_stats.get("active_days", 0)} |
| 活跃下载占比 | {download_stats.get("active_days_rate", 0)}% |

### Fork 统计

| 指标 | 数值 |
|------|------|
| Fork 总数 | {fork_stats.get("total", 0)} |
| 近 {self.days} 天新增 Fork | {fork_stats.get("new_in_period", 0)} |
| Fork 人员数 | {fork_stats.get("unique_fork_owners", 0)} |

#### 下载峰值 Top 10

| 日期 | 当日下载 | 截止当日累计 |
|------|----------|--------------|
'''
        for item in download_stats.get("top_days", [])[:10]:
            md_content += f"| {item.get('date', '-')} | {item.get('count', 0)} | {item.get('total', 0):,} |\n"

        md_content += f'''
#### Fork 人员 Top 10

| 用户 | Fork 数 | 最新 Fork 时间 |
|------|--------|----------------|
'''
        for item in fork_stats.get("top_fork_users", [])[:10]:
            md_content += f"| {item.get('owner', '-')} | {item.get('count', 0)} | {item.get('latest_created_at', '-')[:19]} |\n"

        md_content += f'''
## 社区活跃

### 订阅用户

| 指标 | 数值 |
|------|------|
| 订阅用户总数 | {subscriber_stats.get("total", 0)} |
| 近 {self.days} 天新增订阅 | {subscriber_stats.get("new_in_period", 0)} |

### 编程语言

| 指标 | 数值 |
|------|------|
| 语言种类数 | {language_stats.get("total_languages", 0)} |
| 主要语言 | {language_stats.get("primary_language", "-")} |

#### 语言占比

'''
        # 添加语言占比
        languages = language_stats.get("languages", {})
        for lang, percent in list(languages.items())[:10]:
            md_content += f"- {lang}: {percent}%\n"

        md_content += f'''
---

*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"已生成 Markdown 报告: {output_file}")

    def save_to_json(self, data: Dict) -> str:
        """保存整合的 JSON 数据"""
        filename = os.path.join(
            self.output_dir,
            f"report_{self.owner}_{self.repo}_{self.days}d.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filename

    def run(self) -> Dict:
        """执行完整流程"""
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"仓库综合报告: {self.owner}/{self.repo}")
        print(f"分析周期: 近 {self.days} 天")
        print(f"{'='*60}\n")

        # 1. 采集所有数据
        data = self.collect_all_data()

        # 2. 保存 JSON 数据
        json_file = self.save_to_json(data)

        # 3. 生成 HTML 报告
        html_file = os.path.join(self.output_dir, f"report_{self.owner}_{self.repo}_{self.days}d.html")
        self.generate_html_report(data, html_file)

        # 4. 生成 Markdown 报告
        md_file = os.path.join(self.output_dir, f"report_{self.owner}_{self.repo}_{self.days}d.md")
        self.generate_markdown_report(data, md_file)

        # 5. 打印摘要
        print(f"\n{'='*60}")
        print(f"综合报告生成完成!")
        print(f"{'='*60}")
        print(f"- JSON 数据: {json_file}")
        print(f"- HTML 报告: {html_file}")
        print(f"- Markdown 报告: {md_file}")
        print(f"{'='*60}\n")

        return data

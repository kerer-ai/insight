# -*- coding: utf-8 -*-
"""
GitCode Issue 洞察模块
分析指定仓库近 N 天的 Issue 情况
"""

import json
import time
import csv
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import requests

from .utils import request_with_retry


class GitCodeIssueInsight:
    """GitCode Issue 洞察分析器"""

    def __init__(self, repo: str, token: str, owner: str = None, days: int = 30, range_by: str = "created", output_dir: str = None):
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
        self.range_by = range_by or "created"
        self.base_url = "https://api.gitcode.com/api/v5"

        # 设置输出目录
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "output")
        self.output_dir = output_dir

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # 计算时间范围
        self.since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    def _get_default_owner(self) -> str:
        """从配置文件获取默认 owner"""
        config_file = os.path.join(os.getcwd(), "config", "gitcode.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("owner", "")
        return ""

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        except Exception:
            return None

    def get_issues(self) -> List[Dict]:
        """获取 Issue 列表"""
        print(f"获取 {self.owner}/{self.repo} 近 {self.days} 天的 Issue 列表...")

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        all_issues = []
        page = 1
        max_pages = 50
        sort_field = "created" if self.range_by == "created" else "updated"

        while page <= max_pages:
            params = {
                "access_token": self.token,
                "state": "all",
                "since": self.since_date,
                "per_page": 100,
                "page": page,
                "sort": sort_field,
                "direction": "desc"
            }

            data = request_with_retry(self.session, url, params)
            if data is None:
                break

            if not isinstance(data, list) or len(data) == 0:
                break

            filtered = [issue for issue in data if self._is_issue_in_range(issue)]

            all_issues.extend(filtered)
            print(f"  第 {page} 页获取到 {len(filtered)} 条 Issue")

            if self._should_stop_paging(data):
                break

            if len(data) < 100:
                break

            page += 1

        all_issues.sort(key=self._sort_key, reverse=True)
        print(f"共获取到 {len(all_issues)} 条 Issue")
        return all_issues

    def _should_stop_paging(self, data: List[Dict]) -> bool:
        if not data:
            return True
        tail = data[-1]
        since = self._parse_datetime(self.since_date)
        if since is None:
            return False

        if self.range_by == "created":
            tail_dt = self._parse_datetime(tail.get("created_at"))
        else:
            tail_dt = self._parse_datetime(tail.get("updated_at"))

        if tail_dt is None:
            return False
        return tail_dt < since

    def _is_issue_in_range(self, issue: Dict) -> bool:
        if not isinstance(issue, dict):
            return False
        created_at = issue.get("created_at", "")
        updated_at = issue.get("updated_at", "")

        if self.range_by == "created":
            return self._is_within_range(created_at)
        if self.range_by == "updated":
            return self._is_within_range(updated_at)
        return self._is_within_range(created_at) or self._is_within_range(updated_at)

    def _sort_key(self, issue: Dict):
        if not isinstance(issue, dict):
            return datetime.min.replace(tzinfo=timezone.utc)
        created_dt = self._parse_datetime(issue.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)
        updated_dt = self._parse_datetime(issue.get("updated_at")) or created_dt

        if self.range_by == "created":
            return created_dt
        if self.range_by == "updated":
            return updated_dt
        return updated_dt if updated_dt >= created_dt else created_dt

    def _is_within_range(self, date_str: str) -> bool:
        """检查日期是否在统计范围内"""
        if not date_str:
            return False
        try:
            issue_date = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            since = datetime.fromisoformat(str(self.since_date).replace("Z", "+00:00"))
            return issue_date >= since
        except:
            return False

    def get_issue_events(self, issue_number: str) -> List[Dict]:
        """获取 Issue 事件列表"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}/events"
        params = {"access_token": self.token}
        data = request_with_retry(self.session, url, params)
        return data if isinstance(data, list) else []

    def get_issue_comments(self, issue_number: str) -> List[Dict]:
        """获取 Issue 评论列表"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments"
        params = {"access_token": self.token}
        data = request_with_retry(self.session, url, params)
        return data if isinstance(data, list) else []

    def analyze_issue(self, issue: Dict) -> Dict:
        """分析单个 Issue，计算响应时间等指标"""
        issue_number = issue.get("number", "")
        created_at_str = issue.get("created_at", "")

        # 获取评论
        comments = self.get_issue_comments(issue_number)

        # 计算首次响应时间
        first_response_time = None
        if comments:
            creator_id = issue.get("user", {}).get("id")
            for comment in comments:
                commenter_id = comment.get("user", {}).get("id")
                if commenter_id != creator_id:
                    comment_time = datetime.fromisoformat(comment.get("created_at", "").replace("Z", "+00:00"))
                    created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    first_response_time = (comment_time - created_time).total_seconds() / 60
                    break

        # 计算关闭耗时
        close_duration = None
        closed_at = issue.get("closed_at")
        if closed_at and created_at_str:
            try:
                closed_time = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                close_duration = (closed_time - created_time).total_seconds() / 60
            except:
                pass

        # 提取指派人
        assignees = [a.get("login", "") for a in issue.get("assignees", [])]
        if not assignees and issue.get("assignee"):
            assignees = [issue.get("assignee", {}).get("login", "")]

        # 提取标签
        labels = [l.get("name", "") for l in issue.get("labels", [])]

        return {
            "issue_number": issue_number,
            "title": issue.get("title", ""),
            "state": issue.get("state", ""),
            "created_at": created_at_str,
            "updated_at": issue.get("updated_at", ""),
            "closed_at": closed_at or "",
            "creator": issue.get("user", {}).get("login", ""),
            "labels": ",".join(labels),
            "comments_count": issue.get("comments", 0),
            "assignees": ",".join(assignees),
            "milestone": issue.get("milestone", {}).get("title", "") if issue.get("milestone") else "",
            "html_url": issue.get("html_url", ""),
            "first_response_time": round(first_response_time, 2) if first_response_time else None,
            "close_duration": round(close_duration, 2) if close_duration else None
        }

    def save_to_csv(self, issues_data: List[Dict], filename: str):
        """保存到 CSV 文件"""
        if not issues_data:
            print("没有数据可保存")
            return

        fieldnames = [
            "issue_number", "title", "state", "created_at", "updated_at",
            "closed_at", "creator", "labels", "comments_count", "assignees",
            "milestone", "html_url", "first_response_time", "close_duration"
        ]

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(issues_data)

        print(f"已保存到: {filename}")

    def calculate_insights(self, issues_data: List[Dict]) -> Dict:
        """计算洞察指标"""
        total = len(issues_data)
        opened = [i for i in issues_data if i["state"] == "opened"]
        closed = [i for i in issues_data if i["state"] == "closed"]

        # 新增 Issue
        new_issues = [i for i in issues_data if self._is_within_range(i["created_at"])]

        # 响应时间统计
        response_times = [i["first_response_time"] for i in issues_data if i["first_response_time"]]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # 关闭耗时统计
        close_durations = [i["close_duration"] for i in issues_data if i["close_duration"]]
        avg_close_duration = sum(close_durations) / len(close_durations) if close_durations else 0

        # 标签分布
        label_dist = {}
        for issue in issues_data:
            for label in issue["labels"].split(","):
                if label:
                    label_dist[label] = label_dist.get(label, 0) + 1

        # 创建人分布
        creator_dist = {}
        for issue in issues_data:
            creator = issue["creator"]
            if creator:
                creator_dist[creator] = creator_dist.get(creator, 0) + 1

        # 每日趋势
        daily_trend = {}
        for issue in issues_data:
            try:
                created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                date_str = created.strftime("%Y-%m-%d")
                if date_str not in daily_trend:
                    daily_trend[date_str] = {"created": 0, "closed": 0}
                daily_trend[date_str]["created"] += 1
            except:
                pass

        for issue in closed:
            try:
                closed_date = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
                date_str = closed_date.strftime("%Y-%m-%d")
                if date_str in daily_trend:
                    daily_trend[date_str]["closed"] += 1
            except:
                pass

        # 响应及时率
        timely_response = len([t for t in response_times if t <= 1440])
        timely_response_rate = timely_response / len(response_times) * 100 if response_times else 0

        return {
            "repo": f"{self.owner}/{self.repo}",
            "analysis_period": f"近 {self.days} 天",
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_issues": total,
                "opened_issues": len(opened),
                "closed_issues": len(closed),
                "new_issues": len(new_issues),
                "close_rate": round(len(closed) / total * 100, 2) if total > 0 else 0
            },
            "efficiency": {
                "avg_first_response_time_minutes": round(avg_response_time, 2),
                "avg_close_duration_hours": round(avg_close_duration / 60, 2),
                "timely_response_rate": round(timely_response_rate, 2),
                "response_time_samples": len(response_times),
                "close_duration_samples": len(close_durations)
            },
            "distribution": {
                "by_label": dict(sorted(label_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
                "by_creator": dict(sorted(creator_dist.items(), key=lambda x: x[1], reverse=True)[:10])
            },
            "daily_trend": dict(sorted(daily_trend.items())),
            "issues": issues_data
        }

    def generate_html_report(self, insights: Dict, output_file: str):
        """生成 HTML 报告"""
        summary = insights["summary"]
        efficiency = insights["efficiency"]
        distribution = insights["distribution"]
        daily_trend = insights["daily_trend"]

        # 准备图表数据
        dates = list(daily_trend.keys())
        created_counts = [daily_trend[d]["created"] for d in dates]
        closed_counts = [daily_trend[d]["closed"] for d in dates]

        label_names = list(distribution["by_label"].keys())
        label_counts = list(distribution["by_label"].values())

        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Issue 洞察报告 - {insights["repo"]}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ text-align: center; color: #1a365d; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #e2e8f0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #1e40af; }}
        .stat-label {{ color: #64748b; margin-top: 5px; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .chart-box {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .chart-title {{ font-size: 16px; font-weight: bold; color: #1a365d; margin-bottom: 15px; }}
        .table-section {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th, td {{ padding: 10px 8px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; font-weight: 600; }}
        tr:hover {{ background: #f8fafc; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
        .badge-opened {{ background: #dcfce7; color: #166534; }}
        .badge-closed {{ background: #fee2e2; color: #991b1b; }}
        .footer {{ text-align: center; color: #64748b; padding: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Issue 洞察报告 - {insights["repo"]}</h1>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary["total_issues"]}</div>
                <div class="stat-label">总 Issue 数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["new_issues"]}</div>
                <div class="stat-label">新增 Issue</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["opened_issues"]}</div>
                <div class="stat-label">未关闭</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["closed_issues"]}</div>
                <div class="stat-label">已关闭</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["close_rate"]}%</div>
                <div class="stat-label">关闭率</div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{efficiency["avg_first_response_time_minutes"]:.1f}</div>
                <div class="stat-label">平均首次响应(分钟)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{efficiency["avg_close_duration_hours"]:.1f}</div>
                <div class="stat-label">平均关闭耗时(小时)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{efficiency["timely_response_rate"]}%</div>
                <div class="stat-label">24h响应率</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-box">
                <div class="chart-title">每日 Issue 趋势</div>
                <canvas id="trendChart"></canvas>
            </div>
            <div class="chart-box">
                <div class="chart-title">标签分布 Top 10</div>
                <canvas id="labelChart"></canvas>
            </div>
        </div>

        <div class="table-section">
            <h3 style="margin-bottom: 15px; color: #1a365d;">Issue 列表</h3>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>标题</th>
                        <th>状态</th>
                        <th>创建人</th>
                        <th>创建时间</th>
                        <th>标签</th>
                        <th>评论</th>
                        <th>首次响应(分钟)</th>
                        <th>关闭耗时(小时)</th>
                    </tr>
                </thead>
                <tbody>
'''

        # 添加 Issue 行
        for issue in insights["issues"][:100]:
            state_class = "badge-opened" if issue["state"] == "opened" else "badge-closed"
            response_time = f"{issue['first_response_time']:.1f}" if issue["first_response_time"] else "-"
            close_hours = f"{issue['close_duration']/60:.1f}" if issue["close_duration"] else "-"

            html_content += f'''
                    <tr>
                        <td><a href="{issue['html_url']}" target="_blank">{issue['issue_number']}</a></td>
                        <td>{issue['title'][:50]}{'...' if len(issue['title']) > 50 else ''}</td>
                        <td><span class="badge {state_class}">{issue['state']}</span></td>
                        <td>{issue['creator']}</td>
                        <td>{issue['created_at'][:10] if issue['created_at'] else '-'}</td>
                        <td>{issue['labels'][:30]}{'...' if len(issue['labels']) > 30 else ''}</td>
                        <td>{issue['comments_count']}</td>
                        <td>{response_time}</td>
                        <td>{close_hours}</td>
                    </tr>
'''

        html_content += f'''
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>分析时间: {insights["analysis_time"]} | 分析周期: {insights["analysis_period"]}</p>
        </div>
    </div>

    <script>
    // 趋势图
    new Chart(document.getElementById('trendChart'), {{
        type: 'line',
        data: {{
            labels: {json.dumps(dates)},
            datasets: [
                {{
                    label: '新增',
                    data: {json.dumps(created_counts)},
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true
                }},
                {{
                    label: '关闭',
                    data: {json.dumps(closed_counts)},
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

    // 标签分布图
    new Chart(document.getElementById('labelChart'), {{
        type: 'bar',
        data: {{
            labels: {json.dumps(label_names)},
            datasets: [{{
                label: 'Issue 数量',
                data: {json.dumps(label_counts)},
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1']
            }}]
        }},
        options: {{
            responsive: true,
            indexAxis: 'y',
            scales: {{ x: {{ beginAtZero: true }} }}
        }}
    }});
    </script>
</body>
</html>
'''

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"已生成 HTML 报告: {output_file}")

    def run(self) -> Dict:
        """执行完整的分析流程"""
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Issue 洞察分析: {self.owner}/{self.repo}")
        print(f"分析周期: 近 {self.days} 天")
        print(f"{'='*60}\n")

        # 获取 Issue 列表
        issues = self.get_issues()

        if not issues:
            print("未获取到任何 Issue 数据")
            return {}

        # 分析每个 Issue
        print(f"\n分析 Issue 详情...")
        issues_data = []
        for i, issue in enumerate(issues, 1):
            print(f"  处理 {i}/{len(issues)}: Issue #{issue.get('number')}")
            analyzed = self.analyze_issue(issue)
            issues_data.append(analyzed)

        # 保存中间数据 CSV
        csv_file = os.path.join(self.output_dir, f"issues_{self.repo}_{self.days}d.csv")
        self.save_to_csv(issues_data, csv_file)

        # 计算洞察指标
        print(f"\n计算洞察指标...")
        insights = self.calculate_insights(issues_data)

        # 保存洞察结果 JSON
        json_file = os.path.join(self.output_dir, f"issue_insight_{self.repo}_{self.days}d.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
        print(f"已保存洞察结果: {json_file}")

        # 生成 HTML 报告
        html_file = os.path.join(self.output_dir, f"issue_insight_{self.repo}_{self.days}d.html")
        self.generate_html_report(insights, html_file)

        # 打印摘要
        print(f"\n{'='*60}")
        print(f"分析完成!")
        print(f"{'='*60}")
        print(f"总 Issue 数: {insights['summary']['total_issues']}")
        print(f"新增 Issue: {insights['summary']['new_issues']}")
        print(f"已关闭: {insights['summary']['closed_issues']}")
        print(f"关闭率: {insights['summary']['close_rate']}%")
        print(f"平均首次响应: {insights['efficiency']['avg_first_response_time_minutes']:.1f} 分钟")
        print(f"平均关闭耗时: {insights['efficiency']['avg_close_duration_hours']:.1f} 小时")
        print(f"{'='*60}\n")

        return insights

# -*- coding: utf-8 -*-
"""
GitCode Issue 洞察模块
分析指定仓库近 N 天的 Issue 情况
"""

import json
import time
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
        # GitCode API 返回 finished_at 而非 closed_at
        close_duration = None
        finished_at = issue.get("finished_at") or issue.get("closed_at")
        if finished_at and created_at_str:
            try:
                finished_time = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
                created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                close_duration = (finished_time - created_time).total_seconds() / 60
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
            "finished_at": finished_at or "",
            "creator": issue.get("user", {}).get("login", ""),
            "labels": ",".join(labels),
            "comments_count": issue.get("comments", 0),
            "assignees": ",".join(assignees),
            "milestone": issue.get("milestone", {}).get("title", "") if issue.get("milestone") else "",
            "html_url": issue.get("html_url", ""),
            "first_response_time": round(first_response_time, 2) if first_response_time else None,
            "close_duration": round(close_duration, 2) if close_duration else None
        }

    def calculate_insights(self, issues_data: List[Dict]) -> Dict:
        """计算洞察指标"""
        total = len(issues_data)
        opened = [i for i in issues_data if i["state"] == "open"]
        closed = [i for i in issues_data if i["state"] == "closed"]

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
                finished_date = datetime.fromisoformat(issue["finished_at"].replace("Z", "+00:00"))
                date_str = finished_date.strftime("%Y-%m-%d")
                if date_str not in daily_trend:
                    daily_trend[date_str] = {"created": 0, "closed": 0}
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
            "daily_trend": dict(sorted(daily_trend.items()))
        }, issues_data

    def generate_html_report(self, insights: Dict, output_file: str):
        """生成 HTML 报告（统计数据总结）"""
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

        # 创建人分布
        creator_names = list(distribution["by_creator"].keys())[:10]
        creator_counts = list(distribution["by_creator"].values())[:10]

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
        h2 {{ color: #1a365d; margin: 20px 0 15px 0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #1e40af; }}
        .stat-label {{ color: #64748b; margin-top: 5px; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .chart-box {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .chart-title {{ font-size: 16px; font-weight: bold; color: #1a365d; margin-bottom: 15px; }}
        .dist-section {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .dist-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
        .dist-item:last-child {{ border-bottom: none; }}
        .footer {{ text-align: center; color: #64748b; padding: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Issue 洞察报告 - {insights["repo"]}</h1>

        <h2>统计概览</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary["total_issues"]}</div>
                <div class="stat-label">总 Issue 数</div>
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

        <h2>效率指标</h2>
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

        <h2>趋势图表</h2>
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

        <h2>分布统计</h2>
        <div class="charts-grid">
            <div class="dist-section">
                <div class="chart-title">标签分布 Top 10</div>
'''
        for label, count in distribution["by_label"].items():
            html_content += f'''                <div class="dist-item"><span>{label}</span><span>{count}</span></div>\n'''

        html_content += f'''            </div>
            <div class="dist-section">
                <div class="chart-title">创建人分布 Top 10</div>
'''
        for creator, count in distribution["by_creator"].items():
            html_content += f'''                <div class="dist-item"><span>{creator}</span><span>{count}</span></div>\n'''

        html_content += f'''            </div>
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

        print(f"HTML 报告: {output_file}")

    def generate_markdown_report(self, insights: Dict, output_file: str):
        """生成 Markdown 报告（统计数据总结）"""
        summary = insights["summary"]
        efficiency = insights["efficiency"]
        distribution = insights["distribution"]
        daily_trend = insights["daily_trend"]

        md_content = f'''# Issue 洞察报告 - {insights["repo"]}

> 分析时间: {insights["analysis_time"]} | 分析周期: {insights["analysis_period"]}

## 统计概览

| 指标 | 数值 |
|------|------|
| 总 Issue 数 | {summary["total_issues"]} |
| 未关闭 | {summary["opened_issues"]} |
| 已关闭 | {summary["closed_issues"]} |
| 关闭率 | {summary["close_rate"]}% |

## 效率指标

| 指标 | 数值 |
|------|------|
| 平均首次响应 | {efficiency["avg_first_response_time_minutes"]:.1f} 分钟 |
| 平均关闭耗时 | {efficiency["avg_close_duration_hours"]:.1f} 小时 |
| 24h响应率 | {efficiency["timely_response_rate"]}% |
| 响应时间样本数 | {efficiency["response_time_samples"]} |
| 关闭耗时样本数 | {efficiency["close_duration_samples"]} |

## 每日趋势

| 日期 | 新增 | 关闭 |
|------|------|------|
'''
        for date, counts in sorted(daily_trend.items()):
            md_content += f"| {date} | {counts['created']} | {counts['closed']} |\n"

        md_content += '''
## 标签分布 Top 10

| 标签 | 数量 |
|------|------|
'''
        for label, count in distribution["by_label"].items():
            md_content += f"| {label} | {count} |\n"

        md_content += '''
## 创建人分布 Top 10

| 创建人 | 数量 |
|------|------|
'''
        for creator, count in distribution["by_creator"].items():
            md_content += f"| {creator} | {count} |\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"Markdown 报告: {output_file}")

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

        # 计算洞察指标
        print(f"\n计算洞察指标...")
        insights, raw_data = self.calculate_insights(issues_data)

        # 保存 JSON（统计数据 + 原始数据）
        json_file = os.path.join(self.output_dir, f"issue_insight_{self.repo}_{self.days}d.json")
        full_data = {
            "statistics": insights,
            "raw_data": raw_data
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        # 生成 HTML 报告
        html_file = os.path.join(self.output_dir, f"issue_insight_{self.repo}_{self.days}d.html")
        self.generate_html_report(insights, html_file)

        # 生成 Markdown 报告
        md_file = os.path.join(self.output_dir, f"issue_insight_{self.repo}_{self.days}d.md")
        self.generate_markdown_report(insights, md_file)

        # 打印摘要
        print(f"\n{'='*60}")
        print(f"分析完成!")
        print(f"{'='*60}")
        print(f"总 Issue 数: {insights['summary']['total_issues']}")
        print(f"未关闭: {insights['summary']['opened_issues']}")
        print(f"已关闭: {insights['summary']['closed_issues']}")
        print(f"关闭率: {insights['summary']['close_rate']}%")
        print(f"平均首次响应: {insights['efficiency']['avg_first_response_time_minutes']:.1f} 分钟")
        print(f"平均关闭耗时: {insights['efficiency']['avg_close_duration_hours']:.1f} 小时")
        print(f"\n输出文件:")
        print(f"- JSON 数据: {json_file}")
        print(f"- HTML 报告: {html_file}")
        print(f"- Markdown 报告: {md_file}")
        print(f"{'='*60}\n")

        return full_data

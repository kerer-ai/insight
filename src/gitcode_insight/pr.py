# -*- coding: utf-8 -*-
"""
GitCode PR 洞察模块
分析指定仓库近 N 天的 PR 情况
"""

import json
import time
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import requests

from .utils import request_with_retry


class GitCodePRInsight:
    """GitCode PR 洞察分析器"""

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

    def get_prs(self) -> List[Dict]:
        """获取 PR 列表"""
        print(f"获取 {self.owner}/{self.repo} 近 {self.days} 天的 PR 列表...")

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls"
        all_prs = []
        page = 1
        max_pages = 50

        while page <= max_pages:
            params = {
                "access_token": self.token,
                "state": "all",
                "per_page": 100,
                "page": page,
                "sort": "created",
                "direction": "desc"
            }

            data = request_with_retry(self.session, url, params)
            if data is None:
                break

            if not isinstance(data, list) or len(data) == 0:
                break

            # 过滤在时间范围内的 PR
            filtered = [
                pr for pr in data
                if self._is_within_range(pr.get("created_at", ""))
                or self._is_within_range(pr.get("updated_at", ""))
            ]

            all_prs.extend(filtered)
            print(f"  第 {page} 页获取到 {len(filtered)} 条 PR")

            if len(data) < 100:
                break

            page += 1
            time.sleep(0.6)  # API 限流控制

        print(f"共获取到 {len(all_prs)} 条 PR")
        return all_prs

    def _is_within_range(self, date_str: str) -> bool:
        """检查日期是否在统计范围内"""
        if not date_str:
            return False
        try:
            pr_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            since = datetime.fromisoformat(self.since_date.replace("Z", "+00:00"))
            return pr_date >= since
        except:
            return False

    def get_pr_comments(self, pr_number: int) -> List[Dict]:
        """获取 PR 评论列表"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}/comments"
        params = {"access_token": self.token, "per_page": 100}
        data = request_with_retry(self.session, url, params)
        return data if isinstance(data, list) else []

    def analyze_pr(self, pr: Dict) -> Dict:
        """分析单个 PR，计算各项指标"""
        pr_number = pr.get("number", "")
        created_at_str = pr.get("created_at", "")
        merged_at = pr.get("merged_at")
        closed_at = pr.get("closed_at")

        # 获取评论计算首次评审时间
        comments = self.get_pr_comments(pr_number)

        first_review_time = None
        if comments:
            creator_id = pr.get("user", {}).get("id")
            for comment in comments:
                commenter_id = comment.get("user", {}).get("id")
                if commenter_id != creator_id:
                    try:
                        comment_time = datetime.fromisoformat(comment.get("created_at", "").replace("Z", "+00:00"))
                        created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        first_review_time = (comment_time - created_time).total_seconds() / 60
                    except:
                        pass
                    break

        # 计算合并耗时
        merge_duration = None
        if merged_at and created_at_str:
            try:
                merged_time = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                merge_duration = (merged_time - created_time).total_seconds() / 60
            except:
                pass

        # 计算关闭耗时（未合并的 PR）
        close_duration = None
        if closed_at and not merged_at and created_at_str:
            try:
                closed_time = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                close_duration = (closed_time - created_time).total_seconds() / 60
            except:
                pass

        # 计算打开天数
        open_days = None
        if pr.get("state") == "open":
            try:
                created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                open_days = (datetime.now(timezone.utc) - created_time).total_seconds() / 86400
            except:
                pass

        # 代码变更行数
        added_lines = pr.get("added_lines", 0) or 0
        removed_lines = pr.get("removed_lines", 0) or 0
        total_changes = added_lines + removed_lines

        # 提取评审者
        assignees = [a.get("login", "") for a in pr.get("assignees", [])]
        testers = [t.get("login", "") for t in pr.get("testers", [])]

        # 提取标签
        labels = [l.get("name", "") for l in pr.get("labels", [])]

        # 合并者
        merged_by = pr.get("merged_by", {})
        merged_by_login = merged_by.get("login", "") if merged_by else ""

        return {
            "pr_number": pr_number,
            "title": pr.get("title", ""),
            "state": pr.get("state", ""),
            "draft": pr.get("draft", False),
            "locked": pr.get("locked", False),
            "created_at": created_at_str,
            "updated_at": pr.get("updated_at", ""),
            "merged_at": merged_at or "",
            "closed_at": closed_at or "",
            "creator": pr.get("user", {}).get("login", ""),
            "source_branch": pr.get("source_branch", ""),
            "target_branch": pr.get("target_branch", ""),
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "total_changes": total_changes,
            "notes_count": pr.get("notes", 0) or 0,
            "labels": ",".join(labels),
            "assignees": ",".join(assignees),
            "testers": ",".join(testers),
            "merged_by": merged_by_login,
            "mergeable": pr.get("mergeable"),
            "pipeline_status": pr.get("pipeline_status", ""),
            "html_url": pr.get("html_url", ""),
            "first_review_time": round(first_review_time, 2) if first_review_time else None,
            "merge_duration": round(merge_duration, 2) if merge_duration else None,
            "close_duration": round(close_duration, 2) if close_duration else None,
            "open_days": round(open_days, 2) if open_days else None
        }

    def calculate_insights(self, prs_data: List[Dict]) -> tuple:
        """计算洞察指标"""
        total = len(prs_data)

        # 状态分布
        opened = [p for p in prs_data if p["state"] == "open"]
        merged = [p for p in prs_data if p["merged_at"]]
        closed_not_merged = [p for p in prs_data if p["state"] == "closed" and not p["merged_at"]]

        # 草稿 PR
        drafts = [p for p in prs_data if p["draft"]]

        # 冲突 PR
        conflicts = [p for p in prs_data if p["mergeable"] is False]

        # 代码变更统计
        change_sizes = [p["total_changes"] for p in prs_data if p["total_changes"] > 0]
        avg_changes = sum(change_sizes) / len(change_sizes) if change_sizes else 0
        large_prs = [p for p in prs_data if p["total_changes"] > 500]

        # 评论密度
        total_notes = sum(p["notes_count"] for p in prs_data)
        total_lines = sum(p["total_changes"] for p in prs_data)
        comment_density = total_notes / total_lines if total_lines > 0 else 0

        # 评审时间统计
        review_times = [p["first_review_time"] for p in prs_data if p["first_review_time"]]
        avg_review_time = sum(review_times) / len(review_times) if review_times else 0

        # 合并耗时统计
        merge_durations = [p["merge_duration"] for p in prs_data if p["merge_duration"]]
        avg_merge_duration = sum(merge_durations) / len(merge_durations) if merge_durations else 0

        # 打开天数统计
        open_days_list = [p["open_days"] for p in prs_data if p["open_days"]]
        avg_open_days = sum(open_days_list) / len(open_days_list) if open_days_list else 0

        # 创建者分布
        creator_dist = {}
        for pr in prs_data:
            creator = pr["creator"]
            if creator:
                creator_dist[creator] = creator_dist.get(creator, 0) + 1

        # 目标分支分布
        branch_dist = {}
        for pr in prs_data:
            branch = pr["target_branch"]
            if branch:
                branch_dist[branch] = branch_dist.get(branch, 0) + 1

        # 标签分布
        label_dist = {}
        for pr in prs_data:
            for label in pr["labels"].split(","):
                if label:
                    label_dist[label] = label_dist.get(label, 0) + 1

        # 评审者分布
        reviewer_dist = {}
        for pr in prs_data:
            for assignee in pr["assignees"].split(","):
                if assignee:
                    reviewer_dist[assignee] = reviewer_dist.get(assignee, 0) + 1

        # 合并者分布
        merger_dist = {}
        for pr in prs_data:
            merger = pr["merged_by"]
            if merger:
                merger_dist[merger] = merger_dist.get(merger, 0) + 1

        # CI 状态统计
        ci_success = [p for p in prs_data if p["pipeline_status"] == "success"]
        ci_stats = {}
        for pr in prs_data:
            status = pr["pipeline_status"] or "unknown"
            ci_stats[status] = ci_stats.get(status, 0) + 1

        # 每日趋势
        daily_trend = {}
        for pr in prs_data:
            try:
                created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                date_str = created.strftime("%Y-%m-%d")
                if date_str not in daily_trend:
                    daily_trend[date_str] = {"created": 0, "merged": 0, "closed": 0}
                daily_trend[date_str]["created"] += 1
            except:
                pass

        for pr in merged:
            try:
                merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                date_str = merged_date.strftime("%Y-%m-%d")
                if date_str not in daily_trend:
                    daily_trend[date_str] = {"created": 0, "merged": 0, "closed": 0}
                daily_trend[date_str]["merged"] += 1
            except:
                pass

        for pr in closed_not_merged:
            try:
                closed_date = datetime.fromisoformat(pr["closed_at"].replace("Z", "+00:00"))
                date_str = closed_date.strftime("%Y-%m-%d")
                if date_str not in daily_trend:
                    daily_trend[date_str] = {"created": 0, "merged": 0, "closed": 0}
                daily_trend[date_str]["closed"] += 1
            except:
                pass

        # 24小时内评审率
        timely_reviews = len([t for t in review_times if t <= 1440])
        timely_review_rate = timely_reviews / len(review_times) * 100 if review_times else 0

        return {
            "repo": f"{self.owner}/{self.repo}",
            "analysis_period": f"近 {self.days} 天",
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_prs": total,
                "opened_prs": len(opened),
                "merged_prs": len(merged),
                "closed_prs": len(closed_not_merged),
                "draft_prs": len(drafts),
                "merge_rate": round(len(merged) / total * 100, 2) if total > 0 else 0,
                "draft_rate": round(len(drafts) / total * 100, 2) if total > 0 else 0,
                "conflict_rate": round(len(conflicts) / total * 100, 2) if total > 0 else 0
            },
            "efficiency": {
                "avg_first_review_time_minutes": round(avg_review_time, 2),
                "avg_merge_duration_hours": round(avg_merge_duration / 60, 2),
                "avg_open_days": round(avg_open_days, 2),
                "timely_review_rate": round(timely_review_rate, 2),
                "review_time_samples": len(review_times),
                "merge_duration_samples": len(merge_durations)
            },
            "quality": {
                "avg_change_lines": round(avg_changes, 2),
                "large_pr_count": len(large_prs),
                "large_pr_rate": round(len(large_prs) / total * 100, 2) if total > 0 else 0,
                "comment_density": round(comment_density, 4),
                "ci_success_count": len(ci_success),
                "ci_success_rate": round(len(ci_success) / total * 100, 2) if total > 0 else 0,
                "ci_stats": ci_stats
            },
            "distribution": {
                "by_creator": dict(sorted(creator_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
                "by_target_branch": dict(sorted(branch_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
                "by_label": dict(sorted(label_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
                "by_reviewer": dict(sorted(reviewer_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
                "by_merger": dict(sorted(merger_dist.items(), key=lambda x: x[1], reverse=True)[:10])
            },
            "daily_trend": dict(sorted(daily_trend.items()))
        }, prs_data

    def generate_html_report(self, insights: Dict, prs_data: List[Dict], output_file: str):
        """生成 HTML 报告（统计数据总结）"""
        summary = insights["summary"]
        efficiency = insights["efficiency"]
        quality = insights["quality"]
        distribution = insights["distribution"]
        daily_trend = insights["daily_trend"]

        # 准备图表数据
        dates = list(daily_trend.keys())
        created_counts = [daily_trend[d]["created"] for d in dates]
        merged_counts = [daily_trend[d]["merged"] for d in dates]
        closed_counts = [daily_trend[d]["closed"] for d in dates]

        creator_names = list(distribution["by_creator"].keys())
        creator_counts = list(distribution["by_creator"].values())

        branch_names = list(distribution["by_target_branch"].keys())
        branch_counts = list(distribution["by_target_branch"].values())

        # 准备规模分布数据
        size_ranges = {"0-50": 0, "51-200": 0, "201-500": 0, "501-1000": 0, ">1000": 0}
        for pr in prs_data:
            size = pr["total_changes"]
            if size <= 50:
                size_ranges["0-50"] += 1
            elif size <= 200:
                size_ranges["51-200"] += 1
            elif size <= 500:
                size_ranges["201-500"] += 1
            elif size <= 1000:
                size_ranges["501-1000"] += 1
            else:
                size_ranges[">1000"] += 1

        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR 洞察报告 - {insights["repo"]}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ text-align: center; color: #1a365d; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #e2e8f0; }}
        h2 {{ color: #1a365d; margin: 20px 0 15px 0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 25px; }}
        .stat-card {{ background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 26px; font-weight: bold; color: #1e40af; }}
        .stat-label {{ color: #64748b; margin-top: 5px; font-size: 13px; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 25px; }}
        .chart-box {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .chart-title {{ font-size: 15px; font-weight: bold; color: #1a365d; margin-bottom: 12px; }}
        .dist-section {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .dist-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
        .dist-item:last-child {{ border-bottom: none; }}
        .footer {{ text-align: center; color: #64748b; padding: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>PR 洞察报告 - {insights["repo"]}</h1>

        <h2>概览统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary["total_prs"]}</div>
                <div class="stat-label">总 PR 数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["opened_prs"]}</div>
                <div class="stat-label">打开中</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["merged_prs"]}</div>
                <div class="stat-label">已合并</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["closed_prs"]}</div>
                <div class="stat-label">已关闭(未合并)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["draft_prs"]}</div>
                <div class="stat-label">草稿 PR</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["merge_rate"]}%</div>
                <div class="stat-label">合并率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["draft_rate"]}%</div>
                <div class="stat-label">草稿率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary["conflict_rate"]}%</div>
                <div class="stat-label">冲突率</div>
            </div>
        </div>

        <h2>效率指标</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{efficiency["avg_first_review_time_minutes"]:.1f}</div>
                <div class="stat-label">平均首次评审(分钟)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{efficiency["avg_merge_duration_hours"]:.1f}</div>
                <div class="stat-label">平均合并耗时(小时)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{efficiency["avg_open_days"]:.1f}</div>
                <div class="stat-label">平均打开天数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{efficiency["timely_review_rate"]}%</div>
                <div class="stat-label">24h评审率</div>
            </div>
        </div>

        <h2>质量指标</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{quality["avg_change_lines"]:.0f}</div>
                <div class="stat-label">平均变更行数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{quality["large_pr_count"]}</div>
                <div class="stat-label">大PR数(>500行)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{quality["large_pr_rate"]}%</div>
                <div class="stat-label">大PR占比</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{quality["comment_density"]:.4f}</div>
                <div class="stat-label">评论密度</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{quality["ci_success_rate"]}%</div>
                <div class="stat-label">CI成功率</div>
            </div>
        </div>

        <h2>趋势图表</h2>
        <div class="charts-grid">
            <div class="chart-box">
                <div class="chart-title">每日 PR 趋势</div>
                <canvas id="trendChart"></canvas>
            </div>
            <div class="chart-box">
                <div class="chart-title">创建者分布 Top 10</div>
                <canvas id="creatorChart"></canvas>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-box">
                <div class="chart-title">目标分支分布</div>
                <canvas id="branchChart"></canvas>
            </div>
            <div class="chart-box">
                <div class="chart-title">代码变更规模分布</div>
                <canvas id="sizeChart"></canvas>
            </div>
        </div>

        <h2>分布统计</h2>
        <div class="charts-grid">
            <div class="dist-section">
                <div class="chart-title">创建者分布 Top 10</div>
'''
        for creator, count in distribution["by_creator"].items():
            html_content += f'                <div class="dist-item"><span>{creator}</span><span>{count}</span></div>\n'

        html_content += f'''            </div>
            <div class="dist-section">
                <div class="chart-title">目标分支分布</div>
'''
        for branch, count in distribution["by_target_branch"].items():
            html_content += f'                <div class="dist-item"><span>{branch}</span><span>{count}</span></div>\n'

        html_content += f'''            </div>
        </div>

        <div class="charts-grid">
            <div class="dist-section">
                <div class="chart-title">标签分布 Top 10</div>
'''
        for label, count in distribution["by_label"].items():
            html_content += f'                <div class="dist-item"><span>{label}</span><span>{count}</span></div>\n'

        html_content += f'''            </div>
            <div class="dist-section">
                <div class="chart-title">合并者分布</div>
'''
        for merger, count in distribution["by_merger"].items():
            html_content += f'                <div class="dist-item"><span>{merger}</span><span>{count}</span></div>\n'

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
                    label: '创建',
                    data: {json.dumps(created_counts)},
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true
                }},
                {{
                    label: '合并',
                    data: {json.dumps(merged_counts)},
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true
                }},
                {{
                    label: '关闭',
                    data: {json.dumps(closed_counts)},
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true
                }}
            ]
        }},
        options: {{
            responsive: true,
            scales: {{ y: {{ beginAtZero: true }} }}
        }}
    }});

    // 创建者分布图
    new Chart(document.getElementById('creatorChart'), {{
        type: 'bar',
        data: {{
            labels: {json.dumps(creator_names)},
            datasets: [{{
                label: 'PR 数量',
                data: {json.dumps(creator_counts)},
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1']
            }}]
        }},
        options: {{
            responsive: true,
            indexAxis: 'y',
            scales: {{ x: {{ beginAtZero: true }} }}
        }}
    }});

    // 目标分支分布图
    new Chart(document.getElementById('branchChart'), {{
        type: 'bar',
        data: {{
            labels: {json.dumps(branch_names)},
            datasets: [{{
                label: 'PR 数量',
                data: {json.dumps(branch_counts)},
                backgroundColor: '#8b5cf6'
            }}]
        }},
        options: {{
            responsive: true,
            indexAxis: 'y',
            scales: {{ x: {{ beginAtZero: true }} }}
        }}
    }});

    // 规模分布图
    new Chart(document.getElementById('sizeChart'), {{
        type: 'bar',
        data: {{
            labels: {json.dumps(list(size_ranges.keys()))},
            datasets: [{{
                label: 'PR 数量',
                data: {json.dumps(list(size_ranges.values()))},
                backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
            }}]
        }},
        options: {{
            responsive: true,
            scales: {{ y: {{ beginAtZero: true }} }}
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
        quality = insights["quality"]
        distribution = insights["distribution"]
        daily_trend = insights["daily_trend"]

        md_content = f'''# PR 洞察报告 - {insights["repo"]}

> 分析时间: {insights["analysis_time"]} | 分析周期: {insights["analysis_period"]}

## 概览统计

| 指标 | 数值 |
|------|------|
| 总 PR 数 | {summary["total_prs"]} |
| 打开中 | {summary["opened_prs"]} |
| 已合并 | {summary["merged_prs"]} |
| 已关闭(未合并) | {summary["closed_prs"]} |
| 草稿 PR | {summary["draft_prs"]} |
| 合并率 | {summary["merge_rate"]}% |
| 草稿率 | {summary["draft_rate"]}% |
| 冲突率 | {summary["conflict_rate"]}% |

## 效率指标

| 指标 | 数值 |
|------|------|
| 平均首次评审 | {efficiency["avg_first_review_time_minutes"]:.1f} 分钟 |
| 平均合并耗时 | {efficiency["avg_merge_duration_hours"]:.1f} 小时 |
| 平均打开天数 | {efficiency["avg_open_days"]:.1f} 天 |
| 24h评审率 | {efficiency["timely_review_rate"]}% |
| 评审时间样本数 | {efficiency["review_time_samples"]} |
| 合并耗时样本数 | {efficiency["merge_duration_samples"]} |

## 质量指标

| 指标 | 数值 |
|------|------|
| 平均变更行数 | {quality["avg_change_lines"]:.0f} |
| 大PR数(>500行) | {quality["large_pr_count"]} |
| 大PR占比 | {quality["large_pr_rate"]}% |
| 评论密度 | {quality["comment_density"]:.4f} |
| CI成功率 | {quality["ci_success_rate"]}% |

## 每日趋势

| 日期 | 创建 | 合并 | 关闭 |
|------|------|------|------|
'''
        for date, counts in sorted(daily_trend.items()):
            md_content += f"| {date} | {counts['created']} | {counts['merged']} | {counts['closed']} |\n"

        md_content += '''
## 创建者分布 Top 10

| 创建者 | 数量 |
|------|------|
'''
        for creator, count in distribution["by_creator"].items():
            md_content += f"| {creator} | {count} |\n"

        md_content += '''
## 目标分支分布

| 分支 | 数量 |
|------|------|
'''
        for branch, count in distribution["by_target_branch"].items():
            md_content += f"| {branch} | {count} |\n"

        md_content += '''
## 标签分布 Top 10

| 标签 | 数量 |
|------|------|
'''
        for label, count in distribution["by_label"].items():
            md_content += f"| {label} | {count} |\n"

        md_content += '''
## 合并者分布

| 合并者 | 数量 |
|------|------|
'''
        for merger, count in distribution["by_merger"].items():
            md_content += f"| {merger} | {count} |\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"Markdown 报告: {output_file}")

    def run(self) -> Dict:
        """执行完整的分析流程"""
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"PR 洞察分析: {self.owner}/{self.repo}")
        print(f"分析周期: 近 {self.days} 天")
        print(f"{'='*60}\n")

        # 获取 PR 列表
        prs = self.get_prs()

        if not prs:
            print("未获取到任何 PR 数据")
            return {}

        # 分析每个 PR
        print(f"\n分析 PR 详情...")
        prs_data = []
        for i, pr in enumerate(prs, 1):
            print(f"  处理 {i}/{len(prs)}: PR #{pr.get('number')}")
            analyzed = self.analyze_pr(pr)
            prs_data.append(analyzed)
            time.sleep(0.6)  # API 限流控制

        # 计算洞察指标
        print(f"\n计算洞察指标...")
        insights, raw_data = self.calculate_insights(prs_data)

        # 保存 JSON（统计数据 + 原始数据）
        json_file = os.path.join(self.output_dir, f"pr_insight_{self.repo}_{self.days}d.json")
        full_data = {
            "statistics": insights,
            "raw_data": raw_data
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        # 生成 HTML 报告
        html_file = os.path.join(self.output_dir, f"pr_insight_{self.repo}_{self.days}d.html")
        self.generate_html_report(insights, prs_data, html_file)

        # 生成 Markdown 报告
        md_file = os.path.join(self.output_dir, f"pr_insight_{self.repo}_{self.days}d.md")
        self.generate_markdown_report(insights, md_file)

        # 打印摘要
        print(f"\n{'='*60}")
        print(f"分析完成!")
        print(f"{'='*60}")
        print(f"总 PR 数: {insights['summary']['total_prs']}")
        print(f"打开中: {insights['summary']['opened_prs']}")
        print(f"已合并: {insights['summary']['merged_prs']}")
        print(f"合并率: {insights['summary']['merge_rate']}%")
        print(f"平均首次评审: {insights['efficiency']['avg_first_review_time_minutes']:.1f} 分钟")
        print(f"平均合并耗时: {insights['efficiency']['avg_merge_duration_hours']:.1f} 小时")
        print(f"平均变更行数: {insights['quality']['avg_change_lines']:.0f}")
        print(f"\n输出文件:")
        print(f"- JSON 数据: {json_file}")
        print(f"- HTML 报告: {html_file}")
        print(f"- Markdown 报告: {md_file}")
        print(f"{'='*60}\n")

        return full_data
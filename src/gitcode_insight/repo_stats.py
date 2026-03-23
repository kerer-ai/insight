# -*- coding: utf-8 -*-
"""
GitCode 仓库统计模块
整合下载统计、Fork、订阅用户和编程语言统计
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
import requests

from .utils import request_with_retry


class GitCodeRepoStats:
    """GitCode 仓库统计分析器"""

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

        # 计算时间范围
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        self.start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        self.since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    def _parse_datetime(self, value: str) -> Optional[datetime]:
        """解析时间字符串"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def _build_download_daily_trend(self, details: List[Dict[str, Any]]) -> Dict[str, int]:
        """构建下载按日趋势"""
        trend = {}
        for item in details:
            pdate = item.get("pdate")
            if not pdate:
                continue
            trend[pdate] = item.get("today_dl_cnt", 0)
        return trend

    def _build_fork_daily_trend(self, forks: List[Dict[str, Any]]) -> Dict[str, int]:
        """构建 Fork 按日趋势"""
        trend = {}
        for fork in forks:
            created_at = fork.get("created_at", "")
            parsed = self._parse_datetime(created_at)
            if not parsed:
                continue
            day = parsed.strftime("%Y-%m-%d")
            trend[day] = trend.get(day, 0) + 1
        return dict(sorted(trend.items(), key=lambda x: x[0]))

    def _build_subscriber_daily_trend(self, subscribers: List[Dict[str, Any]]) -> Dict[str, int]:
        """构建订阅用户按日趋势"""
        trend = {}
        for sub in subscribers:
            watch_at = sub.get("watch_at", "")
            parsed = self._parse_datetime(watch_at)
            if not parsed:
                continue
            day = parsed.strftime("%Y-%m-%d")
            trend[day] = trend.get(day, 0) + 1
        return dict(sorted(trend.items(), key=lambda x: x[0]))

    def _get_default_owner(self) -> str:
        """从配置文件获取默认 owner"""
        config_file = os.path.join(os.getcwd(), "config", "gitcode.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("owner", "")
        return ""

    def get_download_statistics(self) -> Dict:
        """获取下载统计数据"""
        print(f"获取 {self.owner}/{self.repo} 下载统计...")

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/download_statistics"
        params = {
            "access_token": self.token,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "direction": "desc"
        }

        data = request_with_retry(self.session, url, params)
        return data if data else {}

    def get_forks(self) -> List[Dict]:
        """获取 Fork 列表"""
        print(f"获取 {self.owner}/{self.repo} Fork 列表...")

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/forks"
        all_forks = []
        page = 1
        max_pages = 50

        while page <= max_pages:
            params = {
                "access_token": self.token,
                "sort": "newest",
                "per_page": 100,
                "page": page
            }

            data = request_with_retry(self.session, url, params)
            if data is None or not isinstance(data, list):
                break

            if len(data) == 0:
                break

            all_forks.extend(data)
            print(f"  第 {page} 页获取到 {len(data)} 条 Fork")

            if len(data) < 100:
                break

            page += 1
            time.sleep(0.6)  # API 限流控制

        print(f"共获取到 {len(all_forks)} 条 Fork")
        return all_forks

    def get_subscribers(self) -> List[Dict]:
        """获取订阅用户列表"""
        print(f"获取 {self.owner}/{self.repo} 订阅用户列表...")

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/subscribers"
        all_subscribers = []
        page = 1
        max_pages = 50

        while page <= max_pages:
            params = {
                "access_token": self.token,
                "per_page": 100,
                "page": page
            }

            data = request_with_retry(self.session, url, params)
            if data is None or not isinstance(data, list):
                break

            if len(data) == 0:
                break

            all_subscribers.extend(data)
            print(f"  第 {page} 页获取到 {len(data)} 条记录")

            if len(data) < 100:
                break

            page += 1
            time.sleep(0.6)  # API 限流控制

        print(f"共获取到 {len(all_subscribers)} 位订阅用户")
        return all_subscribers

    def get_languages(self) -> Dict:
        """获取编程语言占比"""
        print(f"获取 {self.owner}/{self.repo} 编程语言占比...")

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/languages"
        params = {"access_token": self.token}

        data = request_with_retry(self.session, url, params)
        return data if data else {}

    def analyze_download_stats(self, download_data: Dict) -> Dict:
        """分析下载统计"""
        download_stats = {
            "period_total": 0,
            "history_total": 0,
            "daily_average": 0,
            "peak_date": None,
            "peak_count": 0,
            "active_days": 0,
            "active_days_rate": 0,
            "trend": "flat",
            "top_days": [],
            "daily_trend": {}
        }

        if download_data:
            download_stats["period_total"] = download_data.get("download_statistics_total", 0)
            download_stats["history_total"] = download_data.get("download_statistics_history_total", 0)

            details = download_data.get("download_statistics_detail", [])
            if details:
                download_stats["daily_average"] = round(
                    sum(d.get("today_dl_cnt", 0) for d in details) / len(details), 2
                ) if details else 0

                max_day = max(details, key=lambda x: x.get("today_dl_cnt", 0), default=None)
                if max_day:
                    download_stats["peak_date"] = max_day.get("pdate")
                    download_stats["peak_count"] = max_day.get("today_dl_cnt", 0)

                sorted_by_date = sorted(details, key=lambda x: x.get("pdate", ""))
                if sorted_by_date:
                    latest_day = sorted_by_date[-1]
                    first_day = sorted_by_date[0]
                    diff = latest_day.get("today_dl_cnt", 0) - first_day.get("today_dl_cnt", 0)
                    if diff > 0:
                        download_stats["trend"] = "up"
                    elif diff < 0:
                        download_stats["trend"] = "down"

                active_days = sum(1 for d in details if d.get("today_dl_cnt", 0) > 0)
                download_stats["active_days"] = active_days
                download_stats["active_days_rate"] = round((active_days / len(details) * 100), 2) if details else 0
                download_stats["top_days"] = [
                    {
                        "date": d.get("pdate"),
                        "count": d.get("today_dl_cnt", 0),
                        "total": d.get("total_dl_cnt", 0)
                    }
                    for d in sorted(details, key=lambda x: x.get("today_dl_cnt", 0), reverse=True)[:10]
                ]
                download_stats["daily_trend"] = self._build_download_daily_trend(details)

        return download_stats

    def analyze_fork_stats(self, forks: List[Dict]) -> tuple:
        """分析 Fork 统计，返回 (stats, fork_list)"""
        since = datetime.fromisoformat(self.since_date.replace("Z", "+00:00"))

        fork_stats = {
            "total": len(forks),
            "new_in_period": 0,
            "unique_fork_owners": 0,
            "personal_forks": 0,
            "organization_forks": 0,
            "top_fork_users": [],
            "daily_trend": {},
            "latest_fork": None,
            "latest_forks": []
        }

        fork_list = []

        if forks:
            new_forks = []
            owner_counter = {}
            owner_latest_time = {}

            for fork in forks:
                created_at_str = fork.get("created_at", "")
                if created_at_str:
                    created_at = self._parse_datetime(created_at_str)
                    if created_at and created_at >= since:
                        new_forks.append(fork)

                owner_login = fork.get("owner", {}).get("login", "") or "unknown"
                owner_counter[owner_login] = owner_counter.get(owner_login, 0) + 1
                if created_at_str and (
                    owner_login not in owner_latest_time or created_at_str > owner_latest_time[owner_login]
                ):
                    owner_latest_time[owner_login] = created_at_str

            fork_stats["new_in_period"] = len(new_forks)
            fork_stats["unique_fork_owners"] = len(owner_counter)
            fork_stats["personal_forks"] = sum(
                1 for f in forks if f.get("namespace", {}).get("type", "") == "personal"
            )
            fork_stats["organization_forks"] = sum(
                1 for f in forks if f.get("namespace", {}).get("type", "") == "organization"
            )
            fork_stats["top_fork_users"] = [
                {
                    "owner": owner,
                    "count": count,
                    "latest_created_at": owner_latest_time.get(owner, "")
                }
                for owner, count in sorted(owner_counter.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            fork_stats["daily_trend"] = self._build_fork_daily_trend(forks)

            latest = forks[0]
            fork_stats["latest_fork"] = {
                "full_name": latest.get("full_name", ""),
                "created_at": latest.get("created_at", ""),
                "owner": latest.get("owner", {}).get("login", "")
            }
            fork_stats["latest_forks"] = [
                {
                    "full_name": f.get("full_name", ""),
                    "owner": f.get("owner", {}).get("login", ""),
                    "namespace_type": f.get("namespace", {}).get("type", ""),
                    "created_at": f.get("created_at", ""),
                    "pushed_at": f.get("pushed_at", "")
                }
                for f in forks[:10]
            ]

            fork_list = [
                {
                    "full_name": f.get("full_name", ""),
                    "owner": f.get("owner", {}).get("login", ""),
                    "namespace_type": f.get("namespace", {}).get("type", ""),
                    "created_at": f.get("created_at", ""),
                    "pushed_at": f.get("pushed_at", "")
                }
                for f in forks
            ]

        return fork_stats, fork_list

    def analyze_subscriber_stats(self, subscribers: List[Dict]) -> tuple:
        """分析订阅用户统计，返回 (stats, subscriber_list)"""
        since = datetime.fromisoformat(self.since_date.replace("Z", "+00:00"))

        subscriber_stats = {
            "total": len(subscribers),
            "new_in_period": 0,
            "latest_subscriber": None,
            "latest_subscribers": [],
            "daily_trend": {}
        }

        subscriber_list = []

        if subscribers:
            new_subscribers = []

            for sub in subscribers:
                watch_at_str = sub.get("watch_at", "")
                if watch_at_str:
                    try:
                        watch_at = self._parse_datetime(watch_at_str)
                        if watch_at and watch_at >= since:
                            new_subscribers.append(sub)
                    except:
                        pass

            subscriber_stats["new_in_period"] = len(new_subscribers)
            subscriber_stats["daily_trend"] = self._build_subscriber_daily_trend(subscribers)

            latest = subscribers[0]
            subscriber_stats["latest_subscriber"] = {
                "login": latest.get("login", ""),
                "name": latest.get("name", ""),
                "watch_at": latest.get("watch_at", "")
            }
            subscriber_stats["latest_subscribers"] = [
                {
                    "login": s.get("login", ""),
                    "name": s.get("name", ""),
                    "watch_at": s.get("watch_at", "")
                }
                for s in subscribers[:10]
            ]

            subscriber_list = [
                {
                    "login": s.get("login", ""),
                    "name": s.get("name", ""),
                    "watch_at": s.get("watch_at", "")
                }
                for s in subscribers
            ]

        return subscriber_stats, subscriber_list

    def analyze_language_stats(self, languages: Dict) -> Dict:
        """分析编程语言统计"""
        if not languages:
            return {
                "total_languages": 0,
                "primary_language": None,
                "languages": {}
            }

        sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        primary_language = sorted_languages[0][0] if sorted_languages else None

        return {
            "total_languages": len(languages),
            "primary_language": primary_language,
            "languages": dict(sorted_languages)
        }

    def analyze_stats(self, download_data: Dict, forks: List[Dict],
                      subscribers: List[Dict], languages: Dict) -> Dict:
        """分析所有统计数据"""
        download_stats = self.analyze_download_stats(download_data)
        fork_stats, fork_list = self.analyze_fork_stats(forks)
        subscriber_stats, subscriber_list = self.analyze_subscriber_stats(subscribers)
        language_stats = self.analyze_language_stats(languages)

        return {
            "repo": f"{self.owner}/{self.repo}",
            "analysis_period": f"近 {self.days} 天",
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "download_stats": download_stats,
            "fork_stats": fork_stats,
            "subscriber_stats": subscriber_stats,
            "language_stats": language_stats,
            "fork_list": fork_list,
            "subscriber_list": subscriber_list
        }

    def generate_html_report(self, data: Dict, output_file: str):
        """生成 HTML 报告"""
        import json as json_module

        download_stats = data.get("download_stats", {})
        fork_stats = data.get("fork_stats", {})
        subscriber_stats = data.get("subscriber_stats", {})
        language_stats = data.get("language_stats", {})
        fork_list = data.get("fork_list", [])
        subscriber_list = data.get("subscriber_list", [])

        # 图表数据
        download_trend = download_stats.get("daily_trend", {})
        dl_dates = list(download_trend.keys())
        dl_counts = list(download_trend.values())

        fork_trend = fork_stats.get("daily_trend", {})
        fork_dates = list(fork_trend.keys())
        fork_counts = list(fork_trend.values())

        subscriber_trend = subscriber_stats.get("daily_trend", {})
        sub_dates = list(subscriber_trend.keys())
        sub_counts = list(subscriber_trend.values())

        # 语言数据
        lang_names = list(language_stats.get("languages", {}).keys())[:10]
        lang_values = list(language_stats.get("languages", {}).values())[:10]

        # 表格行
        download_top_rows = "".join([
            f"<tr><td>{d.get('date', '-')}</td><td>{d.get('count', 0)}</td><td>{d.get('total', 0):,}</td></tr>"
            for d in download_stats.get("top_days", [])
        ])
        top_fork_users_rows = "".join([
            f"<tr><td>{u.get('owner', '-')}</td><td>{u.get('count', 0)}</td><td>{u.get('latest_created_at', '-')[:10]}</td></tr>"
            for u in fork_stats.get("top_fork_users", [])
        ])
        latest_subscribers_rows = "".join([
            f"<tr><td>{s.get('login', '-')}</td><td>{s.get('name', '-')}</td><td>{s.get('watch_at', '-')[:10]}</td></tr>"
            for s in subscriber_stats.get("latest_subscribers", [])
        ])
        fork_list_rows = "".join([
            f"<tr><td><a href='https://gitcode.com/{f.get('full_name', '')}' target='_blank'>{f.get('full_name', '-')}</a></td>"
            f"<td>{f.get('owner', '-')}</td><td>{f.get('namespace_type', '-')}</td>"
            f"<td>{f.get('created_at', '-')[:10]}</td><td>{f.get('pushed_at', '-')[:10]}</td></tr>"
            for f in fork_list
        ])
        subscriber_list_rows = "".join([
            f"<tr><td>{s.get('login', '-')}</td><td>{s.get('name', '-')}</td><td>{s.get('watch_at', '-')[:10]}</td></tr>"
            for s in subscriber_list[:50]  # 限制显示
        ])

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>仓库统计报告 - {data.get('repo', '')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ text-align: center; color: #1a365d; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #e2e8f0; }}
        h2 {{ color: #1a365d; margin: 20px 0 15px 0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 25px; }}
        .stat-card {{ background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 22px; font-weight: bold; color: #1e40af; }}
        .stat-label {{ color: #64748b; margin-top: 5px; font-size: 12px; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 25px; }}
        .chart-box {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .chart-title {{ font-size: 14px; font-weight: bold; color: #1a365d; margin-bottom: 12px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 15px; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; }}
        th {{ background: #f1f5f9; color: #334155; }}
        .footer {{ text-align: center; color: #64748b; padding: 20px; font-size: 12px; }}
        a {{ color: #3b82f6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>仓库统计报告 - {data.get('repo', '')}</h1>

        <h2>概览统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{download_stats.get('period_total', 0)}</div>
                <div class="stat-label">下载量({self.days}天)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{fork_stats.get('total', 0)}</div>
                <div class="stat-label">Fork总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{subscriber_stats.get('total', 0)}</div>
                <div class="stat-label">订阅用户</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{language_stats.get('total_languages', 0)}</div>
                <div class="stat-label">编程语言数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{language_stats.get('primary_language', '-')}</div>
                <div class="stat-label">主要语言</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{fork_stats.get('new_in_period', 0)}</div>
                <div class="stat-label">新增Fork({self.days}天)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{subscriber_stats.get('new_in_period', 0)}</div>
                <div class="stat-label">新增订阅({self.days}天)</div>
            </div>
        </div>

        <h2>趋势图表</h2>
        <div class="charts-grid">
            <div class="chart-box">
                <div class="chart-title">下载趋势</div>
                <canvas id="downloadChart"></canvas>
            </div>
            <div class="chart-box">
                <div class="chart-title">Fork趋势</div>
                <canvas id="forkChart"></canvas>
            </div>
            <div class="chart-box">
                <div class="chart-title">订阅趋势</div>
                <canvas id="subscriberChart"></canvas>
            </div>
            <div class="chart-box">
                <div class="chart-title">编程语言分布 Top 10</div>
                <canvas id="languageChart"></canvas>
            </div>
        </div>

        <h2>下载统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{download_stats.get('history_total', 0):,}</div>
                <div class="stat-label">历史累计下载</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{download_stats.get('daily_average', 0):.0f}</div>
                <div class="stat-label">日均下载量</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{download_stats.get('active_days_rate', 0)}%</div>
                <div class="stat-label">活跃下载占比</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{download_stats.get('trend', '-')}</div>
                <div class="stat-label">下载趋势</div>
            </div>
        </div>
        <div class="chart-box">
            <div class="chart-title">下载峰值 Top 10</div>
            <table>
                <thead><tr><th>日期</th><th>当日下载</th><th>截止当日累计</th></tr></thead>
                <tbody>{download_top_rows}</tbody>
            </table>
        </div>

        <h2>Fork 统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{fork_stats.get('unique_fork_owners', 0)}</div>
                <div class="stat-label">Fork人员数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{fork_stats.get('personal_forks', 0)}</div>
                <div class="stat-label">个人Fork数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{fork_stats.get('organization_forks', 0)}</div>
                <div class="stat-label">组织Fork数</div>
            </div>
        </div>
        <div class="chart-box">
            <div class="chart-title">Fork人员 Top 10</div>
            <table>
                <thead><tr><th>用户</th><th>Fork数</th><th>最新Fork时间</th></tr></thead>
                <tbody>{top_fork_users_rows}</tbody>
            </table>
        </div>

        <h2>Fork 列表</h2>
        <div class="chart-box">
            <table>
                <thead><tr><th>仓库</th><th>Fork人员</th><th>类型</th><th>创建时间</th><th>最近推送</th></tr></thead>
                <tbody>{fork_list_rows}</tbody>
            </table>
        </div>

        <h2>订阅用户统计</h2>
        <div class="chart-box">
            <div class="chart-title">最新订阅用户</div>
            <table>
                <thead><tr><th>用户</th><th>名称</th><th>订阅时间</th></tr></thead>
                <tbody>{latest_subscribers_rows}</tbody>
            </table>
        </div>
        <div class="chart-box">
            <div class="chart-title">订阅用户列表</div>
            <table>
                <thead><tr><th>用户</th><th>名称</th><th>订阅时间</th></tr></thead>
                <tbody>{subscriber_list_rows}</tbody>
            </table>
        </div>

        <div class="footer">
            <p>分析时间: {data.get('analysis_time', '')} | 分析周期: {data.get('analysis_period', '')}</p>
        </div>
    </div>

    <script>
    new Chart(document.getElementById('downloadChart'), {{
        type: 'line',
        data: {{
            labels: {json_module.dumps(dl_dates)},
            datasets: [{{label: '当日下载', data: {json_module.dumps(dl_counts)}, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true}}]
        }},
        options: {{responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});

    new Chart(document.getElementById('forkChart'), {{
        type: 'line',
        data: {{
            labels: {json_module.dumps(fork_dates)},
            datasets: [{{label: '当日新增Fork', data: {json_module.dumps(fork_counts)}, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true}}]
        }},
        options: {{responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});

    new Chart(document.getElementById('subscriberChart'), {{
        type: 'line',
        data: {{
            labels: {json_module.dumps(sub_dates)},
            datasets: [{{label: '当日新增订阅', data: {json_module.dumps(sub_counts)}, borderColor: '#8b5cf6', backgroundColor: 'rgba(139, 92, 246, 0.1)', fill: true}}]
        }},
        options: {{responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});

    new Chart(document.getElementById('languageChart'), {{
        type: 'bar',
        data: {{
            labels: {json_module.dumps(lang_names)},
            datasets: [{{label: '占比(%)', data: {json_module.dumps(lang_values)}, backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1']}}]
        }},
        options: {{responsive: true, indexAxis: 'y', scales: {{ x: {{ beginAtZero: true }} }} }}
    }});
    </script>
</body>
</html>
"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTML 报告: {output_file}")

    def generate_markdown_report(self, data: Dict, output_file: str):
        """生成 Markdown 报告"""
        download_stats = data.get("download_stats", {})
        fork_stats = data.get("fork_stats", {})
        subscriber_stats = data.get("subscriber_stats", {})
        language_stats = data.get("language_stats", {})
        fork_list = data.get("fork_list", [])
        subscriber_list = data.get("subscriber_list", [])

        md_content = f'''# 仓库统计报告 - {data.get('repo', '')}

> 分析时间: {data.get('analysis_time', '')} | 分析周期: {data.get('analysis_period', '')}

## 概览统计

| 指标 | 数值 |
|------|------|
| 下载量({self.days}天) | {download_stats.get('period_total', 0)} |
| 历史累计下载 | {download_stats.get('history_total', 0):,} |
| Fork总数 | {fork_stats.get('total', 0)} |
| 新增Fork({self.days}天) | {fork_stats.get('new_in_period', 0)} |
| 订阅用户 | {subscriber_stats.get('total', 0)} |
| 新增订阅({self.days}天) | {subscriber_stats.get('new_in_period', 0)} |
| 编程语言数 | {language_stats.get('total_languages', 0)} |
| 主要语言 | {language_stats.get('primary_language', '-')} |

## 下载统计

| 指标 | 数值 |
|------|------|
| 日均下载量 | {download_stats.get('daily_average', 0):.0f} |
| 活跃下载天数 | {download_stats.get('active_days', 0)} |
| 活跃下载占比 | {download_stats.get('active_days_rate', 0)}% |
| 下载趋势 | {download_stats.get('trend', '-')} |

### 下载峰值 Top 10

| 日期 | 当日下载 | 截止当日累计 |
|------|----------|--------------|
'''
        for d in download_stats.get("top_days", []):
            md_content += f"| {d.get('date', '-')} | {d.get('count', 0)} | {d.get('total', 0):,} |\n"

        md_content += f'''
## Fork 统计

| 指标 | 数值 |
|------|------|
| Fork人员数 | {fork_stats.get('unique_fork_owners', 0)} |
| 个人Fork数 | {fork_stats.get('personal_forks', 0)} |
| 组织Fork数 | {fork_stats.get('organization_forks', 0)} |

### Fork人员 Top 10

| 用户 | Fork数 | 最新Fork时间 |
|------|--------|----------------|
'''
        for u in fork_stats.get("top_fork_users", []):
            md_content += f"| {u.get('owner', '-')} | {u.get('count', 0)} | {u.get('latest_created_at', '-')[:10]} |\n"

        md_content += f'''
### Fork 列表

| 仓库 | Fork人员 | 类型 | 创建时间 | 最近推送 |
|------|----------|------|----------|----------|
'''
        for f in fork_list:
            md_content += f"| [{f.get('full_name', '-')}] | {f.get('owner', '-')} | {f.get('namespace_type', '-')} | {f.get('created_at', '-')[:10]} | {f.get('pushed_at', '-')[:10]} |\n"

        md_content += f'''
## 订阅用户统计

### 最新订阅用户

| 用户 | 名称 | 订阅时间 |
|------|------|----------|
'''
        for s in subscriber_stats.get("latest_subscribers", []):
            md_content += f"| {s.get('login', '-')} | {s.get('name', '-')} | {s.get('watch_at', '-')[:10]} |\n"

        md_content += f'''
### 订阅用户列表

| 用户 | 名称 | 订阅时间 |
|------|------|----------|
'''
        for s in subscriber_list[:50]:
            md_content += f"| {s.get('login', '-')} | {s.get('name', '-')} | {s.get('watch_at', '-')[:10]} |\n"

        md_content += f'''
## 编程语言统计

| 语言 | 占比 |
|------|------|
'''
        for lang, percent in list(language_stats.get("languages", {}).items())[:15]:
            md_content += f"| {lang} | {percent}% |\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"Markdown 报告: {output_file}")

    def save_to_json(self, data: Dict) -> str:
        """保存到 JSON 文件（统计数据 + 原始数据）"""
        os.makedirs(self.output_dir, exist_ok=True)
        filename = os.path.join(
            self.output_dir,
            f"repo_stats_{self.owner}_{self.repo}_{self.days}d.json"
        )
        # 构建与 PR 一致的 JSON 结构
        full_data = {
            "statistics": {
                "repo": data.get("repo", ""),
                "analysis_period": data.get("analysis_period", ""),
                "analysis_time": data.get("analysis_time", ""),
                "download_stats": data.get("download_stats", {}),
                "fork_stats": data.get("fork_stats", {}),
                "subscriber_stats": data.get("subscriber_stats", {}),
                "language_stats": data.get("language_stats", {})
            },
            "raw_data": {
                "fork_list": data.get("fork_list", []),
                "subscriber_list": data.get("subscriber_list", [])
            }
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        return filename

    def run(self) -> Dict:
        """执行完整的分析流程"""
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"仓库统计: {self.owner}/{self.repo}")
        print(f"分析周期: 近 {self.days} 天")
        print(f"{'='*60}\n")

        # 获取数据
        download_data = self.get_download_statistics()
        forks = self.get_forks()
        subscribers = self.get_subscribers()
        languages = self.get_languages()

        # 分析统计
        print(f"\n分析统计数据...")
        result = self.analyze_stats(download_data, forks, subscribers, languages)

        # 保存文件
        json_file = self.save_to_json(result)
        html_file = os.path.join(
            self.output_dir,
            f"repo_stats_{self.owner}_{self.repo}_{self.days}d.html"
        )
        md_file = os.path.join(
            self.output_dir,
            f"repo_stats_{self.owner}_{self.repo}_{self.days}d.md"
        )
        self.generate_html_report(result, html_file)
        self.generate_markdown_report(result, md_file)

        # 打印摘要
        print(f"\n{'='*60}")
        print(f"【下载统计】")
        print(f"- 时间范围下载量: {result['download_stats']['period_total']}")
        print(f"- 历史累计下载: {result['download_stats']['history_total']:,}")
        if result['download_stats']['peak_date']:
            print(f"- 下载峰值日: {result['download_stats']['peak_date']} ({result['download_stats']['peak_count']} 次)")

        print(f"\n【Fork 统计】")
        print(f"- Fork总数: {result['fork_stats']['total']}")
        print(f"- 近 {self.days} 天新增: {result['fork_stats']['new_in_period']}")
        print(f"- Fork人员数: {result['fork_stats']['unique_fork_owners']}")

        print(f"\n【订阅用户】")
        print(f"- 订阅用户总数: {result['subscriber_stats']['total']}")
        print(f"- 近 {self.days} 天新增: {result['subscriber_stats']['new_in_period']}")

        print(f"\n【编程语言】")
        print(f"- 语言种类数: {result['language_stats']['total_languages']}")
        if result['language_stats']['primary_language']:
            print(f"- 主要语言: {result['language_stats']['primary_language']}")

        print(f"\n输出文件:")
        print(f"- JSON 数据: {json_file}")
        print(f"- HTML 报告: {html_file}")
        print(f"- Markdown 报告: {md_file}")
        print(f"{'='*60}\n")

        return result
# -*- coding: utf-8 -*-
"""
GitCode 仓库订阅用户模块
获取仓库的 Watch（订阅）用户列表
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import requests

from .utils import request_with_retry


class GitCodeSubscribers:
    """GitCode 仓库订阅用户分析器"""

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

    def _parse_datetime(self, value: str) -> Optional[datetime]:
        """解析时间字符串"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def _build_daily_trend(self, subscribers: List[Dict]) -> Dict[str, int]:
        """构建按日订阅趋势"""
        trend = {}
        for sub in subscribers:
            watch_at = sub.get("watch_at", "")
            parsed = self._parse_datetime(watch_at)
            if not parsed:
                continue
            day = parsed.strftime("%Y-%m-%d")
            trend[day] = trend.get(day, 0) + 1
        return dict(sorted(trend.items(), key=lambda x: x[0]))

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

    def analyze_subscribers(self, subscribers: List[Dict]) -> Dict:
        """分析订阅用户数据"""
        total = len(subscribers)

        # 计算时间范围内新增订阅
        since = datetime.fromisoformat(self.since_date.replace("Z", "+00:00"))
        new_subscribers = []

        for sub in subscribers:
            watch_at_str = sub.get("watch_at", "")
            if watch_at_str:
                try:
                    watch_at = datetime.fromisoformat(watch_at_str.replace("Z", "+00:00"))
                    if watch_at >= since:
                        new_subscribers.append(sub)
                except:
                    pass

        # 最新订阅用户
        latest_subscribers = []
        for sub in subscribers[:10]:  # 取前10个
            latest_subscribers.append({
                "login": sub.get("login", ""),
                "name": sub.get("name", ""),
                "watch_at": sub.get("watch_at", "")
            })

        # 最新订阅用户
        latest_subscriber = None
        if subscribers:
            latest = subscribers[0]  # API 默认按时间倒序
            latest_subscriber = {
                "login": latest.get("login", ""),
                "name": latest.get("name", ""),
                "watch_at": latest.get("watch_at", "")
            }

        # 按日趋势
        daily_trend = self._build_daily_trend(subscribers)

        return {
            "repo": f"{self.owner}/{self.repo}",
            "analysis_period": f"近 {self.days} 天",
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "subscriber_stats": {
                "total": total,
                "new_in_period": len(new_subscribers),
                "latest_subscriber": latest_subscriber,
                "latest_subscribers": latest_subscribers,
                "daily_trend": daily_trend
            },
            "subscriber_list": [
                {
                    "login": s.get("login", ""),
                    "name": s.get("name", ""),
                    "watch_at": s.get("watch_at", "")
                }
                for s in subscribers
            ]
        }

    def generate_html_report(self, data: Dict, output_file: str):
        """生成 HTML 报告"""
        stats = data.get("subscriber_stats", {})
        subscriber_list = data.get("subscriber_list", [])

        # 图表数据
        daily_trend = stats.get("daily_trend", {})
        dates = list(daily_trend.keys())
        counts = list(daily_trend.values())

        # 最新订阅用户表格
        latest_rows = "".join([
            f"<tr><td>{s.get('login', '-')}</td><td>{s.get('name', '-')}</td><td>{s.get('watch_at', '-')[:10] if s.get('watch_at') else '-'}</td></tr>"
            for s in stats.get("latest_subscribers", [])
        ])

        # 订阅者列表表格
        list_rows = "".join([
            f"<tr><td>{s.get('login', '-')}</td><td>{s.get('name', '-')}</td><td>{s.get('watch_at', '-')[:10] if s.get('watch_at') else '-'}</td></tr>"
            for s in subscriber_list
        ])

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>订阅用户统计 - {data.get('repo', '')}</title>
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
        .chart-box {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .chart-title {{ font-size: 15px; font-weight: bold; color: #1a365d; margin-bottom: 12px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 15px; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; }}
        th {{ background: #f1f5f9; color: #334155; }}
        .footer {{ text-align: center; color: #64748b; padding: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>订阅用户统计 - {data.get('repo', '')}</h1>

        <h2>概览统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats.get('total', 0)}</div>
                <div class="stat-label">订阅用户总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('new_in_period', 0)}</div>
                <div class="stat-label">近 {self.days} 天新增</div>
            </div>
        </div>

        <h2>订阅趋势</h2>
        <div class="chart-box">
            <div class="chart-title">每日新增订阅趋势</div>
            <canvas id="trendChart"></canvas>
        </div>

        <h2>最新订阅用户</h2>
        <div class="chart-box">
            <table>
                <thead><tr><th>用户</th><th>名称</th><th>订阅时间</th></tr></thead>
                <tbody>{latest_rows}</tbody>
            </table>
        </div>

        <h2>订阅用户列表</h2>
        <div class="chart-box">
            <table>
                <thead><tr><th>用户</th><th>名称</th><th>订阅时间</th></tr></thead>
                <tbody>{list_rows}</tbody>
            </table>
        </div>

        <div class="footer">
            <p>分析时间: {data.get('analysis_time', '')} | 分析周期: {data.get('analysis_period', '')}</p>
        </div>
    </div>

    <script>
    new Chart(document.getElementById('trendChart'), {{
        type: 'line',
        data: {{
            labels: {json.dumps(dates)},
            datasets: [{{
                label: '当日新增订阅',
                data: {json.dumps(counts)},
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                fill: true
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
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML 报告: {output_file}")

    def generate_markdown_report(self, data: Dict, output_file: str):
        """生成 Markdown 报告"""
        stats = data.get("subscriber_stats", {})
        subscriber_list = data.get("subscriber_list", [])

        md_content = f'''# 订阅用户统计 - {data.get('repo', '')}

> 分析时间: {data.get('analysis_time', '')} | 分析周期: {data.get('analysis_period', '')}

## 概览统计

| 指标 | 数值 |
|------|------|
| 订阅用户总数 | {stats.get('total', 0)} |
| 近 {self.days} 天新增 | {stats.get('new_in_period', 0)} |

## 最新订阅用户

| 用户 | 名称 | 订阅时间 |
|------|------|----------|
'''
        for s in stats.get("latest_subscribers", []):
            md_content += f"| {s.get('login', '-')} | {s.get('name', '-')} | {s.get('watch_at', '-')[:10] if s.get('watch_at') else '-'} |\n"

        md_content += '''
## 订阅用户列表

| 用户 | 名称 | 订阅时间 |
|------|------|----------|
'''
        for s in subscriber_list:
            md_content += f"| {s.get('login', '-')} | {s.get('name', '-')} | {s.get('watch_at', '-')[:10] if s.get('watch_at') else '-'} |\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"Markdown 报告: {output_file}")

    def save_to_json(self, data: Dict) -> str:
        """保存到 JSON 文件（统计数据 + 原始数据）"""
        os.makedirs(self.output_dir, exist_ok=True)
        filename = os.path.join(
            self.output_dir,
            f"subscribers_{self.owner}_{self.repo}_{self.days}d.json"
        )
        # 构建与 PR 一致的 JSON 结构
        full_data = {
            "statistics": {
                "repo": data.get("repo", ""),
                "analysis_period": data.get("analysis_period", ""),
                "analysis_time": data.get("analysis_time", ""),
                "subscriber_stats": data.get("subscriber_stats", {})
            },
            "raw_data": data.get("subscriber_list", [])
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        return filename

    def run(self) -> Dict:
        """执行完整的分析流程"""
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"订阅用户统计: {self.owner}/{self.repo}")
        print(f"分析周期: 近 {self.days} 天")
        print(f"{'='*60}\n")

        # 获取订阅用户列表
        subscribers = self.get_subscribers()

        # 分析统计
        print(f"\n分析统计数据...")
        result = self.analyze_subscribers(subscribers)

        # 保存 JSON
        json_file = self.save_to_json(result)

        # 生成 HTML 报告
        html_file = os.path.join(
            self.output_dir,
            f"subscribers_{self.owner}_{self.repo}_{self.days}d.html"
        )
        self.generate_html_report(result, html_file)

        # 生成 Markdown 报告
        md_file = os.path.join(
            self.output_dir,
            f"subscribers_{self.owner}_{self.repo}_{self.days}d.md"
        )
        self.generate_markdown_report(result, md_file)

        # 打印摘要
        stats = result["subscriber_stats"]
        print(f"\n{'='*60}")
        print(f"【订阅用户统计】")
        print(f"- 订阅用户总数: {stats['total']}")
        print(f"- 近 {self.days} 天新增订阅: {stats['new_in_period']}")
        if stats['latest_subscriber']:
            latest = stats['latest_subscriber']
            watch_date = latest['watch_at'][:10] if latest['watch_at'] else '-'
            print(f"- 最新订阅用户: {latest['login']} ({watch_date})")

        print(f"\n输出文件:")
        print(f"- JSON 数据: {json_file}")
        print(f"- HTML 报告: {html_file}")
        print(f"- Markdown 报告: {md_file}")
        print(f"{'='*60}\n")

        return result
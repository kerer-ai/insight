# -*- coding: utf-8 -*-
"""
GitCode 仓库订阅用户模块
获取仓库的 Watch（订阅）用户列表
"""

import json
import os
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
        latest_subscriber = None
        if subscribers:
            latest = subscribers[0]  # API 默认按时间倒序
            latest_subscriber = {
                "login": latest.get("login", ""),
                "name": latest.get("name", ""),
                "watch_at": latest.get("watch_at", "")
            }

        return {
            "repo": f"{self.owner}/{self.repo}",
            "analysis_period": f"近 {self.days} 天",
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "subscriber_stats": {
                "total": total,
                "new_in_period": len(new_subscribers),
                "latest_subscriber": latest_subscriber,
                "subscribers": [
                    {
                        "login": s.get("login", ""),
                        "name": s.get("name", ""),
                        "watch_at": s.get("watch_at", "")
                    }
                    for s in subscribers[:50]  # 只保留前50条
                ]
            }
        }

    def save_to_json(self, data: Dict) -> str:
        """保存到 JSON 文件"""
        os.makedirs(self.output_dir, exist_ok=True)
        filename = os.path.join(
            self.output_dir,
            f"subscribers_{self.owner}_{self.repo}_{self.days}d.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
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

        print(f"\n数据已保存到: {json_file}")
        print(f"{'='*60}\n")

        return result
# -*- coding: utf-8 -*-
"""
GitCode 仓库统计模块
整合下载统计和 Fork 列表信息
"""

import json
import time
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
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
        self.session.headers.update({"Content-Type": "application/json"})

        # 计算时间范围
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        self.start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        self.since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

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

        print(f"共获取到 {len(all_forks)} 条 Fork")
        return all_forks

    def analyze_stats(self, download_data: Dict, forks: List[Dict]) -> Dict:
        """分析统计数据"""
        # 分析下载统计
        download_stats = {
            "period_total": 0,
            "history_total": 0,
            "daily_average": 0,
            "peak_date": None,
            "peak_count": 0,
            "details": []
        }

        if download_data:
            download_stats["period_total"] = download_data.get("download_statistics_total", 0)
            download_stats["history_total"] = download_data.get("download_statistics_history_total", 0)

            details = download_data.get("download_statistics_detail", [])
            if details:
                download_stats["details"] = details
                download_stats["daily_average"] = round(
                    sum(d.get("today_dl_cnt", 0) for d in details) / len(details), 2
                ) if details else 0

                # 找出下载峰值日
                max_day = max(details, key=lambda x: x.get("today_dl_cnt", 0), default=None)
                if max_day:
                    download_stats["peak_date"] = max_day.get("pdate")
                    download_stats["peak_count"] = max_day.get("today_dl_cnt", 0)

        # 分析 Fork 统计
        fork_stats = {
            "total": len(forks),
            "new_in_period": 0,
            "latest_fork": None,
            "forks": []
        }

        if forks:
            # 计算时间范围内新增的 Fork
            since = datetime.fromisoformat(self.since_date.replace("Z", "+00:00"))
            new_forks = []
            for fork in forks:
                created_at_str = fork.get("created_at", "")
                if created_at_str:
                    try:
                        # 处理不同格式的时间
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if created_at >= since:
                            new_forks.append(fork)
                    except:
                        pass

            fork_stats["new_in_period"] = len(new_forks)

            # 最新 Fork
            if forks:
                latest = forks[0]  # 已经按 newest 排序
                fork_stats["latest_fork"] = {
                    "full_name": latest.get("full_name", ""),
                    "created_at": latest.get("created_at", ""),
                    "owner": latest.get("owner", {}).get("login", "")
                }

            # 简化 Fork 列表
            fork_stats["forks"] = [
                {
                    "full_name": f.get("full_name", ""),
                    "owner": f.get("owner", {}).get("login", ""),
                    "created_at": f.get("created_at", ""),
                    "updated_at": f.get("updated_at", "")
                }
                for f in forks[:50]  # 只保留前50条
            ]

        return {
            "repo": f"{self.owner}/{self.repo}",
            "analysis_period": f"近 {self.days} 天",
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "download_stats": download_stats,
            "fork_stats": fork_stats
        }

    def save_to_json(self, data: Dict) -> str:
        """保存到 JSON 文件"""
        os.makedirs(self.output_dir, exist_ok=True)
        filename = os.path.join(
            self.output_dir,
            f"repo_stats_{self.owner}_{self.repo}_{self.days}d.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filename

    def run(self) -> Dict:
        """执行完整的分析流程"""
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"仓库统计: {self.owner}/{self.repo}")
        print(f"分析周期: 近 {self.days} 天")
        print(f"{'='*60}\n")

        # 获取下载统计
        download_data = self.get_download_statistics()

        # 获取 Fork 列表
        forks = self.get_forks()

        # 分析统计
        print(f"\n分析统计数据...")
        result = self.analyze_stats(download_data, forks)

        # 保存 JSON
        json_file = self.save_to_json(result)

        # 打印摘要
        print(f"\n{'='*60}")
        print(f"【下载统计】")
        print(f"- 时间范围总下载量: {result['download_stats']['period_total']}")
        print(f"- 历史累计下载量: {result['download_stats']['history_total']:,}")
        print(f"- 日均下载量: {result['download_stats']['daily_average']}")
        if result['download_stats']['peak_date']:
            print(f"- 下载峰值日: {result['download_stats']['peak_date']} ({result['download_stats']['peak_count']} 次)")

        print(f"\n【Fork 统计】")
        print(f"- Fork 总数: {result['fork_stats']['total']}")
        print(f"- 近 {self.days} 天新增 Fork: {result['fork_stats']['new_in_period']}")
        if result['fork_stats']['latest_fork']:
            latest = result['fork_stats']['latest_fork']
            print(f"- 最新 Fork: {latest['full_name']} ({latest['created_at'][:10] if latest['created_at'] else '-'})")

        print(f"\n数据已保存到: {json_file}")
        print(f"{'='*60}\n")

        return result
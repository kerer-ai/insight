# -*- coding: utf-8 -*-
"""
GitCode 仓库语言统计模块
获取仓库的编程语言占比
"""

import json
import os
from datetime import datetime
from typing import Dict
import requests

from .utils import request_with_retry


class GitCodeLanguages:
    """GitCode 仓库语言统计"""

    def __init__(self, repo: str, token: str, owner: str = None, output_dir: str = None):
        """
        初始化

        Args:
            repo: 仓库名称（path）
            token: API 访问令牌
            owner: 组织名
            output_dir: 输出目录
        """
        self.repo = repo
        self.token = token
        self.owner = owner or self._get_default_owner()
        self.base_url = "https://api.gitcode.com/api/v5"

        # 设置输出目录
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "output")
        self.output_dir = output_dir

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _get_default_owner(self) -> str:
        """从配置文件获取默认 owner"""
        config_file = os.path.join(os.getcwd(), "config", "gitcode.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("owner", "")
        return ""

    def get_languages(self) -> Dict:
        """获取语言占比数据"""
        print(f"获取 {self.owner}/{self.repo} 编程语言占比...")

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/languages"
        params = {
            "access_token": self.token
        }

        data = request_with_retry(self.session, url, params)
        return data if data else {}

    def analyze_languages(self, languages: Dict) -> Dict:
        """分析语言数据"""
        if not languages:
            return {
                "repo": f"{self.owner}/{self.repo}",
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "language_stats": {
                    "total_languages": 0,
                    "languages": {},
                    "primary_language": None
                }
            }

        # 按占比排序
        sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)

        # 主要语言
        primary_language = sorted_languages[0][0] if sorted_languages else None

        return {
            "repo": f"{self.owner}/{self.repo}",
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "language_stats": {
                "total_languages": len(languages),
                "primary_language": primary_language,
                "languages": dict(sorted_languages)
            }
        }

    def save_to_json(self, data: Dict) -> str:
        """保存到 JSON 文件"""
        os.makedirs(self.output_dir, exist_ok=True)
        filename = os.path.join(
            self.output_dir,
            f"languages_{self.owner}_{self.repo}.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filename

    def run(self) -> Dict:
        """执行完整的分析流程"""
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"编程语言统计: {self.owner}/{self.repo}")
        print(f"{'='*60}\n")

        # 获取语言数据
        languages = self.get_languages()

        # 分析统计
        result = self.analyze_languages(languages)

        # 保存 JSON
        json_file = self.save_to_json(result)

        # 打印摘要
        stats = result["language_stats"]
        print(f"\n{'='*60}")
        print(f"【编程语言统计】")
        print(f"- 语言种类数: {stats['total_languages']}")
        if stats['primary_language']:
            print(f"- 主要语言: {stats['primary_language']}")

        if stats['languages']:
            print(f"- 语言占比:")
            for lang, percent in list(stats['languages'].items())[:10]:
                print(f"    {lang}: {percent}%")

        print(f"\n数据已保存到: {json_file}")
        print(f"{'='*60}\n")

        return result
# -*- coding: utf-8 -*-
"""
GitCode Subscribers 模块测试
"""

import json
import os
import tempfile
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from gitcode_insight.subscribers import GitCodeSubscribers


class TestGitCodeSubscribers:
    """GitCodeSubscribers 测试类"""

    def test_analyze_subscribers(self):
        """测试订阅用户分析"""
        subscribers = GitCodeSubscribers(
            repo="test_repo",
            token="test_token",
            owner="test_owner"
        )

        now = datetime.now(timezone.utc)
        test_data = [
            {
                "login": "user1",
                "name": "User One",
                "watch_at": (now - timedelta(days=5)).isoformat()
            },
            {
                "login": "user2",
                "name": "User Two",
                "watch_at": (now - timedelta(days=1)).isoformat()
            },
            {
                "login": "user3",
                "name": "User Three",
                "watch_at": (now - timedelta(days=50)).isoformat()  # 超出时间范围
            }
        ]

        result = subscribers.analyze_subscribers(test_data)

        assert result["subscriber_stats"]["total"] == 3
        assert result["subscriber_stats"]["new_in_period"] == 2  # user1 和 user2
        assert len(result["subscriber_list"]) == 3
        assert result["subscriber_stats"]["latest_subscriber"]["login"] == "user1"

    def test_generate_reports(self):
        """测试生成 HTML 和 Markdown 报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subscribers = GitCodeSubscribers(
                repo="test_repo",
                token="test_token",
                owner="test_owner",
                output_dir=tmpdir
            )

            data = {
                "repo": "test_owner/test_repo",
                "analysis_period": "近 30 天",
                "analysis_time": "2026-03-19 12:00:00",
                "subscriber_stats": {
                    "total": 10,
                    "new_in_period": 3,
                    "latest_subscriber": {"login": "user1", "name": "User One", "watch_at": "2026-03-19T10:00:00+08:00"},
                    "latest_subscribers": [{"login": "user1", "name": "User One", "watch_at": "2026-03-19T10:00:00+08:00"}],
                    "daily_trend": {"2026-03-18": 2, "2026-03-19": 1}
                },
                "subscriber_list": [
                    {"login": "user1", "name": "User One", "watch_at": "2026-03-19T10:00:00+08:00"}
                ]
            }

            html_file = os.path.join(tmpdir, "test.html")
            md_file = os.path.join(tmpdir, "test.md")

            subscribers.generate_html_report(data, html_file)
            subscribers.generate_markdown_report(data, md_file)

            assert os.path.exists(html_file)
            assert os.path.exists(md_file)

            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                assert "订阅用户统计" in html_content
                assert "cdn.jsdelivr.net/npm/chart.js" in html_content

            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
                assert "订阅用户统计" in md_content
                assert "订阅用户列表" in md_content

    def test_save_to_json_structure(self):
        """测试 JSON 结构符合 statistics + raw_data 格式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subscribers = GitCodeSubscribers(
                repo="test_repo",
                token="test_token",
                owner="test_owner",
                output_dir=tmpdir
            )

            data = {
                "repo": "test_owner/test_repo",
                "analysis_period": "近 30 天",
                "analysis_time": "2026-03-19 12:00:00",
                "subscriber_stats": {
                    "total": 5,
                    "new_in_period": 2,
                    "latest_subscriber": {"login": "user1", "name": "User One", "watch_at": "2026-03-19T10:00:00+08:00"}
                },
                "subscriber_list": [
                    {"login": "user1", "name": "User One", "watch_at": "2026-03-19T10:00:00+08:00"},
                    {"login": "user2", "name": "User Two", "watch_at": "2026-03-18T10:00:00+08:00"}
                ]
            }

            json_file = subscribers.save_to_json(data)

            with open(json_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)

            assert "statistics" in loaded
            assert "raw_data" in loaded
            assert "subscriber_stats" in loaded["statistics"]
            assert len(loaded["raw_data"]) == 2

    def test_run_generates_three_output_files(self):
        """测试 run 生成 JSON/HTML/MD 三类文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subscribers = GitCodeSubscribers(
                repo="test_repo",
                token="test_token",
                owner="test_owner",
                output_dir=tmpdir
            )

            with patch.object(subscribers, "get_subscribers", return_value=[
                {"login": "user1", "name": "User One", "watch_at": "2026-03-19T10:00:00+08:00"}
            ]):
                result = subscribers.run()

            assert "subscriber_stats" in result
            assert "subscriber_list" in result

            json_file = os.path.join(tmpdir, "subscribers_test_owner_test_repo_30d.json")
            html_file = os.path.join(tmpdir, "subscribers_test_owner_test_repo_30d.html")
            md_file = os.path.join(tmpdir, "subscribers_test_owner_test_repo_30d.md")

            assert os.path.exists(json_file)
            assert os.path.exists(html_file)
            assert os.path.exists(md_file)
# -*- coding: utf-8 -*-
"""
GitCode RepoStats 模块测试
"""

import json
import os
import tempfile
from unittest.mock import patch

from gitcode_insight.repo_stats import GitCodeRepoStats


class TestGitCodeRepoStats:
    """GitCodeRepoStats 测试类"""

    def test_analyze_stats_with_detailed_data(self):
        """测试详细下载、Fork、订阅用户和编程语言分析"""
        stats = GitCodeRepoStats(
            repo="test_repo",
            token="test_token",
            owner="test_owner"
        )

        download_data = {
            "download_statistics_total": 25,
            "download_statistics_history_total": 120,
            "download_statistics_detail": [
                {"pdate": "2026-03-01", "today_dl_cnt": 5, "total_dl_cnt": 100},
                {"pdate": "2026-03-02", "today_dl_cnt": 10, "total_dl_cnt": 110},
                {"pdate": "2026-03-03", "today_dl_cnt": 10, "total_dl_cnt": 120}
            ]
        }
        forks = [
            {
                "full_name": "user1/test_repo",
                "created_at": "2026-03-03T10:00:00+08:00",
                "updated_at": "2026-03-04T10:00:00+08:00",
                "pushed_at": "2026-03-05T10:00:00+08:00",
                "owner": {"login": "user1", "name": "User One"},
                "namespace": {"type": "personal", "path": "user1"},
                "private": False,
                "public": True
            },
            {
                "full_name": "orgA/test_repo",
                "created_at": "2026-02-01T10:00:00+08:00",
                "updated_at": "2026-02-02T10:00:00+08:00",
                "pushed_at": "2026-02-03T10:00:00+08:00",
                "owner": {"login": "orgA", "name": "Org A"},
                "namespace": {"type": "organization", "path": "orgA"},
                "private": False,
                "public": True
            }
        ]
        subscribers = [
            {
                "login": "user1",
                "name": "User One",
                "watch_at": "2026-03-03T10:00:00+08:00"
            },
            {
                "login": "user2",
                "name": "User Two",
                "watch_at": "2026-02-01T10:00:00+08:00"
            }
        ]
        languages = {
            "Python": 60,
            "JavaScript": 30,
            "Shell": 10
        }

        result = stats.analyze_stats(download_data, forks, subscribers, languages)

        assert result["download_stats"]["period_total"] == 25
        assert result["download_stats"]["daily_average"] == 8.33
        assert result["download_stats"]["peak_count"] == 10
        assert result["download_stats"]["active_days"] == 3
        assert result["download_stats"]["active_days_rate"] == 100.0
        assert len(result["download_stats"]["top_days"]) == 3
        assert "2026-03-01" in result["download_stats"]["daily_trend"]

        assert result["fork_stats"]["total"] == 2
        assert result["fork_stats"]["unique_fork_owners"] == 2
        assert result["fork_stats"]["personal_forks"] == 1
        assert result["fork_stats"]["organization_forks"] == 1
        assert len(result["fork_stats"]["latest_forks"]) == 2
        assert len(result["fork_list"]) == 2
        assert len(result["fork_stats"]["top_fork_users"]) == 2
        assert "2026-03-03" in result["fork_stats"]["daily_trend"]

        assert result["subscriber_stats"]["total"] == 2
        assert result["subscriber_stats"]["new_in_period"] == 1
        assert len(result["subscriber_stats"]["latest_subscribers"]) == 2
        assert len(result["subscriber_list"]) == 2

        assert result["language_stats"]["total_languages"] == 3
        assert result["language_stats"]["primary_language"] == "Python"
        assert "Python" in result["language_stats"]["languages"]

    def test_generate_markdown_and_html_report(self):
        """测试 repo-stats 生成 Markdown 和 HTML 报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = GitCodeRepoStats(
                repo="test_repo",
                token="test_token",
                owner="test_owner",
                output_dir=tmpdir
            )

            data = {
                "repo": "test_owner/test_repo",
                "analysis_period": "近 30 天",
                "analysis_time": "2026-03-19 11:00:00",
                "download_stats": {
                    "period_total": 25,
                    "history_total": 120,
                    "daily_average": 8.33,
                    "active_days": 3,
                    "active_days_rate": 100.0,
                    "trend": "up",
                    "daily_trend": {"2026-03-03": 10},
                    "top_days": [{"date": "2026-03-03", "count": 10, "total": 120}],
                    "details": [{"pdate": "2026-03-03", "today_dl_cnt": 10, "total_dl_cnt": 120}]
                },
                "fork_stats": {
                    "total": 2,
                    "new_in_period": 1,
                    "unique_fork_owners": 2,
                    "personal_forks": 1,
                    "organization_forks": 1,
                    "daily_trend": {"2026-03-03": 1},
                    "latest_fork": {"full_name": "user1/test_repo", "created_at": "2026-03-03T10:00:00+08:00"},
                    "top_fork_users": [{"owner": "user1", "count": 1, "latest_created_at": "2026-03-03T10:00:00+08:00"}],
                    "latest_forks": [{"full_name": "user1/test_repo", "owner": "user1", "namespace_type": "personal", "created_at": "2026-03-03T10:00:00+08:00", "pushed_at": "2026-03-05T10:00:00+08:00"}]
                },
                "subscriber_stats": {
                    "total": 5,
                    "new_in_period": 2,
                    "latest_subscribers": [{"login": "user1", "name": "User One", "watch_at": "2026-03-03T10:00:00+08:00"}],
                    "daily_trend": {"2026-03-03": 1}
                },
                "language_stats": {
                    "total_languages": 3,
                    "primary_language": "Python",
                    "languages": {"Python": 60, "JavaScript": 30, "Shell": 10}
                },
                "fork_list": [
                    {"full_name": "user1/test_repo", "owner": "user1", "namespace_type": "personal", "created_at": "2026-03-03T10:00:00+08:00", "pushed_at": "2026-03-05T10:00:00+08:00"}
                ],
                "subscriber_list": [
                    {"login": "user1", "name": "User One", "watch_at": "2026-03-03T10:00:00+08:00"}
                ]
            }

            md_file = os.path.join(tmpdir, "repo_stats_test_owner_test_repo_30d.md")
            html_file = os.path.join(tmpdir, "repo_stats_test_owner_test_repo_30d.html")

            stats.generate_markdown_report(data, md_file)
            stats.generate_html_report(data, html_file)

            assert os.path.exists(md_file)
            assert os.path.exists(html_file)

            with open(md_file, "r", encoding="utf-8") as f:
                md_content = f.read()
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()

            assert "仓库统计报告" in md_content
            assert "下载峰值 Top 10" in md_content
            assert "Fork人员 Top 10" in md_content
            assert "订阅用户" in md_content
            assert "编程语言" in md_content
            assert "仓库统计报告" in html_content
            assert "Fork 统计" in html_content
            assert "下载峰值 Top 10" in html_content
            assert "订阅用户" in html_content

    def test_run_generates_three_output_files(self):
        """测试 run 生成 JSON/HTML/MD 三类文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = GitCodeRepoStats(
                repo="test_repo",
                token="test_token",
                owner="test_owner",
                output_dir=tmpdir
            )

            with patch.object(stats, "get_download_statistics", return_value={"download_statistics_detail": []}), \
                    patch.object(stats, "get_forks", return_value=[]), \
                    patch.object(stats, "get_subscribers", return_value=[]), \
                    patch.object(stats, "get_languages", return_value={}):
                result = stats.run()

            assert "download_stats" in result
            assert "fork_stats" in result
            assert "subscriber_stats" in result
            assert "language_stats" in result

            json_file = os.path.join(tmpdir, "repo_stats_test_owner_test_repo_30d.json")
            html_file = os.path.join(tmpdir, "repo_stats_test_owner_test_repo_30d.html")
            md_file = os.path.join(tmpdir, "repo_stats_test_owner_test_repo_30d.md")

            assert os.path.exists(json_file)
            assert os.path.exists(html_file)
            assert os.path.exists(md_file)

            with open(json_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # 新的 JSON 结构
            assert "statistics" in loaded
            assert "raw_data" in loaded
            assert "download_stats" in loaded["statistics"]
            assert "fork_stats" in loaded["statistics"]
            assert "subscriber_stats" in loaded["statistics"]
            assert "language_stats" in loaded["statistics"]

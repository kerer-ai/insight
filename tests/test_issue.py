# -*- coding: utf-8 -*-
"""
issue 模块测试
测试 GitCodeIssueInsight 类
"""

import os
import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from gitcode_insight.issue import GitCodeIssueInsight


class TestGitCodeIssueInsight:
    """测试 GitCodeIssueInsight 类"""

    def test_init_with_params(self, temp_output_dir):
        """使用参数初始化"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        assert insight.repo == "test-repo"
        assert insight.token == "test_token"
        assert insight.owner == "test_org"
        assert insight.days == 30
        assert insight.output_dir == temp_output_dir

    def test_init_default_owner(self, temp_output_dir):
        """测试从配置文件读取默认 owner"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            days=30,
            output_dir=temp_output_dir
        )

        # 当配置文件存在时，会读取配置文件中的 owner
        # 这里测试 owner 被正确设置（具体值取决于当前目录下的配置文件）
        assert isinstance(insight.owner, str)

    def test_is_within_range_true(self, temp_output_dir):
        """测试时间范围判断 - 在范围内"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        # 当前时间
        now = datetime.now(timezone.utc).isoformat()
        assert insight._is_within_range(now) is True

        # 10天前
        ten_days_ago = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        assert insight._is_within_range(ten_days_ago) is True

    def test_is_within_range_false(self, temp_output_dir):
        """测试时间范围判断 - 超出范围"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        # 40天前
        forty_days_ago = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        assert insight._is_within_range(forty_days_ago) is False

    def test_is_within_range_empty_string(self, temp_output_dir):
        """测试时间范围判断 - 空字符串"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        assert insight._is_within_range("") is False
        assert insight._is_within_range(None) is False

    def test_get_issues(self, temp_output_dir, sample_issue_data):
        """测试获取 Issue 列表"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            range_by="created",
            output_dir=temp_output_dir
        )

        with patch('gitcode_insight.issue.request_with_retry') as mock_request:
            mock_request.return_value = sample_issue_data

            with patch('builtins.print'):
                issues = insight.get_issues()

        assert len(issues) == 2
        assert issues[0]["number"] == 1

    def test_get_issues_range_by_active_includes_updated(self, temp_output_dir):
        """测试 active 口径包含近 N 天更新的旧 Issue"""
        now = datetime.now(timezone.utc)
        sample = [
            {
                "number": 1,
                "created_at": (now - timedelta(days=200)).isoformat(),
                "updated_at": (now - timedelta(days=1)).isoformat()
            },
            {
                "number": 2,
                "created_at": (now - timedelta(days=1)).isoformat(),
                "updated_at": (now - timedelta(days=1)).isoformat()
            }
        ]

        insight_created = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=3,
            range_by="created",
            output_dir=temp_output_dir
        )
        insight_active = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=3,
            range_by="active",
            output_dir=temp_output_dir
        )

        with patch('gitcode_insight.issue.request_with_retry') as mock_request:
            mock_request.return_value = sample
            with patch('builtins.print'):
                issues_created = insight_created.get_issues()
                issues_active = insight_active.get_issues()

        assert [i["number"] for i in issues_created] == [2]
        assert sorted([i["number"] for i in issues_active]) == [1, 2]

    def test_get_issue_comments(self, temp_output_dir, sample_issue_comments):
        """测试获取 Issue 评论"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        with patch('gitcode_insight.issue.request_with_retry') as mock_request:
            mock_request.return_value = sample_issue_comments

            comments = insight.get_issue_comments("1")

        assert len(comments) == 2
        assert comments[0]["user"]["login"] == "developer1"

    def test_get_issue_events(self, temp_output_dir):
        """测试获取 Issue 事件"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        mock_events = [
            {"event": "labeled", "label": {"name": "bug"}},
            {"event": "closed", "created_at": datetime.now(timezone.utc).isoformat()}
        ]

        with patch('gitcode_insight.issue.request_with_retry') as mock_request:
            mock_request.return_value = mock_events

            events = insight.get_issue_events("1")

        assert len(events) == 2

    def test_analyze_issue(self, temp_output_dir, sample_issue_data, sample_issue_comments):
        """测试分析单个 Issue"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        with patch.object(insight, 'get_issue_comments') as mock_comments:
            mock_comments.return_value = sample_issue_comments

            result = insight.analyze_issue(sample_issue_data[0])

        assert result["issue_number"] == 1
        assert result["state"] == "open"
        assert result["creator"] == "user1"
        assert result["labels"] == "bug"
        assert result["first_response_time"] is not None  # 有响应时间

    def test_analyze_issue_closed(self, temp_output_dir, sample_issue_data):
        """测试分析已关闭的 Issue"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        with patch.object(insight, 'get_issue_comments') as mock_comments:
            mock_comments.return_value = []

            result = insight.analyze_issue(sample_issue_data[1])

        assert result["issue_number"] == 2
        assert result["state"] == "closed"
        assert result["close_duration"] is not None  # 有关闭耗时

    def test_calculate_insights(self, temp_output_dir):
        """测试计算洞察指标"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        issues_data = [
            {
                "issue_number": 1,
                "title": "Bug 1",
                "state": "open",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": "",
                "creator": "user1",
                "labels": "bug",
                "comments_count": 2,
                "assignees": "dev1",
                "milestone": "",
                "html_url": "https://example.com/issues/1",
                "first_response_time": 120.0,
                "close_duration": None
            },
            {
                "issue_number": 2,
                "title": "Feature 1",
                "state": "closed",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
                "creator": "user2",
                "labels": "enhancement",
                "comments_count": 5,
                "assignees": "dev2",
                "milestone": "v1.0",
                "html_url": "https://example.com/issues/2",
                "first_response_time": 60.0,
                "close_duration": 2880.0  # 2 天
            }
        ]

        insights, raw_data = insight.calculate_insights(issues_data)

        assert insights["summary"]["total_issues"] == 2
        assert insights["summary"]["opened_issues"] == 1
        assert insights["summary"]["closed_issues"] == 1
        assert insights["summary"]["close_rate"] == 50.0
        assert insights["efficiency"]["avg_first_response_time_minutes"] == 90.0  # (120+60)/2
        assert insights["efficiency"]["avg_close_duration_hours"] == 48.0  # 2880/60
        assert len(raw_data) == 2

    def test_calculate_insights_empty(self, temp_output_dir):
        """测试计算洞察指标 - 空数据"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        insights, raw_data = insight.calculate_insights([])

        assert insights["summary"]["total_issues"] == 0
        assert insights["summary"]["close_rate"] == 0
        assert len(raw_data) == 0

    def test_calculate_insights_daily_trend_closed_on_different_day(self, temp_output_dir):
        """测试每日趋势 - Issue 在没有新 Issue 创建的日期被关闭"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        now = datetime.now(timezone.utc)
        # Issue 创建于 day1，关闭于 day3（day3 没有新 Issue 创建）
        issues_data = [
            {
                "issue_number": 1,
                "title": "Bug 1",
                "state": "closed",
                "created_at": (now - timedelta(days=5)).isoformat(),  # day1: 创建
                "updated_at": now.isoformat(),
                "finished_at": (now - timedelta(days=3)).isoformat(),  # day3: 关闭（该天无新 Issue）
                "creator": "user1",
                "labels": "bug",
                "comments_count": 1,
                "assignees": "",
                "milestone": "",
                "html_url": "https://example.com/issues/1",
                "first_response_time": 60.0,
                "close_duration": 2880.0  # 2 天
            },
            {
                "issue_number": 2,
                "title": "Feature 1",
                "state": "open",
                "created_at": (now - timedelta(days=5)).isoformat(),  # day1: 创建
                "updated_at": now.isoformat(),
                "finished_at": "",
                "creator": "user2",
                "labels": "enhancement",
                "comments_count": 0,
                "assignees": "",
                "milestone": "",
                "html_url": "https://example.com/issues/2",
                "first_response_time": None,
                "close_duration": None
            }
        ]

        insights, raw_data = insight.calculate_insights(issues_data)

        # 验证 daily_trend 包含关闭日期
        daily_trend = insights["daily_trend"]
        closed_dates = [date for date, counts in daily_trend.items() if counts["closed"] > 0]

        assert len(closed_dates) == 1  # 应该有 1 个关闭日期
        assert daily_trend[closed_dates[0]]["closed"] == 1  # 关闭计数应该正确

    def test_generate_html_report(self, temp_output_dir):
        """测试生成 HTML 报告"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        insights = {
            "repo": "test_org/test-repo",
            "analysis_period": "近 30 天",
            "analysis_time": "2024-01-01 12:00:00",
            "summary": {
                "total_issues": 10,
                "opened_issues": 5,
                "closed_issues": 5,
                "new_issues": 10,
                "close_rate": 50.0
            },
            "efficiency": {
                "avg_first_response_time_minutes": 60.0,
                "avg_close_duration_hours": 24.0,
                "timely_response_rate": 80.0,
                "response_time_samples": 10,
                "close_duration_samples": 5
            },
            "distribution": {
                "by_label": {"bug": 5, "enhancement": 3},
                "by_creator": {"user1": 4, "user2": 3}
            },
            "daily_trend": {
                "2024-01-01": {"created": 3, "closed": 1},
                "2024-01-02": {"created": 2, "closed": 2}
            }
        }

        output_file = os.path.join(temp_output_dir, "test_report.html")
        with patch('builtins.print'):
            insight.generate_html_report(insights, output_file)

        assert os.path.exists(output_file)

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Issue 洞察报告" in content
            assert "test_org/test-repo" in content

    def test_generate_markdown_report(self, temp_output_dir):
        """测试生成 Markdown 报告"""
        insight = GitCodeIssueInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        insights = {
            "repo": "test_org/test-repo",
            "analysis_period": "近 30 天",
            "analysis_time": "2024-01-01 12:00:00",
            "summary": {
                "total_issues": 10,
                "opened_issues": 5,
                "closed_issues": 5,
                "new_issues": 10,
                "close_rate": 50.0
            },
            "efficiency": {
                "avg_first_response_time_minutes": 60.0,
                "avg_close_duration_hours": 24.0,
                "timely_response_rate": 80.0,
                "response_time_samples": 10,
                "close_duration_samples": 5
            },
            "distribution": {
                "by_label": {"bug": 5, "enhancement": 3},
                "by_creator": {"user1": 4, "user2": 3}
            },
            "daily_trend": {
                "2024-01-01": {"created": 3, "closed": 1},
                "2024-01-02": {"created": 2, "closed": 2}
            }
        }

        output_file = os.path.join(temp_output_dir, "test_report.md")
        with patch('builtins.print'):
            insight.generate_markdown_report(insights, output_file)

        assert os.path.exists(output_file)

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "# Issue 洞察报告" in content
            assert "test_org/test-repo" in content
            assert "统计概览" in content
            assert "效率指标" in content


@pytest.mark.integration
class TestGitCodeIssueInsightIntegration:
    """集成测试 - 需要真实 API Token"""

    def test_get_issues_real_api(self, temp_output_dir, api_token):
        """真实 API 测试 - 获取 Issue 列表"""
        if not api_token:
            pytest.skip("GITCODE_TOKEN 环境变量未设置")

        insight = GitCodeIssueInsight(
            repo="test-repo",  # 需要替换为真实存在的仓库
            token=api_token,
            owner="test_org",  # 需要替换为真实的组织
            days=7,
            output_dir=temp_output_dir
        )

        with patch('builtins.print'):
            issues = insight.get_issues()

        assert isinstance(issues, list)
# -*- coding: utf-8 -*-
"""
pr 模块测试
测试 GitCodePRInsight 类
"""

import os
import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from gitcode_insight.pr import GitCodePRInsight


@pytest.fixture
def sample_pr_list_data():
    """示例 PR 列表数据"""
    now = datetime.now(timezone.utc)
    return [
        {
            "number": 1,
            "title": "Feature: Add new feature",
            "state": "opened",
            "draft": False,
            "locked": False,
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": now.isoformat(),
            "merged_at": None,
            "closed_at": None,
            "user": {"id": 1, "login": "user1"},
            "source_branch": "feature/new-feature",
            "target_branch": "main",
            "added_lines": 100,
            "removed_lines": 20,
            "notes": 3,
            "labels": [{"name": "enhancement"}],
            "assignees": [{"login": "reviewer1"}],
            "testers": [],
            "merged_by": None,
            "mergeable": True,
            "pipeline_status": "success",
            "html_url": "https://gitcode.com/test_org/test-repo/pull/1"
        },
        {
            "number": 2,
            "title": "Fix: Bug fix",
            "state": "closed",
            "draft": False,
            "locked": False,
            "created_at": (now - timedelta(days=10)).isoformat(),
            "updated_at": (now - timedelta(days=8)).isoformat(),
            "merged_at": (now - timedelta(days=8)).isoformat(),
            "closed_at": (now - timedelta(days=8)).isoformat(),
            "user": {"id": 2, "login": "user2"},
            "source_branch": "fix/bug",
            "target_branch": "main",
            "added_lines": 50,
            "removed_lines": 10,
            "notes": 2,
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "reviewer2"}],
            "testers": [],
            "merged_by": {"login": "merger1"},
            "mergeable": True,
            "pipeline_status": "success",
            "html_url": "https://gitcode.com/test_org/test-repo/pull/2"
        },
        {
            "number": 3,
            "title": "WIP: Draft PR",
            "state": "opened",
            "draft": True,
            "locked": False,
            "created_at": (now - timedelta(days=2)).isoformat(),
            "updated_at": now.isoformat(),
            "merged_at": None,
            "closed_at": None,
            "user": {"id": 1, "login": "user1"},
            "source_branch": "draft/feature",
            "target_branch": "main",
            "added_lines": 600,
            "removed_lines": 200,
            "notes": 0,
            "labels": [],
            "assignees": [],
            "testers": [],
            "merged_by": None,
            "mergeable": False,
            "pipeline_status": "pending",
            "html_url": "https://gitcode.com/test_org/test-repo/pull/3"
        }
    ]


@pytest.fixture
def sample_pr_comments():
    """示例 PR 评论数据"""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "user": {"id": 100, "login": "reviewer1"},
            "created_at": (now - timedelta(days=4)).isoformat(),
            "body": "Looks good to me!"
        },
        {
            "id": 2,
            "user": {"id": 1, "login": "user1"},
            "created_at": (now - timedelta(days=3)).isoformat(),
            "body": "Thanks for the review!"
        }
    ]


class TestGitCodePRInsight:
    """测试 GitCodePRInsight 类"""

    def test_init_with_params(self, temp_output_dir):
        """使用参数初始化"""
        insight = GitCodePRInsight(
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
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            days=30,
            output_dir=temp_output_dir
        )

        assert isinstance(insight.owner, str)

    def test_is_within_range_true(self, temp_output_dir):
        """测试时间范围判断 - 在范围内"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        now = datetime.now(timezone.utc).isoformat()
        assert insight._is_within_range(now) is True

        ten_days_ago = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        assert insight._is_within_range(ten_days_ago) is True

    def test_is_within_range_false(self, temp_output_dir):
        """测试时间范围判断 - 超出范围"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        forty_days_ago = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        assert insight._is_within_range(forty_days_ago) is False

    def test_is_within_range_empty_string(self, temp_output_dir):
        """测试时间范围判断 - 空字符串"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        assert insight._is_within_range("") is False
        assert insight._is_within_range(None) is False

    def test_get_prs(self, temp_output_dir, sample_pr_list_data):
        """测试获取 PR 列表"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        with patch('gitcode_insight.pr.request_with_retry') as mock_request:
            mock_request.return_value = sample_pr_list_data

            with patch('builtins.print'):
                prs = insight.get_prs()

        assert len(prs) == 3
        assert prs[0]["number"] == 1

    def test_get_pr_comments(self, temp_output_dir, sample_pr_comments):
        """测试获取 PR 评论"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        with patch('gitcode_insight.pr.request_with_retry') as mock_request:
            mock_request.return_value = sample_pr_comments

            comments = insight.get_pr_comments(1)

        assert len(comments) == 2
        assert comments[0]["user"]["login"] == "reviewer1"

    def test_analyze_pr(self, temp_output_dir, sample_pr_list_data, sample_pr_comments):
        """测试分析单个 PR"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        with patch.object(insight, 'get_pr_comments') as mock_comments:
            mock_comments.return_value = sample_pr_comments

            result = insight.analyze_pr(sample_pr_list_data[0])

        assert result["pr_number"] == 1
        assert result["state"] == "opened"
        assert result["creator"] == "user1"
        assert result["target_branch"] == "main"
        assert result["total_changes"] == 120  # 100 + 20
        assert result["first_review_time"] is not None

    def test_analyze_pr_merged(self, temp_output_dir, sample_pr_list_data):
        """测试分析已合并的 PR"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        with patch.object(insight, 'get_pr_comments') as mock_comments:
            mock_comments.return_value = []

            result = insight.analyze_pr(sample_pr_list_data[1])

        assert result["pr_number"] == 2
        assert result["merged_by"] == "merger1"
        assert result["merge_duration"] is not None

    def test_analyze_pr_draft(self, temp_output_dir, sample_pr_list_data):
        """测试分析草稿 PR"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        with patch.object(insight, 'get_pr_comments') as mock_comments:
            mock_comments.return_value = []

            result = insight.analyze_pr(sample_pr_list_data[2])

        assert result["pr_number"] == 3
        assert result["draft"] is True
        assert result["total_changes"] == 800  # 600 + 200
        assert result["mergeable"] is False

    def test_calculate_insights(self, temp_output_dir):
        """测试计算洞察指标"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        now = datetime.now(timezone.utc)
        prs_data = [
            {
                "pr_number": 1,
                "title": "Feature 1",
                "state": "opened",
                "draft": False,
                "locked": False,
                "created_at": (now - timedelta(days=5)).isoformat(),
                "updated_at": now.isoformat(),
                "merged_at": None,
                "closed_at": None,
                "creator": "user1",
                "source_branch": "feature/1",
                "target_branch": "main",
                "added_lines": 100,
                "removed_lines": 20,
                "total_changes": 120,
                "notes_count": 3,
                "labels": "enhancement",
                "assignees": "reviewer1",
                "testers": "",
                "merged_by": "",
                "mergeable": True,
                "pipeline_status": "success",
                "html_url": "https://example.com/pull/1",
                "first_review_time": 120.0,
                "merge_duration": None,
                "close_duration": None,
                "open_days": 5.0
            },
            {
                "pr_number": 2,
                "title": "Fix 1",
                "state": "closed",
                "draft": False,
                "locked": False,
                "created_at": (now - timedelta(days=10)).isoformat(),
                "updated_at": (now - timedelta(days=8)).isoformat(),
                "merged_at": (now - timedelta(days=8)).isoformat(),
                "closed_at": (now - timedelta(days=8)).isoformat(),
                "creator": "user2",
                "source_branch": "fix/1",
                "target_branch": "main",
                "added_lines": 50,
                "removed_lines": 10,
                "total_changes": 60,
                "notes_count": 2,
                "labels": "bug",
                "assignees": "reviewer2",
                "testers": "",
                "merged_by": "merger1",
                "mergeable": True,
                "pipeline_status": "success",
                "html_url": "https://example.com/pull/2",
                "first_review_time": 60.0,
                "merge_duration": 2880.0,  # 2 天
                "close_duration": None,
                "open_days": None
            }
        ]

        result = insight.calculate_insights(prs_data)

        assert result["summary"]["total_prs"] == 2
        assert result["summary"]["opened_prs"] == 1
        assert result["summary"]["merged_prs"] == 1
        assert result["summary"]["merge_rate"] == 50.0
        assert result["efficiency"]["avg_first_review_time_minutes"] == 90.0
        assert result["quality"]["avg_change_lines"] == 90.0

    def test_calculate_insights_empty(self, temp_output_dir):
        """测试计算洞察指标 - 空数据"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        result = insight.calculate_insights([])

        assert result["summary"]["total_prs"] == 0
        assert result["summary"]["merge_rate"] == 0

    def test_save_to_csv(self, temp_output_dir):
        """测试保存 CSV 文件"""
        insight = GitCodePRInsight(
            repo="test-repo",
            token="test_token",
            owner="test_org",
            days=30,
            output_dir=temp_output_dir
        )

        prs_data = [
            {
                "pr_number": 1,
                "title": "Test PR",
                "state": "opened",
                "draft": False,
                "locked": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "merged_at": "",
                "closed_at": "",
                "creator": "user1",
                "source_branch": "feature/test",
                "target_branch": "main",
                "added_lines": 100,
                "removed_lines": 20,
                "total_changes": 120,
                "notes_count": 3,
                "labels": "enhancement",
                "assignees": "reviewer1",
                "testers": "",
                "merged_by": "",
                "mergeable": True,
                "pipeline_status": "success",
                "html_url": "https://example.com/pull/1",
                "first_review_time": 60.0,
                "merge_duration": None,
                "close_duration": None,
                "open_days": None
            }
        ]

        output_file = os.path.join(temp_output_dir, "test_prs.csv")
        with patch('builtins.print'):
            insight.save_to_csv(prs_data, output_file)

        assert os.path.exists(output_file)

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            assert "Test PR" in content
            assert "user1" in content

    def test_generate_html_report(self, temp_output_dir):
        """测试生成 HTML 报告"""
        insight = GitCodePRInsight(
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
                "total_prs": 10,
                "opened_prs": 3,
                "merged_prs": 6,
                "closed_prs": 1,
                "draft_prs": 2,
                "merge_rate": 60.0,
                "draft_rate": 20.0,
                "conflict_rate": 10.0
            },
            "efficiency": {
                "avg_first_review_time_minutes": 120.0,
                "avg_merge_duration_hours": 24.0,
                "avg_open_days": 3.5,
                "timely_review_rate": 80.0
            },
            "quality": {
                "avg_change_lines": 150.0,
                "large_pr_count": 2,
                "large_pr_rate": 20.0,
                "comment_density": 0.05,
                "ci_success_count": 8,
                "ci_success_rate": 80.0,
                "ci_stats": {"success": 8, "pending": 2}
            },
            "distribution": {
                "by_creator": {"user1": 5, "user2": 3},
                "by_target_branch": {"main": 8, "develop": 2},
                "by_label": {"enhancement": 4, "bug": 3},
                "by_reviewer": {"reviewer1": 5},
                "by_merger": {"merger1": 6}
            },
            "daily_trend": {
                "2024-01-01": {"created": 2, "merged": 1, "closed": 0},
                "2024-01-02": {"created": 3, "merged": 2, "closed": 1}
            },
            "prs": []
        }

        output_file = os.path.join(temp_output_dir, "test_report.html")
        with patch('builtins.print'):
            insight.generate_html_report(insights, output_file)

        assert os.path.exists(output_file)

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "PR 洞察报告" in content
            assert "test_org/test-repo" in content


@pytest.mark.integration
class TestGitCodePRInsightIntegration:
    """集成测试 - 需要真实 API Token"""

    def test_get_prs_real_api(self, temp_output_dir, api_token):
        """真实 API 测试 - 获取 PR 列表"""
        if not api_token:
            pytest.skip("GITCODE_TOKEN 环境变量未设置")

        insight = GitCodePRInsight(
            repo="test-repo",
            token=api_token,
            owner="test_org",
            days=7,
            output_dir=temp_output_dir
        )

        with patch('builtins.print'):
            prs = insight.get_prs()

        assert isinstance(prs, list)
# -*- coding: utf-8 -*-
"""
community 模块测试
测试 GitCodeCommunityStats 类
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from gitcode_insight.community import GitCodeCommunityStats


class TestGitCodeCommunityStats:
    """测试 GitCodeCommunityStats 类"""

    def test_init_with_config_file(self, temp_config_file, temp_output_dir):
        """使用配置文件初始化"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        assert stats.access_token == "test_token_123"
        assert stats.owner == "test_org"
        assert stats.label_ci_success == "ci-pipeline-passed"
        assert stats.output_dir == temp_output_dir

    def test_get_community_projects(self, temp_config_file, temp_output_dir):
        """测试获取项目列表"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        mock_projects = [
            {"name": "project1", "path": "project1"},
            {"name": "project2", "path": "project2"}
        ]

        with patch.object(stats, 'session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_projects
            mock_response.raise_for_status = Mock()
            mock_session.get.return_value = mock_response

            with patch('gitcode_insight.utils.time.sleep'):
                result = stats.get_community_projects(page=1, per_page=20)

        assert result == mock_projects

    def test_get_project_contributors(self, temp_config_file, temp_output_dir, sample_contributors_data):
        """测试获取贡献者列表"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        with patch('gitcode_insight.community.request_with_retry') as mock_request:
            mock_request.return_value = sample_contributors_data

            result = stats.get_project_contributors("test-project")

        assert len(result) == 3
        assert result[0]["login"] == "user1"

    def test_get_project_contributors_empty(self, temp_config_file, temp_output_dir):
        """测试获取贡献者返回空列表"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        with patch('gitcode_insight.community.request_with_retry') as mock_request:
            mock_request.return_value = None

            result = stats.get_project_contributors("test-project")

        assert result == []

    def test_get_project_merge_requests(self, temp_config_file, temp_output_dir, sample_pr_data):
        """测试获取 PR 列表"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        with patch('gitcode_insight.community.request_with_retry') as mock_request:
            mock_request.return_value = sample_pr_data

            with patch('gitcode_insight.community.time.sleep'):
                result = stats.get_project_merge_requests("test-project", days=30)

        assert len(result) == 3
        assert result[0]["number"] == 1

    def test_get_30_days_prs(self, temp_config_file, temp_output_dir):
        """测试筛选 30 天内的 PR"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        now = datetime.now(timezone.utc)
        all_prs = [
            {"number": 1, "created_at": (now - timedelta(days=5)).isoformat()},
            {"number": 2, "created_at": (now - timedelta(days=40)).isoformat()},  # 超过30天
            {"number": 3, "created_at": (now - timedelta(days=15)).isoformat()}
        ]

        result = stats.get_30_days_prs(all_prs)

        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[1]["number"] == 3

    def test_get_7_days_prs(self, temp_config_file, temp_output_dir):
        """测试统计 7 天内的 PR 数量"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        now = datetime.now(timezone.utc)
        all_prs = [
            {"number": 1, "created_at": (now - timedelta(days=3)).isoformat()},
            {"number": 2, "created_at": (now - timedelta(days=10)).isoformat()},  # 超过7天
            {"number": 3, "created_at": (now - timedelta(days=5)).isoformat()}
        ]

        result = stats.get_7_days_prs(all_prs)

        assert result == 2

    def test_calculate_gatekeeper_duration_with_ci_passed(self, temp_config_file, temp_output_dir, sample_pr_events_data):
        """测试门禁时长计算 - 有 CI 通过"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        with patch.object(stats, 'get_pr_events') as mock_events:
            mock_events.return_value = sample_pr_events_data

            result = stats.calculate_gatekeeper_duration("test-project", 1)

        assert result is not None
        assert result["blue_ci_flag"] is True
        assert result["duration_minutes"] > 0

    def test_calculate_gatekeeper_duration_no_ci_passed(self, temp_config_file, temp_output_dir):
        """测试门禁时长计算 - 无 CI 通过"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        events_without_passed = [
            {
                "action": "enterprise_label",
                "content": "add label ci-pipeline-running",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "user": {"id": 100}
            }
        ]

        with patch.object(stats, 'get_pr_events') as mock_events:
            mock_events.return_value = events_without_passed

            result = stats.calculate_gatekeeper_duration("test-project", 1)

        assert result is not None
        assert result["blue_ci_flag"] is False
        assert result["duration_minutes"] == 0

    def test_calculate_gatekeeper_duration_no_events(self, temp_config_file, temp_output_dir):
        """测试门禁时长计算 - 无事件"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        with patch.object(stats, 'get_pr_events') as mock_events:
            mock_events.return_value = []

            result = stats.calculate_gatekeeper_duration("test-project", 1)

        assert result is None

    def test_save_to_csv(self, temp_config_file, temp_output_dir, sample_community_stats):
        """测试保存 CSV 文件"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        output_file = os.path.join(temp_output_dir, "test_stats.csv")
        stats.save_to_csv(sample_community_stats, filename=output_file)

        assert os.path.exists(output_file)

        # 读取并验证内容
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            assert "project1" in content
            assert "project2" in content

    def test_save_to_json(self, temp_config_file, temp_output_dir, sample_community_stats):
        """测试保存 JSON 文件"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        output_file = os.path.join(temp_output_dir, "test_stats.json")
        stats.save_to_json(sample_community_stats, filename=output_file)

        assert os.path.exists(output_file)

        # 读取并验证内容
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data["total_repos"] == 2
            assert "project1" in data["project_stats"]

    def test_analyze_project_stats(self, temp_config_file, temp_output_dir, sample_contributors_data, sample_pr_data):
        """测试分析项目统计"""
        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)

        with patch.object(stats, 'get_project_contributors') as mock_contrib:
            with patch.object(stats, 'get_project_contributor_year') as mock_contrib_year:
                with patch.object(stats, 'get_project_merge_requests') as mock_prs:
                    mock_contrib.return_value = sample_contributors_data
                    mock_contrib_year.return_value = sample_contributors_data[:2]
                    mock_prs.return_value = sample_pr_data

                    with patch.object(stats, 'calculate_gatekeeper_duration') as mock_gate:
                        mock_gate.return_value = {
                            "yellow_ci_flag": True,
                            "blue_ci_flag": True,
                            "duration_minutes": 60.0
                        }

                        with patch('builtins.print'):
                            result = stats.analyze_project_stats("test-project")

        assert result["contributor_count"] == 3
        assert result["total_pr_count"] == 3
        assert result["yellow_ci_flag"] is True
        assert result["blue_ci_flag"] is True


@pytest.mark.integration
class TestGitCodeCommunityStatsIntegration:
    """集成测试 - 需要真实 API Token"""

    def test_get_community_projects_real_api(self, temp_config_file, temp_output_dir, api_token):
        """真实 API 测试 - 获取项目列表"""
        if not api_token:
            pytest.skip("GITCODE_TOKEN 环境变量未设置")

        # 更新配置文件使用真实 token
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config["access_token"] = api_token
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f)

        stats = GitCodeCommunityStats(config_file=temp_config_file, output_dir=temp_output_dir)
        projects = stats.get_community_projects(page=1, per_page=5)

        assert isinstance(projects, list)
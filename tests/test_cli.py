# -*- coding: utf-8 -*-
"""
cli 模块测试
测试命令行入口和参数解析
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from gitcode_insight.cli import main, cmd_community, cmd_issue, cmd_dashboard, get_config_owner


class TestGetConfigOwner:
    """测试 get_config_owner 函数"""

    def test_get_owner_from_config(self, temp_config_file):
        """从配置文件获取 owner"""
        owner = get_config_owner(temp_config_file)
        assert owner == "test_org"

    def test_get_owner_missing_config(self):
        """配置文件不存在"""
        owner = get_config_owner("/nonexistent/config.json")
        assert owner == ""

    def test_get_owner_missing_key(self, temp_output_dir):
        """配置文件中缺少 owner 键"""
        config = {"access_token": "test_token"}
        config_path = os.path.join(temp_output_dir, "config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f)

        owner = get_config_owner(config_path)
        assert owner == ""


class TestCmdCommunity:
    """测试 community 子命令"""

    def test_cmd_community_calls_stats(self, temp_config_file, temp_output_dir):
        """测试 community 命令调用统计功能"""
        args = Mock()
        args.config = temp_config_file
        args.output = temp_output_dir

        mock_stats = Mock()
        mock_stats.crawl_community_stats.return_value = {"total_repos": 1}
        mock_stats.generate_report = Mock()
        mock_stats.save_to_csv = Mock()
        mock_stats.save_to_json = Mock()

        with patch('gitcode_insight.cli.GitCodeCommunityStats') as MockClass:
            MockClass.return_value = mock_stats

            with patch('builtins.print'):
                cmd_community(args)

        mock_stats.crawl_community_stats.assert_called_once()
        mock_stats.generate_report.assert_called_once()
        mock_stats.save_to_csv.assert_called_once()
        mock_stats.save_to_json.assert_called_once()


class TestCmdIssue:
    """测试 issue 子命令"""

    def test_cmd_issue_calls_insight(self, temp_output_dir):
        """测试 issue 命令调用洞察功能"""
        args = Mock()
        args.repo = "test-repo"
        args.token = "test_token"
        args.owner = "test_org"
        args.days = 30
        args.output = temp_output_dir

        mock_insight = Mock()
        mock_insight.run.return_value = {}

        with patch('gitcode_insight.cli.GitCodeIssueInsight') as MockClass:
            MockClass.return_value = mock_insight

            cmd_issue(args)

        mock_insight.run.assert_called_once()

    def test_cmd_issue_passes_correct_params(self, temp_output_dir):
        """测试 issue 命令传递正确参数"""
        args = Mock()
        args.repo = "my-repo"
        args.token = "my_token"
        args.owner = "my_org"
        args.days = 60
        args.output = temp_output_dir

        with patch('gitcode_insight.cli.GitCodeIssueInsight') as MockClass:
            mock_instance = Mock()
            MockClass.return_value = mock_instance

            cmd_issue(args)

            MockClass.assert_called_once_with(
                repo="my-repo",
                token="my_token",
                owner="my_org",
                days=60,
                output_dir=temp_output_dir
            )


class TestCmdDashboard:
    """测试 dashboard 子命令"""

    def test_cmd_dashboard_with_existing_data(self, temp_config_file, temp_output_dir, sample_community_stats):
        """测试 dashboard 命令 - 数据已存在"""
        # 创建数据文件
        owner = "test_org"
        json_file = os.path.join(temp_output_dir, f"{owner}_community_stats_detailed.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_community_stats, f)

        args = Mock()
        args.config = temp_config_file
        args.output = temp_output_dir

        with patch('gitcode_insight.cli.generate_dashboard') as mock_gen:
            with patch('builtins.print'):
                cmd_dashboard(args)

        mock_gen.assert_called_once_with(
            config_file=temp_config_file,
            output_dir=temp_output_dir
        )

    def test_cmd_dashboard_auto_collects_data(self, temp_config_file, temp_output_dir):
        """测试 dashboard 命令 - 自动采集数据"""
        args = Mock()
        args.config = temp_config_file
        args.output = temp_output_dir

        mock_stats = Mock()
        mock_stats.crawl_community_stats.return_value = {"total_repos": 1}
        mock_stats.generate_report = Mock()
        mock_stats.save_to_csv = Mock()
        mock_stats.save_to_json = Mock()

        with patch('gitcode_insight.cli.GitCodeCommunityStats') as MockStats:
            with patch('gitcode_insight.cli.generate_dashboard') as mock_gen:
                with patch('builtins.print'):
                    MockStats.return_value = mock_stats
                    cmd_dashboard(args)

        # 应该调用采集
        mock_stats.crawl_community_stats.assert_called_once()
        mock_stats.save_to_json.assert_called_once()
        # 应该生成看板
        mock_gen.assert_called_once()


class TestMain:
    """测试 main 入口函数"""

    def test_main_no_command_shows_help(self):
        """无子命令时显示帮助"""
        with patch('sys.argv', ['gc-insight']):
            with patch('builtins.print') as mock_print:
                main()
                # main() 会调用 print_help() 而不是抛出 SystemExit

    def test_main_community_command(self, temp_config_file, temp_output_dir):
        """测试 community 子命令解析"""
        mock_stats = Mock()
        mock_stats.crawl_community_stats.return_value = {"total_repos": 0}
        mock_stats.generate_report = Mock()
        mock_stats.save_to_csv = Mock()
        mock_stats.save_to_json = Mock()

        with patch('sys.argv', [
            'gc-insight', 'community',
            '--config', temp_config_file,
            '--output', temp_output_dir
        ]):
            with patch('gitcode_insight.cli.GitCodeCommunityStats') as MockClass:
                with patch('builtins.print'):
                    MockClass.return_value = mock_stats
                    main()

        MockClass.assert_called_once()

    def test_main_issue_command(self, temp_output_dir):
        """测试 issue 子命令解析"""
        mock_insight = Mock()
        mock_insight.run.return_value = {}

        with patch('sys.argv', [
            'gc-insight', 'issue',
            '--repo', 'test-repo',
            '--token', 'test_token',
            '--owner', 'test_org',
            '--days', '30',
            '--output', temp_output_dir
        ]):
            with patch('gitcode_insight.cli.GitCodeIssueInsight') as MockClass:
                MockClass.return_value = mock_insight
                main()

        MockClass.assert_called_once()

    def test_main_dashboard_command(self, temp_config_file, temp_output_dir, sample_community_stats):
        """测试 dashboard 子命令解析"""
        # 创建数据文件
        owner = "test_org"
        json_file = os.path.join(temp_output_dir, f"{owner}_community_stats_detailed.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_community_stats, f)

        with patch('sys.argv', [
            'gc-insight', 'dashboard',
            '--config', temp_config_file,
            '--output', temp_output_dir
        ]):
            with patch('gitcode_insight.cli.generate_dashboard') as mock_gen:
                with patch('builtins.print'):
                    main()

        mock_gen.assert_called_once()


class TestArgumentParsing:
    """测试参数解析"""

    def test_community_default_params(self):
        """测试 community 默认参数"""
        import argparse
        from gitcode_insight.cli import main

        with patch('sys.argv', ['gc-insight', 'community']):
            with patch('gitcode_insight.cli.cmd_community') as mock_cmd:
                with patch('builtins.print'):
                    main()

                call_args = mock_cmd.call_args[0][0]
                assert call_args.config is None
                assert call_args.output is None

    def test_issue_required_params(self):
        """测试 issue 必需参数"""
        with patch('sys.argv', ['gc-insight', 'issue']):
            with pytest.raises(SystemExit):
                main()

    def test_issue_optional_params(self):
        """测试 issue 可选参数"""
        with patch('sys.argv', [
            'gc-insight', 'issue',
            '--repo', 'test-repo',
            '--token', 'test_token'
        ]):
            with patch('gitcode_insight.cli.cmd_issue') as mock_cmd:
                with patch('gitcode_insight.cli.GitCodeIssueInsight'):
                    main()

                call_args = mock_cmd.call_args[0][0]
                assert call_args.days == 30  # 默认值
                assert call_args.owner is None
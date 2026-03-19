# -*- coding: utf-8 -*-
"""
dashboard 模块测试
测试 generate_dashboard 和 generate_markdown_file 函数
"""

import os
import json
import pytest
from unittest.mock import patch

from gitcode_insight.dashboard import generate_dashboard, generate_markdown_file


class TestGenerateDashboard:
    """测试 generate_dashboard 函数"""

    def test_generate_html_file(self, temp_config_file, temp_output_dir, sample_community_stats):
        """测试生成 HTML 文件"""
        # 先创建数据文件
        owner = "test_org"
        json_file = os.path.join(temp_output_dir, f"{owner}_community_stats_detailed.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_community_stats, f)

        with patch('builtins.print'):
            generate_dashboard(config_file=temp_config_file, output_dir=temp_output_dir)

        # 检查 HTML 文件生成
        html_file = os.path.join(temp_output_dir, f"{owner}_community_dashboard.html")
        assert os.path.exists(html_file)

        # 验证 HTML 内容
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "test_org社区数字化看板" in content
            assert "project1" in content
            assert "project2" in content

    def test_generate_dashboard_missing_config(self, temp_output_dir):
        """测试配置文件不存在"""
        with patch('builtins.print') as mock_print:
            generate_dashboard(config_file="/nonexistent/config.json", output_dir=temp_output_dir)

        mock_print.assert_called()

    def test_generate_dashboard_missing_data(self, temp_config_file, temp_output_dir):
        """测试数据文件不存在"""
        with patch('builtins.print') as mock_print:
            generate_dashboard(config_file=temp_config_file, output_dir=temp_output_dir)

        # 应该打印错误信息
        assert any("错误" in str(call) for call in mock_print.call_args_list)


class TestGenerateMarkdownFile:
    """测试 generate_markdown_file 函数"""

    def test_generate_markdown_file(self, temp_output_dir, sample_community_stats):
        """测试生成 Markdown 文件"""
        owner = "test_org"
        current_time = "2024-01-20 10:00:00"

        with patch('builtins.print'):
            generate_markdown_file(
                sample_community_stats,
                owner,
                current_time,
                output_dir=temp_output_dir
            )

        # 检查 Markdown 文件生成
        md_file = os.path.join(temp_output_dir, f"{owner}_community_dashboard.md")
        assert os.path.exists(md_file)

        # 验证 Markdown 内容
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "# test_org社区数字化看板" in content
            assert "**统计时间**: 2024-01-20 10:00:00" in content
            assert "| 仓库总数 | 2 |" in content
            assert "project1" in content

    def test_markdown_contains_stats(self, temp_output_dir, sample_community_stats):
        """测试 Markdown 包含统计指标"""
        owner = "test_org"
        current_time = "2024-01-20 10:00:00"

        with patch('builtins.print'):
            generate_markdown_file(
                sample_community_stats,
                owner,
                current_time,
                output_dir=temp_output_dir
            )

        md_file = os.path.join(temp_output_dir, f"{owner}_community_dashboard.md")
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # 验证统计概览
            assert "## 统计概览" in content
            assert "总贡献者数" in content
            assert "总PR数" in content
            assert "30天内PR数" in content
            assert "平均门禁时长" in content

    def test_markdown_contains_top_projects(self, temp_output_dir, sample_community_stats):
        """测试 Markdown 包含 Top 项目"""
        owner = "test_org"
        current_time = "2024-01-20 10:00:00"

        with patch('builtins.print'):
            generate_markdown_file(
                sample_community_stats,
                owner,
                current_time,
                output_dir=temp_output_dir
            )

        md_file = os.path.join(temp_output_dir, f"{owner}_community_dashboard.md")
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # 验证 Top 项目部分
            assert "## Top 5 贡献者最多的仓库" in content
            assert "## Top 5 PR数量最多的仓库" in content

    def test_markdown_project_details(self, temp_output_dir, sample_community_stats):
        """测试 Markdown 包含项目详情表格"""
        owner = "test_org"
        current_time = "2024-01-20 10:00:00"

        with patch('builtins.print'):
            generate_markdown_file(
                sample_community_stats,
                owner,
                current_time,
                output_dir=temp_output_dir
            )

        md_file = os.path.join(temp_output_dir, f"{owner}_community_dashboard.md")
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # 验证项目详细统计表格
            assert "## 项目详细统计" in content
            assert "贡献者数量" in content
            assert "门禁类型" in content


class TestDashboardCalculations:
    """测试 dashboard 统计计算"""

    def test_calculate_total_stats(self, temp_output_dir, sample_community_stats):
        """测试计算总统计指标"""
        owner = "test_org"
        current_time = "2024-01-20 10:00:00"

        with patch('builtins.print'):
            generate_markdown_file(
                sample_community_stats,
                owner,
                current_time,
                output_dir=temp_output_dir
            )

        md_file = os.path.join(temp_output_dir, f"{owner}_community_dashboard.md")
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # 总贡献者数 = 10 + 5 = 15
            assert "| 总贡献者数 | 15 |" in content
            # 总PR数 = 50 + 30 = 80
            assert "| 总PR数（100天内） | 80 |" in content
            # 30天PR数 = 20 + 10 = 30
            assert "| 30天内PR数 | 30 |" in content

    def test_calculate_avg_gatekeeper_duration(self, temp_output_dir, sample_community_stats):
        """测试计算平均门禁时长"""
        owner = "test_org"
        current_time = "2024-01-20 10:00:00"

        with patch('builtins.print'):
            generate_markdown_file(
                sample_community_stats,
                owner,
                current_time,
                output_dir=temp_output_dir
            )

        md_file = os.path.join(temp_output_dir, f"{owner}_community_dashboard.md")
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # 平均门禁时长 = (15.5 + 20.0) / 2 = 17.75
            assert "| 平均门禁时长(分钟) | 17.75 |" in content

    def test_handle_empty_project_stats(self, temp_output_dir):
        """测试处理空项目统计数据"""
        owner = "test_org"
        current_time = "2024-01-20 10:00:00"

        empty_stats = {
            "total_repos": 0,
            "project_stats": {}
        }

        with patch('builtins.print'):
            generate_markdown_file(
                empty_stats,
                owner,
                current_time,
                output_dir=temp_output_dir
            )

        md_file = os.path.join(temp_output_dir, f"{owner}_community_dashboard.md")
        assert os.path.exists(md_file)

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "| 仓库总数 | 0 |" in content
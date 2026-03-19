# -*- coding: utf-8 -*-
"""
GitCode Report 模块测试
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch, mock_open

import pytest

from gitcode_insight.report import GitCodeReport


class TestGitCodeReport:
    """GitCodeReport 测试类"""

    def test_init_with_defaults(self):
        """测试使用默认参数初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(GitCodeReport, '_get_default_owner', return_value='test_owner'):
                report = GitCodeReport(
                    repo='test_repo',
                    token='test_token',
                    output_dir=tmpdir
                )

                assert report.repo == 'test_repo'
                assert report.token == 'test_token'
                assert report.owner == 'test_owner'
                assert report.days == 30
                assert report.output_dir == tmpdir

    def test_init_with_custom_params(self):
        """测试使用自定义参数初始化"""
        report = GitCodeReport(
            repo='test_repo',
            token='test_token',
            owner='custom_owner',
            days=60,
            output_dir='/custom/output'
        )

        assert report.repo == 'test_repo'
        assert report.token == 'test_token'
        assert report.owner == 'custom_owner'
        assert report.days == 60
        assert report.output_dir == '/custom/output'

    def test_get_default_owner_from_config(self):
        """测试从配置文件获取默认 owner"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config', 'gitcode.json')
            os.makedirs(os.path.dirname(config_file))
            with open(config_file, 'w') as f:
                json.dump({'owner': 'config_owner'}, f)

            with patch('os.getcwd', return_value=tmpdir):
                report = GitCodeReport(
                    repo='test_repo',
                    token='test_token',
                    output_dir=tmpdir
                )
                assert report.owner == 'config_owner'

    def test_check_or_collect_issue_existing_file(self):
        """测试检测到现有 Issue 数据文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建现有的 Issue 数据文件
            existing_data = {'summary': {'total_issues': 100}}
            issue_file = os.path.join(tmpdir, 'issue_insight_test_repo_30d.json')
            with open(issue_file, 'w') as f:
                json.dump(existing_data, f)

            report = GitCodeReport(
                repo='test_repo',
                token='test_token',
                owner='test_owner',
                output_dir=tmpdir
            )

            result = report._check_or_collect_issue()
            assert result == existing_data

    def test_check_or_collect_pr_existing_file(self):
        """测试检测到现有 PR 数据文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_data = {'summary': {'total_prs': 50}}
            pr_file = os.path.join(tmpdir, 'pr_insight_test_repo_30d.json')
            with open(pr_file, 'w') as f:
                json.dump(existing_data, f)

            report = GitCodeReport(
                repo='test_repo',
                token='test_token',
                owner='test_owner',
                output_dir=tmpdir
            )

            result = report._check_or_collect_pr()
            assert result == existing_data

    def test_check_or_collect_repo_stats_existing_file(self):
        """测试检测到现有仓库统计数据文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_data = {'download_stats': {'period_total': 1000}}
            stats_file = os.path.join(tmpdir, 'repo_stats_test_owner_test_repo_30d.json')
            with open(stats_file, 'w') as f:
                json.dump(existing_data, f)

            report = GitCodeReport(
                repo='test_repo',
                token='test_token',
                owner='test_owner',
                output_dir=tmpdir
            )

            result = report._check_or_collect_repo_stats()
            assert result == existing_data

    def test_collect_all_data(self):
        """测试采集所有数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = GitCodeReport(
                repo='test_repo',
                token='test_token',
                owner='test_owner',
                output_dir=tmpdir
            )

            # Mock 各个采集方法
            mock_issue_data = {'summary': {'total_issues': 10}}
            mock_pr_data = {'summary': {'total_prs': 5}}
            # repo_stats 现在包含订阅用户和编程语言数据
            mock_repo_stats_data = {
                'statistics': {
                    'download_stats': {'period_total': 100},
                    'fork_stats': {'total': 50},
                    'subscriber_stats': {'total': 20},
                    'language_stats': {'primary_language': 'Python'}
                },
                'raw_data': {
                    'fork_list': [],
                    'subscriber_list': []
                }
            }

            with patch.object(report, '_check_or_collect_issue', return_value=mock_issue_data), \
                 patch.object(report, '_check_or_collect_pr', return_value=mock_pr_data), \
                 patch.object(report, '_check_or_collect_repo_stats', return_value=mock_repo_stats_data):

                data = report.collect_all_data()

                assert data['repo'] == 'test_owner/test_repo'
                assert data['analysis_period'] == '近 30 天'
                assert data['issue'] == mock_issue_data
                assert data['pr'] == mock_pr_data
                assert data['repo_stats'] == {'download_stats': {'period_total': 100}, 'fork_stats': {'total': 50}}
                assert data['subscribers'] == {'subscriber_stats': {'total': 20}}
                assert data['languages'] == {'language_stats': {'primary_language': 'Python'}}

    def test_save_to_json(self):
        """测试保存 JSON 数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = GitCodeReport(
                repo='test_repo',
                token='test_token',
                owner='test_owner',
                output_dir=tmpdir
            )

            data = {
                'repo': 'test_owner/test_repo',
                'issue': {'summary': {'total_issues': 10}},
                'pr': {'summary': {'total_prs': 5}}
            }

            json_file = report.save_to_json(data)

            assert os.path.exists(json_file)
            assert json_file.endswith('report_test_owner_test_repo_30d.json')

            with open(json_file, 'r') as f:
                loaded = json.load(f)
            assert loaded == data

    def test_generate_html_report(self):
        """测试生成 HTML 报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = GitCodeReport(
                repo='test_repo',
                token='test_token',
                owner='test_owner',
                output_dir=tmpdir
            )

            data = {
                'repo': 'test_owner/test_repo',
                'analysis_time': '2024-01-01 12:00:00',
                'analysis_period': '近 30 天',
                'issue': {
                    'summary': {'total_issues': 10, 'close_rate': 80},
                    'efficiency': {'avg_first_response_time_minutes': 120},
                    'daily_trend': {'2024-01-01': {'created': 2, 'closed': 1}}
                },
                'pr': {
                    'summary': {'total_prs': 5, 'merge_rate': 60},
                    'efficiency': {'avg_first_review_time_minutes': 60},
                    'quality': {'avg_change_lines': 100, 'ci_success_rate': 90},
                    'daily_trend': {'2024-01-01': {'created': 1, 'merged': 1}}
                },
                'repo_stats': {
                    'download_stats': {'period_total': 1000, 'history_total': 5000, 'daily_average': 33.3},
                    'fork_stats': {'total': 50, 'new_in_period': 5}
                },
                'subscribers': {
                    'subscriber_stats': {'total': 100, 'new_in_period': 10}
                },
                'languages': {
                    'language_stats': {'total_languages': 3, 'primary_language': 'Python', 'languages': {'Python': 80, 'JavaScript': 15, 'Shell': 5}}
                }
            }

            html_file = os.path.join(tmpdir, 'test_report.html')
            report.generate_html_report(data, html_file)

            assert os.path.exists(html_file)

            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            assert '仓库综合报告' in content
            assert 'test_owner/test_repo' in content
            assert 'Issue 分析' in content
            assert 'PR 分析' in content

    def test_generate_markdown_report(self):
        """测试生成 Markdown 报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = GitCodeReport(
                repo='test_repo',
                token='test_token',
                owner='test_owner',
                output_dir=tmpdir
            )

            data = {
                'repo': 'test_owner/test_repo',
                'analysis_time': '2024-01-01 12:00:00',
                'analysis_period': '近 30 天',
                'issue': {
                    'summary': {'total_issues': 10, 'close_rate': 80, 'opened_issues': 2, 'closed_issues': 8},
                    'efficiency': {'avg_first_response_time_minutes': 120, 'avg_close_duration_hours': 24, 'timely_response_rate': 90}
                },
                'pr': {
                    'summary': {'total_prs': 5, 'merge_rate': 60, 'merged_prs': 3},
                    'efficiency': {'avg_first_review_time_minutes': 60, 'avg_merge_duration_hours': 12},
                    'quality': {'avg_change_lines': 100, 'large_pr_count': 1, 'ci_success_rate': 90}
                },
                'repo_stats': {
                    'download_stats': {'period_total': 1000, 'history_total': 5000, 'daily_average': 33.3},
                    'fork_stats': {'total': 50, 'new_in_period': 5}
                },
                'subscribers': {
                    'subscriber_stats': {'total': 100, 'new_in_period': 10}
                },
                'languages': {
                    'language_stats': {'total_languages': 3, 'primary_language': 'Python', 'languages': {'Python': 80, 'JavaScript': 15, 'Shell': 5}}
                }
            }

            md_file = os.path.join(tmpdir, 'test_report.md')
            report.generate_markdown_report(data, md_file)

            assert os.path.exists(md_file)

            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            assert '# 仓库综合报告' in content
            assert 'test_owner/test_repo' in content
            assert '## Issue 分析' in content
            assert '## PR 分析' in content
            assert 'Python: 80%' in content

    def test_run(self):
        """测试完整执行流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = GitCodeReport(
                repo='test_repo',
                token='test_token',
                owner='test_owner',
                output_dir=tmpdir
            )

            mock_data = {
                'repo': 'test_owner/test_repo',
                'analysis_time': '2024-01-01 12:00:00',
                'analysis_period': '近 30 天',
                'issue': {'summary': {}, 'efficiency': {}, 'daily_trend': {}},
                'pr': {'summary': {}, 'efficiency': {}, 'quality': {}, 'daily_trend': {}},
                'repo_stats': {'download_stats': {}, 'fork_stats': {}},
                'subscribers': {'subscriber_stats': {}},
                'languages': {'language_stats': {'languages': {}}}
            }

            with patch.object(report, 'collect_all_data', return_value=mock_data):
                result = report.run()

                assert result == mock_data

                # 检查输出文件
                json_file = os.path.join(tmpdir, 'report_test_owner_test_repo_30d.json')
                html_file = os.path.join(tmpdir, 'report_test_owner_test_repo_30d.html')
                md_file = os.path.join(tmpdir, 'report_test_owner_test_repo_30d.md')

                assert os.path.exists(json_file)
                assert os.path.exists(html_file)
                assert os.path.exists(md_file)


class TestGitCodeReportIntegration:
    """GitCodeReport 集成测试"""

    @pytest.mark.integration
    def test_full_report_generation(self):
        """测试完整的报告生成流程（需要真实 API Token）"""
        # 此测试需要真实的 API Token 和仓库信息
        # 在 CI 中跳过，仅本地测试
        pytest.skip("需要真实 API Token 的集成测试")

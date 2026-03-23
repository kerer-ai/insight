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
            mock_issue_data = {'statistics': {'summary': {'total_issues': 10}}, 'raw_data': []}
            mock_pr_data = {'statistics': {'summary': {'total_prs': 5}}, 'raw_data': []}
            # repo_stats.run() 返回扁平结构
            mock_repo_stats_data = {
                'download_stats': {'period_total': 100},
                'fork_stats': {'total': 50},
                'subscriber_stats': {'total': 20},
                'language_stats': {'primary_language': 'Python'}
            }

            with patch.object(report, '_collect_issue_data', return_value=mock_issue_data), \
                 patch.object(report, '_collect_pr_data', return_value=mock_pr_data), \
                 patch.object(report, '_collect_repo_stats_data', return_value=mock_repo_stats_data):

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
                    'statistics': {
                        'summary': {'total_issues': 10, 'close_rate': 80, 'opened_issues': 2, 'closed_issues': 8},
                        'efficiency': {'avg_first_response_time_minutes': 120, 'avg_close_duration_hours': 24, 'timely_response_rate': 90, 'response_time_samples': 8, 'close_duration_samples': 6},
                        'distribution': {'by_label': {'bug': 5, 'feature': 3}, 'by_creator': {'user1': 4, 'user2': 3}},
                        'daily_trend': {'2024-01-01': {'created': 2, 'closed': 1}}
                    },
                    'raw_data': []
                },
                'pr': {
                    'statistics': {
                        'summary': {'total_prs': 5, 'merge_rate': 60, 'opened_prs': 1, 'merged_prs': 3, 'closed_prs': 1, 'conflict_rate': 10},
                        'efficiency': {'avg_first_review_time_minutes': 60, 'avg_merge_duration_hours': 12, 'min_merge_duration_hours': 2, 'max_merge_duration_hours': 48, 'timely_review_rate': 80, 'review_time_samples': 4, 'merge_duration_samples': 3},
                        'quality': {'avg_change_lines': 100, 'max_change_lines': 500, 'large_pr_count': 1, 'large_pr_rate': 20, 'comment_density': 0.05, 'ci_success_rate': 90},
                        'distribution': {'by_creator': {'dev1': 2, 'dev2': 2}, 'by_target_branch': {'main': 4, 'develop': 1}, 'by_reviewer': {'reviewer1': 3}},
                        'daily_trend': {'2024-01-01': {'created': 1, 'merged': 1}}
                    },
                    'raw_data': []
                },
                'repo_stats': {
                    'download_stats': {'period_total': 1000, 'history_total': 5000, 'daily_average': 33.3, 'peak_date': '2024-01-15', 'peak_count': 100, 'active_days': 25, 'active_days_rate': 83.3, 'trend': 'up', 'top_days': [{'date': '2024-01-15', 'count': 100, 'total': 4500}]},
                    'fork_stats': {'total': 50, 'new_in_period': 5, 'unique_fork_owners': 45, 'personal_forks': 40, 'organization_forks': 10, 'top_fork_users': [{'owner': 'user1', 'count': 2, 'latest_created_at': '2024-01-20'}], 'latest_forks': [{'owner': 'user2', 'namespace_type': 'personal', 'created_at': '2024-01-25'}]}
                },
                'subscribers': {
                    'subscriber_stats': {'total': 100, 'new_in_period': 10, 'latest_subscribers': [{'login': 'sub1', 'name': 'Subscriber 1', 'watch_at': '2024-01-25'}]}
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
            # 验证数据正确映射
            assert '总 Issue 数' in content
            assert '10' in content  # total_issues
            # 验证新增字段
            assert 'Issue 分布分析' in content
            assert 'PR 分布分析' in content
            assert '冲突率' in content
            assert '最短合并' in content
            assert '最长合并' in content
            assert '24h评审率' in content
            assert '最大变更行' in content
            assert '大PR占比' in content
            assert '评论密度' in content
            assert '下载峰值日' in content
            assert '下载趋势' in content
            assert '个人 Fork' in content
            assert '组织 Fork' in content
            assert '最新 Fork 信息' in content
            assert '最新订阅用户' in content

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
                    'statistics': {
                        'summary': {'total_issues': 10, 'close_rate': 80, 'opened_issues': 2, 'closed_issues': 8},
                        'efficiency': {'avg_first_response_time_minutes': 120, 'avg_close_duration_hours': 24, 'timely_response_rate': 90, 'response_time_samples': 8, 'close_duration_samples': 6},
                        'distribution': {'by_label': {'bug': 5, 'feature': 3}, 'by_creator': {'user1': 4, 'user2': 3}}
                    },
                    'raw_data': []
                },
                'pr': {
                    'statistics': {
                        'summary': {'total_prs': 5, 'merge_rate': 60, 'merged_prs': 3, 'opened_prs': 1, 'closed_prs': 1, 'conflict_rate': 10},
                        'efficiency': {'avg_first_review_time_minutes': 60, 'avg_merge_duration_hours': 12, 'min_merge_duration_hours': 2, 'max_merge_duration_hours': 48, 'timely_review_rate': 80, 'review_time_samples': 4, 'merge_duration_samples': 3},
                        'quality': {'avg_change_lines': 100, 'max_change_lines': 500, 'large_pr_count': 1, 'large_pr_rate': 20, 'comment_density': 0.05, 'ci_success_rate': 90},
                        'distribution': {'by_creator': {'dev1': 2, 'dev2': 2}, 'by_target_branch': {'main': 4, 'develop': 1}, 'by_reviewer': {'reviewer1': 3}}
                    },
                    'raw_data': []
                },
                'repo_stats': {
                    'download_stats': {'period_total': 1000, 'history_total': 5000, 'daily_average': 33.3, 'peak_date': '2024-01-15', 'peak_count': 100, 'active_days': 25, 'active_days_rate': 83.3, 'trend': 'up', 'top_days': []},
                    'fork_stats': {'total': 50, 'new_in_period': 5, 'unique_fork_owners': 45, 'personal_forks': 40, 'organization_forks': 10, 'top_fork_users': [], 'latest_forks': []}
                },
                'subscribers': {
                    'subscriber_stats': {'total': 100, 'new_in_period': 10, 'latest_subscribers': []}
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
            # 验证数据正确映射
            assert '| 总 Issue 数 | 10 |' in content
            assert '| 总 PR 数 | 5 |' in content
            # 验证新增字段
            assert '### 标签分布' in content
            assert '### 创建人分布' in content
            assert '冲突率' in content
            assert '最短合并耗时' in content
            assert '最长合并耗时' in content
            assert '24小时评审率' in content
            assert '最大变更行数' in content
            assert '大 PR 占比' in content
            assert '评论密度' in content
            assert '下载峰值日' in content
            assert '下载趋势' in content
            assert '个人 Fork 数' in content
            assert '组织 Fork 数' in content
            assert '最新 Fork 信息' in content
            assert '最新订阅用户' in content

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
                'issue': {'statistics': {'summary': {}, 'efficiency': {}, 'distribution': {}, 'daily_trend': {}}, 'raw_data': []},
                'pr': {'statistics': {'summary': {}, 'efficiency': {}, 'quality': {}, 'distribution': {}, 'daily_trend': {}}, 'raw_data': []},
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

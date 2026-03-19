# -*- coding: utf-8 -*-
"""
pytest 配置和共享 fixtures
"""

import os
import json
import tempfile
import pytest


@pytest.fixture
def temp_output_dir():
    """临时输出目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_config_file(temp_output_dir):
    """测试用配置文件"""
    config = {
        "access_token": "test_token_123",
        "owner": "test_org",
        "label_ci_success": "ci-pipeline-passed",
        "label_ci_running": "ci-pipeline-running",
        "label_yellow_ci_running": "SC-RUNNING",
        "label_yellow_ci_success": "SC-SUCC"
    }
    config_path = os.path.join(temp_output_dir, "gitcode.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f)
    yield config_path


@pytest.fixture
def api_token():
    """从环境变量读取 API token"""
    return os.environ.get("GITCODE_TOKEN", "")


@pytest.fixture
def sample_project_data():
    """示例项目数据"""
    return {
        "name": "test-project",
        "path": "test-project",
        "html_url": "https://gitcode.com/test_org/test-project",
        "description": "A test project for unit testing"
    }


@pytest.fixture
def sample_contributors_data():
    """示例贡献者数据"""
    return [
        {"id": 1, "login": "user1", "contributions": 100},
        {"id": 2, "login": "user2", "contributions": 50},
        {"id": 3, "login": "user3", "contributions": 25}
    ]


@pytest.fixture
def sample_pr_data():
    """示例 PR 数据"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    return [
        {
            "number": 1,
            "title": "Feature: Add new feature",
            "state": "merged",
            "created_at": (now - timedelta(days=5)).isoformat(),
            "merged_at": (now - timedelta(days=4)).isoformat(),
            "closed_at": None,
            "user": {"id": 1, "login": "user1"}
        },
        {
            "number": 2,
            "title": "Fix: Bug fix",
            "state": "opened",
            "created_at": (now - timedelta(days=2)).isoformat(),
            "merged_at": None,
            "closed_at": None,
            "user": {"id": 2, "login": "user2"}
        },
        {
            "number": 3,
            "title": "Docs: Update README",
            "state": "closed",
            "created_at": (now - timedelta(days=10)).isoformat(),
            "merged_at": None,
            "closed_at": (now - timedelta(days=9)).isoformat(),
            "user": {"id": 3, "login": "user3"}
        }
    ]


@pytest.fixture
def sample_pr_events_data():
    """示例 PR 事件数据"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    running_time = (now - timedelta(hours=2)).isoformat()
    passed_time = (now - timedelta(hours=1)).isoformat()

    return [
        {
            "action": "enterprise_label",
            "content": "add label ci-pipeline-running",
            "created_at": running_time,
            "user": {"id": 100}
        },
        {
            "action": "enterprise_label",
            "content": "add label ci-pipeline-passed",
            "created_at": passed_time,
            "user": {"id": 100}
        }
    ]


@pytest.fixture
def sample_community_stats():
    """示例社区统计数据"""
    return {
        "total_repos": 2,
        "project_stats": {
            "project1": {
                "project_info": {
                    "name": "project1",
                    "url": "https://gitcode.com/test_org/project1",
                    "description": "First project"
                },
                "stats": {
                    "contributor_count": 10,
                    "contributor_count_year": 8,
                    "total_pr_count": 50,
                    "pr_count_7_days": 5,
                    "pr_count_30_days": 20,
                    "max_pr_count_30_days": 3,
                    "max_pr_date_30_days": "2024-01-15",
                    "avg_gatekeeper_duration": 15.5,
                    "max_duration": 45.0,
                    "max_duration_pr_url": "https://gitcode.com/test_org/project1/pull/123",
                    "avg_pr_close_duration": 1440.0,
                    "max_pr_close_duration": 2880.0,
                    "max_close_duration_pr_url": "https://gitcode.com/test_org/project1/pull/456",
                    "yellow_ci_flag": True,
                    "blue_ci_flag": True
                }
            },
            "project2": {
                "project_info": {
                    "name": "project2",
                    "url": "https://gitcode.com/test_org/project2",
                    "description": "Second project"
                },
                "stats": {
                    "contributor_count": 5,
                    "contributor_count_year": 4,
                    "total_pr_count": 30,
                    "pr_count_7_days": 2,
                    "pr_count_30_days": 10,
                    "max_pr_count_30_days": 2,
                    "max_pr_date_30_days": "2024-01-14",
                    "avg_gatekeeper_duration": 20.0,
                    "max_duration": 60.0,
                    "max_duration_pr_url": "https://gitcode.com/test_org/project2/pull/789",
                    "avg_pr_close_duration": 2160.0,
                    "max_pr_close_duration": 4320.0,
                    "max_close_duration_pr_url": "https://gitcode.com/test_org/project2/pull/101",
                    "yellow_ci_flag": False,
                    "blue_ci_flag": True
                }
            }
        }
    }


@pytest.fixture
def sample_issue_data():
    """示例 Issue 数据"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    return [
        {
            "number": 1,
            "title": "Bug: Something is broken",
            "state": "opened",
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": (now - timedelta(days=4)).isoformat(),
            "closed_at": None,
            "user": {"id": 1, "login": "user1"},
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "developer1"}],
            "comments": 2,
            "milestone": None,
            "html_url": "https://gitcode.com/test_org/test-project/issues/1"
        },
        {
            "number": 2,
            "title": "Feature: New feature request",
            "state": "closed",
            "created_at": (now - timedelta(days=10)).isoformat(),
            "updated_at": (now - timedelta(days=8)).isoformat(),
            "closed_at": (now - timedelta(days=8)).isoformat(),
            "user": {"id": 2, "login": "user2"},
            "labels": [{"name": "enhancement"}],
            "assignees": [],
            "assignee": {"login": "developer2"},
            "comments": 5,
            "milestone": {"title": "v1.0"},
            "html_url": "https://gitcode.com/test_org/test-project/issues/2"
        }
    ]


@pytest.fixture
def sample_issue_comments():
    """示例 Issue 评论数据"""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "user": {"id": 100, "login": "developer1"},
            "created_at": (now - timedelta(days=4, hours=12)).isoformat(),
            "body": "I'll look into this issue."
        },
        {
            "id": 2,
            "user": {"id": 1, "login": "user1"},
            "created_at": (now - timedelta(days=4)).isoformat(),
            "body": "Thanks for looking into it."
        }
    ]
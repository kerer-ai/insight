# -*- coding: utf-8 -*-
"""
utils 模块测试
测试 request_with_retry 和 request_with_retry_raw 函数
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from gitcode_insight.utils import request_with_retry, request_with_retry_raw


class TestRequestWithRetry:
    """测试 request_with_retry 函数"""

    def test_normal_request_returns_json(self):
        """正常请求返回 JSON 数据"""
        session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = Mock()
        session.get.return_value = mock_response

        with patch('gitcode_insight.utils.time.sleep'):
            result = request_with_retry(session, "https://api.example.com/test")

        assert result == {"key": "value"}
        session.get.assert_called_once()

    def test_rate_limit_429_retries(self):
        """429 限流时自动重试"""
        session = Mock()

        # 第一次返回 429，第二次返回正常
        mock_response_429 = Mock()
        mock_response_429.status_code = 429

        mock_response_ok = Mock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {"success": True}
        mock_response_ok.raise_for_status = Mock()

        session.get.side_effect = [mock_response_429, mock_response_ok]

        with patch('gitcode_insight.utils.time.sleep'):
            result = request_with_retry(
                session,
                "https://api.example.com/test",
                rate_limit_wait=1.0
            )

        assert result == {"success": True}
        assert session.get.call_count == 2

    def test_request_failure_retries(self):
        """请求失败时重试"""
        session = Mock()

        # 前两次失败，第三次成功
        mock_response_ok = Mock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {"success": True}
        mock_response_ok.raise_for_status = Mock()

        session.get.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            requests.exceptions.Timeout("Timeout"),
            mock_response_ok
        ]

        with patch('gitcode_insight.utils.time.sleep'):
            result = request_with_retry(
                session,
                "https://api.example.com/test",
                error_wait=0.1
            )

        assert result == {"success": True}
        assert session.get.call_count == 3

    def test_max_retries_returns_none(self):
        """达到最大重试次数后返回 None"""
        session = Mock()
        session.get.side_effect = requests.exceptions.ConnectionError("Network error")

        with patch('gitcode_insight.utils.time.sleep'):
            with patch('builtins.print'):
                result = request_with_retry(
                    session,
                    "https://api.example.com/test",
                    max_retries=2,
                    error_wait=0.1
                )

        assert result is None
        assert session.get.call_count == 2

    def test_params_passed_correctly(self):
        """参数正确传递给请求"""
        session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        session.get.return_value = mock_response

        params = {"key": "value", "page": 1}

        with patch('gitcode_insight.utils.time.sleep'):
            request_with_retry(session, "https://api.example.com/test", params=params)

        session.get.assert_called_once_with(
            "https://api.example.com/test",
            params=params
        )

    def test_none_params_converts_to_empty_dict(self):
        """None 参数转换为空字典"""
        session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        session.get.return_value = mock_response

        with patch('gitcode_insight.utils.time.sleep'):
            request_with_retry(session, "https://api.example.com/test", params=None)

        session.get.assert_called_once_with(
            "https://api.example.com/test",
            params={}
        )


class TestRequestWithRetryRaw:
    """测试 request_with_retry_raw 函数"""

    def test_returns_response_object(self):
        """返回原始 Response 对象"""
        session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        session.get.return_value = mock_response

        with patch('gitcode_insight.utils.time.sleep'):
            result = request_with_retry_raw(session, "https://api.example.com/test")

        assert result is mock_response

    def test_rate_limit_429_retries_raw(self):
        """429 限流时自动重试（raw 版本）"""
        session = Mock()

        mock_response_429 = Mock()
        mock_response_429.status_code = 429

        mock_response_ok = Mock()
        mock_response_ok.status_code = 200
        mock_response_ok.raise_for_status = Mock()

        session.get.side_effect = [mock_response_429, mock_response_ok]

        with patch('gitcode_insight.utils.time.sleep'):
            result = request_with_retry_raw(
                session,
                "https://api.example.com/test",
                rate_limit_wait=1.0
            )

        assert result is mock_response_ok
        assert session.get.call_count == 2

    def test_max_retries_returns_none_raw(self):
        """达到最大重试次数后返回 None（raw 版本）"""
        session = Mock()
        session.get.side_effect = requests.exceptions.ConnectionError("Network error")

        with patch('gitcode_insight.utils.time.sleep'):
            with patch('builtins.print'):
                result = request_with_retry_raw(
                    session,
                    "https://api.example.com/test",
                    max_retries=2,
                    error_wait=0.1
                )

        assert result is None
        assert session.get.call_count == 2
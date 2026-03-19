# -*- coding: utf-8 -*-
"""
公共工具模块
提供统一的请求重试、限流处理等功能
"""

import time
from typing import Optional, Dict, Any
import requests


def request_with_retry(
    session: requests.Session,
    url: str,
    params: Dict[str, Any] = None,
    max_retries: int = 3,
    request_interval: float = 0.6,
    rate_limit_wait: float = 5.0,
    error_wait: float = 3.0,
) -> Optional[Any]:
    """
    带重试机制的请求方法

    Args:
        session: requests Session 对象
        url: 请求 URL
        params: 请求参数
        max_retries: 最大重试次数
        request_interval: 请求养殖业（秒）
        rate_limit_wait: 限流等待时间（秒）
        error_wait: 错误等待时间（秒）

    Returns:
        响应 JSON 数据，失败返回 None
    """
    if params is None:
        params = {}

    for retry in range(max_retries):
        try:
            response = session.get(url, params=params)

            # 处理限流
            if response.status_code == 429:
                print(f"  触发限流，等待 {rate_limit_wait} 秒后重试...")
                time.sleep(rate_limit_wait)
                continue

            response.raise_for_status()
            time.sleep(request_interval)
            return response.json()

        except requests.exceptions.RequestException as e:
            if retry == max_retries - 1:
                print(f"  请求失败: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"  状态码: {e.response.status_code}")
                return None
            time.sleep(error_wait)

    return None


def request_with_retry_raw(
    session: requests.Session,
    url: str,
    params: Dict[str, Any] = None,
    max_retries: int = 3,
    request_interval: float = 0.6,
    rate_limit_wait: float = 5.0,
    error_wait: float = 3.0,
) -> Optional[requests.Response]:
    """
    带重试机制的请求方法（返回原始响应）

    Args:
        session: requests Session 对象
        url: 请求 URL
        params: 请求参数
        max_retries: 最大重试次数
        request_interval: 请求间隔（秒）
        rate_limit_wait: 限流等待时间（秒）
        error_wait: 错误等待时间（秒）

    Returns:
        requests Response 对象，失败返回 None
    """
    if params is None:
        params = {}

    for retry in range(max_retries):
        try:
            response = session.get(url, params=params)

            # 处理限流
            if response.status_code == 429:
                print(f"  触发限流，等待 {rate_limit_wait} 秒后重试...")
                time.sleep(rate_limit_wait)
                continue

            response.raise_for_status()
            time.sleep(request_interval)
            return response

        except requests.exceptions.RequestException as e:
            if retry == max_retries - 1:
                print(f"  请求失败: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"  状态码: {e.response.status_code}")
                return None
            time.sleep(error_wait)

    return None
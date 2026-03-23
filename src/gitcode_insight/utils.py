# -*- coding: utf-8 -*-
"""
公共工具模块
提供统一的请求重试、限流处理等功能
"""

import json
import os
import sys
import time
from typing import Optional, Dict, Any
import requests


def load_config(config_file: str) -> dict:
    """
    加载并验证配置文件

    Args:
        config_file: 配置文件路径

    Returns:
        配置字典

    Raises:
        SystemExit: 配置文件不存在、格式错误或必填项缺失时退出程序
    """
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"错误: 配置文件不存在")
        print(f"  路径: {config_file}")
        print(f"  请创建配置文件: cp config/gitcode.json.example config/gitcode.json")
        sys.exit(1)

    # 尝试解析 JSON 文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件格式错误")
        print(f"  路径: {config_file}")
        print(f"  详情: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 无法读取配置文件")
        print(f"  路径: {config_file}")
        print(f"  详情: {e}")
        sys.exit(1)

    # 验证必填项
    required_fields = ["access_token", "owner"]
    missing_fields = [field for field in required_fields if not config.get(field)]

    if missing_fields:
        print(f"错误: 配置文件缺少必填项")
        print(f"  路径: {config_file}")
        print(f"  缺失字段: {', '.join(missing_fields)}")
        sys.exit(1)

    return config


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
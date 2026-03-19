# GitCode Insight 命令开发流程

将 GitCode API 接口开发成 `gc-insight` 命令的标准流程。

## 前置条件

1. API 接口文档已放入 `doc/gitcode_api/` 目录
2. 了解接口的请求参数、响应结构和字段说明

## 开发步骤

### Step 1: 整理 API 文档

将原始接口信息整理成标准 Markdown 格式：

```markdown
# GitCode API - {接口名称}

## 接口信息

| 项目 | 说明 |
|------|------|
| 接口标识 | `GET /api/v5/repos/:owner/:repo/{endpoint}` |
| 接口用途 | {接口用途描述} |
| 请求方式 | GET |
| 基础域名 | `https://api.gitcode.com` |
| 完整地址 | `https://api.gitcode.com/api/v5/repos/:owner/:repo/{endpoint}` |
| 响应格式 | application/json |
| 权限要求 | 需携带有效 access_token |

## 请求参数

### 路径参数（Path）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 仓库所属空间地址 |
| repo | string | 是 | 仓库路径（path） |

### 查询参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 用户授权码 |
| ... | ... | ... | ... |

## 响应结构

### 成功响应（200 OK）

```json
{
  "field": "value"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| field | type | 说明 |

## 调用示例

### curl

```bash
curl -X GET "https://api.gitcode.com/api/v5/repos/owner/repo/{endpoint}?access_token=your_token"
```

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 不存在 |

## 注意事项

1. ...
```

### Step 2: 创建模块文件

在 `src/gitcode_insight/` 目录下创建模块文件，参考 `issue.py` 模式：

```python
# -*- coding: utf-8 -*-
"""
GitCode {功能名称}模块
{功能描述}
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import requests

from .utils import request_with_retry


class GitCode{FeatureName}:
    """GitCode {功能名称}分析器"""

    def __init__(self, repo: str, token: str, owner: str = None,
                 days: int = 30, output_dir: str = None):
        """
        初始化

        Args:
            repo: 仓库名称（path）
            token: API 访问令牌
            owner: 组织名
            days: 统计天数
            output_dir: 输出目录
        """
        self.repo = repo
        self.token = token
        self.owner = owner or self._get_default_owner()
        self.days = days
        self.base_url = "https://api.gitcode.com/api/v5"

        # 设置输出目录
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "output")
        self.output_dir = output_dir

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _get_default_owner(self) -> str:
        """从配置文件获取默认 owner"""
        config_file = os.path.join(os.getcwd(), "config", "gitcode.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("owner", "")
        return ""

    def get_{endpoint}(self) -> Dict:
        """获取数据"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/{endpoint}"
        params = {
            "access_token": self.token
        }
        data = request_with_retry(self.session, url, params)
        return data if data else {}

    def analyze(self, data: Dict) -> Dict:
        """分析数据"""
        # 实现分析逻辑
        pass

    def save_to_json(self, data: Dict) -> str:
        """保存到 JSON 文件"""
        os.makedirs(self.output_dir, exist_ok=True)
        filename = os.path.join(
            self.output_dir,
            f"{prefix}_{self.owner}_{self.repo}_{self.days}d.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filename

    def run(self) -> Dict:
        """执行完整的分析流程"""
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"{功能名称}: {self.owner}/{self.repo}")
        print(f"分析周期: 近 {self.days} 天")
        print(f"{'='*60}\n")

        # 获取数据
        data = self.get_{endpoint}()

        # 分析统计
        result = self.analyze(data)

        # 保存 JSON
        json_file = self.save_to_json(result)

        # 打印摘要
        print(f"\n{'='*60}")
        # 输出统计摘要
        print(f"数据已保存到: {json_file}")
        print(f"{'='*60}\n")

        return result
```

### Step 3: 修改 CLI 入口

在 `src/gitcode_insight/cli.py` 中添加：

1. **导入新模块**：

```python
from .{module} import GitCode{FeatureName}
```

2. **添加命令处理函数**：

```python
def cmd_{command}(args):
    """{功能名称}命令"""
    instance = GitCode{FeatureName}(
        repo=args.repo,
        token=args.token,
        owner=args.owner,
        days=args.days,
        output_dir=args.output
    )
    instance.run()
```

3. **添加子命令定义**：

```python
# {command} 子命令
{command}_parser = subparsers.add_parser("{command}", help="{功能名称}")
{command}_parser.add_argument("--repo", required=True, help="仓库名称（path）")
{command}_parser.add_argument("--token", required=True, help="API 访问令牌")
{command}_parser.add_argument("--owner", default=None, help="组织名，默认从配置文件读取")
{command}_parser.add_argument("--days", type=int, default=30, help="统计天数，默认 30")
{command}_parser.add_argument("--output", default=None, help="输出目录，默认使用 ./output/")
{command}_parser.set_defaults(func=cmd_{command})
```

### Step 4: 更新包导出

在 `src/gitcode_insight/__init__.py` 中添加导出：

```python
from .{module} import GitCode{FeatureName}

__all__ = [
    # ... 现有导出
    "GitCode{FeatureName}",
]
```

### Step 5: 测试验证

```bash
# 安装开发模式
.venv/bin/pip install -e ".[test]"

# 查看命令帮助
.venv/bin/gc-insight {command} --help

# 测试命令
.venv/bin/gc-insight {command} --repo test-repo --token gct_xxx --days 30

# 运行测试
.venv/bin/pytest tests/ -v
```

### Step 6: 编写单元测试（可选）

在 `tests/` 目录下创建测试文件：

```python
import pytest
from unittest.mock import Mock, patch
from gitcode_insight.{module} import GitCode{FeatureName}


class TestGitCode{FeatureName}:
    def test_init_with_params(self):
        """测试初始化参数"""
        instance = GitCode{FeatureName}(
            repo="test-repo",
            token="test-token",
            owner="test-owner",
            days=30
        )
        assert instance.repo == "test-repo"
        assert instance.token == "test-token"
        assert instance.owner == "test-owner"
        assert instance.days == 30

    @patch('gitcode_insight.{module}.request_with_retry')
    def test_get_{endpoint}(self, mock_retry):
        """测试获取数据"""
        mock_retry.return_value = {"key": "value"}
        instance = GitCode{FeatureName}(
            repo="test-repo",
            token="test-token"
        )
        result = instance.get_{endpoint}()
        assert result == {"key": "value"}
```

## 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `doc/gitcode_api/{endpoint}.md` | 新增/修改 | API 接口文档 |
| `src/gitcode_insight/{module}.py` | 新增 | 功能模块 |
| `src/gitcode_insight/cli.py` | 修改 | 添加子命令 |
| `src/gitcode_insight/__init__.py` | 修改 | 导出新类 |
| `tests/test_{module}.py` | 新增（可选） | 单元测试 |

## 关键工具函数

- `request_with_retry()`: 带重试机制的 HTTP 请求，自动处理 429 限流
- `_get_default_owner()`: 从 `config/gitcode.json` 读取默认 owner

## 输出规范

### 控制台输出格式

```
============================================================
{功能名称}: {owner}/{repo}
分析周期: 近 {days} 天
============================================================

{获取数据的进度信息}

分析统计数据...

============================================================
【{分类1}】
- 指标1: 值1
- 指标2: 值2

【{分类2}】
- 指标3: 值3

数据已保存到: {output_file}
============================================================
```

### JSON 输出格式

```json
{
  "repo": "owner/repo",
  "analysis_period": "近 30 天",
  "analysis_time": "2024-11-19 10:30:00",
  "category1": {
    "metric1": "value1"
  },
  "category2": {
    "metric2": "value2"
  }
}
```

文件命名：`{prefix}_{owner}_{repo}_{days}d.json`

## 注意事项

1. API 每分钟 100 次请求限制，使用 `request_with_retry` 自动处理
2. 所有文本输出使用中文
3. 日期格式统一使用 `YYYY-MM-DD`
4. 时间戳格式统一使用 ISO 8601
5. 输出目录默认为 `./output/`
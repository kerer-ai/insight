# GitCode Insight 开发指南

## 目录

- [环境搭建](#环境搭建)
- [项目结构](#项目结构)
- [运行测试](#运行测试)
- [开发新命令](#开发新命令)
- [发布流程](#发布流程)

## 环境搭建

```bash
# 克隆仓库
git clone https://gitcode.com/gitcode-cli/insight.git
cd insight

# 创建虚拟环境
python3 -m venv .venv

# 安装开发模式（包含测试依赖）
.venv/bin/pip install -e ".[test]"

# 创建配置文件
cp config/gitcode.json.example config/gitcode.json
# 编辑配置文件，填入 access_token 和 owner
```

## 项目结构

```
insight/
├── src/gitcode_insight/        # 包源码
│   ├── __init__.py             # 包入口
│   ├── cli.py                  # 命令行接口
│   ├── community.py            # 社区洞察模块
│   ├── issue.py                # Issue 洞察模块
│   ├── pr.py                   # PR 洞察模块
│   ├── dashboard.py            # 看板生成模块
│   ├── repo_stats.py           # 仓库统计模块
│   ├── report.py               # 综合报告模块
│   └── utils.py                # 公共工具
├── config/                     # 配置文件目录
├── doc/                        # 文档目录
│   └── gitcode_api/            # GitCode API 文档
├── tests/                      # 单元测试
├── .skill/                     # 开发流程文档
├── pyproject.toml              # 包配置
└── README.md
```

### 模块说明

| 模块 | 说明 |
|------|------|
| `cli.py` | 命令行入口，定义子命令 |
| `community.py` | `GitCodeCommunityStats` 类 |
| `issue.py` | `GitCodeIssueInsight` 类 |
| `pr.py` | `GitCodePRInsight` 类 |
| `repo_stats.py` | `GitCodeRepoStats` 类 |
| `report.py` | `GitCodeReport` 类 |
| `dashboard.py` | `generate_dashboard()`, `generate_markdown_file()` |
| `utils.py` | `request_with_retry()` 请求重试工具 |

### 模块依赖关系

```
report.py
    ├── issue.py
    ├── pr.py
    └── repo_stats.py

dashboard.py
    └── community.py (数据文件)

所有模块
    └── utils.py
```

### 类设计模式

每个模块遵循相同模式：

```python
class GitCodeFeature:
    def __init__(self, repo, token, owner=None, days=30, output_dir=None):
        # 初始化参数，设置 base_url

    def get_data(self) -> Dict:
        # 调用 API 获取数据

    def analyze(self, data) -> Dict:
        # 分析统计数据

    def save_to_json(self, data) -> str:
        # 保存 JSON 文件

    def run(self) -> Dict:
        # 执行完整流程：获取 → 分析 → 保存 → 输出
```

## 运行测试

### 基本命令

```bash
# 运行所有测试
.venv/bin/pytest

# 运行单个测试文件
.venv/bin/pytest tests/test_utils.py

# 显示详细输出
.venv/bin/pytest -v

# 生成覆盖率报告
.venv/bin/pytest --cov=gitcode_insight --cov-report=term-missing
```

### 集成测试

集成测试需要真实的 GitCode API Token：

```bash
# 跳过集成测试（默认）
.venv/bin/pytest -m "not integration"

# 运行集成测试
GITCODE_TOKEN=your_token .venv/bin/pytest -m integration
```

### 测试结构

```
tests/
├── conftest.py          # pytest 配置和共享 fixtures
├── test_utils.py        # utils 模块测试
├── test_community.py    # community 模块测试
├── test_dashboard.py    # dashboard 模块测试
├── test_issue.py        # issue 模块测试
├── test_pr.py           # pr 模块测试
├── test_repo_stats.py   # repo_stats 模块测试
├── test_report.py       # report 模块测试
└── test_cli.py          # cli 模块测试
```

### 编写测试

测试使用 `unittest.mock.patch` mock API 请求：

```python
import pytest
from unittest.mock import patch
from gitcode_insight.issue import GitCodeIssueInsight


class TestGitCodeIssueInsight:
    def test_init(self):
        """测试初始化"""
        instance = GitCodeIssueInsight(
            repo="test-repo",
            token="test-token",
            owner="test-owner",
            days=30
        )
        assert instance.repo == "test-repo"
        assert instance.token == "test-token"

    @patch('gitcode_insight.issue.request_with_retry')
    def test_get_issues(self, mock_retry):
        """测试获取数据"""
        mock_retry.return_value = [{"id": 1, "title": "Test Issue"}]
        instance = GitCodeIssueInsight(repo="test-repo", token="test-token")
        result = instance.get_issues()
        assert len(result) == 1
```

## 开发新命令

详细流程见 `.skill/develop-command.md`，核心步骤：

### 1. 整理 API 文档

将 API 文档放入 `doc/gitcode_api/`，格式参考现有文档。

### 2. 创建模块文件

在 `src/gitcode_insight/` 下创建模块，参考 `issue.py` 模式。

### 3. 修改 CLI

在 `cli.py` 中：
1. 导入新模块
2. 添加命令处理函数
3. 添加子命令定义

### 4. 更新导出

在 `__init__.py` 中添加导出。

### 5. 编写测试

创建 `tests/test_{module}.py`。

### 6. 验证

```bash
# 重新安装
.venv/bin/pip install -e ".[test]"

# 测试命令
.venv/bin/gc-insight new-command --help

# 运行测试
.venv/bin/pytest
```

## 发布流程

### 构建

```bash
# 安装构建工具
.venv/bin/pip install build

# 构建
.venv/bin/python -m build
```

生成的文件在 `dist/` 目录：
- `gitcode_insight-{version}-py3-none-any.whl`
- `gitcode_insight-{version}.tar.gz`

### 发布到 PyPI

```bash
# 安装 twine
.venv/bin/pip install twine

# 上传到 PyPI
.venv/bin/twine upload dist/*
```

### 版本更新

1. 更新 `pyproject.toml` 中的 `version`
2. 更新 `README.md` 更新日志
3. 创建 Git tag：`git tag v{version}`
4. 推送：`git push origin v{version}`
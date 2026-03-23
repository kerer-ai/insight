# 贡献指南

感谢您考虑为 GitCode Insight 做出贡献！

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [项目架构](#项目架构)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试要求](#测试要求)
- [文档规范](#文档规范)
- [Pull Request 流程](#pull-request-流程)

## 行为准则

- 尊重所有贡献者
- 接受建设性批评
- 关注对项目最有利的事情
- 对代码审查意见保持开放态度

## 如何贡献

### 报告问题

1. 在 [Issues](https://github.com/kerer-ai/insight/issues) 中搜索是否已有相同问题
2. 如果没有，创建新 Issue，包含：
   - 清晰的标题和描述
   - 复现步骤（如适用）
   - 期望行为和实际行为
   - 环境信息（Python 版本、操作系统）

### 提交代码

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature-name`
3. 进行修改
4. 运行测试确保通过
5. 提交代码
6. 创建 Pull Request

## 项目架构

### 目录结构

```
insight/
├── src/gitcode_insight/     # 核心源码
│   ├── cli.py               # CLI 入口
│   ├── community.py         # 社区洞察
│   ├── issue.py             # Issue 分析
│   ├── pr.py                # PR 分析
│   ├── repo_stats.py        # 仓库统计
│   ├── report.py            # 综合报告
│   ├── dashboard.py         # 看板生成
│   └── utils.py             # 工具函数
├── tests/                   # 单元测试
├── doc/                     # 文档
│   └── gitcode_api/         # API 文档
├── config/                  # 配置文件
└── .skill/                  # 开发流程文档
```

### 模块架构

```
┌─────────────────────────────────────────────────────────┐
│                      cli.py                              │
│                   (命令行入口)                            │
└─────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ community.py │  │   issue.py   │  │    pr.py     │
│              │  │              │  │              │
│  (社区洞察)   │  │ (Issue分析)  │  │  (PR分析)    │
└──────────────┘  └──────────────┘  └──────────────┘
          │                │                │
          ▼                └────────┬───────┘
┌──────────────┐                    │
│ dashboard.py │                    ▼
│              │           ┌──────────────┐
│  (看板生成)  │           │  report.py   │
└──────────────┘           │              │
                           │ (综合报告)    │
                           └──────────────┘
                                  │
                                  ▼
                          ┌──────────────┐
                          │ repo_stats.py│
                          │              │
                          │ (仓库统计)    │
                          └──────────────┘
                                  │
                                  ▼
                          ┌──────────────┐
                          │   utils.py   │
                          │              │
                          │ (请求重试等)  │
                          └──────────────┘
```

### 设计原则

#### 1. 模块化设计

每个功能模块独立，遵循单一职责原则：

- **community.py**: 组织维度的数据采集
- **issue.py**: 单仓库 Issue 分析
- **pr.py**: 单仓库 PR 分析
- **repo_stats.py**: 单仓库统计数据
- **report.py**: 整合各模块生成综合报告
- **dashboard.py**: 数据可视化

#### 2. 类设计模式

所有分析模块遵循统一的类设计模式：

```python
class GitCodeFeature:
    """功能模块类"""

    def __init__(self, repo, token, owner=None, days=30, output_dir=None):
        """
        初始化

        Args:
            repo: 仓库名称
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
        self.output_dir = output_dir or os.path.join(os.getcwd(), "output")

    def get_data(self) -> List[Dict]:
        """获取 API 数据"""
        pass

    def analyze(self, data) -> Dict:
        """分析统计数据"""
        pass

    def save_to_json(self, data) -> str:
        """保存 JSON 文件"""
        pass

    def run(self) -> Dict:
        """执行完整流程"""
        data = self.get_data()
        result = self.analyze(data)
        self.save_to_json(result)
        return result
```

#### 3. 数据流向

```
API 请求 → 数据获取 → 统计分析 → 多格式输出
                         │
                         ├── JSON 数据文件
                         ├── HTML 可视化报告
                         └── Markdown 报告
```

#### 4. 错误处理

所有 API 请求必须使用 `utils.request_with_retry()`：

```python
from .utils import request_with_retry

# 正确做法
data = request_with_retry(self.session, url, params)

# 错误做法 - 直接使用 requests
response = self.session.get(url, params=params)  # ❌
```

## 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用 4 空格缩进
- 行长度不超过 100 字符
- 文件编码使用 UTF-8

### 文件头部

```python
# -*- coding: utf-8 -*-
"""
模块简述
详细描述（可选）
"""
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `GitCodeIssueInsight` |
| 函数名 | snake_case | `get_issues()` |
| 变量名 | snake_case | `total_count` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| 私有方法 | _前缀 | `_get_default_owner()` |

### 文档字符串

使用 Google 风格：

```python
def get_issues(self, state: str = "all") -> List[Dict]:
    """
    获取 Issue 列表

    Args:
        state: Issue 状态，可选 'open', 'closed', 'all'

    Returns:
        Issue 列表，每个元素为字典

    Raises:
        ValueError: 当 state 参数无效时
    """
    pass
```

### 类型注解

建议使用类型注解提高代码可读性：

```python
from typing import List, Dict, Optional

def analyze(self, issues: List[Dict]) -> Dict:
    """分析 Issue 数据"""
    pass
```

### 中文文本

- 所有用户可见文本使用中文
- 控制台输出使用中文
- 错误消息使用中文

```python
# 正确
print(f"获取 {self.owner}/{self.repo} 的数据...")

# 错误
print(f"Fetching data for {self.owner}/{self.repo}...")  # ❌
```

## 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构（不增加功能、不修复 Bug） |
| `test` | 测试相关 |
| `chore` | 构建/工具变动 |

### Scope 范围

| 范围 | 说明 |
|------|------|
| `cli` | 命令行接口 |
| `community` | 社区洞察模块 |
| `issue` | Issue 模块 |
| `pr` | PR 模块 |
| `report` | 报告模块 |
| `docs` | 文档 |

### 示例

```
feat(issue): 添加 --range-by 参数支持多种统计口径

- 新增 created/updated/active 三种统计范围
- 更新文档说明参数用途
- 添加相关测试用例

Closes #123
```

```
fix(report): 修复 CI 成功率计算错误

原先 CI 成功率始终显示 0%，现在根据 PR 标签正确计算。
```

## 测试要求

### 测试文件命名

- 测试文件：`tests/test_{module}.py`
- 测试类：`Test{ClassName}`
- 测试方法：`test_{method_name}`

### 测试覆盖

新增功能必须包含测试：

```python
import pytest
from unittest.mock import patch, Mock
from gitcode_insight.issue import GitCodeIssueInsight


class TestGitCodeIssueInsight:
    """Issue 模块测试"""

    def test_init_with_params(self):
        """测试初始化参数"""
        instance = GitCodeIssueInsight(
            repo="test-repo",
            token="test-token",
            owner="test-owner",
            days=30
        )
        assert instance.repo == "test-repo"
        assert instance.days == 30

    @patch('gitcode_insight.issue.request_with_retry')
    def test_get_issues(self, mock_retry):
        """测试获取 Issue 列表"""
        mock_retry.return_value = [
            {"id": 1, "state": "open", "title": "Test Issue"}
        ]

        instance = GitCodeIssueInsight(
            repo="test-repo",
            token="test-token"
        )
        issues = instance.get_issues()

        assert len(issues) == 1
        assert issues[0]["state"] == "open"
```

### Mock API 请求

测试中必须 mock API 请求，不要调用真实 API：

```python
# 正确
@patch('gitcode_insight.issue.request_with_retry')
def test_something(self, mock_retry):
    mock_retry.return_value = {"key": "value"}
    # ...

# 错误 - 调用真实 API
def test_something(self):
    instance = GitCodeIssueInsight(...)
    data = instance.get_issues()  # ❌ 会发起真实请求
```

### 运行测试

```bash
# 运行所有测试
.venv/bin/pytest

# 运行单个文件
.venv/bin/pytest tests/test_issue.py

# 生成覆盖率报告
.venv/bin/pytest --cov=gitcode_insight --cov-report=term-missing
```

### 覆盖率要求

- 新增代码测试覆盖率应达到 80% 以上
- 关键业务逻辑应达到 90% 以上

## 文档规范

### 文档位置

| 文档 | 位置 | 内容 |
|------|------|------|
| 项目介绍 | `README.md` | 简介和快速开始 |
| 用户指南 | `doc/user_guide.md` | 详细使用说明 |
| 开发指南 | `doc/development.md` | 开发环境搭建 |
| API 文档 | `doc/gitcode_api/` | GitCode API 说明 |
| 贡献指南 | `CONTRIBUTING.md` | 本文档 |
| 项目指引 | `CLAUDE.md` | Claude Code 指引 |

### 文档更新

代码修改时同步更新相关文档：

1. **新增命令**：更新 `README.md`、`doc/user_guide.md`、`CLAUDE.md`
2. **修改参数**：更新 `doc/user_guide.md` 命令详解
3. **新增 API**：添加 API 文档到 `doc/gitcode_api/`
4. **修改架构**：更新 `CLAUDE.md` 和 `CONTRIBUTING.md`

### Markdown 格式

- 使用中文标题
- 标题层级：`#` → `##` → `###` → `####`
- 代码块指定语言：` ```python `
- 表格对齐：

```markdown
| 列1 | 列2 | 列3 |
|-----|------|-----|
| 内容 | 内容 | 内容 |
```

## Pull Request 流程

### PR 前检查清单

- [ ] 代码通过所有测试：`.venv/bin/pytest`
- [ ] 新增代码有对应测试
- [ ] 代码风格符合规范
- [ ] 更新相关文档
- [ ] Commit message 符合规范

### PR 标题格式

与 Commit message 相同：

```
feat(issue): 添加 --range-by 参数
```

### PR 描述模板

```markdown
## 变更类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 重构

## 变更说明
<!-- 描述本次变更的内容和原因 -->

## 测试
<!-- 如何测试本次变更 -->

## 相关 Issue
<!-- 关联的 Issue 编号 -->
```

### 代码审查

- 所有 PR 需要至少一人审查
- 审查者关注：
  - 代码质量和规范
  - 测试覆盖
  - 文档完整性
  - 架构合理性

### 合并要求

- 所有 CI 检查通过
- 至少一人 approve
- 解决所有 review 意见
- squash merge 或 rebase merge

## 开发环境

### 环境搭建

```bash
# 克隆仓库
git clone https://github.com/kerer-ai/insight.git
cd insight

# 创建虚拟环境
python3 -m venv .venv

# 安装开发依赖
.venv/bin/pip install -e ".[test]"

# 创建配置文件
cp config/gitcode.json.example config/gitcode.json
```

### 推荐工具

- Python 3.7+
- pytest + pytest-cov
- 代码格式化：black / isort
- 类型检查：mypy（可选）

## 获取帮助

- 提交 Issue：https://github.com/kerer-ai/insight/issues
- 阅读文档：`doc/` 目录

---

再次感谢您的贡献！
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用命令

```bash
# 安装（开发模式，包含测试依赖）
.venv/bin/pip install -e ".[test]"

# 运行所有测试
.venv/bin/pytest

# 运行单个测试文件
.venv/bin/pytest tests/test_utils.py

# 运行测试并生成覆盖率报告
.venv/bin/pytest --cov=gitcode_insight --cov-report=term-missing

# 跳过集成测试（默认）
.venv/bin/pytest -m "not integration"

# 构建发布包
.venv/bin/pip install build && .venv/bin/python -m build
```

## 子命令快速参考

| 命令 | 用途 | 数据来源 |
|------|------|----------|
| `community` | 社区洞察 | 组织下所有仓库 |
| `dashboard` | 可视化看板 | 复用 community 数据 |
| `issue` | Issue 分析 | 单个仓库 |
| `pr` | PR 分析 | 单个仓库 |
| `repo-stats` | 仓库统计 | 单个仓库 |
| `report` | 综合报告 | 单个仓库（直接采集） |

## 配置文件

`config/gitcode.json`：
- `access_token`: GitCode API 访问令牌（必填）
- `owner`: 组织/社区名称（必填）
- `label_ci_success/label_ci_running`: 蓝区 CI 标签
- `label_yellow_ci_success/label_yellow_ci_running`: 黄区 CI 标签
- `repo_whitelist/repo_blacklist`: 仓库白名单/黑名单（仅影响 community/dashboard）

## 模块架构

```
src/gitcode_insight/
├── cli.py          # 命令行入口，定义 gc-insight 子命令
├── community.py    # GitCodeCommunityStats 类，社区数据爬取
├── dashboard.py    # generate_dashboard(), generate_markdown_file()
├── issue.py        # GitCodeIssueInsight 类，Issue 分析
├── pr.py           # GitCodePRInsight 类，PR 洞察分析
├── repo_stats.py   # GitCodeRepoStats 类，仓库统计
├── report.py       # GitCodeReport 类，整合所有模块
└── utils.py        # request_with_retry() 请求重试工具
```

**模块依赖关系**：
- `report.py` 依赖 `issue.py`, `pr.py`, `repo_stats.py`（直接调用类实例采集数据）
- `dashboard.py` 依赖 `community.py` 的数据文件
- 所有模块依赖 `utils.py` 的 `request_with_retry()` 函数

**类设计模式**：每个模块（除 dashboard）遵循相同模式：
- 构造函数：`repo`, `token`, `owner`, `days`, `output_dir` 参数
- 核心方法：`get_*()` 获取 API 数据，`analyze()` 统计分析，`run()` 执行完整流程
- 输出：JSON 数据文件 + HTML 可视化报告 + Markdown 报告

## 开发新命令

详细流程见 `.skill/develop-command.md`，核心步骤：
1. 整理 API 文档到 `doc/gitcode_api/`
2. 创建模块文件（参考 `issue.py` 模式：构造函数 → get_*() → analyze() → run()）
3. 修改 `cli.py` 添加子命令
4. 更新 `__init__.py` 导出
5. 编写单元测试（mock `request_with_retry`）

## API 限流

GitCode API 每分钟 100 次请求限制。代码通过 `time.sleep(0.6)` 控制间隔，429 状态码自动等待重试。所有请求必须使用 `utils.request_with_retry()` 函数。

## 输出目录

所有输出文件默认保存在 `./output/` 目录。

## 测试

```bash
# 运行所有测试
.venv/bin/pytest

# 跳过集成测试（默认行为）
.venv/bin/pytest -m "not integration"

# 运行集成测试（需要真实 Token）
GITCODE_TOKEN=your_token .venv/bin/pytest -m integration
```

测试结构：每个模块对应 `tests/test_{module}.py`，使用 `unittest.mock.patch` mock API 请求。
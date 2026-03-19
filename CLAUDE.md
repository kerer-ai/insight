# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

GitCode Insight 是一个命令行工具，用于从 GitCode 平台获取数据并生成分析报告。支持社区洞察、Issue 洞察、PR 洞察、仓库统计、订阅用户统计、编程语言统计和仓库综合报告。

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

# 跳过集成测试
.venv/bin/pytest -m "not integration"

# 社区洞察 - 采集数据
.venv/bin/gc-insight community

# 社区洞察 - 生成看板（自动检测数据，不存在则自动采集）
.venv/bin/gc-insight dashboard

# Issue 洞察（--range-by: created/updated/active）
.venv/bin/gc-insight issue --repo <repo> --token <token> --days 30

# PR 洞察
.venv/bin/gc-insight pr --repo <repo> --token <token> --days 30

# 仓库统计（下载 + Fork 分析）
.venv/bin/gc-insight repo-stats --repo <repo> --token <token> --days 30

# 订阅用户统计
.venv/bin/gc-insight subscribers --repo <repo> --token <token> --days 30

# 编程语言统计
.venv/bin/gc-insight languages --repo <repo> --token <token>

# 仓库综合报告（整合所有模块）
.venv/bin/gc-insight report --repo <repo> --token <token> --days 30
```

## 配置文件

`config/gitcode.json`：
- `access_token`: GitCode API 访问令牌（必填）
- `owner`: 组织/社区名称（必填）
- `label_ci_success/label_ci_running`: 蓝区 CI 标签
- `label_yellow_ci_success/label_yellow_ci_running`: 黄区 CI 标签
- `repo_whitelist/repo_blacklist`: 仓库白名单/黑名单（仅影响 community/dashboard）

## 代码架构

```
src/gitcode_insight/
├── cli.py          # 命令行入口，定义 gc-insight 子命令
├── community.py    # GitCodeCommunityStats 类，社区数据爬取
├── issue.py        # GitCodeIssueInsight 类，Issue 分析
├── pr.py           # GitCodePRInsight 类，PR 洞察分析
├── repo_stats.py   # GitCodeRepoStats 类，仓库统计（下载/Fork）
├── subscribers.py  # GitCodeSubscribers 类，订阅用户统计
├── languages.py    # GitCodeLanguages 类，编程语言统计
├── report.py       # GitCodeReport 类，仓库综合报告（整合所有模块）
├── dashboard.py    # generate_dashboard(), generate_markdown_file()
└── utils.py        # request_with_retry() 请求重试工具
```

**核心流程**：
- `community`: 获取组织下所有项目 → 遍历获取统计数据 → 保存 CSV/JSON
- `dashboard`: 检测数据文件 → 不存在则自动采集 → 生成 HTML/Markdown 看板
- `issue/pr/repo-stats/subscribers/languages`: 获取仓库数据 → 分析统计 → 生成报告
- `report`: 智能检测各模块数据 → 不存在则自动采集 → 整合生成综合报告

**智能数据采集**：`dashboard` 和 `report` 命令会自动检测数据文件是否存在，不存在则调用对应命令采集。

## 开发新命令

开发新命令的标准流程见 `.skill/develop-command.md`，主要步骤：
1. 整理 API 文档到 `doc/gitcode_api/`
2. 创建模块文件（参考 `issue.py` 模式）
3. 修改 `cli.py` 添加子命令
4. 更新 `__init__.py` 导出
5. 编写单元测试

## API 限流

GitCode API 每分钟 100 次请求限制。代码通过 `time.sleep(0.6)` 控制间隔，429 状态码自动等待重试。所有请求应使用 `utils.request_with_retry()` 函数。

## 输出目录

所有输出文件默认保存在 `./output/` 目录。
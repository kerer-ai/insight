# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

代码洞察工具集（Insight），用于从 GitCode 平台获取数据并生成分析报告。支持社区洞察和 Issue 洞察。

## 常用命令

```bash
# 安装（开发模式）
pip install -e ".[test]"

# 社区洞察 - 采集数据
gc-insight community

# 社区洞察 - 生成看板（自动检测数据，不存在则自动采集）
gc-insight dashboard

# Issue 洞察
gc-insight issue --repo <repo> --token <token> --days 30

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=gitcode_insight --cov-report=term-missing
```

## 配置文件

`config/gitcode.json`：
- `access_token`: GitCode API 访问令牌（必填）
- `owner`: 组织/社区名称（必填）
- `label_ci_success/label_ci_running`: 蓝区 CI 标签
- `label_yellow_ci_success/label_yellow_ci_running`: 黄区 CI 标签

## 代码架构

```
src/gitcode_insight/
├── cli.py          # 命令行入口，定义 gc-insight 子命令
├── community.py    # GitCodeCommunityStats 类，社区数据爬取
├── issue.py        # GitCodeIssueInsight 类，Issue 分析
├── dashboard.py    # generate_dashboard(), generate_markdown_file()
└── utils.py        # request_with_retry() 请求重试工具
```

核心流程：
- `community`: 获取组织下所有项目 → 遍历获取统计数据 → 保存 CSV/JSON
- `dashboard`: 检测数据文件 → 不存在则自动采集 → 生成 HTML/Markdown 看板
- `issue`: 获取仓库 Issue → 计算响应时间/关闭率等指标 → 生成洞察报告

## API 限流

GitCode API 每分钟 100 次请求限制。代码通过 `time.sleep(0.6)` 控制间隔，429 状态码自动等待重试。
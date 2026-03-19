# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

代码洞察工具集（Insight），用于从代码托管平台获取数据并生成分析报告。当前支持 GitCode 平台。

## 目录结构

```
insight/
├── config/                  # 配置文件目录
├── scripts/                 # 脚本目录
├── output/                  # 输出文件目录
├── README.md
└── CLAUDE.md
```

## 常用命令

```bash
# 获取社区统计数据
python scripts/gitcode_crawler.py

# 生成可视化看板（HTML + Markdown）
python scripts/gitcode_dashboard.py
```

## 运行顺序

1. 先运行 `scripts/gitcode_crawler.py` 获取数据，输出到 `output/` 目录
2. 再运行 `scripts/gitcode_dashboard.py` 读取 JSON 数据，生成看板

## 配置文件

`config/gitcode.json` 包含以下配置项：
- `access_token`: GitCode API 访问令牌
- `owner`: 社区/组织名称
- `label_ci_success`: CI 成功标签名称
- `label_ci_running`: CI 运行中标签名称
- `label_yellow_ci_running`: 黄区 CI 运行中标签名称
- `label_yellow_ci_success`: 黄区 CI 成功标签名称

## 代码架构

### scripts/gitcode_crawler.py
`GitCodeCommunityStats` 类负责数据爬取，主要方法：
- `get_all_community_projects()`: 获取组织下所有项目
- `get_project_contributors()`: 获取项目贡献者
- `get_project_merge_requests()`: 获取项目 PR 列表
- `calculate_gatekeeper_duration()`: 计算门禁时长（基于标签操作日志）
- `analyze_project_stats()`: 汇总单个项目的所有统计指标
- `crawl_community_stats()`: 主入口，爬取所有项目数据

### scripts/gitcode_dashboard.py
- `generate_dashboard()`: 生成 HTML 看板页面
- `generate_markdown_file()`: 生成 Markdown 格式报告

## API 限流处理

GitCode API 限制每分钟 100 次请求。代码中通过 `time.sleep(0.6)` 控制请求间隔，并在遇到 429 状态码时自动重试。
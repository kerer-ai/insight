# GitCode Insight - GitCode 平台代码洞察工具

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

GitCode Insight 是一个命令行工具，用于从 GitCode 平台获取数据并生成分析报告。支持社区统计分析和 Issue 洞察，生成可视化看板和 Markdown 报告。

---

## 目录

- [功能特性](#功能特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [命令详解](#命令详解)
- [输出文件](#输出文件)
- [作为库使用](#作为库使用)
- [项目结构](#项目结构)
- [API 限流说明](#api-限流说明)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 功能特性

### 社区洞察

分析 GitCode 组织/社区下所有项目的统计数据：

- 仓库总数、贡献者数量统计
- PR 数量分析（7天、30天、100天）
- 门禁时长分析（支持蓝区/黄区 CI）
- PR 闭环时间分析
- 单日 PR 提交峰值统计
- 生成 HTML 可视化看板和 Markdown 报告

### Issue 洞察

分析指定仓库近 N 天的 Issue 情况：

- Issue 总数、新增数、关闭率
- 平均首次响应时间
- 平均关闭耗时
- 24小时响应率
- 每日新增/关闭趋势图
- 标签分布、创建人分布
- 生成 HTML 洞察报告

---

## 安装

### 方式一：从源码安装

```bash
# 克隆仓库
git clone https://github.com/kerer-ai/insight.git
cd insight

# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装
pip install .
```

### 方式二：构建 wheel 包

```bash
# 安装构建工具
pip install build

# 构建
python -m build

# 安装生成的 wheel 包
pip install dist/gitcode_insight-0.1.0-py3-none-any.whl
```

### 系统要求

- Python 3.7+
- 依赖：`requests >= 2.25.0`

---

## 快速开始

### 1. 创建配置文件

```bash
# 复制配置模板
cp config/gitcode.json.example config/gitcode.json

# 编辑配置文件，填入你的 Access Token 和组织名
vim config/gitcode.json
```

配置文件示例：

```json
{
    "access_token": "your_gitcode_access_token",
    "owner": "your_organization_name",
    "label_ci_success": "ci-pipeline-passed",
    "label_ci_running": "ci-pipeline-running",
    "label_yellow_ci_running": "SC-RUNNING",
    "label_yellow_ci_success": "SC-SUCC"
}
```

### 2. 运行社区洞察

```bash
# 一键生成看板（自动采集数据并生成报告）
gc-insight dashboard

# 或分步执行
gc-insight community  # 仅采集数据
gc-insight dashboard  # 仅生成报告
```

### 3. 运行 Issue 洞察

```bash
gc-insight issue --repo your-repo --token your_token --days 30
```

### 4. 查看输出

所有输出文件默认保存在 `./output/` 目录。

---

## 配置说明

配置文件 `config/gitcode.json` 支持以下配置项：

| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `access_token` | string | 是 | GitCode API 访问令牌 |
| `owner` | string | 是 | 组织/社区名称 |
| `label_ci_success` | string | 否 | 蓝区 CI 成功标签，默认 `ci-pipeline-passed` |
| `label_ci_running` | string | 否 | 蓝区 CI 运行中标签，默认 `ci-pipeline-running` |
| `label_yellow_ci_success` | string | 否 | 黄区 CI 成功标签，默认 `SC-SUCC` |
| `label_yellow_ci_running` | string | 否 | 黄区 CI 运行中标签，默认 `SC-RUNNING` |

### 获取 Access Token

1. 登录 GitCode
2. 进入「设置」→「访问令牌」
3. 创建新令牌，选择所需权限
4. 复制令牌到配置文件

---

## 命令详解

### gc-insight

查看帮助：

```bash
gc-insight --help
```

### gc-insight community

获取社区统计数据。

```bash
gc-insight community [选项]
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--config` | `./config/gitcode.json` | 配置文件路径 |
| `--output` | `./output/` | 输出目录 |

**示例：**

```bash
# 使用默认配置
gc-insight community

# 指定配置文件和输出目录
gc-insight community --config /path/to/config.json --output /path/to/output/
```

**执行流程：**

1. 读取配置文件
2. 获取组织下所有项目列表
3. 遍历每个项目获取统计数据
4. 保存 CSV 和 JSON 文件
5. 打印统计报告

### gc-insight dashboard

生成可视化看板（自动检测数据，不存在则自动采集）。

```bash
gc-insight dashboard [选项]
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--config` | `./config/gitcode.json` | 配置文件路径 |
| `--output` | `./output/` | 输出目录 |

**智能检测：**

- 自动检测数据文件 `{owner}_community_stats_detailed.json` 是否存在
- 如果不存在，自动执行 `community` 采集流程
- 采集完成后自动生成看板

**执行流程：**

```
检测数据文件
  ├── 存在 → 直接生成看板
  └── 不存在 → 自动采集数据 → 生成看板
```

**生成的看板包含：**

- 统计概览卡片（仓库数、贡献者、PR 数等）
- 项目贡献者分布图（Top 10）
- 项目 PR 数量分布图（Top 10）
- 项目详细统计表格（支持点击表头排序）

### gc-insight issue

分析仓库 Issue 数据。

```bash
gc-insight issue --repo REPO --token TOKEN [选项]
```

| 选项 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--repo` | 是 | - | 仓库名称（path） |
| `--token` | 是 | - | API 访问令牌 |
| `--days` | 否 | 30 | 统计天数 |
| `--owner` | 否 | 从配置读取 | 组织名 |
| `--output` | 否 | `./output/` | 输出目录 |

**示例：**

```bash
# 分析近 30 天的 Issue
gc-insight issue --repo kvrocks --token gct_xxxx

# 分析近 90 天的 Issue
gc-insight issue --repo kvrocks --token gct_xxxx --days 90
```

---

## 输出文件

### 社区洞察输出

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `{owner}_community_stats.csv` | CSV | 统计数据表格 |
| `{owner}_community_stats_detailed.json` | JSON | 完整统计数据 |
| `{owner}_community_dashboard.html` | HTML | 可视化看板 |
| `{owner}_community_dashboard.md` | Markdown | Markdown 报告 |

### Issue 洞察输出

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `issues_{repo}_{days}d.csv` | CSV | Issue 原始数据 |
| `issue_insight_{repo}_{days}d.json` | JSON | 洞察结论数据 |
| `issue_insight_{repo}_{days}d.html` | HTML | 可视化洞察报告 |

---

## 作为库使用

除了命令行工具，也可以作为 Python 库在代码中使用：

```python
from gitcode_insight import GitCodeCommunityStats, GitCodeIssueInsight, generate_dashboard

# 社区洞察
stats = GitCodeCommunityStats(config_file="config/gitcode.json")
data = stats.crawl_community_stats()
stats.save_to_csv(data)
stats.save_to_json(data)

# 生成看板
generate_dashboard()

# Issue 洞察
insight = GitCodeIssueInsight(
    repo="kvrocks",
    token="your_token",
    days=30
)
result = insight.run()
```

---

## 项目结构

```
insight/
├── src/gitcode_insight/        # 包源码
│   ├── __init__.py             # 包入口
│   ├── cli.py                  # 命令行接口
│   ├── community.py            # 社区洞察模块
│   ├── issue.py                # Issue 洞察模块
│   ├── dashboard.py            # 看板生成模块
│   └── utils.py                # 公共工具
├── config/                     # 配置文件目录
│   └── gitcode.json.example    # 配置示例
├── doc/                        # 文档目录
│   └── gitcode_api/            # GitCode API 文档
├── pyproject.toml              # 包配置
├── LICENSE                     # MIT 许可证
├── CLAUDE.md                   # Claude Code 项目指引
└── README.md                   # 本文档
```

### 模块说明

| 模块 | 说明 |
|------|------|
| `cli.py` | 命令行入口，定义 `gc-insight` 命令和子命令 |
| `community.py` | `GitCodeCommunityStats` 类，社区数据爬取 |
| `issue.py` | `GitCodeIssueInsight` 类，Issue 分析 |
| `dashboard.py` | `generate_dashboard()` 和 `generate_markdown_file()` 函数 |
| `utils.py` | `request_with_retry()` 请求重试工具函数 |

---

## API 限流说明

GitCode API 限制每分钟 100 次请求。工具已内置以下处理机制：

| 机制 | 说明 |
|------|------|
| 请求间隔控制 | 每次请求间隔 0.6 秒 |
| 限流重试 | 遇到 429 状态码自动等待 5 秒后重试 |
| 错误重试 | 其他错误等待 3 秒后重试，最多 3 次 |

---

## 开发指南

```bash
# 克隆仓库
git clone https://github.com/kerer-ai/insight.git
cd insight

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 开发模式安装
pip install -e .
```

---

## 常见问题

### Q: 如何获取 GitCode Access Token？

A: 登录 GitCode → 设置 → 访问令牌 → 创建新令牌

### Q: 门禁时长是如何计算的？

A: 通过分析 PR 操作日志，计算 CI 运行标签添加到 CI 成功标签添加的时间间隔。支持蓝区和黄区两种 CI 门禁。

### Q: 输出文件中文乱码怎么办？

A: CSV 文件使用 UTF-8-BOM 编码，Excel 可正常打开。

### Q: 请求频繁失败怎么办？

A: 检查网络连接，确认 Access Token 有效。如遇限流，等待几分钟后重试。

---

## 更新日志

### v0.1.0 (2026-03-19)

- 初始版本
- 支持社区洞察功能
- 支持 Issue 洞察功能
- 支持生成 HTML 看板和 Markdown 报告
- 命令行工具 `gc-insight`
- `dashboard` 命令支持自动检测并采集数据

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

- 项目主页：https://github.com/kerer-ai/insight
- 问题反馈：https://github.com/kerer-ai/insight/issues
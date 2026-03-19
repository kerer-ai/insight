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

### 方式一：从 wheel 包安装（推荐）

```bash
# 下载或构建 wheel 包后
pip install gitcode_insight-0.1.0-py3-none-any.whl
```

### 方式二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/example/insight.git
cd insight

# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装
pip install .

# 或开发模式安装
pip install -e .
```

### 方式三：构建 wheel 包

```bash
# 安装构建工具
pip install build

# 构建
python -m build

# 生成的文件在 dist/ 目录
ls dist/
# gitcode_insight-0.1.0-py3-none-any.whl
# gitcode_insight-0.1.0.tar.gz
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

# 编辑配置文件
vim config/gitcode.json
```

配置文件内容：

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
# 获取社区数据
gc-insight community

# 生成可视化看板
gc-insight dashboard
```

### 3. 运行 Issue 洞察

```bash
gc-insight issue --repo your-repo --token your_token --days 30
```

### 4. 查看输出

所有输出文件默认保存在 `./output/` 目录：

```bash
ls output/
# {owner}_community_stats.csv
# {owner}_community_stats_detailed.json
# {owner}_community_dashboard.html
# {owner}_community_dashboard.md
```

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

| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--config` | `-c` | `./config/gitcode.json` | 配置文件路径 |
| `--output` | `-o` | `./output/` | 输出目录 |

**示例：**

```bash
# 使用默认配置
gc-insight community

# 指定配置文件和输出目录
gc-insight community --config /path/to/config.json --output /path/to/output/

# 简写形式
gc-insight community -c ./my-config.json -o ./reports/
```

**执行流程：**

1. 读取配置文件
2. 获取组织下所有项目列表
3. 遍历每个项目获取统计数据：
   - 贡献者数量
   - PR 数量统计
   - 门禁时长分析
   - PR 闭环时间
4. 保存 CSV 和 JSON 文件
5. 打印统计报告

### gc-insight dashboard

生成可视化看板。

```bash
gc-insight dashboard [选项]
```

| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--config` | `-c` | `./config/gitcode.json` | 配置文件路径 |
| `--output` | `-o` | `./output/` | 输出目录 |

**前提条件：**

需要先运行 `gc-insight community` 生成数据文件。

**示例：**

```bash
gc-insight dashboard
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

| 选项 | 简写 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--repo` | `-r` | 是 | - | 仓库名称（path） |
| `--token` | `-t` | 是 | - | API 访问令牌 |
| `--days` | `-d` | 否 | 30 | 统计天数 |
| `--owner` | | 否 | 从配置读取 | 组织名 |
| `--output` | `-o` | 否 | `./output/` | 输出目录 |

**示例：**

```bash
# 分析近 30 天的 Issue
gc-insight issue --repo kvrocks --token gct_xxxx

# 分析近 90 天的 Issue
gc-insight issue --repo kvrocks --token gct_xxxx --days 90

# 指定组织名
gc-insight issue --repo my-repo --token gct_xxxx --owner my-org --days 60
```

**生成的报告包含：**

- Issue 统计概览（总数、新增、关闭率）
- 效率指标（响应时间、关闭耗时、24h响应率）
- 每日 Issue 趋势图
- 标签分布图（Top 10）
- Issue 详细列表

---

## 输出文件

### 社区洞察输出

运行 `gc-insight community` 和 `gc-insight dashboard` 后生成：

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `{owner}_community_stats.csv` | CSV | 统计数据表格，可用 Excel 打开 |
| `{owner}_community_stats_detailed.json` | JSON | 完整统计数据，包含项目详情 |
| `{owner}_community_dashboard.html` | HTML | 可视化看板，浏览器打开 |
| `{owner}_community_dashboard.md` | Markdown | Markdown 格式报告 |

**CSV 文件字段：**

| 字段 | 说明 |
|------|------|
| 项目名称 | 仓库名称 |
| 项目URL | 仓库链接 |
| 项目描述 | 仓库描述 |
| 贡献者数量 | 总贡献者数 |
| 一年贡献者 | 近一年活跃贡献者 |
| 总PR数 | 100天内 PR 总数 |
| 近7天PR | 7天内 PR 数 |
| 近30天PR | 30天内 PR 数 |
| 单日PR峰值 | 30天内单日最高 PR 数 |
| 峰值日期 | PR 峰值对应日期 |
| 门禁类型 | 蓝区/黄区/无 |
| 平均门禁时长(分钟) | 平均 CI 门禁耗时 |
| 最长门禁时长(分钟) | 最长 CI 门禁耗时 |
| 最长门禁时长PR链接 | 耗时最长的 PR |
| 平均PR闭环时间(分钟) | PR 平均闭环时间 |
| 最长PR闭环时间(分钟) | PR 最长闭环时间 |
| 最长闭环PR链接 | 闭环最久的 PR |

### Issue 洞察输出

运行 `gc-insight issue` 后生成：

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `issues_{repo}_{days}d.csv` | CSV | Issue 原始数据 |
| `issue_insight_{repo}_{days}d.json` | JSON | 洞察结论数据 |
| `issue_insight_{repo}_{days}d.html` | HTML | 可视化洞察报告 |

**JSON 文件结构：**

```json
{
  "repo": "org/repo",
  "analysis_period": "近 30 天",
  "analysis_time": "2026-03-19 10:00:00",
  "summary": {
    "total_issues": 100,
    "opened_issues": 30,
    "closed_issues": 70,
    "new_issues": 50,
    "close_rate": 70.0
  },
  "efficiency": {
    "avg_first_response_time_minutes": 120.5,
    "avg_close_duration_hours": 48.2,
    "timely_response_rate": 85.0
  },
  "distribution": {
    "by_label": {"bug": 30, "feature": 20},
    "by_creator": {"user1": 15, "user2": 10}
  },
  "daily_trend": {
    "2026-03-01": {"created": 5, "closed": 3}
  },
  "issues": [...]
}
```

---

## 作为库使用

除了命令行工具，也可以作为 Python 库在代码中使用：

### 社区洞察

```python
from gitcode_insight import GitCodeCommunityStats, generate_dashboard

# 创建实例
stats = GitCodeCommunityStats(
    config_file="config/gitcode.json",
    output_dir="output/"
)

# 爬取数据
data = stats.crawl_community_stats()

# 保存结果
stats.save_to_csv(data)
stats.save_to_json(data)

# 生成报告
stats.generate_report(data)

# 生成看板
generate_dashboard(
    config_file="config/gitcode.json",
    output_dir="output/"
)
```

### Issue 洞察

```python
from gitcode_insight import GitCodeIssueInsight

# 创建实例
insight = GitCodeIssueInsight(
    repo="kvrocks",
    token="your_token",
    owner="your_org",  # 可选
    days=30,
    output_dir="output/"
)

# 执行分析
result = insight.run()

# 获取结果
print(f"总 Issue 数: {result['summary']['total_issues']}")
print(f"关闭率: {result['summary']['close_rate']}%")
print(f"平均响应时间: {result['efficiency']['avg_first_response_time_minutes']} 分钟")

# 单独调用各方法
issues = insight.get_issues()
insights = insight.calculate_insights(issues_data)
insight.generate_html_report(insights, "report.html")
```

### 自定义处理

```python
from gitcode_insight import GitCodeCommunityStats

stats = GitCodeCommunityStats("config/gitcode.json")

# 只获取项目列表
projects = stats.get_all_community_projects()
print(f"项目数: {len(projects)}")

# 分析单个项目
project_stats = stats.analyze_project_stats("repo-name")
print(f"贡献者: {project_stats['contributor_count']}")
print(f"PR数: {project_stats['total_pr_count']}")
```

---

## 项目结构

```
insight/
├── src/
│   └── gitcode_insight/        # 包源码
│       ├── __init__.py         # 包入口，版本信息
│       ├── cli.py              # 命令行接口
│       ├── community.py        # 社区洞察模块
│       ├── issue.py            # Issue 洞察模块
│       ├── dashboard.py        # 看板生成模块
│       └── utils.py            # 公共工具
├── config/                     # 配置文件目录
│   ├── gitcode.json            # 配置文件（需创建）
│   └── gitcode.json.example    # 配置示例
├── output/                     # 输出文件目录
├── dist/                       # 构建产物
│   ├── gitcode_insight-0.1.0-py3-none-any.whl
│   └── gitcode_insight-0.1.0.tar.gz
├── pyproject.toml              # 包配置
├── LICENSE                     # MIT 许可证
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

**建议：**

- 大型社区（项目数 > 50）爬取时间较长，请耐心等待
- 避免在短时间内多次运行爬取命令
- 如遇频繁限流，可适当增加请求间隔

---

## 开发指南

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/example/insight.git
cd insight

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 开发模式安装
pip install -e ".[dev]"
```

### 运行测试

```bash
python -m pytest tests/
```

### 代码风格

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 函数和类添加 docstring

### 版本发布

```bash
# 更新版本号
# 编辑 src/gitcode_insight/__init__.py 中的 __version__

# 构建
python -m build

# 检查
twine check dist/*

# 上传到 PyPI（需要账号）
twine upload dist/*
```

---

## 常见问题

### Q: 如何获取 GitCode Access Token？

A: 登录 GitCode → 设置 → 访问令牌 → 创建新令牌

### Q: 门禁时长是如何计算的？

A: 通过分析 PR 操作日志，计算 CI 运行标签添加到 CI 成功标签添加的时间间隔。支持蓝区和黄区两种 CI 门禁。

### Q: 输出文件中文乱码怎么办？

A: CSV 文件使用 UTF-8-BOM 编码，Excel 可正常打开。如仍有问题，可使用 VS Code 或其他编辑器打开后另存为正确编码。

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

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

## 联系方式

- 项目主页：https://github.com/example/insight
- 问题反馈：https://github.com/example/insight/issues
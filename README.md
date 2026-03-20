# GitCode Insight - GitCode 平台代码洞察工具

[!\[Python Version\](https://img.shields.io/badge/python-3.7%2B-blue.svg null)](https://www.python.org/downloads/)
[!\[License\](https://img.shields.io/badge/license-MIT-green.svg null)](LICENSE)

GitCode Insight 是一个命令行工具，用于从 GitCode 平台获取数据并生成分析报告。支持社区统计分析、Issue 洞察、PR 洞察、仓库统计（含订阅用户和编程语言）和仓库综合报告，生成可视化看板和 Markdown 报告。

***

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
- [本地调测](#本地调测)
- [常见问题](#常见问题)
- [许可证](#许可证)

***

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

- Issue 总数、未关闭数、已关闭数、关闭率
- 平均首次响应时间
- 平均关闭耗时
- 24小时响应率
- 每日新增/关闭趋势图
- 标签分布、创建人分布
- 生成 HTML 洞察报告

### PR 洞察

分析指定仓库近 N 天的 PR 情况：

- **效率指标**：首次评审时间、合并耗时（平均/最短/最长）、24h评审率
- **质量指标**：平均变更行数、最大变更行数、合并率、冲突率、大PR占比、评论密度
- **分布指标**：创建者、目标分支、标签、评审者分布
- **趋势指标**：每日创建/合并/关闭趋势
- **PR 列表**：所有 PR 基础信息列表，按创建时间排序
- 生成 HTML 可视化报告和 Markdown 报告

### 仓库统计

获取指定仓库的综合统计数据：

- **下载统计**：时间范围下载量、历史累计、日均下载、峰值日、下载趋势图
- **Fork 统计**：Fork 总数、新增 Fork、Fork 人员分布、最新 Fork 信息
- **订阅用户统计**：订阅用户总数、新增订阅、最新订阅用户、订阅趋势图
- **编程语言统计**：语言种类数量、主要编程语言、各语言占比百分比
- **趋势图表**：下载趋势、Fork 趋势、订阅趋势可视化
- **详细列表**：Fork 列表、订阅用户列表
- 生成 HTML 可视化报告和 Markdown 报告

### 仓库综合报告

整合所有模块数据，生成一站式仓库综合分析报告：

- **全模块整合**：Issue + PR + 仓库统计（含订阅用户和编程语言）
- **多格式输出**：HTML 可视化报告 + Markdown 报告 + JSON 数据
- **概览统计**：总 Issue/PR 数、关闭率/合并率、订阅用户、Fork 数
- **详细分析**：Issue 效率指标、PR 效率/质量指标、下载统计、语言分布

***

## 安装

### 方式一：从源码安装

```bash
# 克隆仓库
git clone https://github.com/kerer-ai/insight.git
cd insight

# 创建虚拟环境
python3 -m venv .venv

# 安装（开发模式，包含测试依赖）
.venv/bin/pip install -e ".[test]"
```

> **注意**：推荐直接使用 `.venv/bin/pip` 而不依赖 `source .venv/bin/activate`，避免 shell 环境问题。

### 方式二：构建 wheel 包

```bash
# 安装构建工具
.venv/bin/pip install build

# 构建
.venv/bin/python -m build

# 安装生成的 wheel 包
.venv/bin/pip install dist/gitcode_insight-0.1.0-py3-none-any.whl
```

### 系统要求

- Python 3.7+
- 依赖：`requests >= 2.25.0`

***

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
    "label_yellow_ci_success": "SC-SUCC",
    "repo_whitelist": [],
    "repo_blacklist": []
}
```

仓库白名单/黑名单仅影响社区维度统计（`community` / `dashboard`），用于控制社区统计时包含/排除的仓库范围：

```json
{
    "owner": "boostkit",
    "repo_whitelist": ["opencv", "redis-dtoe"]
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

### 4. 运行 PR 洞察

```bash
gc-insight pr --repo your-repo --token your_token --days 30
```

### 5. 运行仓库统计

```bash
gc-insight repo-stats --repo your-repo --token your_token --days 30
```

### 6. 运行仓库综合报告

```bash
gc-insight report --repo your-repo --token your_token --days 30
```

### 7. 查看输出

所有输出文件默认保存在 `./output/` 目录。

***

## 配置说明

配置文件 `config/gitcode.json` 支持以下配置项：

| 配置项                       | 类型        | 必填 | 说明                                   |
| ------------------------- | --------- | -- | ------------------------------------ |
| `access_token`            | string    | 是  | GitCode API 访问令牌                     |
| `owner`                   | string    | 是  | 组织/社区名称                              |
| `label_ci_success`        | string    | 否  | 蓝区 CI 成功标签，默认 `ci-pipeline-passed`   |
| `label_ci_running`        | string    | 否  | 蓝区 CI 运行中标签，默认 `ci-pipeline-running` |
| `label_yellow_ci_success` | string    | 否  | 黄区 CI 成功标签，默认 `SC-SUCC`              |
| `label_yellow_ci_running` | string    | 否  | 黄区 CI 运行中标签，默认 `SC-RUNNING`          |
| `repo_whitelist`          | string\[] | 否  | 仓库白名单，仅统计白名单内仓库（优先级高于黑名单）            |
| `repo_blacklist`          | string\[] | 否  | 仓库黑名单，统计时跳过黑名单仓库                     |

### 仓库白名单/黑名单（仅社区洞察生效）

该配置只影响社区维度统计命令：`gc-insight community` 与 `gc-insight dashboard`。

- 白名单：仅统计白名单中的仓库
- 黑名单：统计时跳过黑名单中的仓库
- 同时配置：若 `repo_whitelist` 与 `repo_blacklist` 同时存在，则白名单优先
- 仓库名填写：填写仓库的 `path`（URL 最后一段）或仓库 `name` 均可（例如 `opencv`、`redis-dtoe`）

### 获取 Access Token

1. 登录 GitCode
2. 进入「设置」→「访问令牌」
3. 创建新令牌，选择所需权限
4. 复制令牌到配置文件

***

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

| 选项         | 默认值                     | 说明     |
| ---------- | ----------------------- | ------ |
| `--config` | `./config/gitcode.json` | 配置文件路径 |
| `--output` | `./output/`             | 输出目录   |

**示例：**

```bash
# 使用默认配置
gc-insight community

# 指定配置文件和输出目录
gc-insight community --config /path/to/config.json --output /path/to/output/
```

**执行流程：**

1. 读取配置文件
2. 获取组织下所有项目列表（按 `repo_whitelist` / `repo_blacklist` 过滤）
3. 遍历每个项目获取统计数据
4. 保存 CSV 和 JSON 文件
5. 打印统计报告

### gc-insight dashboard

生成可视化看板（自动检测数据，不存在则自动采集）。

```bash
gc-insight dashboard [选项]
```

| 选项         | 默认值                     | 说明     |
| ---------- | ----------------------- | ------ |
| `--config` | `./config/gitcode.json` | 配置文件路径 |
| `--output` | `./output/`             | 输出目录   |

**智能检测：**

- 自动检测数据文件 `{owner}_community_stats_detailed.json` 是否存在
- 如果不存在，自动执行 `community` 采集流程
- 采集完成后自动生成看板
- 生成看板时会按 `repo_whitelist` / `repo_blacklist` 过滤展示范围

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

| 选项         | 必填 | 默认值         | 说明         |
| ---------- | -- | ----------- | ---------- |
| `--repo`   | 是  | -           | 仓库名称（path） |
| `--token`  | 是  | -           | API 访问令牌   |
| `--days`   | 否  | 30          | 统计天数       |
| `--range-by` | 否 | created | 统计范围口径：created=近N天创建；updated=近N天更新；active=近N天创建或更新 |
| `--owner`  | 否  | 从配置读取       | 组织名        |
| `--output` | 否  | `./output/` | 输出目录       |

**示例：**

```bash
# 分析近 30 天的 Issue
gc-insight issue --repo kvrocks --token gct_xxxx

# 分析近 90 天的 Issue
gc-insight issue --repo kvrocks --token gct_xxxx --days 90

# 近 3 天活跃 Issue（近 3 天创建或更新）
gc-insight issue --repo kernel --owner openeuler --token gct_xxxx --days 3 --range-by active
```

### gc-insight pr

分析仓库 PR 数据，提供全面的 PR 洞察分析。

```bash
gc-insight pr --repo REPO --token TOKEN [选项]
```

| 选项         | 必填 | 默认值         | 说明         |
| ---------- | -- | ----------- | ---------- |
| `--repo`   | 是  | -           | 仓库名称（path） |
| `--token`  | 是  | -           | API 访问令牌   |
| `--days`   | 否  | 30          | 统计天数       |
| `--owner`  | 否  | 从配置读取       | 组织名        |
| `--output` | 否  | `./output/` | 输出目录       |

**示例：**

```bash
# 分析近 30 天的 PR
gc-insight pr --repo kernel --token gct_xxxx --owner openeuler

# 分析近 7 天的 PR
gc-insight pr --repo kernel --token gct_xxxx --owner openeuler --days 7
```

**分析指标：**

| 类别 | 指标     | 说明                |
| -- | ------ | ----------------- |
| 效率 | 首次评审时间 | PR 创建到首个非作者评论的时间  |
| 效率 | 合并耗时   | PR 创建到合并的时间（平均/最短/最长） |
| 效率 | 24h评审率 | 24小时内获得评审的 PR 占比  |
| 质量 | 合并率    | 已合并 PR 占总数比例      |
| 质量 | 冲突率    | 存在冲突的 PR 占比       |
| 质量 | 平均变更行数 | PR 平均代码变更量        |
| 质量 | 最大变更行数 | PR 最大代码变更量        |
| 质量 | 大PR占比  | 变更超过 500 行的 PR 占比 |
| 质量 | 评论密度   | 评论数/代码行数          |

**输出示例：**

```
============================================================
PR 洞察分析: openeuler/kernel
分析周期: 近 3 天
============================================================

分析 PR 详情...
共获取到 138 条 PR

分析完成!
============================================================
总 PR 数: 138
已合并: 19
合并率: 13.77%
平均首次评审: 0.2 分钟
平均合并耗时: 165.4 小时
最短合并耗时: 3.1 小时
最长合并耗时: 888.1 小时
平均变更行数: 6059
最大变更行数: 125000
============================================================
```

### gc-insight repo-stats

获取仓库综合统计数据（下载统计 + Fork 分析 + 订阅用户 + 编程语言），并生成 JSON/HTML/Markdown 报告。

```bash
gc-insight repo-stats --repo REPO --token TOKEN [选项]
```

| 选项         | 必填 | 默认值         | 说明         |
| ---------- | -- | ----------- | ---------- |
| `--repo`   | 是  | -           | 仓库名称（path） |
| `--token`  | 是  | -           | API 访问令牌   |
| `--days`   | 否  | 30          | 统计天数       |
| `--owner`  | 否  | 从配置读取       | 组织名        |
| `--output` | 否  | `./output/` | 输出目录       |

**示例：**

```bash
# 获取仓库统计
gc-insight repo-stats --repo kernel --token gct_xxxx --owner openeuler --days 30
```

**输出示例：**

```
============================================================
仓库统计: openeuler/kernel
分析周期: 近 30 天
============================================================

【下载统计】
- 时间范围总下载量: 61142
- 历史累计下载量: 162,547
- 日均下载量: 2038.07
- 下载峰值日: 2026-03-06 (5257 次)
- 活跃下载天数: 28
- 下载趋势: up

【Fork 统计】
- Fork 总数: 244
- 近 30 天新增 Fork: 61
- Fork 人员数: 232
- 最新 Fork: gcw_6G9b00H9/kernel (2026-03-19)

【订阅用户】
- 订阅用户总数: 5
- 近 30 天新增订阅: 0
- 最新订阅用户: qinruan (2025-12-25)

【编程语言】
- 语言种类数: 25
- 主要语言: C

数据已保存到: output/repo_stats_openeuler_kernel_30d.json
HTML 报告: output/repo_stats_openeuler_kernel_30d.html
Markdown 报告: output/repo_stats_openeuler_kernel_30d.md
============================================================
```

### gc-insight report

生成仓库综合报告，整合 Issue、PR、仓库统计、订阅用户、编程语言数据。

```bash
gc-insight report --repo REPO --token TOKEN [选项]
```

| 选项         | 必填 | 默认值         | 说明         |
| ---------- | -- | ----------- | ---------- |
| `--repo`   | 是  | -           | 仓库名称（path） |
| `--token`  | 是  | -           | API 访问令牌   |
| `--days`   | 否  | 30          | 统计天数       |
| `--owner`  | 否  | 从配置读取       | 组织名        |
| `--output` | 否  | `./output/` | 输出目录       |

**示例：**

```bash
# 生成 openeuler/kernel 近 30 天的综合报告
gc-insight report --repo kernel --token gct_xxxx --owner openeuler --days 30

# 生成近 7 天的综合报告
gc-insight report --repo kernel --token gct_xxxx --owner openeuler --days 7
```

**输出示例：**

```
============================================================
仓库综合报告: openeuler/kernel
分析周期: 近 3 天
============================================================

开始采集数据...

采集 Issue 数据...
采集 PR 数据...
采集仓库统计数据...

============================================================
综合报告生成完成!
============================================================
- JSON 数据: output/report_openeuler_kernel_3d.json
- HTML 报告: output/report_openeuler_kernel_3d.html
- Markdown 报告: output/report_openeuler_kernel_3d.md
============================================================
```

**报告内容：**

| 模块       | 内容                               |
| -------- | -------------------------------- |
| 概览统计     | 总 Issue/PR 数、关闭率/合并率、订阅用户、Fork 数 |
| Issue 分析 | 效率指标、每日趋势图                       |
| PR 分析    | 效率指标、质量指标、每日趋势图                  |
| 仓库统计     | 下载统计、Fork 统计                     |
| 社区活跃     | 订阅用户、编程语言分布图                     |

***

## 输出文件

### 社区洞察输出

| 文件名                                     | 格式       | 说明          |
| --------------------------------------- | -------- | ----------- |
| `{owner}_community_stats.csv`           | CSV      | 统计数据表格      |
| `{owner}_community_stats_detailed.json` | JSON     | 完整统计数据      |
| `{owner}_community_dashboard.html`      | HTML     | 可视化看板       |
| `{owner}_community_dashboard.md`        | Markdown | Markdown 报告 |

### Issue 洞察输出

| 文件名                                 | 格式       | 说明              |
| ----------------------------------- | -------- | --------------- |
| `issue_insight_{repo}_{days}d.json` | JSON     | 统计数据 + 原始数据     |
| `issue_insight_{repo}_{days}d.html` | HTML     | 可视化洞察报告         |
| `issue_insight_{repo}_{days}d.md`   | Markdown | Markdown 洞察报告 |

### PR 洞察输出

| 文件名                              | 格式       | 说明              |
| -------------------------------- | -------- | --------------- |
| `pr_insight_{repo}_{days}d.json` | JSON     | 统计数据 + 原始数据     |
| `pr_insight_{repo}_{days}d.html` | HTML     | 可视化洞察报告         |
| `pr_insight_{repo}_{days}d.md`   | Markdown | Markdown 洞察报告 |

### 仓库统计输出

| 文件名                                      | 格式   | 说明             |
| ---------------------------------------- | ---- | -------------- |
| `repo_stats_{owner}_{repo}_{days}d.json` | JSON | 统计数据（下载/Fork/订阅用户/编程语言）+ 原始数据 |
| `repo_stats_{owner}_{repo}_{days}d.html` | HTML | 仓库统计可视化报告 |
| `repo_stats_{owner}_{repo}_{days}d.md` | Markdown | 仓库统计 Markdown 报告 |

### 仓库综合报告输出

| 文件名                                  | 格式       | 说明            |
| ------------------------------------ | -------- | ------------- |
| `report_{owner}_{repo}_{days}d.json` | JSON     | 整合的完整数据       |
| `report_{owner}_{repo}_{days}d.html` | HTML     | 可视化综合报告       |
| `report_{owner}_{repo}_{days}d.md`   | Markdown | Markdown 综合报告 |

***

## 作为库使用

除了命令行工具，也可以作为 Python 库在代码中使用：

```python
from gitcode_insight import (
    GitCodeCommunityStats,
    GitCodeIssueInsight,
    GitCodePRInsight,
    GitCodeRepoStats,
    GitCodeReport,
    generate_dashboard
)

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

# PR 洞察
pr_insight = GitCodePRInsight(
    repo="kernel",
    token="your_token",
    owner="openeuler",
    days=30
)
result = pr_insight.run()

# 仓库统计（包含订阅用户和编程语言）
repo_stats = GitCodeRepoStats(
    repo="kernel",
    token="your_token",
    owner="openeuler",
    days=30
)
result = repo_stats.run()

# 仓库综合报告
report = GitCodeReport(
    repo="kernel",
    token="your_token",
    owner="openeuler",
    days=30
)
result = report.run()
```

***

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
│   ├── repo_stats.py           # 仓库统计模块（含订阅用户和编程语言）
│   ├── report.py               # 仓库综合报告模块
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

| 模块              | 说明                                                     |
| ---------------- | ------------------------------------------------------ |
| `cli.py`         | 命令行入口，定义 `gc-insight` 命令和子命令                           |
| `community.py`   | `GitCodeCommunityStats` 类，社区数据爬取                       |
| `issue.py`       | `GitCodeIssueInsight` 类，Issue 分析                       |
| `pr.py`          | `GitCodePRInsight` 类，PR 洞察分析                           |
| `dashboard.py`   | `generate_dashboard()` 和 `generate_markdown_file()` 函数 |
| `repo_stats.py`  | `GitCodeRepoStats` 类，仓库综合统计（下载/Fork/订阅用户/编程语言）        |
| `report.py`      | `GitCodeReport` 类，仓库综合报告生成                             |
| `utils.py`       | `request_with_retry()` 请求重试工具函数                        |

***

## API 限流说明

GitCode API 限制每分钟 100 次请求。工具已内置以下处理机制：

| 机制     | 说明                    |
| ------ | --------------------- |
| 请求间隔控制 | 每次请求间隔 0.6 秒          |
| 限流重试   | 遇到 429 状态码自动等待 5 秒后重试 |
| 错误重试   | 其他错误等待 3 秒后重试，最多 3 次  |

***

## 本地调测

本章节介绍如何在本地环境中进行开发、调试和测试。

### 1. 克隆代码

```bash
# 克隆仓库
git clone https://github.com/kerer-ai/insight.git
cd insight
```

### 2. 环境准备

```bash
# 创建虚拟环境
python3 -m venv .venv

# 安装（开发模式，包含测试依赖）
.venv/bin/pip install -e ".[test]"
```

### 3. 配置文件

```bash
# 复制配置模板
cp config/gitcode.json.example config/gitcode.json

# 编辑配置文件，填入你的 Access Token 和组织名
vim config/gitcode.json
```

### 4. CLI 命令自验证

开发完成后，可通过 CLI 命令进行功能自验证：

```bash
# 查看帮助
.venv/bin/gc-insight --help

# 测试社区洞察（采集数据）
.venv/bin/gc-insight community

# 测试看板生成（自动检测数据，不存在则自动采集）
.venv/bin/gc-insight dashboard

# 测试 Issue 洞察
.venv/bin/gc-insight issue --repo your-repo --token your_token --days 30

# 测试 PR 洞察
.venv/bin/gc-insight pr --repo your-repo --token your_token --days 30

# 测试仓库统计
.venv/bin/gc-insight repo-stats --repo your-repo --token your_token --days 30

# 测试仓库综合报告
.venv/bin/gc-insight report --repo your-repo --token your_token --days 30
```

### 5. 运行测试

项目包含完整的单元测试，测试覆盖所有核心模块。

#### 基本测试命令

```bash
# 运行所有测试
.venv/bin/pytest

# 运行测试并显示详细输出
.venv/bin/pytest -v

# 运行指定模块的测试
.venv/bin/pytest tests/test_utils.py

# 运行指定的测试类
.venv/bin/pytest tests/test_community.py::TestGitCodeCommunityStats
```

#### 测试覆盖率

```bash
# 生成覆盖率报告
.venv/bin/pytest --cov=gitcode_insight

# 生成详细覆盖率报告（显示未覆盖行）
.venv/bin/pytest --cov=gitcode_insight --cov-report=term-missing
```

#### 集成测试

部分测试标记为 `@pytest.mark.integration`，需要真实的 GitCode API Token：

```bash
# 跳过集成测试（默认）
.venv/bin/pytest -m "not integration"

# 运行集成测试（需设置环境变量）
GITCODE_TOKEN=your_token pytest -m integration
```

### 6. 测试结构

```
tests/
├── __init__.py          # 测试包初始化
├── conftest.py          # pytest 配置和共享 fixtures
├── test_utils.py        # utils 模块测试（请求重试机制）
├── test_community.py    # community 模块测试（社区统计）
├── test_dashboard.py    # dashboard 模块测试（看板生成）
├── test_issue.py        # issue 模块测试（Issue 分析）
├── test_pr.py           # pr 模块测试（PR 洞察分析）
├── test_report.py       # report 模块测试（仓库综合报告）
└── test_cli.py          # cli 模块测试（命令行接口）
```

### 7. 测试覆盖范围

| 模块             | 测试数量 | 覆盖率 | 测试内容                    |
| -------------- | ---- | --- | ----------------------- |
| `utils.py`     | 8    | 91% | 请求重试、限流处理、错误处理          |
| `cli.py`       | 15   | 92% | 参数解析、命令分发               |
| `dashboard.py` | 11   | 98% | HTML/Markdown 生成、统计计算   |
| `community.py` | 14   | 71% | 项目获取、贡献者统计、PR 分析、门禁时长   |
| `issue.py`     | 12   | 65% | Issue 获取、分析、洞察计算        |
| `pr.py`        | 14   | 67% | PR 获取、分析、洞察计算           |
| `report.py`    | 14   | 89% | 数据采集、HTML/Markdown 报告生成 |

### 8. CI/CD 集成

项目配置了 GitHub Actions 自动测试工作流（`.github/workflows/test.yml`）：

- **触发条件**：push 到 main 分支、Pull Request
- **Python 版本**：3.11
- **自动上传覆盖率**：支持 Codecov

***

## 常见问题

### Q: 如何获取 GitCode Access Token？

A: 登录 GitCode → 设置 → 访问令牌 → 创建新令牌

### Q: 门禁时长是如何计算的？

A: 通过分析 PR 操作日志，计算 CI 运行标签添加到 CI 成功标签添加的时间间隔。支持蓝区和黄区两种 CI 门禁。

### Q: 输出文件中文乱码怎么办？

A: CSV 文件使用 UTF-8-BOM 编码，Excel 可正常打开。

### Q: 请求频繁失败怎么办？

A: 检查网络连接，确认 Access Token 有效。如遇限流，等待几分钟后重试。

***

## 更新日志

### v0.5.2 (2026-03-20)

- 修复：`report` 命令 HTML/Markdown 报告数据映射问题
  - 修复 Issue 和 PR 数据从 `statistics` 嵌套结构正确获取
  - 修复 repo_stats 数据提取逻辑（扁平结构而非嵌套）
  - 所有数据（Issue/PR/下载/Fork/订阅用户/编程语言）现已正确显示

### v0.5.1 (2026-03-20)

- 重构：`report` 命令不再复用检测数据文件，改为直接采集生成独立数据文件
  - 产物命名与其他命令独立：`report_{owner}_{repo}_{days}d.json/html/md`
  - 简化数据采集逻辑，移除文件检测代码

### v0.5.0 (2026-03-19)

- 重构：将 `subscribers` 和 `languages` 命令合并到 `repo-stats` 命令
  - `repo-stats` 现在包含四个数据源：下载统计、Fork、订阅用户、编程语言
  - 删除独立的 `subscribers` 和 `languages` CLI 子命令
  - 删除 `GitCodeSubscribers` 和 `GitCodeLanguages` 类
  - 更新 `report` 命令以从 `repo-stats` 数据中提取订阅用户和编程语言信息
- 测试数量：97 个测试用例

### v0.4.0 (2026-03-19)

- 新增 `report` 命令：仓库综合报告
  - 智能数据采集：自动检测数据文件，不存在则调用对应命令采集
  - 全模块整合：Issue + PR + 仓库统计 + 订阅用户 + 编程语言
  - 多格式输出：HTML 可视化报告 + Markdown 报告 + JSON 数据
  - 概览统计：总 Issue/PR 数、关闭率/合并率、订阅用户、Fork 数
- 新增 `test_report.py` 测试模块（14 个测试用例）
- 总测试数量达到 91 个，覆盖率 66%

### v0.3.0 (2026-03-19)

- 新增 `pr` 命令：PR 洞察分析
  - 效率指标：首次评审时间、合并耗时、平均打开天数、24h评审率
  - 质量指标：合并率、草稿率、冲突率、CI成功率
  - 规模指标：平均变更行数、大PR占比、评论密度
  - 分布指标：创建者、目标分支、标签、评审者、合并者分布
  - 趋势指标：每日创建/合并/关闭趋势
  - 生成 HTML 可视化报告
- 新增 `test_pr.py` 测试模块（14 个测试用例）
- 新增 PR 列表 API 文档

### v0.2.0 (2026-03-19)

- 新增 `repo-stats` 命令：仓库综合统计（下载统计 + Fork 列表）
- 新增 `subscribers` 命令：订阅用户统计
- 新增 `languages` 命令：编程语言占比统计
- 新增命令开发流程文档（`.skill/develop-command.md`）
- 完善 GitCode API 文档

### v0.1.0 (2026-03-19)

- 初始版本
- 支持社区洞察功能
- 支持 Issue 洞察功能
- 支持生成 HTML 看板和 Markdown 报告
- 命令行工具 `gc-insight`
- `dashboard` 命令支持自动检测并采集数据
- 完整的单元测试覆盖（60 个测试，79% 覆盖率）
- CI/CD 自动测试工作流

***

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

***

## 贡献

欢迎提交 Issue 和 Pull Request！

- 项目主页：<https://github.com/kerer-ai/insight>
- 问题反馈：<https://github.com/kerer-ai/insight/issues>

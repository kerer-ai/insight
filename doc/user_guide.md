# GitCode Insight 用户指南

## 目录

- [安装](#安装)
- [配置说明](#配置说明)
- [命令详解](#命令详解)
- [输出文件](#输出文件)
- [作为库使用](#作为库使用)

## 安装

### 方式一：pip 安装

```bash
pip install gitcode-insight
```

### 方式二：从源码安装

```bash
# 克隆仓库
git clone https://gitcode.com/gitcode-cli/insight.git
cd insight

# 创建虚拟环境
python3 -m venv .venv

# 安装（开发模式）
.venv/bin/pip install -e ".[test]"
```

### 系统要求

- Python 3.7+
- 依赖：`requests >= 2.25.0`

## 配置说明

### 创建配置文件

```bash
cp config/gitcode.json.example config/gitcode.json
```

### 配置项

| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `access_token` | string | 是 | GitCode API 访问令牌 |
| `owner` | string | 是 | 组织/社区名称 |
| `label_ci_success` | string | 否 | 蓝区 CI 成功标签，默认 `ci-pipeline-passed` |
| `label_ci_running` | string | 否 | 蓝区 CI 运行中标签，默认 `ci-pipeline-running` |
| `label_yellow_ci_success` | string | 否 | 黄区 CI 成功标签，默认 `SC-SUCC` |
| `label_yellow_ci_running` | string | 否 | 黄区 CI 运行中标签，默认 `SC-RUNNING` |
| `repo_whitelist` | string[] | 否 | 仓库白名单（仅影响 community/dashboard） |
| `repo_blacklist` | string[] | 否 | 仓库黑名单（仅影响 community/dashboard） |

### 获取 Access Token

1. 登录 GitCode
2. 进入「设置」→「访问令牌」
3. 创建新令牌，选择所需权限
4. 复制令牌到配置文件

### 仓库白名单/黑名单

仅影响 `community` 和 `dashboard` 命令：

```json
{
    "owner": "boostkit",
    "repo_whitelist": ["opencv", "redis-dtoe"]
}
```

- 白名单：仅统计白名单中的仓库
- 黑名单：统计时跳过黑名单中的仓库
- 同时配置时白名单优先

## 命令详解

### gc-insight community

获取社区统计数据。

```bash
gc-insight community [选项]
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--config` | `./config/gitcode.json` | 配置文件路径 |
| `--output` | `./output/` | 输出目录 |

**执行流程**：
1. 读取配置文件
2. 获取组织下所有项目列表
3. 遍历获取统计数据
4. 保存 CSV 和 JSON 文件

### gc-insight dashboard

生成可视化看板（自动检测数据，不存在则自动采集）。

```bash
gc-insight dashboard [选项]
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--config` | `./config/gitcode.json` | 配置文件路径 |
| `--output` | `./output/` | 输出目录 |

**智能检测**：
- 自动检测数据文件是否存在
- 不存在则自动执行 `community` 采集
- 采集完成后生成看板

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
| `--range-by` | 否 | created | 统计范围：created/updated/active |
| `--owner` | 否 | 从配置读取 | 组织名 |
| `--output` | 否 | `./output/` | 输出目录 |

**--range-by 说明**：
- `created`: 近 N 天创建的 Issue
- `updated`: 近 N 天更新的 Issue
- `active`: 近 N 天创建或更新的 Issue

**分析指标**：

| 指标 | 说明 |
|------|------|
| Issue 总数 | 统计范围内的 Issue 数量 |
| 未关闭数 | 未关闭的 Issue 数量 |
| 关闭率 | 已关闭 Issue 占比 |
| 平均首次响应时间 | Issue 创建到首个评论的时间 |
| 平均关闭耗时 | Issue 创建到关闭的时间 |
| 24小时响应率 | 24小时内获得响应的 Issue 占比 |

### gc-insight pr

分析仓库 PR 数据。

```bash
gc-insight pr --repo REPO --token TOKEN [选项]
```

| 选项 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--repo` | 是 | - | 仓库名称（path） |
| `--token` | 是 | - | API 访问令牌 |
| `--days` | 否 | 30 | 统计天数 |
| `--owner` | 否 | 从配置读取 | 组织名 |
| `--output` | 否 | `./output/` | 输出目录 |

**分析指标**：

| 类别 | 指标 | 说明 |
|------|------|------|
| 效率 | 首次评审时间 | PR 创建到首个非作者评论的时间 |
| 效率 | 合并耗时 | PR 创建到合并的时间 |
| 效率 | 24h评审率 | 24小时内获得评审的 PR 占比 |
| 质量 | 合并率 | 已合并 PR 占比 |
| 质量 | 冲突率 | 存在冲突的 PR 占比 |
| 质量 | CI 成功率 | CI 通过的 PR 占比 |
| 规模 | 平均变更行数 | PR 平均代码变更量 |
| 规模 | 大PR占比 | 变更超过 500 行的 PR 占比 |
| 规模 | 评论密度 | 评论数/代码行数 |

### gc-insight repo-stats

获取仓库综合统计数据。

```bash
gc-insight repo-stats --repo REPO --token TOKEN [选项]
```

| 选项 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--repo` | 是 | - | 仓库名称（path） |
| `--token` | 是 | - | API 访问令牌 |
| `--days` | 否 | 30 | 统计天数 |
| `--owner` | 否 | 从配置读取 | 组织名 |
| `--output` | 否 | `./output/` | 输出目录 |

**统计内容**：
- 下载统计：期间下载量、累计下载、日均下载、峰值日、趋势
- Fork 统计：Fork 总数、新增 Fork、人员分布
- 订阅用户：订阅用户总数、新增订阅、最新订阅用户
- 编程语言：语言种类、主要语言、语言占比

### gc-insight report

生成仓库综合报告，整合所有模块数据。

```bash
gc-insight report --repo REPO --token TOKEN [选项]
```

| 选项 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--repo` | 是 | - | 仓库名称（path） |
| `--token` | 是 | - | API 访问令牌 |
| `--days` | 否 | 30 | 统计天数 |
| `--owner` | 否 | 从配置读取 | 组织名 |
| `--output` | 否 | `./output/` | 输出目录 |

**报告内容**：
- 概览统计：Issue/PR 总数、关闭率/合并率、订阅用户、Fork 数
- Issue 分析：效率指标、标签分布、创建人分布、每日趋势
- PR 分析：效率指标、质量指标、分布分析、每日趋势
- 仓库统计：下载统计、Fork 统计
- 社区活跃：订阅用户、编程语言分布

## 输出文件

### 社区洞察

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `{owner}_community_stats.csv` | CSV | 统计数据表格 |
| `{owner}_community_stats_detailed.json` | JSON | 完整统计数据 |
| `{owner}_community_dashboard.html` | HTML | 可视化看板 |
| `{owner}_community_dashboard.md` | Markdown | Markdown 报告 |

### Issue/PR 洞察

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `{module}_insight_{repo}_{days}d.json` | JSON | 统计数据 |
| `{module}_insight_{repo}_{days}d.html` | HTML | 可视化报告 |
| `{module}_insight_{repo}_{days}d.md` | Markdown | Markdown 报告 |

### 仓库统计/综合报告

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `{prefix}_{owner}_{repo}_{days}d.json` | JSON | 统计数据 |
| `{prefix}_{owner}_{repo}_{days}d.html` | HTML | 可视化报告 |
| `{prefix}_{owner}_{repo}_{days}d.md` | Markdown | Markdown 报告 |

## 作为库使用

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

# Issue 洞察
insight = GitCodeIssueInsight(repo="kvrocks", token="your_token", days=30)
result = insight.run()

# PR 洞察
pr_insight = GitCodePRInsight(repo="kernel", token="your_token", owner="openeuler", days=30)
result = pr_insight.run()

# 仓库统计
repo_stats = GitCodeRepoStats(repo="kernel", token="your_token", owner="openeuler", days=30)
result = repo_stats.run()

# 综合报告
report = GitCodeReport(repo="kernel", token="your_token", owner="openeuler", days=30)
result = report.run()
```

## API 限流说明

GitCode API 每分钟限制 100 次请求。工具内置处理机制：

| 机制 | 说明 |
|------|------|
| 请求间隔控制 | 每次请求间隔 0.6 秒 |
| 限流重试 | 遇到 429 状态码自动等待 5 秒后重试 |
| 错误重试 | 其他错误等待 3 秒后重试，最多 3 次 |
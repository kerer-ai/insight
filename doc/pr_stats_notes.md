# PR 统计模块开发笔记

## 概述

本文档记录了 `gc-insight pr` 命令开发过程中遇到的问题、解决方案和注意事项。

## GitCode PR API 特殊性

### PR 状态值

GitCode API 返回的 PR `state` 字段值为：
- `"open"` - 打开中
- `"merged"` - 已合并
- `"closed"` - 已关闭（未合并）

**注意**：不是 `"opened"`，只有 `"open"`。这与 Issue 不同（Issue 只有 `"open"` 和 `"closed"`）。

### 合并状态判断

判断 PR 是否已合并，应优先检查 `merged_at` 字段：

```python
# 推荐方式
merged_prs = [pr for pr in prs_data if pr["merged_at"]]

# 不推荐
merged_prs = [pr for pr in prs_data if pr["state"] == "merged"]
```

### 关闭状态判断

关闭但未合并的 PR 需同时检查两个条件：

```python
closed_not_merged = [pr for pr in prs_data if pr["state"] == "closed" and not pr["merged_at"]]
```

### API 返回示例

```json
{
  "id": 12345,
  "number": 100,
  "state": "merged",
  "title": "feat: add new feature",
  "created_at": "2026-03-10T10:00:00+08:00",
  "updated_at": "2026-03-15T14:30:00+08:00",
  "merged_at": "2026-03-15T14:30:00+08:00",
  "closed_at": null,
  "merged_by": {"login": "reviewer1"},
  "source_branch": "feature-branch",
  "target_branch": "main",
  "added_lines": 150,
  "removed_lines": 30,
  "draft": false,
  "mergeable": true,
  "pipeline_status": "success"
}
```

## 发现的 Bug 及修复

### Bug 1: `daily_trend` 合并/关闭计数不准确

**表现**：`daily_trend` 中合并/关闭总数与实际数不一致。

**案例**：
- 实际合并 PR：10 个
- `daily_trend` 合并总数：9 个
- 差异原因：某天有 PR 合并，但该天没有 PR 创建

**原因代码**：

```python
# pr.py:336-339 (修复前)
for pr in merged:
    try:
        merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
        date_str = merged_date.strftime("%Y-%m-%d")
        if date_str in daily_trend:  # BUG: 只在日期已存在时计数
            daily_trend[date_str]["merged"] += 1
    except:
        pass
```

**问题分析**：
- `daily_trend` 字典只包含有 PR 创建的日期
- 当 PR 在没有新 PR 创建的日期被合并时，该日期不在 `daily_trend` 中
- 导致合并计数丢失

**修复方案**：

```python
for pr in merged:
    try:
        merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
        date_str = merged_date.strftime("%Y-%m-%d")
        if date_str not in daily_trend:  # 修复：日期不存在则创建
            daily_trend[date_str] = {"created": 0, "merged": 0, "closed": 0}
        daily_trend[date_str]["merged"] += 1
    except:
        pass
```

**相同问题位置**：
- `pr.py` line 336（合并计数）
- `pr.py` line 345（关闭计数）

## 统计指标计算

### 1. 概览统计

| 指标 | 数据来源 | 计算方式 |
|------|----------|----------|
| 总 PR 数 | API 返回的 PR 列表 | 时间范围内过滤后的 PR 总数 |
| 打开中 | PR `state` 字段 | `state == "open"` 的 PR 数量 |
| 已合并 | PR `merged_at` 字段 | `merged_at` 非空的 PR 数量（非 `state == "merged"`） |
| 已关闭(未合并) | PR `state` + `merged_at` | `state == "closed" and not merged_at` 的 PR 数量 |
| 合并率 | 计算得出 | `已合并 / 总数 * 100%` |
| 冲突率 | PR `mergeable` 字段 | `mergeable == False` 的 PR 占比 |

**代码位置**：`pr.py:246-254`

```python
opened = [p for p in prs_data if p["state"] == "open"]
merged = [p for p in prs_data if p["merged_at"]]
closed_not_merged = [p for p in prs_data if p["state"] == "closed" and not p["merged_at"]]
conflicts = [p for p in prs_data if p["mergeable"] is False]
```

### 2. 效率指标

| 指标 | 数据来源 | 计算方式 |
|------|----------|----------|
| 平均首次评审(分钟) | PR 评论 API | 非创建者的首条评论时间 - PR 创建时间，取平均值 |
| 平均合并耗时(小时) | PR `merged_at` + `created_at` | `merged_at - created_at`，已合并 PR 的平均值，转换为小时 |
| 最短合并耗时(小时) | PR `merged_at` + `created_at` | 已合并 PR 中耗时最短的，转换为小时 |
| 最长合并耗时(小时) | PR `merged_at` + `created_at` | 已合并 PR 中耗时最长的，转换为小时 |
| 24h 评审率 | 计算得出 | 首次评审时间 ≤ 1440 分钟（24小时）的 PR 占比 |

**首次评审时间计算**（`pr.py:129-143`）：

```python
comments = self.get_pr_comments(pr_number)
if comments:
    creator_id = pr.get("user", {}).get("id")
    for comment in comments:
        commenter_id = comment.get("user", {}).get("id")
        if commenter_id != creator_id:  # 排除创建者自己的评论
            comment_time = datetime.fromisoformat(comment["created_at"])
            created_time = datetime.fromisoformat(pr["created_at"])
            first_review_time = (comment_time - created_time).total_seconds() / 60
            break
```

**合并耗时计算**（`pr.py:146-153`）：

```python
if merged_at and created_at_str:
    merged_time = datetime.fromisoformat(merged_at)
    created_time = datetime.fromisoformat(created_at_str)
    merge_duration = (merged_time - created_time).total_seconds() / 60
```

### 3. 质量指标

| 指标 | 数据来源 | 计算方式 |
|------|----------|----------|
| 平均变更行数 | PR `added_lines` + `removed_lines` | `(added_lines + removed_lines)` 的平均值 |
| 最大变更行数 | PR `added_lines` + `removed_lines` | `(added_lines + removed_lines)` 的最大值 |
| 大 PR 数(>500行) | PR 变更行数 | `total_changes > 500` 的 PR 数量 |
| 大 PR 占比 | 计算得出 | 大 PR 数 / 总数 * 100% |
| 评论密度 | PR `notes` 字段 | 总评论数 / 总变更行数 |

**代码位置**：`pr.py:256-264`

```python
change_sizes = [p["total_changes"] for p in prs_data if p["total_changes"] > 0]
avg_changes = sum(change_sizes) / len(change_sizes) if change_sizes else 0
max_changes = max(change_sizes) if change_sizes else 0
large_prs = [p for p in prs_data if p["total_changes"] > 500]

total_notes = sum(p["notes_count"] for p in prs_data)
total_lines = sum(p["total_changes"] for p in prs_data)
comment_density = total_notes / total_lines if total_lines > 0 else 0
```

### 4. 分布统计

| 指标 | 数据来源 | 计算方式 |
|------|----------|----------|
| 创建者分布 Top 10 | PR `user.login` | 按创建者分组统计 PR 数量，取前 10 |
| 目标分支分布 | PR `target_branch` | 按目标分支分组统计 |
| 标签分布 | PR `labels[].name` | 按标签分组统计 |
| 评审者分布 | PR `assignees[].login` | 按负责人分组统计 |

### 5. 每日趋势

| 指标 | 数据来源 | 计算方式 |
|------|----------|----------|
| 创建数 | PR `created_at` | 按日期分组统计 PR 创建数 |
| 合并数 | PR `merged_at` | 按日期分组统计 PR 合并数 |
| 关闭数 | PR `closed_at` | 按日期分组统计 PR 关闭数（未合并） |

**代码位置**：`pr.py:320-348`

```python
# 创建趋势
for pr in prs_data:
    created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
    date_str = created.strftime("%Y-%m-%d")
    if date_str not in daily_trend:
        daily_trend[date_str] = {"created": 0, "merged": 0, "closed": 0}
    daily_trend[date_str]["created"] += 1

# 合并趋势
for pr in merged:
    merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
    date_str = merged_date.strftime("%Y-%m-%d")
    if date_str not in daily_trend:
        daily_trend[date_str] = {"created": 0, "merged": 0, "closed": 0}
    daily_trend[date_str]["merged"] += 1
```

### 6. 数据来源总结

| API 接口 | 用途 |
|----------|------|
| `GET /repos/{owner}/{repo}/pulls` | 获取 PR 列表及基础信息 |
| `GET /repos/{owner}/{repo}/pulls/{number}/comments` | 获取 PR 评论，计算首次评审时间 |

**API 返回的关键字段**：

| 字段 | 用途 |
|------|------|
| `state` | PR 状态（open/merged/closed） |
| `merged_at` | 合并时间，判断是否已合并 |
| `closed_at` | 关闭时间 |
| `created_at` | 创建时间 |
| `draft` | 是否草稿 |
| `mergeable` | 是否可合并（检测冲突） |
| `added_lines` / `removed_lines` | 代码变更行数 |
| `notes` | 评论数 |
| `pipeline_status` | CI 状态 |
| `user.login` | 创建者 |
| `merged_by.login` | 合并者 |
| `assignees` | 负责人列表 |
| `labels` | 标签列表 |
| `target_branch` | 目标分支 |

## API 限流处理

GitCode API 限制每分钟 100 次请求。代码通过以下方式处理：

1. **请求间隔**：每次请求后 `time.sleep(0.6)` 秒
2. **429 重试**：遇到 429 状态码自动等待后重试
3. **统一请求函数**：使用 `utils.request_with_retry()`

## 输出格式

PR 洞察命令生成三个输出文件，格式与 Issue 命令保持一致：

### 输出文件

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `pr_insight_{repo}_{days}d.json` | JSON | 统计数据 + 原始数据 |
| `pr_insight_{repo}_{days}d.html` | HTML | 可视化洞察报告 |
| `pr_insight_{repo}_{days}d.md` | Markdown | Markdown 洞察报告 |

### JSON 文件结构

```json
{
  "statistics": {
    "repo": "openeuler/kernel",
    "analysis_period": "近 7 天",
    "analysis_time": "2026-03-19 19:18:56",
    "summary": {
      "total_prs": 189,
      "opened_prs": 76,
      "merged_prs": 40,
      "closed_prs": 73,
      "merge_rate": 21.16,
      "conflict_rate": 0.53
    },
    "efficiency": {
      "avg_first_review_time_minutes": 0.2,
      "avg_merge_duration_hours": 97.86,
      "min_merge_duration_hours": 3.1,
      "max_merge_duration_hours": 888.1,
      "timely_review_rate": 100.0,
      "review_time_samples": 189,
      "merge_duration_samples": 40
    },
    "quality": {
      "avg_change_lines": 4520.98,
      "max_change_lines": 125000,
      "large_pr_count": 25,
      "large_pr_rate": 13.23,
      "comment_density": 0.0065
    },
    "distribution": {
      "by_creator": {"gaojuxin09": 70, ...},
      "by_target_branch": {"OLK-6.6": 163, ...},
      "by_label": {"sig/Kernel": 188, ...},
      "by_reviewer": {"zhengzengkai": 188, ...}
    },
    "daily_trend": {
      "2026-03-12": {"created": 30, "merged": 5, "closed": 10},
      ...
    }
  },
  "raw_data": [
    {
      "pr_number": 21311,
      "title": "feat: ...",
      "state": "open",
      "creator": "user1",
      ...
    },
    ...
  ]
}
```

### HTML 报告内容

HTML 报告包含以下部分：

1. **概览统计**：总 PR 数、打开中、已合并、已关闭、合并率、冲突率
2. **效率指标**：平均首次评审时间、平均合并耗时、最短合并耗时、最长合并耗时、24h 评审率
3. **质量指标**：平均变更行数、最大变更行数、大 PR 数、大 PR 占比、评论密度
4. **趋势图表**：每日 PR 趋势、创建者分布、目标分支分布、代码变更规模分布
5. **分布统计**：创建者、目标分支、标签分布列表
6. **PR 列表**：所有 PR 基础信息表格，包含 PR 编号、标题、状态、创建者、目标分支、变更行数、创建时间

### Markdown 报告内容

Markdown 报告包含：

- 概览统计表格
- 效率指标表格
- 质量指标表格
- 每日趋势表格
- 各分布统计表格

### 与 Issue 命令的一致性

PR 命令输出格式与 Issue 命令保持一致：

- **不输出 CSV 文件**：统计数据和原始数据统一保存在 JSON 文件中
- **JSON 结构**：`statistics` 存储汇总指标，`raw_data` 存储原始 PR 数据
- **三种格式**：JSON（数据）、HTML（可视化）、Markdown（文档）

## 相关文档

- [GitCode PR API 文档](./gitcode_api/pulls_list.md)
- [Issue 统计模块开发笔记](./issue_stats_notes.md)
- [开发新命令流程](../.skill/develop-command.md)
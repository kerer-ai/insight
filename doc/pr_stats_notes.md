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

### 核心指标

| 指标 | 计算方式 | 数据来源 |
|------|----------|----------|
| 总 PR 数 | 时间范围内 PR 总数 | API 返回 |
| 打开中 PR | state=open 的数量 | API state 字段 |
| 已合并 PR | merged_at 非空的数量 | API merged_at 字段 |
| 已关闭 PR | state=closed 且 merged_at 为空 | API state + merged_at |
| 合并率 | 已合并 / 总数 * 100% | 计算得出 |
| 平均首次评审时间 | 首条评论时间 - 创建时间 | 评论 API |
| 平均合并耗时 | merged_at - created_at | API merged_at |
| 24h 评审率 | 24 小时内评审的 PR 占比 | 评论数据计算 |

### 首次评审时间计算

```python
def analyze_pr(self, pr):
    comments = self.get_pr_comments(pr["number"])

    first_review_time = None
    if comments:
        creator_id = pr.get("user", {}).get("id")
        for comment in comments:
            commenter_id = comment.get("user", {}).get("id")
            if commenter_id != creator_id:  # 排除创建者自己的评论
                try:
                    comment_time = datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00"))
                    created_time = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    first_review_time = (comment_time - created_time).total_seconds() / 60
                except:
                    pass
                break
```

## API 限流处理

GitCode API 限制每分钟 100 次请求。代码通过以下方式处理：

1. **请求间隔**：每次请求后 `time.sleep(0.6)` 秒
2. **429 重试**：遇到 429 状态码自动等待后重试
3. **统一请求函数**：使用 `utils.request_with_retry()`

## 相关文档

- [GitCode PR API 文档](./gitcode_api/pulls_list.md)
- [Issue 统计模块开发笔记](./issue_stats_notes.md)
- [开发新命令流程](../.skill/develop-command.md)
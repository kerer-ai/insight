# Issue 统计模块开发笔记

## 概述

本文档记录了 `gc-insight issue` 命令开发过程中遇到的问题、解决方案和注意事项。

## GitCode Issue API 特殊性

### `finished_at` vs `closed_at`

**发现的问题**：GitCode API 返回的 Issue 数据中，`closed_at` 字段始终为 `null`，即使 Issue 已关闭。

**根本原因**：GitCode 使用 `finished_at` 字段存储关闭时间，而非标准的 `closed_at`。

**API 返回示例**：

```json
{
  "id": 3796585,
  "number": "8696",
  "state": "closed",
  "title": "[OLK-6.6] l2tp: fix double dst_release()",
  "created_at": "2026-03-10T17:45:19+08:00",
  "updated_at": "2026-03-19T11:03:26+08:00",
  "finished_at": "2026-03-19T11:03:19+08:00",
  "closed_at": null,
  "issue_state": "已完成"
}
```

**修复方案**：代码中优先使用 `finished_at`，并 fallback 到 `closed_at`：

```python
finished_at = issue.get("finished_at") or issue.get("closed_at")
```

### Issue 状态值

GitCode API 中 Issue 的 `state` 字段值为：
- `"open"` - 开放状态
- `"closed"` - 已关闭状态

注意：不是 `"opened"`，只有 `"open"`。

### 时区处理

API 返回的时间带有 `+08:00` 时区标识（北京时间），代码中需要正确处理：

```python
# 处理时区
datetime.fromisoformat(time_str.replace("Z", "+00:00"))
```

## 发现的 Bug 及修复

### Bug 1: 关闭时间始终为空

**表现**：所有已关闭 Issue 的关闭耗时都为 0 或 None。

**原因**：代码使用 `closed_at` 字段，但 GitCode API 该字段始终为 null。

**影响**：无法正确计算：
- 平均关闭耗时
- 每日关闭趋势
- 关闭效率指标

**修复**：见上文 `finished_at` 处理方案。

**测试数据**：修复前关闭耗时为 0.0 小时，修复后为 9.1 小时。

### Bug 2: `daily_trend` 关闭计数不准确

**表现**：`daily_trend` 中关闭总数与实际关闭数不一致。

**案例**：
- 实际关闭 Issue：16 个
- `daily_trend` 关闭总数：15 个
- 差异原因：2026-03-14 有 1 个 Issue 关闭，但该天没有 Issue 创建

**原因代码**：

```python
# issue.py:277-284 (修复前)
for issue in closed:
    try:
        finished_date = datetime.fromisoformat(issue["finished_at"].replace("Z", "+00:00"))
        date_str = finished_date.strftime("%Y-%m-%d")
        if date_str in daily_trend:  # BUG: 只在日期已存在时计数
            daily_trend[date_str]["closed"] += 1
    except:
        pass
```

**问题分析**：
- `daily_trend` 字典只包含有 Issue 创建的日期
- 当 Issue 在没有新 Issue 创建的日期被关闭时，该日期不在 `daily_trend` 中
- 导致关闭计数丢失

**修复方案**：

```python
for issue in closed:
    try:
        finished_date = datetime.fromisoformat(issue["finished_at"].replace("Z", "+00:00"))
        date_str = finished_date.strftime("%Y-%m-%d")
        if date_str not in daily_trend:  # 修复：日期不存在则创建
            daily_trend[date_str] = {"created": 0, "closed": 0}
        daily_trend[date_str]["closed"] += 1
    except:
        pass
```

**测试用例**：

```python
def test_calculate_insights_daily_trend_closed_on_different_day(self, temp_output_dir):
    """测试每日趋势 - Issue 在没有新 Issue 创建的日期被关闭"""
    # Issue 创建于 day1，关闭于 day3（day3 没有新 Issue 创建）
    issues_data = [
        {
            "issue_number": 1,
            "state": "closed",
            "created_at": (now - timedelta(days=5)).isoformat(),  # day1
            "finished_at": (now - timedelta(days=3)).isoformat(),  # day3
            # ...
        }
    ]

    insights, _ = insight.calculate_insights(issues_data)

    # 验证 daily_trend 包含关闭日期
    daily_trend = insights["daily_trend"]
    closed_dates = [date for date, counts in daily_trend.items() if counts["closed"] > 0]
    assert len(closed_dates) == 1
```

## 时间范围过滤逻辑

### `since` 参数

GitCode API 的 `since` 参数用于过滤结果，但 API 可能返回比 `since` 时间更早的数据。因此需要在代码中进行二次过滤：

```python
def get_issues(self):
    # ... API 调用 ...

    # 二次过滤确保时间范围准确
    filtered_issues = []
    for issue in all_issues:
        created_at = issue.get("created_at")
        if created_at and self._is_within_range(created_at):
            filtered_issues.append(issue)

    return filtered_issues
```

### `range_by` 参数

支持三种时间范围统计口径：

| 参数值 | 说明 | 过滤字段 |
|--------|------|----------|
| `created` | 按 created_at 过滤 | Issue 创建时间 |
| `updated` | 按 updated_at 过滤 | Issue 更新时间 |
| `active` | 创建或更新都在范围内 | created_at 或 updated_at |

## 统计指标计算

### 核心指标

| 指标 | 计算方式 | 数据来源 |
|------|----------|----------|
| 总 Issue 数 | 时间范围内 Issue 总数 | API 返回 |
| 新增 Issue | 新创建的 Issue 数 | created_at 在范围内 |
| 未关闭 Issue | state=open 的数量 | API state 字段 |
| 已关闭 Issue | state=closed 的数量 | API state 字段 |
| 关闭率 | 已关闭 / 总数 * 100% | 计算得出 |
| 平均首次响应时间 | 首条评论时间 - 创建时间 | 评论 API |
| 平均关闭耗时 | finished_at - created_at | API finished_at |
| 24h 响应率 | 24 小时内响应的 Issue 占比 | 评论数据计算 |

### 首次响应时间计算

```python
def analyze_issue(self, issue):
    comments = self.get_issue_comments(issue["number"])

    if comments:
        # 排除创建者自己的评论
        creator_login = issue["user"]["login"]
        first_response = next(
            (c for c in comments if c["user"]["login"] != creator_login),
            None
        )
        if first_response:
            created_time = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
            response_time = datetime.fromisoformat(first_response["created_at"].replace("Z", "+00:00"))
            first_response_time = (response_time - created_time).total_seconds() / 60
```

## API 限流处理

GitCode API 限制每分钟 100 次请求。代码中通过以下方式处理：

1. **请求间隔**：每次请求后 `time.sleep(0.6)` 秒
2. **429 重试**：遇到 429 状态码自动等待后重试
3. **统一请求函数**：使用 `utils.request_with_retry()`

```python
# utils.py
def request_with_retry(url, params=None, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, params=params)
        if response.status_code == 429:
            time.sleep(60)  # 等待限流解除
            continue
        if response.status_code == 200:
            return response.json()
    return None
```

## 测试数据结构

### Issue 数据 Fixture

```python
# tests/conftest.py
@pytest.fixture
def sample_issue_data():
    now = datetime.now(timezone.utc)
    return [
        {
            "number": 1,
            "title": "Bug: Something is broken",
            "state": "open",
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": (now - timedelta(days=4)).isoformat(),
            "finished_at": None,
            "user": {"id": 1, "login": "user1"},
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "developer1"}],
            "comments": 2,
            "milestone": None,
            "html_url": "https://gitcode.com/test_org/test-project/issues/1"
        },
        {
            "number": 2,
            "title": "Feature: New feature request",
            "state": "closed",
            "created_at": (now - timedelta(days=10)).isoformat(),
            "finished_at": (now - timedelta(days=8)).isoformat(),
            # ...
        }
    ]
```

## 相关文档

- [GitCode Issue API 文档](./gitcode_api/issue_api.md)
- [开发新命令流程](../.skill/develop-command.md)
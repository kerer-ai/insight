# GitCode Issue 查询接口文档

## 文档说明

| 项目 | 说明 |
|------|------|
| 接口版本 | v5 |
| 基础域名 | `https://api.gitcode.com/api/v5` |
| 请求方式 | GET（查询类，无写操作） |
| 认证方式 | 全部接口必须携带 `access_token` 查询参数 |
| 响应格式 | application/json |

## 接口目录

1. [获取仓库 Issue 列表](#1-获取仓库-issue-列表)
2. [获取单个 Issue 详情](#2-获取单个-issue-详情)
3. [获取 Issue 评论列表](#3-获取-issue-评论列表)
4. [获取 Issue 事件列表](#4-获取-issue-事件列表)
5. [获取仓库 Issue 标签列表](#5-获取仓库-issue-标签列表)
6. [获取仓库 Issue 可指派人员列表](#6-获取仓库-issue-可指派人员列表)

---

## 1. 获取仓库 Issue 列表

### 基本信息

| 项目 | 说明 |
|------|------|
| 接口地址 | `GET /repos/:owner/:repo/issues` |
| 功能 | 查询指定仓库下的 Issue 列表，支持筛选、分页、排序 |
| 权限 | 需仓库访问权限 |

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 个人/组织 path |
| repo | string | 是 | 仓库 path |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 用户授权码 |
| state | string | 否 | 状态：`opened` / `closed` / `all`，默认 opened |
| labels | string | 否 | 标签名，多个用逗号分隔 |
| since | string | 否 | 起始时间，格式：ISO 8601 |
| page | integer | 否 | 页码，默认 1 |
| per_page | integer | 否 | 每页条数，默认 20 |
| sort | string | 否 | 排序字段：`created` / `updated` |
| direction | string | 否 | 排序方向：`asc` / `desc` |

### 请求示例

```http
GET https://api.gitcode.com/api/v5/repos/testowner/testrepo/issues?access_token=xxx&state=opened&page=1&per_page=20
```

### 响应

- **200**: 返回 Issue 数组，字段结构同「单个 Issue」

---

## 2. 获取单个 Issue 详情

### 基本信息

| 项目 | 说明 |
|------|------|
| 接口地址 | `GET /repos/:owner/:repo/issues/:number` |
| 功能 | 获取指定 Issue 完整信息 |

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 个人/组织 path |
| repo | string | 是 | 仓库 path |
| number | string | 是 | Issue 编号，不带 # |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 用户授权码 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | Issue ID |
| html_url | string | 网页地址 |
| number | string | 编号 |
| state | string | 状态 |
| title | string | 标题 |
| body | string | 内容 |
| user | object | 创建人 |
| repository | object | 所属仓库 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| closed_at | string | 关闭时间 |
| labels | array | 标签 |
| comments | integer | 评论数 |
| milestone | object | 里程碑 |
| assignees | array | 指派人 |
| custom_fields | array | 自定义字段 |

### 响应示例

```json
{
  "id": 152212,
  "html_url": "https://test.gitcode.net/dengmengmian/test01/issues/3",
  "number": "3",
  "state": "opened",
  "title": "测试Issue",
  "user": {
    "id": "661ce4eab470b1430d456154",
    "login": "dengmengmian",
    "name": "麻凡_"
  },
  "created_at": "2024-01-15T10:30:00+08:00",
  "updated_at": "2024-01-15T10:30:00+08:00",
  "labels": [],
  "comments": 0
}
```

---

## 3. 获取 Issue 评论列表

### 基本信息

| 项目 | 说明 |
|------|------|
| 接口地址 | `GET /repos/:owner/:repo/issues/:number/comments` |
| 功能 | 获取指定 Issue 下的所有评论 |

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 空间地址 |
| repo | string | 是 | 仓库 path |
| number | string | 是 | Issue 编号 |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 授权码 |
| page | integer | 否 | 页码 |
| per_page | integer | 否 | 每页条数 |

### 响应

返回评论数组，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 评论 ID |
| body | string | 评论内容 |
| user | object | 评论者 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

---

## 4. 获取 Issue 事件列表

### 基本信息

| 项目 | 说明 |
|------|------|
| 接口地址 | `GET /repos/:owner/:repo/issues/:number/events` |
| 功能 | 获取 Issue 的状态变更、指派、关闭等操作日志 |

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 空间地址 |
| repo | string | 是 | 仓库 path |
| number | string | 是 | Issue 编号 |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 授权码 |
| page | integer | 否 | 页码 |
| per_page | integer | 否 | 每页条数 |

### 响应

返回事件数组，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 事件 ID |
| action | string | 动作类型（labeled、closed、assigned 等） |
| user | object | 操作者 |
| created_at | string | 操作时间 |
| issue | object | 关联 Issue |

---

## 5. 获取仓库 Issue 标签列表

### 基本信息

| 项目 | 说明 |
|------|------|
| 接口地址 | `GET /repos/:owner/:repo/issues/labels` |
| 功能 | 获取当前仓库可用于 Issue 的全部标签 |

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 空间地址 |
| repo | string | 是 | 仓库 path |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 授权码 |

### 响应

返回数组，每条包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 标签 ID |
| name | string | 标签名称 |
| color | string | 标签颜色（十六进制） |

---

## 6. 获取仓库 Issue 可指派人员列表

### 基本信息

| 项目 | 说明 |
|------|------|
| 接口地址 | `GET /repos/:owner/:repo/issues/assignees` |
| 功能 | 查询可指派给 Issue 的仓库成员 |

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 空间地址 |
| repo | string | 是 | 仓库 path |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 授权码 |

### 响应

返回数组，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 用户 ID |
| login | string | 登录名 |
| name | string | 显示名 |
| avatar_url | string | 头像地址 |

---

## 常见状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 401 | 未授权 / access_token 无效 |
| 403 | 权限不足 |
| 404 | Issue 或仓库不存在 |
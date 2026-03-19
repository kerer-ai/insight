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
| state | string | 否 | 状态：`open` / `closed` / `all`，默认 open |
| labels | string | 否 | 标签名，多个用逗号分隔 |
| since | string | 否 | 起始时间，格式：ISO 8601 |
| page | integer | 否 | 页码，默认 1 |
| per_page | integer | 否 | 每页条数，默认 20 |
| sort | string | 否 | 排序字段：`created` / `updated` |
| direction | string | 否 | 排序方向：`asc` / `desc` |

### 请求示例

```http
GET https://api.gitcode.com/api/v5/repos/testowner/testrepo/issues?access_token=xxx&state=open&page=1&per_page=20
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
| state | string | 状态：`open` / `closed` |
| title | string | 标题 |
| body | string | 内容 |
| user | object | 创建人 |
| repository | object | 所属仓库 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| finished_at | string | **关闭时间**（GitCode 特有字段，closed_at 始终为空） |
| closed_at | string | 关闭时间（始终为 null，请使用 finished_at） |
| issue_state | string | 详细状态名称，如"已完成" |
| labels | array | 标签 |
| comments | integer | 评论数 |
| milestone | object | 里程碑 |
| assignees | array | 指派人 |
| custom_fields | array | 自定义字段 |

> **重要说明**：GitCode API 中，已关闭 Issue 的关闭时间存储在 `finished_at` 字段，`closed_at` 字段始终为 `null`。 |

### 响应示例

#### 开放状态的 Issue

```json
{
  "id": 3809569,
  "html_url": "https://gitcode.com/openeuler/kernel/issues/8760",
  "number": "8760",
  "state": "open",
  "title": "Feature: Add new feature",
  "user": {
    "id": "6809eb2292685e00dfb27536",
    "login": "mufengyan",
    "name": "mufengyan"
  },
  "repository": {
    "id": 8744898,
    "full_name": "openeuler/kernel",
    "path": "kernel"
  },
  "created_at": "2026-03-18T19:18:33+08:00",
  "updated_at": "2026-03-19T11:30:09+08:00",
  "finished_at": null,
  "closed_at": null,
  "issue_state": "待处理",
  "labels": [{"id": 18027, "name": "sig/Kernel", "color": "#2865E0"}],
  "comments": 4,
  "assignees": []
}
```

#### 已关闭的 Issue

```json
{
  "id": 3796585,
  "html_url": "https://gitcode.com/openeuler/kernel/issues/8696",
  "number": "8696",
  "state": "closed",
  "title": "[OLK-6.6] l2tp: fix double dst_release()",
  "user": {
    "id": "695caf89728aee026d2b7e27",
    "login": "lixiasong",
    "name": "lixiasong"
  },
  "repository": {
    "id": 8744898,
    "full_name": "openeuler/kernel",
    "path": "kernel"
  },
  "created_at": "2026-03-10T17:45:19+08:00",
  "updated_at": "2026-03-19T11:03:26+08:00",
  "finished_at": "2026-03-19T11:03:19+08:00",
  "closed_at": null,
  "issue_state": "已完成",
  "labels": [{"id": 18027, "name": "sig/Kernel", "color": "#2865E0"}],
  "comments": 2,
  "assignees": []
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
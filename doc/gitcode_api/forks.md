# GitCode API - 查看仓库 Fork 列表

## 接口信息

| 项目 | 说明 |
|------|------|
| 接口标识 | `GET /api/v5/repos/:owner/:repo/forks` |
| 接口用途 | 查询指定仓库的所有 Fork 信息，支持按时间/星标排序、时间范围过滤、分页查询 |
| 请求方式 | GET |
| 基础域名 | `https://api.gitcode.com` |
| 完整地址 | `https://api.gitcode.com/api/v5/repos/:owner/:repo/forks` |
| 响应格式 | application/json |
| 权限要求 | 需携带有效 access_token，并对目标仓库有查看权限 |

## 请求参数

### 路径参数（Path）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 仓库所属空间地址（个人/组织/企业 path） |
| repo | string | 是 | 仓库路径（path） |

### 查询参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 用户授权码 |
| sort | string | 否 | 排序方式：`newest`（最新）、`oldest`（最早）、`stargazers`（星标数） |
| page | integer | 否 | 当前页码，默认 1 |
| per_page | integer | 否 | 每页条数，最大 100，默认 20 |
| created_after | string | 否 | 筛选此时间之后创建的 Fork，格式：YYYY-MM-DD |
| created_before | string | 否 | 筛选此时间之前创建的 Fork，格式：YYYY-MM-DD |

## 响应结构

### 成功响应（200 OK）

返回数组格式，单条 Fork 对象结构如下：

```json
{
  "id": 567682,
  "full_name": "wangwt/RuoYi",
  "human_name": "wangwt / RuoYi",
  "url": "https://api.gitcode.com/api/v5/repos/wangwt/RuoYi",
  "namespace": {
    "id": 153748,
    "type": "personal",
    "name": "wangwt",
    "path": "wangwt",
    "html_url": "https://test.gitcode.net/wangwt"
  },
  "description": "",
  "status": "",
  "created_at": "2024-07-29T15:42:45.149+08:00",
  "updated_at": "2024-07-29T15:42:45.149+08:00",
  "owner": {
    "id": 970,
    "login": "wangwt",
    "name": "wangwt"
  },
  "pushed_at": "2024-11-08T16:24:10.576+08:00",
  "parent": {
    "id": 517092,
    "full_name": "xiaogang/RuoYi",
    "human_name": "xiaogang / RuoYi",
    "url": "https://api.gitcode.com/api/v5/repos/xiaogang/RuoYi",
    "namespace": {
      "id": 137117,
      "type": "personal",
      "name": "xiaogang",
      "path": "xiaogang",
      "html_url": "https://test.gitcode.net/xiaogang"
    }
  },
  "private": false,
  "public": true
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | Fork 仓库 ID |
| full_name | string | 完整仓库名 |
| human_name | string | 友好显示名称 |
| url | string | 仓库 API 地址 |
| namespace | object | 命名空间信息 |
| namespace.id | integer | 命名空间 ID |
| namespace.type | string | 类型：personal / organization |
| namespace.name | string | 命名空间名称 |
| namespace.path | string | 命名空间路径 |
| namespace.html_url | string | 命名空间网页地址 |
| description | string | 仓库描述 |
| status | string | 仓库状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| owner | object | 仓库所有者信息 |
| owner.id | integer | 所有者 ID |
| owner.login | string | 登录名 |
| owner.name | string | 显示名 |
| pushed_at | string | 最后推送时间 |
| parent | object | 源仓库信息 |
| parent.id | integer | 源仓库 ID |
| parent.full_name | string | 源仓库完整名 |
| parent.human_name | string | 源仓库友好名称 |
| parent.url | string | 源仓库 API 地址 |
| parent.namespace | object | 源仓库命名空间 |
| private | boolean | 是否私有仓库 |
| public | boolean | 是否公开仓库 |

## 调用示例

### curl

```bash
curl -X GET "https://api.gitcode.com/api/v5/repos/owner/repo/forks?access_token=your_token&sort=newest&page=1&per_page=20" \
  -H "Accept: application/json"
```

### C#

```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Get,
  "https://api.gitcode.com/api/v5/repos/owner/repo/forks?access_token=your_token");
request.Headers.Add("Accept", "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 401 | 未授权 / access_token 无效 |
| 403 | 无权限访问该仓库 |
| 404 | 仓库不存在 |

## 注意事项

1. `per_page` 最大支持 100，超出会被限制为 100
2. 时间筛选参数 `created_after`/`created_before` 建议使用 `YYYY-MM-DD` 格式
3. 公开仓库可直接查询，私有仓库需对应权限
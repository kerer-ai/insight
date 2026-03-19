# GitCode API - 列出仓库 Watch（订阅）用户

## 接口信息

| 项目 | 说明 |
|------|------|
| 接口标识 | `GET /api/v5/repos/:owner/:repo/subscribers` |
| 接口用途 | 获取指定仓库的所有 Watch（订阅）用户列表，支持分页、按关注时间范围筛选 |
| 请求方式 | GET |
| 基础域名 | `https://api.gitcode.com` |
| 完整地址 | `https://api.gitcode.com/api/v5/repos/:owner/:repo/subscribers` |
| 响应格式 | application/json |
| 权限要求 | 需携带有效 access_token，并对仓库有查看权限 |

## 请求参数

### 路径参数（Path）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 仓库所属空间地址（个人 / 组织 / 企业 path） |
| repo | string | 是 | 仓库路径（path） |

### 查询参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 用户授权码 |
| page | integer | 否 | 当前页码，默认 1 |
| per_page | integer | 否 | 每页数量，最大 100，默认 20 |
| watched_after | string | 否 | 筛选此时间之后关注的用户，格式：YYYY-MM-DD |
| watched_before | string | 否 | 筛选此时间之前关注的用户，格式：YYYY-MM-DD |

## 响应结构

### 成功响应（200 OK）

返回用户数组，单条对象格式：

```json
{
  "id": 496,
  "login": "xiaogang",
  "name": "xiaogang",
  "avatar_url": "https://gitcode-img.obs.cn-south-1.myhuaweicloud.com:443/bc/cd/6bc422546cdf276c147f267030d83a43e927fec67ca66f0b22f7e03556206fa3.jpg",
  "watch_at": "2024-11-13T16:15:53.287+08:00"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户 ID |
| login | string | 用户登录名 |
| name | string | 用户显示名称 |
| avatar_url | string | 用户头像地址 |
| watch_at | string | 关注（Watch）时间 |

## 调用示例

### curl

```bash
curl -X GET "https://api.gitcode.com/api/v5/repos/owner/repo/subscribers?access_token=your_token&page=1&per_page=20" \
  -H "Accept: application/json"
```

### C#

```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Get,
  "https://api.gitcode.com/api/v5/repos/owner/repo/subscribers?access_token=your_token");
request.Headers.Add("Accept", "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 401 | 未授权 / Token 无效 |
| 403 | 无权限访问该仓库 |
| 404 | 仓库不存在 |

## 注意事项

1. `per_page` 最大值为 100，超出会被自动限制
2. 时间筛选建议使用 `YYYY-MM-DD` 格式
3. 公开仓库可直接查询，私有仓库需对应权限
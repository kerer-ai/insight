# GitCode API - 获取仓库编程语言占比

## 接口信息

| 项目 | 说明 |
|------|------|
| 接口标识 | `GET /api/v5/repos/:owner/:repo/languages` |
| 接口用途 | 查询指定仓库的代码语言分布，返回各语言占比（百分比） |
| 请求方式 | GET |
| 基础域名 | `https://api.gitcode.com` |
| 完整地址 | `https://api.gitcode.com/api/v5/repos/:owner/:repo/languages` |
| 响应格式 | application/json |
| 权限要求 | 需携带有效 access_token，并对目标仓库有查看权限 |

## 请求参数

### 路径参数（Path）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 仓库所属空间地址（个人 / 组织 path） |
| repo | string | 是 | 仓库路径（path） |

### 查询参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 用户授权码 |

## 响应结构

### 成功响应（200 OK）

返回键值对对象，key 为语言名称，value 为占比数值。

```json
{
  "Shell": 49.77,
  "Python": 50.23
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| {语言名称} | number | 对应编程语言的代码占比（百分比） |

## 调用示例

### curl

```bash
curl -X GET "https://api.gitcode.com/api/v5/repos/owner/repo/languages?access_token=your_token" \
  -H "Accept: application/json"
```

### C#

```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Get,
  "https://api.gitcode.com/api/v5/repos/owner/repo/languages?access_token=your_token");
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

1. 返回值为百分比数值，总和通常接近 100
2. 支持所有 GitCode 可识别的编程语言
3. 空仓库或未统计完成的仓库可能返回空对象或 0 值
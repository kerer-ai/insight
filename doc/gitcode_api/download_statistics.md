# GitCode API - 仓库下载次数统计

## 接口信息

| 项目 | 说明 |
|------|------|
| 接口标识 | `GET /api/v5/repos/:owner/:repo/download_statistics` |
| 接口用途 | 查询指定仓库按日维度的下载统计数据，支持按时间范围筛选与排序 |
| 请求方式 | GET |
| 基础域名 | `https://api.gitcode.com` |
| 完整地址 | `https://api.gitcode.com/api/v5/repos/:owner/:repo/download_statistics` |
| 数据格式 | application/json |
| 权限要求 | 需携带有效 access_token，且对目标仓库具备查看权限 |

## 请求参数

### 路径参数（Path）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| owner | string | 是 | 仓库所属空间地址（个人/组织/企业路径） |
| repo | string | 是 | 仓库路径（path） |

### 查询参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| access_token | string | 是 | 用户授权令牌 |
| start_date | string | 否 | 统计起始日期（含），格式：YYYY-MM-DD |
| end_date | string | 否 | 统计截止日期（含），格式：YYYY-MM-DD |
| direction | string | 否 | 排序方式：asc（升序）/ desc（降序），默认 desc |

## 响应结构

### 成功响应（200 OK）

```json
{
  "download_statistics_detail": [
    {
      "pdate": "2024-11-13",
      "repo_id": "625513",
      "today_dl_cnt": 0,
      "total_dl_cnt": 38
    }
  ],
  "download_statistics_total": 7,
  "download_statistics_history_total": 45
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| download_statistics_detail | array[object] | 按日统计明细列表 |
| pdate | string | 统计日期（YYYY-MM-DD） |
| repo_id | string | 仓库 ID |
| today_dl_cnt | integer | 当日下载次数 |
| total_dl_cnt | integer | 截至当日累计下载次数 |
| download_statistics_total | integer | 时间范围内总下载次数 |
| download_statistics_history_total | integer | 仓库历史累计总下载次数 |

## 调用示例

### curl

```bash
curl -X GET "https://api.gitcode.com/api/v5/repos/your-owner/your-repo/download_statistics?access_token=your-token&start_date=2024-11-01&end_date=2024-11-30&direction=desc" \
  -H "Accept: application/json"
```

### C#

```csharp
var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Get,
  "https://api.gitcode.com/api/v5/repos/your-owner/your-repo/download_statistics?access_token=your-token");
request.Headers.Add("Accept", "application/json");
var response = await client.SendAsync(request);
response.EnsureSuccessStatusCode();
Console.WriteLine(await response.Content.ReadAsStringAsync());
```

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功，返回统计数据 |
| 401 | 未授权/令牌无效 |
| 403 | 权限不足，无法访问该仓库 |
| 404 | 仓库不存在或路径错误 |

## 注意事项

1. 日期参数格式必须为 `YYYY-MM-DD`，否则接口可能返回异常或空数据
2. 不传递 `start_date`/`end_date` 时，默认返回最近一段周期的统计数据
3. `download_statistics_total` 为所选时间区间内的下载总量，`download_statistics_history_total` 为仓库全量历史累计值
4. 令牌需具备仓库读取权限，私有仓库必须授权，公开仓库建议仍携带令牌提升调用稳定性
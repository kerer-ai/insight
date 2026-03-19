# **获取项目 Pull Request 列表 API 文档**

获取指定项目的 Pull Request 列表，支持按状态、分支、排序等条件进行过滤。

## **基本信息**
- **接口地址**: `https://api.gitcode.com/api/v5/repos/{owner}/{repo}/pulls`
- **请求方式**: `GET`
- **认证方式**: 
  - 通过 Query 参数传入 `access_token`
  - 或通过 Header 传入 `Authorization: token <YOUR_TOKEN>`

---

## **请求参数**

### **路径参数 (Path Parameters)**
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| `owner` | string | 是 | 仓库所属空间地址（组织或个人的地址 path） |
| `repo` | string | 是 | 仓库路径（path） |

### **查询参数 (Query Parameters)**
| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `access_token` | string | 是 | - | 用户授权码 |
| `state` | string | 否 | `open` | PR 状态：`open` (开启), `closed` (关闭), `merged` (已合并), `all` (全部) |
| `head` | string | 否 | - | 源分支名称。格式可以是 `branch` 或 `user:branch` |
| `base` | string | 否 | - | 目标分支名称 |
| `sort` | string | 否 | `created` | 排序字段：`created` (创建时间), `updated` (更新时间) |
| `direction` | string | 否 | `desc` | 排序方向：`asc` (升序), `desc` (降序) |
| `page` | integer | 否 | 1 | 当前页码 |
| `per_page` | integer | 否 | 20 | 每页数量，最大为 100 |

---

## **响应参数**

接口返回一个对象数组，每个对象包含以下详细字段：

### **1. 基础信息**
| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `id` | integer | Pull Request 唯一标识 ID |
| `iid` | integer | 项目内的 PR 编号（通常用于 URL 访问，如 pulls/1） |
| `project_id` | integer | 项目唯一 ID |
| `title` | string | Pull Request 标题 |
| `body` | string | Pull Request 描述内容 |
| `state` | string | 当前状态（open, closed, merged） |
| `number` | integer | PR 序号 |
| `draft` | boolean | 是否为草稿 PR |
| `locked` | boolean | 是否已锁定，锁定后不可评论 |

### **2. 分支与项目关联**
| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `source_branch` | string | 源分支名称 |
| `target_branch` | string | 目标分支名称 |
| `source_project_id`| integer | 源项目 ID |
| `head` | object | 源分支信息，包含 `label`, `ref`, `sha`, `user`, `repo` 等 |
| `base` | object | 目标分支信息，包含 `label`, `ref`, `sha`, `user`, `repo` 等 |
| `source_git_url` | string | 源仓库的 Git 地址 |

### **3. 人员与标签**
| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `user` | object | 创建者用户信息对象 |
| `assignees` | array | 负责人列表 |
| `assignees_number`| integer | 负责人数量 |
| `testers` | array | 测试人员列表 |
| `testers_number` | integer | 测试人员数量 |
| `labels` | object[] | 关联的标签列表，每个标签包含 `id`, `name`, `color` 等 |

### **4. 审计与时间**
| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `html_url` | string | PR 在网页上的地址 |
| `url` | string | PR 的 API 访问地址 |
| `web_url` | string | 网页端展示地址 |
| `created_at` | string | 创建时间 (ISO 8601 格式) |
| `updated_at` | string | 更新时间 (ISO 8601 格式) |
| `merged_at` | string | 合并时间 (ISO 8601 格式，未合并则为 null) |
| `closed_at` | string | 关闭时间 (ISO 8601 格式，未关闭则为 null) |
| `merged_by` | object | 合并执行者用户信息 |
| `closed_by` | object | 关闭执行者用户信息 |

### **5. 变更统计与状态控制**
| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `added_lines` | integer | 新增代码行数 |
| `removed_lines` | integer | 删除代码行数 |
| `notes` | integer | 评论/留言数量 |
| `diff_refs` | object | 包含 `base_sha`, `head_sha`, `start_sha`，用于代码对比 |
| `mergeable` | boolean | 是否可合并（由后端检查冲突得出） |
| `can_merge_check` | boolean | 是否可以进行合并检查 |
| `pipeline_status` | string | 流水线执行状态 (success, running, failed, etc.) |
| `prune_branch` | boolean | 合并后是否自动删除源分支 |
| `visibility_reason`| string | 可见性说明。`public`: 公开；`other`: 仅项目成员可见 |

---

## **调用注意事项 (Notes)**

### **1. 身份认证 (Authentication)**
所有的 API 请求都需要 `access_token`。如果您在调用时遇到 `401 Unauthorized`，请检查 token 是否有效或是否具有该项目的访问权限。

### **2. 分页处理 (Pagination)**
- 默认返回 20 条记录。建议在实现时始终处理 `page` 和 `per_page` 参数。
- **响应头**: 检查 `Link` 响应头以获取 `next`, `prev`, `last` 页面的 URL。

### **3. 数据解析建议**
- **日期格式**: `created_at` 等时间字段符合 ISO 8601 标准（例如 `2024-03-19T10:00:00Z`），在前端展示时通常需要转换为本地时区。
- **合并状态**: 判断一个 PR 是否真正完成，应优先检查 `merged_at` 是否非空，而不仅仅是 `state == 'merged'`。
- **代码冲突**: `mergeable` 字段如果为 `false`，表示存在代码冲突，此时无法通过 API 直接合并。

### **4. 错误处理**
- `404 Not Found`: 仓库路径 `owner/repo` 不存在。
- `400 Bad Request`: 参数格式错误（如 `per_page` 超过 100）。

---

## **请求示例 (cURL)**

```bash
# 使用 Query 参数认证
curl -X GET "https://api.gitcode.com/api/v5/repos/xiaogang_test/test222/pulls?access_token=YOUR_TOKEN&state=all&per_page=10" \
     -H "Accept: application/json"

# 使用 Header 认证 (推荐)
curl -X GET "https://api.gitcode.com/api/v5/repos/xiaogang_test/test222/pulls?state=open" \
     -H "Authorization: token YOUR_TOKEN" \
     -H "Accept: application/json"
```

---
## **常见问题 (FAQ)**
- **Q: 为什么返回的列表不完整？**
  - A: 默认只返回 `state=open` 的 PR，如需查看全部，请设置 `state=all`。
- **Q: 负责人 (Assignees) 和 测试人员 (Testers) 有什么区别？**
  - A: 负责人负责代码合并，测试人员负责 PR 的质量验证。


GitCode Issue 相关查询接口文档（完整版）
文档说明
接口版本：v5
基础域名：https://api.gitcode.com/api/v5
请求方式：全部为 GET（查询类，无写操作）
认证方式：全部接口必须携带 access_token 查询参数
响应格式：application/json
接口目录
获取仓库 Issue 列表
获取单个 Issue 详情
获取 Issue 评论列表
获取 Issue 事件列表
获取仓库 Issue 标签列表
获取仓库 Issue 可指派人员列表
1. 获取仓库 Issue 列表
基本信息
接口地址：GET /repos/:owner/:repo/issues
功能：查询指定仓库下的 Issue 列表，支持筛选、分页、排序
权限：需仓库访问权限
请求参数
路径参数
表格
参数名	类型	是否必传	说明
owner	string	是	个人 / 组织 path
repo	string	是	仓库 path
查询参数
表格
参数名	类型	是否必传	说明
access_token	string	是	用户授权码
state	string	否	状态：opened/closed/all，默认 opened
labels	string	否	标签名，多个用逗号分隔
page	integer	否	页码，默认 1
per_page	integer	否	每页条数，默认 20
sort	string	否	排序字段：created/updated
direction	string	否	排序方向：asc/desc
响应
200：返回 Issue 数组
字段结构同「单个 Issue」
请求示例
http
GET https://api.gitcode.com/api/v5/repos/testowner/testrepo/issues?access_token=xxx&state=opened&page=1&per_page=20
2. 获取单个 Issue 详情
基本信息
接口地址：GET /repos/:owner/:repo/issues/:number
功能：获取指定 Issue 完整信息
请求参数
路径参数
表格
参数名	类型	是否必传	说明
owner	string	是	个人 / 组织 path
repo	string	是	仓库 path
number	string	是	Issue 编号，不带 #
查询参数
表格
参数名	类型	是否必传	说明
access_token	string	是	用户授权码
响应字段
表格
字段	类型	说明
id	integer	Issue ID
html_url	string	网页地址
number	string	编号
state	string	状态
title	string	标题
body	string	内容
user	object	创建人
repository	object	所属仓库
created_at	string	创建时间
updated_at	string	更新时间
labels	array	标签
comments	integer	评论数
milestone	object	里程碑
custom_fields	array	自定义字段
响应示例
json
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
  }
}
3. 获取 Issue 评论列表
基本信息
接口地址：GET /repos/:owner/:repo/issues/:number/comments
功能：获取指定 Issue 下的所有评论
请求参数
表格
参数	位置	类型	必传	说明
owner	路径	string	是	空间地址
repo	路径	string	是	仓库
number	路径	string	是	Issue 编号
access_token	查询	string	是	授权码
page	查询	integer	否	页码
per_page	查询	integer	否	每页条数
响应
返回评论数组，包含：id、body、user、created_at、updated_at 等
4. 获取 Issue 事件列表
基本信息
接口地址：GET /repos/:owner/:repo/issues/:number/events
功能：获取 Issue 的状态变更、指派、关闭等操作日志
请求参数
同评论列表，增加事件筛选（可选）
响应
返回事件数组，包含：id、action、user、created_at、issue 等
5. 获取仓库 Issue 标签列表
基本信息
接口地址：GET /repos/:owner/:repo/issues/labels
功能：获取当前仓库可用于 Issue 的全部标签
请求参数
表格
参数	位置	类型	必传
owner	路径	string	是
repo	路径	string	是
access_token	查询	string	是
响应
数组，每条包含：id、name、color
6. 获取仓库 Issue 可指派人员列表
基本信息
接口地址：GET /repos/:owner/:repo/issues/assignees
功能：查询可指派给 Issue 的仓库成员
请求参数
同标签接口
响应
数组，包含：id、login、name、avatar_url 等
可直接下载使用（复制保存为 issue-api-docs.md）
markdown
# GitCode Issue 查询类接口文档 v5
基础URL：https://api.gitcode.com/api/v5

## 1. 获取Issue列表
GET /repos/:owner/:repo/issues

## 2. 获取单个Issue
GET /repos/:owner/:repo/issues/:number

## 3. 获取Issue评论
GET /repos/:owner/:repo/issues/:number/comments

## 4. 获取Issue事件
GET /repos/:owner/:repo/issues/:number/events

## 5. 获取Issue标签
GET /repos/:owner/:repo/issues/labels

## 6. 获取可指派人员
GET /repos/:owner/:repo/issues/assignees

# GitCode Insight

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

GitCode 平台代码洞察命令行工具，支持社区洞察、Issue/PR 分析、仓库统计，生成可视化报告。

## 功能

| 功能 | 说明 |
|------|------|
| 社区洞察 | 分析组织下所有仓库的统计数据，生成看板 |
| Issue 洞察 | Issue 数量、响应时间、关闭率、标签分布 |
| PR 洞察 | 评审效率、合并耗时、变更规模、冲突率 |
| 仓库统计 | 下载量、Fork、订阅用户、编程语言 |
| 综合报告 | 整合所有模块的一站式报告 |

## 快速开始

```bash
# 安装
pip install gitcode-insight

# 或从源码安装
git clone https://gitcode.com/gitcode-cli/insight.git
cd insight
python3 -m venv .venv
.venv/bin/pip install -e ".[test]"

# 创建配置文件
cp config/gitcode.json.example config/gitcode.json
# 编辑配置文件，填入 access_token 和 owner

# 生成社区看板
gc-insight dashboard

# 分析单个仓库
gc-insight issue --repo your-repo --token your_token --days 30
gc-insight pr --repo your-repo --token your_token --days 30
gc-insight repo-stats --repo your-repo --token your_token --days 30
gc-insight report --repo your-repo --token your_token --days 30
```

## 配置

配置文件 `config/gitcode.json`：

```json
{
    "access_token": "your_gitcode_access_token",
    "owner": "your_organization_name"
}
```

获取 Access Token：GitCode → 设置 → 访问令牌 → 创建新令牌

## 常见问题

**Q: 输出文件在哪里？**
A: 默认保存在 `./output/` 目录。

**Q: 请求频繁失败怎么办？**
A: GitCode API 每分钟限制 100 次请求，工具已内置限流处理。如遇问题，等待几分钟后重试。

**Q: CSV 文件中文乱码？**
A: 文件使用 UTF-8-BOM 编码，Excel 可正常打开。

## 文档

- [用户指南](doc/user_guide.md) - 详细的安装配置和命令说明
- [开发指南](doc/development.md) - 本地开发和测试
- [贡献指南](CONTRIBUTING.md) - 参与项目贡献
- [API 文档](doc/gitcode_api/) - GitCode API 接口说明

## 许可证

[MIT License](LICENSE)
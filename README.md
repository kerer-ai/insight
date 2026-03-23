# GitCode Insight

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/gitcode-insight.svg)](https://pypi.org/project/gitcode-insight/)

GitCode 平台代码洞察命令行工具，支持社区洞察、Issue/PR 分析、仓库统计，生成可视化报告。

**PyPI**: https://pypi.org/project/gitcode-insight/

## 功能

| 功能 | 说明 |
|------|------|
| 社区洞察 | 分析组织下所有仓库的统计数据，生成看板 |
| Issue 洞察 | Issue 数量、响应时间、关闭率、标签分布 |
| PR 洞察 | 评审效率、合并耗时、变更规模、冲突率 |
| 仓库统计 | 下载量、Fork、订阅用户、编程语言 |
| 综合报告 | 整合所有模块的一站式报告 |

## 快速开始

### 从 PyPI 安装

```bash
pip install gitcode-insight
```

### 从源码安装（推荐开发使用）

```bash
# 克隆仓库
git clone https://gitcode.com/gitcode-cli/insight.git
cd insight

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# 安装（开发模式，包含测试依赖）
pip install -e ".[test]"

# 创建配置文件
cp config/gitcode.json.example config/gitcode.json
# 编辑配置文件，填入 access_token 和 owner
```

### 使用示例

```bash
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

## 输出产物

所有命令执行后生成三种标准产物，保存在 `./output/` 目录：

| 格式 | 说明 | 用途 |
|------|------|------|
| `.json` | 原始数据 + 统计计算数据 | 数据存档、二次开发 |
| `.md` | Markdown 格式总结报告 | 文档集成、Git 提交 |
| `.html` | HTML 格式可视化报告 | 浏览器查看、分享展示 |

**示例**：

```
output/
├── issue_insight_kvrocks_30d.json    # Issue 数据
├── issue_insight_kvrocks_30d.md      # Issue Markdown 报告
├── issue_insight_kvrocks_30d.html    # Issue 可视化报告
├── pr_insight_kvrocks_30d.json
├── pr_insight_kvrocks_30d.md
├── pr_insight_kvrocks_30d.html
├── report_openeuler_kernel_30d.json
├── report_openeuler_kernel_30d.md
└── report_openeuler_kernel_30d.html
```

## 常见问题

**Q: 输出文件在哪里？**
A: 默认保存在 `./output/` 目录。

**Q: 请求频繁失败怎么办？**
A: GitCode API 每分钟限制 100 次请求，工具已内置限流处理。如遇问题，等待几分钟后重试。

**Q: CSV 文件中文乱码？**
A: 文件使用 UTF-8-BOM 编码，Excel 可正常打开。

**Q: 安装时报错 `externally-managed-environment`？**
A: 这是 Debian/Ubuntu 系统（Python 3.11+）的保护机制，防止破坏系统 Python 环境。请使用虚拟环境安装：

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装
pip install gitcode-insight
```

## 文档

- [用户指南](doc/user_guide.md) - 详细的安装配置和命令说明
- [开发指南](doc/development.md) - 本地开发和测试
- [贡献指南](CONTRIBUTING.md) - 参与项目贡献
- [发布流程](doc/release.md) - PyPI 发布说明
- [API 文档](doc/gitcode_api/) - GitCode API 接口说明

## 许可证

[MIT License](LICENSE)
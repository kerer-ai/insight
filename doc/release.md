# 发布流程

本文档说明如何将 gitcode-insight 发布到 PyPI。

## 目录

- [前置条件](#前置条件)
- [发布步骤](#发布步骤)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

## 前置条件

### 1. PyPI 账号

- 注册 PyPI 账号：https://pypi.org/account/register/
- 完成邮箱验证

### 2. 配置 Trusted Publishers

PyPI 使用 Trusted Publishers 机制，无需管理 API Token。

1. 登录 PyPI：https://pypi.org/
2. 进入账户设置 → Publishing
3. 点击 "Add a new pending publisher"
4. 填写以下信息：

| 字段 | 值 |
|------|-----|
| PyPI Project Name | `gitcode-insight` |
| Owner | 选择你的用户名或组织 |
| Repository name | `kerer-ai/insight` |
| Workflow name | `build.yml` |
| Environment name | `pypi` |

5. 点击 "Add" 保存

### 3. GitHub Environment 配置

1. 进入仓库设置：https://github.com/kerer-ai/insight/settings/environments
2. 点击 "New environment"
3. 名称填写 `pypi`
4. 配置 Deployment branches and tags：
   - 选择 "No restriction"（无限制）
   - 或选择 "Selected branches and tags" 并添加 `v*` 规则
5. 保存

## 发布步骤

### 1. 更新版本号

编辑 `pyproject.toml`：

```toml
[project]
name = "gitcode-insight"
version = "0.2.0"  # 更新版本号
```

### 2. 更新更新日志

编辑 `README.md`，添加新版本的更新日志：

```markdown
## 更新日志

### v0.2.0 (2026-03-23)

- 新增 xxx 功能
- 修复 xxx 问题
```

### 3. 提交代码

```bash
git add .
git commit -m "chore: bump version to 0.2.0"
git push origin main
git push github main
```

### 4. 创建并推送 Tag

```bash
# 创建 tag（格式：v + 版本号）
git tag v0.2.0

# 推送 tag 到 GitHub（触发自动发布）
git push github v0.2.0
```

### 5. 查看发布状态

- GitHub Actions：https://github.com/kerer-ai/insight/actions
- PyPI 页面：https://pypi.org/project/gitcode-insight/

### 6. 验证发布

```bash
# 安装新版本
pip install --upgrade gitcode-insight

# 验证版本
pip show gitcode-insight

# 或直接运行
gc-insight --help
```

## 配置说明

### GitHub Workflow

发布流程定义在 `.github/workflows/build.yml`：

```yaml
name: Build and Publish to PyPI

on:
  push:
    tags:
      - 'v*'  # 匹配 v0.1.0, v1.0.0 等格式
  workflow_dispatch:  # 手动触发

permissions:
  id-token: write  # OIDC token 用于 Trusted Publishers
  contents: read

jobs:
  build:
    # 构建 wheel 和 tar.gz

  publish:
    needs: build
    if: startsWith(github.ref, 'refs/tags/v')
    environment: pypi
    # 发布到 PyPI
```

### 触发条件

| 方式 | 触发条件 | 是否发布 |
|------|----------|----------|
| 推送 tag | `git push github v0.1.0` | ✓ 是 |
| 手动触发 | GitHub Actions 页面 | ✗ 仅构建 |

### 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

| 格式 | 说明 | 示例 |
|------|------|------|
| `MAJOR.MINOR.PATCH` | 主版本.次版本.补丁 | `1.2.3` |
| `MAJOR` | 不兼容的 API 变更 | `1.0.0` → `2.0.0` |
| `MINOR` | 向后兼容的功能新增 | `1.0.0` → `1.1.0` |
| `PATCH` | 向后兼容的问题修复 | `1.0.0` → `1.0.1` |

## 常见问题

### Q: 发布失败，提示 `invalid-publisher`

**原因**：PyPI Trusted Publishers 配置与 GitHub 不匹配。

**解决**：
1. 检查 PyPI 的 Trusted Publishers 配置
2. 确保 Repository name、Workflow name、Environment name 都正确
3. 确保 GitHub Environment 已创建且名称匹配

### Q: 发布失败，提示 `Tag is not allowed to deploy`

**原因**：GitHub Environment 保护规则阻止了 tag 部署。

**解决**：
1. 进入 GitHub Environment 设置
2. 修改 Deployment branches and tags 为 "No restriction"
3. 或添加 `v*` 规则

### Q: 如何重新发布同一版本？

PyPI 不允许覆盖已发布的版本。需要：

1. 更新版本号（如 `0.1.0` → `0.1.1`）
2. 重新创建 tag 并推送

```bash
# 删除本地 tag
git tag -d v0.1.0

# 删除远程 tag（如果需要）
git push github :refs/tags/v0.1.0

# 更新版本号后重新发布
git tag v0.1.1
git push github v0.1.1
```

### Q: 如何发布到 TestPyPI 测试？

1. 在 TestPyPI 配置 Trusted Publishers
2. 修改 workflow，添加 TestPyPI 发布：

```yaml
- name: Publish to TestPyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
```

### Q: 构建产物在哪里？

构建产物（wheel 和 tar.gz）保存在 `dist/` 目录：

```
dist/
├── gitcode_insight-0.1.0-py3-none-any.whl
└── gitcode_insight-0.1.0.tar.gz
```

本地构建命令：

```bash
.venv/bin/pip install build
.venv/bin/python -m build
```

## 发布检查清单

发布前请确认：

- [ ] 更新 `pyproject.toml` 版本号
- [ ] 更新 `README.md` 更新日志
- [ ] 运行测试确保通过：`.venv/bin/pytest`
- [ ] 代码已推送到 GitHub
- [ ] 创建正确格式的 tag（`v*.*.*`）
- [ ] 推送 tag 到 GitHub 触发发布
- [ ] 验证 PyPI 页面更新
- [ ] 验证 `pip install` 可安装新版本
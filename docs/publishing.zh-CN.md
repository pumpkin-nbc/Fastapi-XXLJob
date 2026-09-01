[English](publishing.md) | [简体中文](publishing.zh-CN.md)

# 发布

发布使用 GitHub Actions Trusted Publishing，仓库中不保存长期 PyPI API Token。本地命令负责构建和检查制品，上传由 `.github/workflows/release.yml` 执行。

## 构建

请在新的空目录中构建，避免历史文件被误认为本轮制品：

```powershell
$buildDir = Join-Path $env:TEMP "fastapi-xxljob-0.1.0-dist"
Remove-Item -LiteralPath $buildDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $buildDir | Out-Null
.venv\Scripts\python.exe -m build --outdir $buildDir
```

目录中必须恰好包含：

```text
fastapi_xxljob-0.1.0-py3-none-any.whl
fastapi_xxljob-0.1.0.tar.gz
```

## 检查

```powershell
.venv\Scripts\python.exe scripts\check_docs.py
.venv\Scripts\python.exe scripts\check_package.py --dist-dir $buildDir
.venv\Scripts\python.exe -m twine check `
  (Join-Path $buildDir "fastapi_xxljob-0.1.0-py3-none-any.whl") `
  (Join-Path $buildDir "fastapi_xxljob-0.1.0.tar.gz")
```

项目 Validator 会检查 wheel RECORD 的哈希和大小、元数据、sdist 标准顶层 `PKG-INFO`、必需源码、类型与法律文件，并拒绝缓存和开发目录。

## 隔离安装后冒烟

在源码 checkout 外创建 Python 3.8 虚拟环境和工作目录，安装 wheel 与 `httpx<0.29`，运行 `pip check`，清除 `PYTHONPATH` 后执行 `scripts/smoke_installed_wheel.py`。冒烟会验证安装包和元数据版本、CLI、五个执行器端点、注册、回调和注销。

## 配置 Trusted Publishing

在 PyPI 与 TestPyPI 创建 Pending Trusted Publisher：

- Project：`fastapi-xxljob`
- Owner：`pumpkin-nbc`
- Repository：`Fastapi-XXLJob`
- Workflow：`release.yml`
- PyPI Environment：`pypi`
- TestPyPI Environment：`testpypi`

同时创建同名 GitHub Environments，并建议为 `pypi` 设置人工审批。只有发布 Job 拥有 `id-token: write`，构建和检查保持只读权限。

## 发布到 TestPyPI

在 GitHub Actions 中手动运行 `Release` 工作流。`workflow_dispatch` 会构建并验证一套制品，再通过 `testpypi` Environment 发布。

请先从 PyPI 安装依赖，再使用无依赖解析方式从 TestPyPI 安装本包：

```bash
python -m pip install --index-url https://pypi.org/simple "fastapi>=0.124.4,<1.0" requests
python -m pip install --index-url https://test.pypi.org/simple --no-deps fastapi-xxljob==0.1.0
python -c "import fastapi_xxljob; assert fastapi_xxljob.__version__ == '0.1.0'"
fastapi-xxljob --version
```

## 发布到 PyPI

等待 `develop` 与 `master` 的 Required CI 通过后，从属于 `master` 的提交创建发布 Tag：

```bash
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
```

Tag 会触发 `Release` 工作流。它会校验 Tag、包版本、两份 Changelog 以及提交是否属于 `master`，随后等待 `pypi` Environment 审批并执行 Trusted Publishing。

## 发布前

确认 wheel 和 sdist 包含 `LICENSE` 与 `NOTICE`、声明 Apache-2.0、使用真实项目链接，且不包含密钥、内部域名或 Token。不要验证混有多次构建制品的目录。

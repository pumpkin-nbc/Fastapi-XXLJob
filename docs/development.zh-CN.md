# 开发

请使用仓库中的 `.venv` 并安装 `.[dev]`。本地门槛包括 Ruff、Mypy、文档一致性、覆盖率不低于 90% 的测试、构建、Twine 校验、制品检查和隔离 wheel 冒烟。

协议修改需覆盖成功和失败场景。请保持 HTTP 200 ReturnT 语义、应用隔离、Python 3.8 语法、有限重试和非阻塞异步接口。

CI 会分别在 Python 3.8 + FastAPI 0.124.4、Python 3.9 + FastAPI 0.125.0，以及 Python 3.10–3.14 各版本 + 最新兼容的 1.0 之前 FastAPI 版本上运行完整测试。

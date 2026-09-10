# 迁移指南

迁移现有的 XXL-JOB Python 执行器集成时，请使用 `fastapi_xxljob` 导入包、`FastAPIXXLJob` 扩展类，并通过 `app.state.xxljob` 访问运行时。现有 `XXL_JOB_*` 配置名和 XXL-JOB 2.4.1 请求结构保持兼容。

公开 Admin 和回调方法默认是异步接口。同步调用可改为 `await`，或使用显式 `_sync` 方法。FastAPI Handler 支持同步或异步，自动注册改为跟随 ASGI lifespan。

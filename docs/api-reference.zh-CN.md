# API 参考

`FastAPIXXLJob(app=None, config=None)` 在传入应用时立即绑定；`init_app(app, config=None)` 支持应用工厂。Handler 方法包括 `on_run`、`on_idle_beat`、`on_kill`、`on_log`、`register_callbacks` 和各 `get_*_callback` 读取接口。

Admin 操作包括 `register_executor`、`remove_executor`、各回调助手及其 `_sync` 形式。注册线程通过 `start_registry`、`stop_registry` 和 `get_status` 控制。公开模型、响应类型、`CallResult`、状态类型和异常均从 `fastapi_xxljob` 顶层导出。

同一扩展绑定多个应用时，协议处理之外的调用必须通过 `app=` 明确指定应用。

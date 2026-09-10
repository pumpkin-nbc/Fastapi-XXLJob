# API reference

`FastAPIXXLJob(app=None, config=None)` binds immediately when an application is supplied; `init_app(app, config=None)` supports factories. Handler methods include `on_run`, `on_idle_beat`, `on_kill`, `on_log`, `register_callbacks`, and the `get_*_callback` accessors.

Admin operations are `register_executor`, `remove_executor`, callback helpers, and their `_sync` forms. Registry control uses `start_registry`, `stop_registry`, and `get_status`. Public models, response types, `CallResult`, status types, and exceptions are exported from `fastapi_xxljob`.

When one extension is bound to multiple applications, calls outside protocol handling must identify the application explicitly with `app=`.

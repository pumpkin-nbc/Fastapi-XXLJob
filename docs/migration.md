# Migrating from Flask-XXLJob

Rename the import package to `fastapi_xxljob`, the extension class to `FastAPIXXLJob`, and move runtime access to `app.state.xxljob`. Existing `XXL_JOB_*` configuration names and XXL-JOB 2.4.1 payloads remain compatible.

Public Admin and callback methods are asynchronous by default. Replace a direct synchronous call with `await`, or choose its explicit `_sync` counterpart. FastAPI handlers may be sync or async, and automatic registration follows ASGI lifespan instead of Flask hooks.

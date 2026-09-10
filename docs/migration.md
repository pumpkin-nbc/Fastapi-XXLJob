# Migration guide

When migrating an existing XXL-JOB Python executor integration, use the `fastapi_xxljob` import package, the `FastAPIXXLJob` extension class, and `app.state.xxljob` for runtime access. Existing `XXL_JOB_*` configuration names and XXL-JOB 2.4.1 payloads remain compatible.

Public Admin and callback methods are asynchronous by default. Replace a direct synchronous call with `await`, or choose its explicit `_sync` counterpart. FastAPI handlers may be sync or async, and automatic registration follows the ASGI lifespan.

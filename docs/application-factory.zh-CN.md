# 应用工厂

可先创建未绑定应用的扩展，再分别绑定每个应用。当同一个扩展管理多个应用时，在请求或 lifespan 上下文之外调用需显式传入 `app=`。

```python
from fastapi import FastAPI
from fastapi_xxljob import FastAPIXXLJob

xxljob = FastAPIXXLJob()

def create_app():
    app = FastAPI()
    xxljob.init_app(app, {"XXL_JOB_AUTO_REGISTER": False})
    return app
```

初始化会在修改应用前拒绝重复绑定和 POST 路由冲突。

# 快速入门

安装 `fastapi-xxljob`，创建 FastAPI 应用并绑定 `FastAPIXXLJob`。自动注册只会在应用 lifespan 启动后开始。

```python
from fastapi import FastAPI
from fastapi_xxljob import FastAPIXXLJob

app = FastAPI()
xxljob = FastAPIXXLJob(app, {"XXL_JOB_AUTO_REGISTER": False})

@xxljob.on_run("hello")
def hello(param):
    return "hello " + param.executor_params
```

启用自动注册时，请配置外部可访问的执行器地址。不要在不可信网络中暴露使用空 Token 的执行器。

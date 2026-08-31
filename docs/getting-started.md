# Getting started

Install `fastapi-xxljob`, create a FastAPI application, and bind `FastAPIXXLJob`. Automatic registration starts only after the application lifespan starts.

```python
from fastapi import FastAPI
from fastapi_xxljob import FastAPIXXLJob

app = FastAPI()
xxljob = FastAPIXXLJob(app, {"XXL_JOB_AUTO_REGISTER": False})

@xxljob.on_run("hello")
def hello(param):
    return "hello " + param.executor_params
```

Use an externally reachable executor address when automatic registration is enabled. Never expose an executor with an empty token on an untrusted network.

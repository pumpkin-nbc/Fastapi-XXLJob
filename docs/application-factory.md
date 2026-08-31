# Application factory

Create the extension without an application, then bind each application independently. Outside a request or lifespan context, pass `app=` when one extension owns multiple applications.

```python
from fastapi import FastAPI
from fastapi_xxljob import FastAPIXXLJob

xxljob = FastAPIXXLJob()

def create_app():
    app = FastAPI()
    xxljob.init_app(app, {"XXL_JOB_AUTO_REGISTER": False})
    return app
```

Initialization rejects duplicate binding and conflicting POST routes before mutating the application.

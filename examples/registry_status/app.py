from fastapi import FastAPI

from fastapi_xxljob import FastAPIXXLJob

app = FastAPI(title="Registry status example")
xxljob = FastAPIXXLJob(app, {"XXL_JOB_AUTO_REGISTER": False})


@app.get("/executor-status")
def executor_status():
    return xxljob.get_status().__dict__

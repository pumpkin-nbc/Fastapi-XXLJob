from fastapi import FastAPI

from fastapi_xxljob import FastAPIXXLJob

xxljob = FastAPIXXLJob()
app_a = FastAPI(title="Executor A")
app_b = FastAPI(title="Executor B")
xxljob.init_app(app_a, {"XXL_JOB_AUTO_REGISTER": False})
xxljob.init_app(app_b, {"XXL_JOB_AUTO_REGISTER": False})


def status_for_each_app():
    return xxljob.get_status(app_a), xxljob.get_status(app_b)

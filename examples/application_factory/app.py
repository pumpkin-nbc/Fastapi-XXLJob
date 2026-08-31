from fastapi import FastAPI

from fastapi_xxljob import FastAPIXXLJob

xxljob = FastAPIXXLJob()


@xxljob.on_run("factoryJobHandler")
def factory_job(param):
    return param.executor_params or "ok"


def create_app():
    app = FastAPI(title="Factory example")
    xxljob.init_app(app, {"XXL_JOB_AUTO_REGISTER": False})
    return app

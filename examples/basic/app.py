from fastapi import FastAPI

from fastapi_xxljob import FastAPIXXLJob

app = FastAPI(title="FastAPI-XXLJob basic example")
xxljob = FastAPIXXLJob(
    app,
    {
        "XXL_JOB_AUTO_REGISTER": False,
        "XXL_JOB_ACCESS_TOKEN": "change-me",
    },
)


@xxljob.on_run("demoJobHandler")
async def demo_job(param):
    return "received: " + param.executor_params

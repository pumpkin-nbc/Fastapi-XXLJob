from fastapi import FastAPI

from fastapi_xxljob import FastAPIXXLJob, LogResponse, XXLJobResponse

app = FastAPI(title="Complete XXL-JOB executor")
xxljob = FastAPIXXLJob(
    app,
    {
        "XXL_JOB_ADMIN_ADDRESSES": "http://127.0.0.1:8080/xxl-job-admin",
        "XXL_JOB_ACCESS_TOKEN": "default_token",
        "XXL_JOB_EXECUTOR_APP_NAME": "fastapi-complete-executor",
        "XXL_JOB_EXECUTOR_ADDRESS": "http://127.0.0.1:8000",
    },
)


@xxljob.on_run("completeJobHandler")
async def run_task(param):
    return XXLJobResponse.success("job " + str(param.job_id) + " accepted")


@xxljob.on_idle_beat
def idle_beat(param):
    return XXLJobResponse.success()


@xxljob.on_kill
async def kill_task(param):
    return XXLJobResponse.success("kill requested")


@xxljob.on_log
def read_log(param):
    return LogResponse.success(param.from_line_num, param.from_line_num, "")

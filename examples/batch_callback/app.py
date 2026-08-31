from fastapi import FastAPI

from fastapi_xxljob import CallbackRequest, FastAPIXXLJob

app = FastAPI(title="Batch callback example")
xxljob = FastAPIXXLJob(app, {"XXL_JOB_AUTO_REGISTER": False})


async def report_batch():
    callbacks = [
        CallbackRequest(log_id=1, log_date_time=1730000000000, handle_code=200),
        CallbackRequest(log_id=2, log_date_time=1730000000001, handle_code=500),
    ]
    return await xxljob.callback_many(callbacks)

# Executor request handlers

Register named run handlers with `on_run(name)`. A handler receives a validated `TriggerParam`; synchronous functions run in Starlette's worker thread and asynchronous functions are awaited directly.

```python
@xxljob.on_run("importUsers")
async def import_users(param):
    return "accepted"

@xxljob.on_kill
def stop_task(param):
    return None
```

Use `register_callbacks`, the `get_*_callback` accessors, and replacement options for bulk setup. Unknown names and invalid return types become XXL-JOB business failures while HTTP remains 200.

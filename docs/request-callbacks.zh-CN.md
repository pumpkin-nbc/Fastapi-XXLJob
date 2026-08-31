# 执行器请求 Handler

通过 `on_run(name)` 注册命名运行 Handler。Handler 接收校验后的 `TriggerParam`；同步函数在线程池执行，异步函数直接等待。

```python
@xxljob.on_run("importUsers")
async def import_users(param):
    return "accepted"

@xxljob.on_kill
def stop_task(param):
    return None
```

批量设置可使用 `register_callbacks`、各 `get_*_callback` 读取接口和替换选项。未知名称和错误返回类型会转为 XXL-JOB 业务失败，但 HTTP 状态仍为 200。

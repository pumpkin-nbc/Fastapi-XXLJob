# FastAPI-XXLJob

[English](README.md) | [简体中文](README.zh-CN.md)

`fastapi-xxljob` 是 XXL-JOB 2.4.1 执行器协议的类型化 FastAPI 适配器。0.1.0 版本与 Flask-XXLJob 0.4.0 的协议和能力对齐，同时遵循 FastAPI 的异步与 lifespan 模型。

## 功能

- 完整支持 `/beat`、`/idleBeat`、`/run`、`/kill` 和 `/log` 五个端点。
- 同时支持同步和异步 Handler，并按 FastAPI 应用隔离。
- 自动注册续约、注销、回调、有限重试和多地址故障转移。
- 请求限流式读取、常量时间 Token 校验、敏感信息过滤和托管日志。
- 异步优先接口，以及供脚本和 Worker 使用的显式 `*_sync` 方法。

## 安装

要求 Python 3.8 或更高版本。

```bash
pip install fastapi-xxljob==0.1.0
```

## 快速开始

```python
from fastapi import FastAPI
from fastapi_xxljob import FastAPIXXLJob

app = FastAPI()
xxljob = FastAPIXXLJob(app, {
    "XXL_JOB_ADMIN_ADDRESSES": "http://127.0.0.1:8080/xxl-job-admin",
    "XXL_JOB_ACCESS_TOKEN": "default_token",
    "XXL_JOB_EXECUTOR_APP_NAME": "fastapi-xxljob-executor",
    "XXL_JOB_EXECUTOR_ADDRESS": "http://127.0.0.1:8000",
})

@xxljob.on_run("demoJobHandler")
async def demo(param):
    return f"processed: {param.executor_params}"
```

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

协议路由默认位于应用根路径并从 OpenAPI 隐藏；如需 `/xxl-job` 等前缀可设置 `XXL_JOB_ROUTE_PREFIX`。运行、空闲检测和终止 Handler 返回 `XXLJobResponse`；日志 Handler 还可返回 `LogResponse`。

回调接口异步优先：

```python
await xxljob.callback_success(log_id=1, log_date_time=1730000000000)
xxljob.callback_failure_sync(log_id=2, log_date_time=1730000000000, message="failed")
```

## 主要配置

| 配置项 | 用途 |
| --- | --- |
| `XXL_JOB_ENABLED` | 启用协议和 Admin 操作。 |
| `XXL_JOB_ADMIN_ADDRESSES` | 逗号分隔的 Admin 基础地址。 |
| `XXL_JOB_ACCESS_TOKEN` | 执行器共享 Token。 |
| `XXL_JOB_EXECUTOR_APP_NAME` | 执行器应用名称。 |
| `XXL_JOB_EXECUTOR_ADDRESS` | 执行器公开访问地址。 |
| `XXL_JOB_ROUTE_PREFIX` | 可选路由前缀，默认为空。 |
| `XXL_JOB_AUTO_REGISTER` | 随应用 lifespan 启动注册续约。 |
| `XXL_JOB_DEREGISTER_ON_EXIT` | 正常关闭时注销。 |
| `XXL_JOB_REGISTRY_INTERVAL` | 续约间隔秒数。 |
| `XXL_JOB_HTTP_CONNECT_TIMEOUT` | Admin 连接超时。 |
| `XXL_JOB_HTTP_READ_TIMEOUT` | Admin 响应超时。 |
| `XXL_JOB_ADMIN_RETRY_COUNT` | 每个 Admin 地址的有限重试次数。 |
| `XXL_JOB_MAX_REQUEST_SIZE` | 协议请求最大字节数。 |
| `XXL_JOB_MAX_PARAM_LENGTH` | 字符串字段最大长度。 |
| `XXL_JOB_CALLBACK_BATCH_MAX_SIZE` | 原子回调批次最大数量。 |
| `XXL_JOB_CALLBACK_MESSAGE_MAX_LENGTH` | 回调消息最大长度。 |
| `XXL_JOB_LOG_ENABLED` | 启用插件托管日志。 |
| `XXL_JOB_LOG_FILE_ENABLED` | 启用轮转文件日志。 |
| `XXL_JOB_LOG_CONSOLE_ENABLED` | 启用控制台日志。 |
| `XXL_JOB_LOG_PATH` | 托管日志目录。 |

更多内容见[快速入门](docs/getting-started.zh-CN.md)、[配置](docs/configuration.zh-CN.md)、[API 参考](docs/api-reference.zh-CN.md)和[示例](examples/basic/README.zh-CN.md)。

## 命令行

```bash
fastapi-xxljob --app app:app register
fastapi-xxljob --app app:create_app --factory status
fastapi-xxljob --app app:app remove
```

## 边界

本包只适配执行器协议，不负责调度业务任务、创建任务队列、存储任务日志、提供回调 Outbox 或无限重试。

采用 Apache-2.0 许可证，详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。

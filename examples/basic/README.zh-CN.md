# 基础示例

此应用公开异步 `demoJobHandler`，且不会连接 Admin。

```bash
uvicorn examples.basic.app:app --port 8000
```

将 XXL-JOB 执行器地址配置为 `http://127.0.0.1:8000`；示例 Token 只适合本地测试。

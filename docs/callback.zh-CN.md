# 结果回调

异步应用应等待 `callback`、`callback_success`、`callback_failure` 或 `callback_many`；同步 Worker 使用对应的 `_sync` 方法。

```python
await xxljob.callback_success(10, 1730000000000, "done")
await xxljob.callback_many([item_a, item_b])
```

批量内容会在发送 Admin 请求前完成整体校验。消息会按 Unicode 边界安全截断，并在记录日志前过滤敏感信息。

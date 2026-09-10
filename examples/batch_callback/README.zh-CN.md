# 批量回调示例

`report_batch` 会先校验完整集合，再向 Admin 发送一次请求。

```python
result = await report_batch()
print(result.success)
```

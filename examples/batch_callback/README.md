# Batch callback example

`report_batch` validates the complete collection before it sends one request to Admin.

```python
result = await report_batch()
print(result.success)
```

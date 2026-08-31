# 多应用示例

一个扩展可以为多个应用维护相互隔离的运行时。在请求处理之外调用时需显式传入应用。

```python
status_a, status_b = status_for_each_app()
```

# Multiple applications example

One extension may own isolated runtimes for multiple applications. Explicitly pass the application outside request handling.

```python
status_a, status_b = status_for_each_app()
```

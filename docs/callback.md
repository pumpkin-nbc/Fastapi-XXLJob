# Result callbacks

Async applications should await `callback`, `callback_success`, `callback_failure`, or `callback_many`. Synchronous workers use the matching `_sync` methods.

```python
await xxljob.callback_success(10, 1730000000000, "done")
await xxljob.callback_many([item_a, item_b])
```

Batches are validated completely before an Admin request is sent. Messages are truncated safely at Unicode boundaries and filtered before logging.

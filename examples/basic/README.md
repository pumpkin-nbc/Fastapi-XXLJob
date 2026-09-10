# Basic example

This application exposes an async `demoJobHandler` without contacting Admin.

```bash
uvicorn examples.basic.app:app --port 8000
```

Configure the XXL-JOB executor URL as `http://127.0.0.1:8000` and use the token from the example only for local testing.

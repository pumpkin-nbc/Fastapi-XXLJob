# Application factory example

Handlers may be registered before the application exists and are copied into the bound runtime.

```bash
uvicorn examples.application_factory.app:create_app --factory
```

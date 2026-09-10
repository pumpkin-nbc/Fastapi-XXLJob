# 应用工厂示例

Handler 可以在应用创建前注册，并在绑定时复制到对应运行时。

```bash
uvicorn examples.application_factory.app:create_app --factory
```

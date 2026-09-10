# Integration testing

Default tests use an in-process FastAPI client and mocked Admin transport, so no external service is required. Set `XXLJOB_ADMIN_URL` only when intentionally running the optional XXL-JOB 2.4.1 Admin integration test; configure an isolated executor group and disposable data.

Never point integration tests at production. Validate registration, callback, and removal in that order, then confirm the Admin no longer lists the test executor.

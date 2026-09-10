# Deployment

Run behind a production ASGI server and expose only the configured route prefix. Each ASGI worker maintains one registry thread for its process; the package does not elect a cross-process leader.

Configure HTTPS, a non-empty token, network access controls, bounded timeouts, and an executor address reachable from XXL-JOB Admin. Graceful lifespan shutdown performs idempotent deregistration when enabled.

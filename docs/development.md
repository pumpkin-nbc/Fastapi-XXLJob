# Development

Use the repository `.venv` and install `.[dev]`. Required local gates are Ruff, Mypy, documentation consistency, tests with at least 90% coverage, build, Twine validation, package inspection, and an isolated wheel smoke test.

Protocol changes need success and failure tests. Preserve HTTP 200 ReturnT semantics, per-application isolation, Python 3.8 syntax, bounded retries, and non-blocking async APIs.

CI runs the complete suite against FastAPI 0.124.4 on Python 3.8, FastAPI 0.125.0 on Python 3.9, and the latest compatible pre-1.0 FastAPI release on every Python version from 3.10 through 3.14.

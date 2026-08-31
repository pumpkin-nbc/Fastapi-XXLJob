# Development

Use the repository `.venv` and install `.[dev]`. Required local gates are Ruff, Mypy, documentation consistency, tests with at least 90% coverage, build, Twine validation, package inspection, and an isolated wheel smoke test.

Protocol changes need success and failure tests. Preserve HTTP 200 ReturnT semantics, per-application isolation, Python 3.8 syntax, bounded retries, and non-blocking async APIs.

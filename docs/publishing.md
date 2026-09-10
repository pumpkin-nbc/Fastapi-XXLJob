[English](publishing.md) | [简体中文](publishing.zh-CN.md)

# Publishing

Releases use GitHub Actions Trusted Publishing. No long-lived PyPI API token is stored in the repository. Local commands build and inspect distributions; `.github/workflows/release.yml` performs uploads.

## Build

Build into a new empty directory so historical files cannot be mistaken for the current release:

```powershell
$version = .venv\Scripts\python.exe -c `
  'import runpy; print(runpy.run_path("fastapi_xxljob/_version.py")["__version__"])'
$buildDir = Join-Path $env:TEMP "fastapi-xxljob-$version-dist"
Remove-Item -LiteralPath $buildDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $buildDir | Out-Null
.venv\Scripts\python.exe -m build --outdir $buildDir
```

The directory must contain exactly:

```text
fastapi_xxljob-X.Y.Z-py3-none-any.whl
fastapi_xxljob-X.Y.Z.tar.gz
```

## Check

```powershell
.venv\Scripts\python.exe scripts\check_docs.py
.venv\Scripts\python.exe scripts\check_package.py --dist-dir $buildDir
$artifacts = @(Get-ChildItem -LiteralPath $buildDir -File)
.venv\Scripts\python.exe -m twine check $artifacts.FullName
```

The project validator checks wheel RECORD hashes and sizes, metadata, the standard top-level sdist `PKG-INFO`, required source, typing and legal files, and rejects caches or development directories.

## Isolated installed-wheel smoke test

Create a Python 3.8 virtual environment and working directory outside the source checkout. Install the wheel plus `httpx<0.29`, run `pip check`, clear `PYTHONPATH`, and execute `scripts/smoke_installed_wheel.py`. The smoke test verifies the installed package and metadata version, CLI, five executor endpoints, registration, callback, and removal.

## Configure Trusted Publishing

Create Pending Trusted Publishers on PyPI and TestPyPI with:

- Project: `fastapi-xxljob`
- Owner: `pumpkin-nbc`
- Repository: `Fastapi-XXLJob`
- Workflow: `release.yml`
- PyPI environment: `pypi`
- TestPyPI environment: `testpypi`

Create matching GitHub Environments. Leave required reviewers disabled for unattended tag publishing, or enable them when a manual production gate is preferred. Only the publishing jobs receive `id-token: write`; build and validation remain read-only.

## Publish to TestPyPI

Run the `Release` workflow manually. A `workflow_dispatch` run builds and validates one artifact set, then publishes it through the `testpypi` environment.

Install dependencies from PyPI before installing the package from TestPyPI without dependency resolution:

```bash
python -m pip install --index-url https://pypi.org/simple "fastapi>=0.124.4,<1.0" requests
python -m pip install --index-url https://test.pypi.org/simple --no-deps fastapi-xxljob==X.Y.Z
python -c "import fastapi_xxljob; print(fastapi_xxljob.__version__)"
fastapi-xxljob --version
```

## Publish to PyPI

After Required CI passes on `develop` and `master`, create the release tag from a commit contained in `master`:

```bash
version="$(python -c 'import runpy; print(runpy.run_path("fastapi_xxljob/_version.py")["__version__"])')"
git tag -a "v${version}" -m "Release ${version}"
git push origin "v${version}"
```

The tag starts the `Release` workflow. It first runs the complete Required CI workflow, then verifies the tag, package version, both changelogs, membership in `master`, and the dynamically discovered wheel and sdist before Trusted Publishing. If the `pypi` environment has required reviewers, publication waits for their approval.

## Before publishing

Confirm that wheel and sdist contain `LICENSE` and `NOTICE`, declare Apache-2.0, use the real project URLs, and contain no secrets, internal hostnames, or tokens. Never validate a directory containing artifacts from multiple builds.

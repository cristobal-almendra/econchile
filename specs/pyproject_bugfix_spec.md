# Bug Fix Spec — pyproject.toml (packaging)

Three confirmed defects from the packaging evaluation (deleg_82611153, verified
by building the package in a temp copy). Fix all three + verify with a clean build.

## Bug 1: Invalid build backend

`build-backend = "setuptools.backends._legacy:_Backend"` does not exist
(`ModuleNotFoundError: No module named 'setuptools.backends'`). Every install
and publish path fails: `pip install -e .`, `pip install .`, `python -m build`.

**Fix:** change to `build-backend = "setuptools.build_meta"` (keep
`requires = ["setuptools>=68.0"]`).

## Bug 2: Private annotated files ship in wheel + sdist

`econchile/study/*_annotated.py` (125 KB of private working notes) is picked
up by `packages.find` as a namespace subpackage and ships in BOTH artifacts,
even though `study/` is gitignored (gitignore does not affect packaging).

**Fix:** under `[tool.setuptools.packages.find]` add
`exclude = ["econchile.study*"]`.

**Caution:** the exclude only works on a CLEAN build — a stale `build/` dir
silently reintroduces the files. Always `rm -rf dist build *.egg-info` before
building (verified during evaluation).

## Bug 3: PEP 639 license conflict

`license = {text = "MIT"}` PLUS the
`License :: OSI Approved :: MIT License` classifier → `InvalidConfigError:
License classifiers have been superseded by license expressions` on
setuptools 79.

**Fix:** `license = "MIT"` and DELETE the license classifier line.

## Verification (must pass)

1. `rm -rf dist build econchile.egg-info` then build:
   - `pip install build` (if missing) then `python -m build` — or `uvx build`
2. Inspect the wheel (`unzip -l dist/*.whl` or `python -m zipfile -l`):
   - NO `econchile/study/` entries
   - NO `sample_response.json` (already excluded by default — confirm)
3. Inspect sdist (`tar tzf dist/*.tar.gz`): same exclusions.
4. METADATA check (`unzip -p dist/*.whl '*/METADATA'`):
   - `Requires-Dist: requests>=2.31` present
   - `License-Expression: MIT` (or equivalent)
5. Fresh-venv smoke test:
   `python -m venv /tmp/econchile-smoke && /tmp/econchile-smoke/Scripts/pip install dist/*.whl`
   then `import econchile` and `econchile.__version__ == "0.1.0"`.
6. Full test suite still green: `python -m pytest tests/ -q` (188 passed).

## Constraints
- Touch ONLY pyproject.toml. No source code, no tests, no README edits.
- Do not add `[project.urls]`, MANIFEST.in, CI, or any other enhancement —
  that's a separate step.

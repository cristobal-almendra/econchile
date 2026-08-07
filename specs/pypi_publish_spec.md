# PyPI Publish — econchile v0.1.0

## What you need (credentials)

1. **PyPI account** — https://pypi.org/account/register/
   Use a real email. This is SEPARATE from GitHub — different site, different password.
2. **API token** (not your password) — https://pypi.org/manage/account/token/
   - Click "Add API token", scope = "Entire account" (or "econchile" if it exists)
   - Copy the token immediately: starts with `pypi-...`
   - **This token is like a password — never put it in the repo.** It goes in Windows Credential Manager or a one-time `twine upload` prompt.
3. (Optional) **TestPyPI** first to dry-run: https://test.pypi.org/ — same process, different token.

## Local prep (Hermes does this)

- [x] pyproject.toml fixed (build backend, license, study exclude)
- [ ] Add MANIFEST.in (explicit: keep sample_response.json OUT of wheel/sdist)
- [ ] Build: `rm -rf dist build *.egg-info && python -m build`
- [ ] Verify wheel has NO sample_response.json, NO study/
- [ ] `twine check dist/*` — must pass

## Publish commands (PowerShell, run by Cristobal)

```powershell
# 1. Install publishing tools (one time)
pip install build twine

# 2. Clean build
cd C:\Users\crist\OneDrive\Documentos\hermes-total\econchile
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
python -m build

# 3. Sanity-check the artifacts
twine check dist/*

# 4a. DRY RUN on TestPyPI first (recommended)
twine upload --repository testpypi dist/*
#   → when prompted for username: __token__
#   → when prompted for password: paste your pypi-... TestPyPI token

# 4b. REAL publish to PyPI
twine upload dist/*
#   → username: __token__
#   → password: paste your pypi-... PyPI token
```

## Verify after publish

```powershell
pip install econchile
python -c "import econchile; print(econchile.__version__)"
```

## Gotchas

- `twine` username is literally `__token__` (with the underscores), not your PyPI username.
- The token is entered at the `twine upload` password prompt — it is NOT written to any file. Windows may cache it in Credential Manager; that's fine.
- If "econchile" name is taken on PyPI, pick another (econchile-py, econchile-bcch).
- Version 0.1.0 can only be uploaded ONCE. To republish you must bump version in pyproject.toml + __init__.py.
- NEVER commit the token. If you accidentally do, delete the token on pypi.org immediately and rotate.

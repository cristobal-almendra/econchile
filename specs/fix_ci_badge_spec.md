# Fix CI badge — `skip-existing` on PyPI publish

## Context
The PyPI project page badge `Publish to PyPI` shows **failing**. Root cause: the
`v0.1.1` tag push ran the publish job twice (one trusted-publisher success at 17:21,
then a redundant manual/CI upload at 18:01). The second upload hit PyPI's hard rule
"File already exists" → `400`, failing that run. The badge follows the *latest* workflow
run, so it's red even though 0.1.1 is correctly published.

## Fix
Add `skip-existing: true` to the `pypa/gh-action-pypi-publish` step in
`.github/workflows/workflow.yml`. This makes twine exit 0 (instead of 400) when the
version's files are already on PyPI — so a re-run of the failed job succeeds and the
badge flips to passing. It is also a permanent safety improvement: future accidental
re-runs or duplicate tag pushes will no-op instead of failing.

## Change (exact)
In the `publish` job's `Publish to PyPI` step `with:` block, add:
```yaml
        with:
          packages-dir: dist
          skip-existing: true
```
No other file changes.

## Acceptance
1. `.github/workflows/workflow.yml` has `skip-existing: true` under the publish step.
2. Workflow file is still valid YAML; only that one line added (no version bump, no
   source changes, no test changes).
3. After Hermes re-runs the failed job `31205038308`, its conclusion becomes `success`
   and the badge `https://github.com/cristobal437/econchile/actions/workflows/workflow.yml/badge.svg`
   reports `passing`.

## Out of scope
- No new PyPI release. 0.1.1 stays as-is.
- No branch protection change (ruleset already created by user).

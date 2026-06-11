# Add pre-commit configuration

**Date:** 2026-06-10

## Summary

Added pre-commit hooks for code quality automation.

## Changes

- Created `.pre-commit-config.yaml` with two repos:
  - `pre-commit-hooks` (v5.0.0): trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files, check-merge-conflict, detect-private-key
  - `ruff-pre-commit` (v0.11.0): ruff linter with `--fix` and ruff-formatter

## Usage

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

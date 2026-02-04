# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ormar is an async ORM for Python that combines Pydantic validation with SQLAlchemy core. A single model class serves as both the ORM model and Pydantic model for validation. It's designed for async frameworks like FastAPI and Starlette, supporting PostgreSQL, MySQL, and SQLite.

## Common Commands

```bash
# Testing
make test                  # Run tests with pytest (SQLite)
make test_all              # Run tests with pytest (all DBs)
make test_sqlite           # Run SQLite tests
make test_mysql            # Run MySQL tests (requires Docker)
make test_pg               # Run PostgreSQL tests (requires Docker)
make coverage              # Run tests with 100% coverage requirement

# Run a single test
pytest -svv tests/test_model_definition/test_model_definition.py::test_function_name

# Code quality
make fmt                   # Format with black
make lint                  # Lint with ruff
make type_check           # Type check with mypy
make pre-commit           # Run fmt + lint + type_check
```

# Workflow
- Always create a new branch for code changes
- Prefer running single tests, and not the whole test suite, for performance
- Make sure to run `make pre-commit` before committing

## Architecture

### Core Modules (`ormar/`)

| Module | Purpose |
|--------|---------|
| `models/` | Model class, OrmarConfig, metaclass, model mixins |
| `queryset/` | QuerySet with filters, ordering, joins, CRUD operations |
| `fields/` | Field types (String, Integer, ForeignKey, ManyToMany, etc.) |
| `relations/` | Relation management and reverse accessors |
| `decorators/` | Signal decorators (@pre_save, @post_delete, etc.) |
| `signals/` | Model lifecycle event system |

### Key Patterns

- **Metaclass registration**: Model metaclass registers SQLAlchemy tables in metadata
- **Dual model**: Each Model is both an ORM model and Pydantic model
- **OrmarConfig**: Configuration holder for database, metadata, engine, tablename
- **Async operations**: Uses `sqlalchemy` library for async DB access
- **Automatic reverse relations**: ForeignKey/ManyToMany create reverse accessors


## Code Quality Requirements

- All code must pass `make pre-commit`
- All files, classes, and functions must have docstrings with current formatting
- 100% test coverage required
- Type hints required (mypy strict mode)
- Tests must pass on Python 3.9-3.12
- Tests run against SQLite, PostgreSQL, and MySQL in CI
- Avoid adding information about claude.ai to the code

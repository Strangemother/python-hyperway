# Agents Instructions

The main developer documentation lives in the `docs/` directory. The following points summarise how to set up the environment, build tests, run checks, build docs. Additional examples exist within the `workspace/` Directory. The primary `README.md` contains human-readable documentation about the project.

## Setting up the Development Environment

This is a standard Python package, using `pip` and `venv` for environment management. To set up the development environment. Utilise the `pyproject.toml` file for dependency management.

## Building and Running Tests

Tests are located in the `tests/` directory. You can run tests using `pytest`. Ensure you have all development dependencies installed. For quick testing, you can run `./quicktest.sh` from the root directory.

## Code Quality and Formatting

We use `pep8` for style checking.

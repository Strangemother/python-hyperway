
# Development

## Running Tests

The project uses `pytest` for testing. Run tests with:

```bash
# Quick test (uses virtualenv)
./quick_test.sh

# Or manually with pytest
pytest -v

# With coverage report
pytest --cov=hyperway --cov-report=term-missing
```

## Code Coverage with Tox

The project is configured with [tox](https://tox.wiki/) for running tests across multiple Python versions and generating coverage reports for SonarQube.

### Tox Configuration

```ini
[tox]
envlist = py38,py39,py310,py311,py312
skipsdist = False
skip_missing_interpreters = true

[testenv]
deps =
    pytest
    pytest-cov
commands = pytest --cov=hyperway --cov-report=xml --cov-report=term-missing --cov-config=tox.ini --cov-branch tests/

[coverage:run]
source = src/hyperway
omit = 
    */tests/*
    */__pycache__/*
branch = True
relative_files = True

[coverage:report]
precision = 2
show_missing = True
skip_covered = False

[coverage:xml]
output = coverage.xml
```

### Running Tox

```bash
# Install tox
pip install tox

# Run tests for all configured Python versions
tox

# Run tests for a specific Python version
tox -e py312

# Generate coverage report for SonarQube
tox
# This creates coverage.xml in the project root
```

### SonarQube Integration

The project includes a `sonar-project.properties` file configured for SonarQube analysis:

- Coverage reports are generated in XML format at `coverage.xml`
- Source code is in `src/`
- Tests are in `tests/`
- Supports Python 3.8 through 3.12

To run SonarQube analysis locally:

```bash
# Generate coverage
tox

# Run sonar-scanner (requires sonar-scanner installation)
sonar-scanner
```

## Installing Development Dependencies

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Or manually
pip install pytest pytest-cov tox
```


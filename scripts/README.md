# Build Scripts

This directory contains build and release automation scripts for the python-hyperway project.

## Scripts

### `update_version.py`

Synchronizes the version number from `src/hyperway/_version.py` to `sonar-project.properties`.

**Usage:**
```bash
python scripts/update_version.py
```

**What it does:**
1. Imports the current version from `hyperway.__version__`
2. Updates the `sonar.projectVersion` line in `sonar-project.properties`

**Automated Usage:**
This script is automatically run by GitHub Actions during:
- Release builds (before building the package)
- SonarCloud analysis (before running analysis)

See [Version Management Documentation](../docs/version-management.md) for more details.

---

### `generate_coverage.sh`

Generates code coverage reports for SonarQube/SonarCloud analysis.

**Usage:**
```bash
# Run all configured Python versions
./scripts/generate_coverage.sh

# Run specific Python version
./scripts/generate_coverage.sh py312
```

**What it does:**
1. Runs tests using `tox` with coverage enabled
2. Generates `coverage.xml` in the project root
3. Provides feedback on coverage report generation
4. Verifies the coverage file was created successfully

**Output:**
- `coverage.xml` - Code coverage report in Cobertura format

See [SonarQube Documentation](../docs/sonarqube/) for more details.

---

## Future Scripts

Additional build and release automation tools will be added to this directory as needed.

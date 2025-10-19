# SonarQube Setup for python-hyperway

## Overview

This project is configured for SonarQube code coverage and analysis with the following setup:

## Files Added/Modified

### 1. `tox.ini` - Test Automation and Coverage
- Configures tox to run tests across Python 3.8-3.12
- Generates XML coverage report for SonarQube at `coverage.xml`
- Enables branch coverage analysis
- Uses relative file paths for better portability

### 2. `sonar-project.properties` - SonarQube Configuration
- Project identification and metadata
- Source/test directory configuration
- Coverage report path configuration
- Exclusions for non-source directories

### 3. `pyproject.toml` - Added tox to dev dependencies
- Added `tox` to `[project.optional-dependencies]`

### 4. `README.md` - Development Section
- Added comprehensive "Development" section
- Includes testing instructions
- Documents tox configuration
- Explains SonarQube integration

## Quick Start

### Generate Coverage Report

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tox to generate coverage
tox

# Or for a specific Python version
tox -e py312
```

This will:
1. Run all tests with pytest
2. Generate `coverage.xml` in the project root
3. Display coverage report in terminal

### Current Coverage

Latest run shows **96.38% coverage** with:
- 745 statements
- 721 covered
- 166 branches
- 163 branches covered (98.2% branch coverage)

### SonarQube Integration

The `coverage.xml` file is in Cobertura format, which SonarQube natively supports.

#### For Local Analysis:
```bash
# Generate coverage
tox

# Run sonar-scanner (requires installation)
sonar-scanner
```

#### For CI/CD:
The coverage.xml will be automatically picked up by SonarQube when:
1. The sonar-scanner runs in your CI/CD pipeline
2. The `sonar.python.coverage.reportPaths=coverage.xml` property is set (already configured)

### Configuration Details

#### Tox Environment
- `envlist`: py38, py39, py310, py311, py312
- `skip_missing_interpreters = true`: Skips versions not installed
- Coverage includes branch analysis (`--cov-branch`)

#### Coverage Settings
- Source: `src/hyperway`
- Omits: test files and Python cache
- Precision: 2 decimal places
- Shows missing lines in reports

#### SonarQube Properties
- Project Key: `python-hyperway`
- Project Name: `Python Hyperway`
- Sources: `src`
- Tests: `tests`
- Exclusions: Generated files, docs, test files, virtual environments

## Files Generated

When you run `tox`, these files are created:
- `coverage.xml` - Cobertura format coverage report (commit this if needed)
- `.tox/` - Virtual environments for each Python version (don't commit)
- `.coverage` - Coverage data file (don't commit)

## Troubleshooting

### Only one Python version available
Set `skip_missing_interpreters = true` in `tox.ini` (already done) to allow tox to run with only available Python versions.

### Coverage not showing in SonarQube
1. Verify `coverage.xml` exists in project root
2. Check `sonar-project.properties` has correct path
3. Ensure sonar-scanner runs after `tox`
4. Check SonarQube project settings for Python plugin

### Coverage paths incorrect
The `relative_files = True` setting in tox.ini ensures paths are relative, making the coverage report portable across different environments.

## GitHub Actions Integration

GitHub workflows have been created for automated SonarQube/SonarCloud integration:

### Available Workflows

1. **`.github/workflows/sonarcloud.yml`** - For SonarCloud (recommended for open source)
2. **`.github/workflows/sonarqube.yml`** - For self-hosted SonarQube

### Quick Setup

See detailed instructions in `.github/GITHUB_WORKFLOW_SETUP.md`

**For SonarCloud (recommended):**
```bash
# 1. Sign up at sonarcloud.io with GitHub
# 2. Select python-hyperway repository
# 3. Add SONAR_TOKEN to GitHub Secrets
# 4. Update workflow with your organization name
# 5. Remove the unused sonarqube.yml workflow
# 6. Push to trigger the workflow
```

**For SonarQube:**
```bash
# 1. Set up SonarQube server
# 2. Add SONAR_TOKEN and SONAR_HOST_URL to GitHub Secrets
# 3. Remove the unused sonarcloud.yml workflow
# 4. Push to trigger the workflow
```

### Workflow Features

Both workflows automatically:
- ✅ Run on push to main and pull requests
- ✅ Set up Python 3.12
- ✅ Install tox
- ✅ Generate coverage report
- ✅ Upload to SonarQube/SonarCloud
- ✅ Verify coverage file exists

## Next Steps

1. ✅ Tox configuration is complete and tested
2. ✅ Coverage XML generation is working
3. ✅ SonarQube properties file is created
4. ✅ Documentation is updated
5. ✅ GitHub workflows created for CI/CD
6. 🔲 Choose SonarCloud or SonarQube
7. 🔲 Set up secrets in GitHub repository
8. 🔲 Enable the appropriate workflow
9. 🔲 Add SonarQube/SonarCloud badge to README (optional)

## Additional Resources

- [Tox Documentation](https://tox.wiki/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [SonarQube Python Documentation](https://docs.sonarqube.org/latest/analysis/languages/python/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

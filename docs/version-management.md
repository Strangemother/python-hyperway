# Version Management

The version is defined in **`src/hyperway/_version.py`**:

```python
__version__ = "1.0.5"
```

The `pyproject.toml` uses dynamic versioning to read from the `_version.py` file:

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "hyperway._version.__version__"}
```

`sonar-project.properties` is a plain text config file, we use a Python script to sync it:

```bash
python scripts/update_version.py
```

This script:
1. Reads the version from `src/hyperway/_version.py`
2. Updates the `sonar.projectVersion` line in `sonar-project.properties`

## Updating the Version

**To update the version for a new release:**

1. Edit **only** the version in `src/hyperway/_version.py`:
   ```python
   __version__ = "1.0.6"
   ```

2. (Optional) Run the update script to sync SonarQube config:
   ```bash
   python scripts/update_version.py
   ```
   > **Note:** The GitHub Actions workflow automatically runs this script during release builds, so you don't have to remember to do it manually.

3. Commit the version file:
   ```bash
   git add src/hyperway/_version.py
   # Optionally include sonar-project.properties if you ran scripts/update_version.py
   git commit -m "Bump version to 1.0.6"
   ```

### Automated Workflow

The GitHub Actions workflow (`.github/workflows/python-publish.yml`) automatically syncs the version before:
- **Building releases** - Ensures the package has the correct version
- **SonarCloud analysis** - Ensures the analysis reports the correct version

This means even if you forget to run `scripts/update_version.py` locally, the CI/CD pipeline will ensure everything stays in sync.

## Verification

Check that the version is correctly set:

```bash
# Check package version
python -c "import sys; sys.path.insert(0, 'src'); from hyperway import __version__; print(__version__)"

# Check SonarQube version
grep "sonar.projectVersion" sonar-project.properties

# Or run the sync script to verify
python scripts/update_version.py
```


# GitHub Workflow Setup for SonarQube/SonarCloud

This document explains how to set up automated code quality analysis and coverage reporting using either SonarQube or SonarCloud with GitHub Actions.

## Overview

Two workflow files have been created:

1. **`sonarqube.yml`** - For self-hosted or enterprise SonarQube instances
2. **`sonarcloud.yml`** - For SonarCloud (cloud-based, free for open source)

## Option 1: SonarCloud (Recommended for Open Source)

SonarCloud is free for open-source projects and requires minimal setup.

### Setup Steps

#### 1. Create SonarCloud Account
1. Go to [SonarCloud.io](https://sonarcloud.io)
2. Sign in with your GitHub account
3. Click "Analyze new project"
4. Select `python-hyperway` repository

#### 2. Configure Organization and Project
- **Organization**: Your GitHub username (e.g., `strangemother`)
- **Project Key**: `Strangemother_python-hyperway` (automatically generated)

#### 3. Update Workflow File
Edit `.github/workflows/sonarcloud.yml` and update these values:
```yaml
-Dsonar.projectKey=YOUR_GITHUB_USERNAME_python-hyperway
-Dsonar.organization=YOUR_GITHUB_USERNAME
```

#### 4. Add GitHub Secret
1. Go to GitHub repository: **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `SONAR_TOKEN`
4. Value: Get from SonarCloud → Account → Security → Generate Token
5. Save

#### 5. Enable Workflow
1. Rename or delete the unused workflow:
   ```bash
   # If using SonarCloud, remove SonarQube workflow
   rm .github/workflows/sonarqube.yml
   ```
2. Commit and push to trigger the workflow

### SonarCloud Workflow Features
- ✅ Runs on every push to `main`
- ✅ Runs on every pull request
- ✅ Generates coverage report with tox
- ✅ Uploads coverage to SonarCloud
- ✅ Tests with Python 3.12
- ✅ Uses `coverage.xml` from tox

---

## Option 2: Self-Hosted SonarQube

For private projects or enterprise use.

### Setup Steps

#### 1. SonarQube Server Setup
Ensure you have a SonarQube server running and accessible from GitHub Actions.

#### 2. Create Project in SonarQube
1. Log into your SonarQube instance
2. Create new project
3. Note the **Project Key** (e.g., `python-hyperway`)

#### 3. Generate Token
1. Go to SonarQube → My Account → Security
2. Generate a token for CI/CD
3. Save it securely

#### 4. Add GitHub Secrets
Add these secrets in GitHub repository settings:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `SONAR_TOKEN` | Authentication token from SonarQube | `sqp_1234567890abcdef` |
| `SONAR_HOST_URL` | Your SonarQube server URL | `https://sonarqube.yourcompany.com` |
| `SONAR_ORGANIZATION` | Organization key (if applicable) | `your-org` |

#### 5. Update sonar-project.properties
Ensure `sonar-project.properties` has the correct project key:
```ini
sonar.projectKey=python-hyperway
```

#### 6. Enable Workflow
```bash
# If using SonarQube, remove SonarCloud workflow
rm .github/workflows/sonarcloud.yml
```

### SonarQube Workflow Features
- ✅ Runs on every push to `main`
- ✅ Runs on every pull request
- ✅ Generates coverage report with tox
- ✅ Uploads coverage to SonarQube
- ✅ Includes Quality Gate check
- ✅ Tests with Python 3.12
- ✅ Uses `coverage.xml` from tox

---

## Configuration Details

### Tox Integration

Both workflows use tox to run tests and generate coverage:

```bash
tox -e py312
```

This command:
1. Creates isolated Python 3.12 environment
2. Installs dependencies
3. Runs pytest with coverage
4. Generates `coverage.xml` in project root

### Coverage Report

The `coverage.xml` file is in Cobertura format and includes:
- Line coverage
- Branch coverage
- Source file paths
- Execution counts

Both SonarQube and SonarCloud automatically detect and parse this file via the configuration in `sonar-project.properties`:

```ini
sonar.python.coverage.reportPaths=coverage.xml
```

### Workflow Triggers

Both workflows trigger on:
- **Push to main**: Analyzes code after merging
- **Pull requests**: Analyzes PRs before merging (opened, updated, or reopened)

### Python Version Strategy

Currently configured for Python 3.12 only in CI. To test multiple versions:

```yaml
strategy:
  matrix:
    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
```

However, this is not recommended for SonarQube as it only needs coverage from one Python version.

---

## Verification

### Check Workflow Status

1. Go to GitHub repository → **Actions** tab
2. You should see workflows running after push/PR
3. Click on a workflow to see detailed logs

### Check SonarQube/SonarCloud

1. Log into SonarQube or SonarCloud
2. Navigate to your project
3. Verify:
   - Code coverage percentage
   - Quality metrics
   - Issues detected
   - Security vulnerabilities

### Local Testing

Test the workflow locally before pushing:

```bash
# Generate coverage
./generate_coverage.sh py312

# Verify coverage.xml exists
ls -lh coverage.xml

# Optionally run sonar-scanner locally (requires installation)
sonar-scanner
```

---

## Troubleshooting

### Coverage file not found
**Error**: `coverage.xml not found`

**Solution**:
```bash
# Verify tox generates coverage.xml
tox -e py312
ls -lh coverage.xml
```

### Wrong Python version
**Error**: `No py312 environment`

**Solution**: Update workflow to use available Python version in tox.ini

### Authentication failed
**Error**: `Unauthorized` or `403`

**Solution**:
- Verify `SONAR_TOKEN` secret is set correctly
- Check token hasn't expired
- Ensure token has correct permissions

### Coverage is 0%
**Error**: Coverage shows 0% in SonarQube

**Solution**:
- Check `coverage.xml` paths are relative (set in `tox.ini`)
- Verify `sonar.python.coverage.reportPaths` is correct
- Check source paths in `coverage.xml` match project structure

### Quality Gate fails
**Error**: Workflow fails on quality gate check

**Solution**: 
- Review quality gate settings in SonarQube/SonarCloud
- Fix identified issues
- Or set `continue-on-error: true` (already configured) to not block CI

---

## Badge for README

### SonarCloud Badge

Add to README.md:

```markdown
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Strangemother_python-hyperway&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Strangemother_python-hyperway)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=Strangemother_python-hyperway&metric=coverage)](https://sonarcloud.io/summary/new_code?id=Strangemother_python-hyperway)
```

Update `Strangemother_python-hyperway` with your project key.

### SonarQube Badge

For self-hosted SonarQube:

```markdown
[![Quality Gate Status](https://your-sonarqube-url/api/project_badges/measure?project=python-hyperway&metric=alert_status)](https://your-sonarqube-url/dashboard?id=python-hyperway)
[![Coverage](https://your-sonarqube-url/api/project_badges/measure?project=python-hyperway&metric=coverage)](https://your-sonarqube-url/dashboard?id=python-hyperway)
```

---

## Maintenance

### Updating Dependencies

When updating Python versions or dependencies:

1. Update `tox.ini` with new Python versions
2. Update workflow file with corresponding version
3. Test locally with `tox`
4. Commit and push

### Adjusting Coverage Thresholds

Configure in SonarQube/SonarCloud UI:
- Project Settings → Quality Gates
- Set minimum coverage thresholds
- Configure conditions for new code vs overall code

---

## Additional Resources

- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [SonarQube Python Documentation](https://docs.sonarqube.org/latest/analysis/languages/python/)
- [GitHub Actions - SonarCloud](https://github.com/marketplace/actions/sonarcloud-scan)
- [GitHub Actions - SonarQube](https://github.com/marketplace/actions/official-sonarqube-scan)
- [Tox Documentation](https://tox.wiki/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## Summary

✅ Two workflow options created (SonarQube and SonarCloud)
✅ Integrated with existing tox configuration
✅ Automated coverage generation and upload
✅ Quality gate checks included
✅ Works with pull requests and main branch pushes

Choose the option that best fits your needs:
- **Open source project** → Use SonarCloud (free, easy setup)
- **Private/Enterprise project** → Use SonarQube (self-hosted)

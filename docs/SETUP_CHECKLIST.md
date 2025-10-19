# SonarQube/SonarCloud Setup Checklist

Use this checklist to complete your SonarQube or SonarCloud integration.

## Pre-Setup (Already Complete ✅)

- [x] Tox configuration created (`tox.ini`)
- [x] Coverage generation tested locally (96.38% coverage)
- [x] SonarQube properties file created (`sonar-project.properties`)
- [x] GitHub workflows created (both SonarCloud and SonarQube)
- [x] Documentation written
- [x] YAML syntax validated

## Choose Your Platform

Select **ONE** of the following options:

### [ ] Option A: SonarCloud (Recommended for Open Source)
### [ ] Option B: SonarQube (For Enterprise/Self-Hosted)

---

## If Using SonarCloud

### Setup Steps

- [ ] **Step 1**: Visit [sonarcloud.io](https://sonarcloud.io)
- [ ] **Step 2**: Sign in with your GitHub account
- [ ] **Step 3**: Click "Analyze new project"
- [ ] **Step 4**: Select `python-hyperway` repository
- [ ] **Step 5**: Note your organization name (usually your GitHub username)
- [ ] **Step 6**: Generate authentication token
  - Go to: Account → Security → Generate Token
  - Name: `GitHub Actions`
  - Copy the token

### GitHub Configuration

- [ ] **Step 7**: Add token to GitHub Secrets
  - Go to: Repository → Settings → Secrets and variables → Actions
  - Click "New repository secret"
  - Name: `SONAR_TOKEN`
  - Value: `<paste your token>`
  - Click "Add secret"

### Workflow Configuration

- [ ] **Step 8**: Update `.github/workflows/sonarcloud.yml`
  ```yaml
  # Find these lines and update:
  -Dsonar.projectKey=YOUR_USERNAME_python-hyperway
  -Dsonar.organization=YOUR_USERNAME
  ```
  Replace `YOUR_USERNAME` with your GitHub username

- [ ] **Step 9**: Remove unused workflow
  ```bash
  git rm .github/workflows/sonarqube.yml
  git commit -m "Remove unused SonarQube workflow"
  ```

### Optional: Update sonar-project.properties

- [ ] **Step 10**: Add organization to `sonar-project.properties`
  ```ini
  # Uncomment and update this line:
  sonar.organization=your-github-username
  ```

### Deploy and Verify

- [ ] **Step 11**: Push to GitHub
  ```bash
  git push origin main
  ```

- [ ] **Step 12**: Check GitHub Actions
  - Go to: Repository → Actions tab
  - Wait for workflow to complete (2-3 minutes)
  - Verify green checkmark ✅

- [ ] **Step 13**: Check SonarCloud Dashboard
  - Visit: https://sonarcloud.io/organizations/YOUR_ORG/projects
  - Click on `python-hyperway`
  - Verify coverage appears (should show ~96%)

### Optional Enhancements

- [ ] **Step 14**: Add badges to README.md
  ```markdown
  [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=YOUR_USERNAME_python-hyperway&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=YOUR_USERNAME_python-hyperway)
  [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=YOUR_USERNAME_python-hyperway&metric=coverage)](https://sonarcloud.io/summary/new_code?id=YOUR_USERNAME_python-hyperway)
  ```

- [ ] **Step 15**: Configure PR decoration (automatic)
- [ ] **Step 16**: Set up quality gates (optional)

---

## If Using SonarQube

### Server Setup

- [ ] **Step 1**: Choose deployment method
  - [ ] Docker (recommended)
  - [ ] VM installation
  - [ ] Cloud instance

- [ ] **Step 2**: Deploy SonarQube
  ```bash
  # If using Docker:
  docker run -d --name sonarqube \
    -p 9000:9000 \
    -v sonarqube_data:/opt/sonarqube/data \
    -v sonarqube_logs:/opt/sonarqube/logs \
    -v sonarqube_extensions:/opt/sonarqube/extensions \
    sonarqube:latest
  ```

- [ ] **Step 3**: Access SonarQube
  - URL: http://your-server:9000
  - Default login: admin/admin
  - Change password on first login

### Project Configuration

- [ ] **Step 4**: Create new project
  - Name: `python-hyperway`
  - Project key: `python-hyperway`

- [ ] **Step 5**: Generate authentication token
  - Go to: Administration → Security → Users
  - Click tokens icon for admin user
  - Generate new token
  - Name: `GitHub Actions`
  - Copy the token (you won't see it again!)

### GitHub Configuration

- [ ] **Step 6**: Add secrets to GitHub
  - Go to: Repository → Settings → Secrets and variables → Actions
  
  - Secret 1:
    - Name: `SONAR_TOKEN`
    - Value: `<paste token from Step 5>`
  
  - Secret 2:
    - Name: `SONAR_HOST_URL`
    - Value: `https://your-sonarqube-server.com` (or `http://ip:9000`)
  
  - Secret 3 (if using organizations):
    - Name: `SONAR_ORGANIZATION`
    - Value: `<your-org-key>`

### Workflow Configuration

- [ ] **Step 7**: Verify `.github/workflows/sonarqube.yml` is correct
  - Check projectKey matches your project
  - Ensure secrets are referenced correctly

- [ ] **Step 8**: Remove unused workflow
  ```bash
  git rm .github/workflows/sonarcloud.yml
  git commit -m "Remove unused SonarCloud workflow"
  ```

### Deploy and Verify

- [ ] **Step 9**: Push to GitHub
  ```bash
  git push origin main
  ```

- [ ] **Step 10**: Check GitHub Actions
  - Go to: Repository → Actions tab
  - Wait for workflow to complete
  - Verify green checkmark ✅

- [ ] **Step 11**: Check SonarQube Dashboard
  - Visit: https://your-sonarqube-server.com
  - Go to Projects → python-hyperway
  - Verify coverage appears (should show ~96%)

### Optional Enhancements

- [ ] **Step 12**: Configure quality gates
  - SonarQube → Quality Gates
  - Set coverage thresholds

- [ ] **Step 13**: Set up webhooks for PR decoration
  - Project Settings → Webhooks
  - Add GitHub webhook

- [ ] **Step 14**: Configure email notifications
  - Administration → Configuration → Email

---

## Verification Checklist (Both Platforms)

After setup is complete, verify everything works:

### Local Testing
- [ ] Run `./generate_coverage.sh py312`
- [ ] Verify `coverage.xml` is created
- [ ] Check coverage percentage matches expectations

### GitHub Actions
- [ ] Workflow runs automatically on push
- [ ] Workflow runs on pull requests
- [ ] Coverage file is generated in workflow
- [ ] No errors in workflow logs
- [ ] Workflow completes successfully (green checkmark)

### SonarQube/SonarCloud Dashboard
- [ ] Project appears in dashboard
- [ ] Coverage percentage is displayed (~96%)
- [ ] Code smells are detected
- [ ] Quality gate status is shown
- [ ] Pull requests are decorated (if applicable)

### Pull Request Testing
- [ ] Create a test PR
- [ ] Verify workflow runs on PR
- [ ] Check that PR shows SonarQube/SonarCloud status
- [ ] Verify PR comments appear (if configured)

---

## Troubleshooting

If something doesn't work, check:

- [ ] GitHub secrets are set correctly
- [ ] Token hasn't expired
- [ ] Workflow YAML syntax is valid
- [ ] coverage.xml is being generated
- [ ] Project key matches in all files
- [ ] Network connectivity (for SonarQube)
- [ ] SonarQube server is accessible from GitHub Actions

---

## Rollback Plan

If you need to disable the integration temporarily:

### Disable Workflow
```bash
# Rename workflow to disable it
git mv .github/workflows/sonarcloud.yml .github/workflows/sonarcloud.yml.disabled
git commit -m "Temporarily disable SonarCloud"
git push
```

### Re-enable Workflow
```bash
# Rename back to enable
git mv .github/workflows/sonarcloud.yml.disabled .github/workflows/sonarcloud.yml
git commit -m "Re-enable SonarCloud"
git push
```

---

## Next Actions After Setup

Once everything is working:

- [ ] Update main README.md with badges
- [ ] Announce in project changelog
- [ ] Configure branch protection rules (optional)
- [ ] Set up quality gate notifications
- [ ] Train team on using SonarQube/SonarCloud
- [ ] Review and fix any identified code issues
- [ ] Set up periodic reviews of metrics

---

## Maintenance Schedule

Regular tasks:

### Weekly
- [ ] Review new issues in dashboard
- [ ] Check coverage trends

### Monthly  
- [ ] Review quality gate settings
- [ ] Update dependencies (tox, pytest-cov)
- [ ] Check for SonarQube/SonarCloud updates

### Quarterly
- [ ] Review and update quality standards
- [ ] Audit security hotspots
- [ ] Review technical debt trends

---

## Success Metrics

Track these over time:

- Coverage percentage (target: maintain >90%)
- Number of code smells (target: decrease)
- Technical debt ratio (target: <5%)
- Security hotspots (target: 0)
- Bug count (target: <5)
- Quality gate status (target: always passing)

---

## Help & Resources

- 📖 [GitHub Workflow Setup Guide](.github/GITHUB_WORKFLOW_SETUP.md)
- 📖 [SonarCloud vs SonarQube Comparison](.github/SONARCLOUD_VS_SONARQUBE.md)
- 📖 [Workflow Complete Guide](.github/WORKFLOW_COMPLETE.md)
- 📖 [SonarQube Setup Documentation](SONARQUBE_SETUP.md)
- 🌐 [SonarCloud Documentation](https://docs.sonarcloud.io/)
- 🌐 [SonarQube Documentation](https://docs.sonarqube.org/)

---

**Date Started**: _______________
**Completed By**: _______________
**Platform Chosen**: [ ] SonarCloud  [ ] SonarQube
**Status**: [ ] In Progress  [ ] Complete  [ ] Issues Found

**Notes**:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

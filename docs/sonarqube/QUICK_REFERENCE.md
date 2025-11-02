# Quick Reference Card

## 🚀 Quick Commands

```bash
# Generate coverage locally
./scripts/generate_coverage.sh py312

# Or with tox directly
tox -e py312

# Check coverage file
ls -lh coverage.xml

# Validate workflow YAML
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/sonarcloud.yml'))"
```

## 📋 File Locations

| File | Purpose |
|------|---------|
| `.github/workflows/sonarcloud.yml` | SonarCloud workflow |
| `.github/workflows/sonarqube.yml` | SonarQube workflow |
| `sonar-project.properties` | Sonar configuration |
| `tox.ini` | Test & coverage config |
| `coverage.xml` | Generated coverage report |
| `.github/SETUP_CHECKLIST.md` | Step-by-step checklist |

## 🔑 Required Secrets

### SonarCloud
- `SONAR_TOKEN` - From sonarcloud.io

### SonarQube  
- `SONAR_TOKEN` - From your SonarQube server
- `SONAR_HOST_URL` - Your SonarQube URL
- `SONAR_ORGANIZATION` - Your org (optional)

## 📊 Current Metrics

- Coverage: **96.38%**
- Branch: **98.2%**
- Tests: **303 passing**

## 🔗 Important Links

- [SonarCloud](https://sonarcloud.io)
- [Setup Checklist](.github/SETUP_CHECKLIST.md)
- [Complete Guide](.github/WORKFLOW_COMPLETE.md)
- [Platform Comparison](.github/SONARCLOUD_VS_SONARQUBE.md)

## ⚡ Next Steps

1. Choose: SonarCloud ⭐ or SonarQube
2. Follow: `.github/SETUP_CHECKLIST.md`
3. Deploy: Remove unused workflow, push
4. Verify: Check GitHub Actions & dashboard

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| coverage.xml not found | Run `tox -e py312` |
| Auth failed | Check `SONAR_TOKEN` secret |
| Quality gate fails | Review issues or set `continue-on-error: true` |
| Wrong Python version | Update workflow to use available version |

---

**Status**: ✅ Ready to deploy
**Choose platform**: [ ] SonarCloud [ ] SonarQube
**Time to deploy**: 5-10 minutes (SonarCloud) / 30-60 min (SonarQube)

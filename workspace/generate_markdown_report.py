#!/usr/bin/env python3
"""
Generate a markdown report from SonarCloud issues.

Usage:
    python generate_markdown_report.py
"""

import json
import requests
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
PROJECT_KEY = "Strangemother_python-hyperway"
ORGANIZATION = "strangemother"
BASE_URL = "https://sonarcloud.io/api"

# Read token from file
token_file = Path(__file__).parent / ".sonarcloud.token"
TOKEN = token_file.read_text().strip()


def fetch_issues(issue_type=None):
    """Fetch issues from SonarCloud."""
    url = f"{BASE_URL}/issues/search"
    params = {
        "componentKeys": PROJECT_KEY,
        "organization": ORGANIZATION,
        "ps": 500,
    }
    
    if issue_type:
        params["types"] = issue_type
    
    response = requests.get(url, params=params, auth=(TOKEN, ""))
    response.raise_for_status()
    
    data = response.json()
    return data.get("issues", [])


def fetch_measures():
    """Fetch quality metrics from SonarCloud."""
    url = f"{BASE_URL}/measures/component"
    params = {
        "component": PROJECT_KEY,
        "metricKeys": "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_index,reliability_rating,security_rating,sqale_rating,ncloc,complexity"
    }
    
    response = requests.get(url, params=params, auth=(TOKEN, ""))
    response.raise_for_status()
    
    data = response.json()
    measures = {}
    for measure in data.get("component", {}).get("measures", []):
        measures[measure["metric"]] = measure.get("value", "N/A")
    
    return measures


def group_issues_by_file(issues):
    """Group issues by file path."""
    grouped = defaultdict(list)
    
    for issue in issues:
        component = issue.get("component", "Unknown")
        file_path = component.replace(f"{PROJECT_KEY}:", "")
        
        grouped[file_path].append({
            "line": issue.get("line", "N/A"),
            "message": issue.get("message", "No message"),
            "rule": issue.get("rule", ""),
            "severity": issue.get("severity", ""),
            "type": issue.get("type", ""),
        })
    
    return grouped


def get_severity_badge(severity):
    """Get a badge emoji for severity."""
    badges = {
        "BLOCKER": "🔴",
        "CRITICAL": "🟠",
        "MAJOR": "🟡",
        "MINOR": "🔵",
        "INFO": "⚪",
    }
    return badges.get(severity, "⚫")


def get_rating_badge(rating):
    """Convert numeric rating to letter grade."""
    try:
        rating_num = float(rating)
        if rating_num <= 1.0:
            return "A 🟢"
        elif rating_num <= 2.0:
            return "B 🟡"
        elif rating_num <= 3.0:
            return "C 🟠"
        elif rating_num <= 4.0:
            return "D 🔴"
        else:
            return "E 🔴"
    except:
        return rating


def generate_markdown(measures, all_issues):
    """Generate markdown report."""
    
    # Separate issues by type
    code_smells = [i for i in all_issues if i.get("type") == "CODE_SMELL"]
    bugs = [i for i in all_issues if i.get("type") == "BUG"]
    vulnerabilities = [i for i in all_issues if i.get("type") == "VULNERABILITY"]
    
    # Group by file
    code_smell_files = group_issues_by_file(code_smells)
    bug_files = group_issues_by_file(bugs)
    vulnerability_files = group_issues_by_file(vulnerabilities)
    
    md = []
    
    # Header
    md.append("# SonarCloud Code Quality Report")
    md.append("")
    md.append(f"**Project:** {PROJECT_KEY}")
    md.append(f"**Organization:** {ORGANIZATION}")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    md.append("")
    md.append("---")
    md.append("")
    
    # Quality Gate Status
    md.append("## 📊 Quality Metrics")
    md.append("")
    
    # Create metrics table
    md.append("| Metric | Value | Status |")
    md.append("|--------|-------|--------|")
    
    coverage = measures.get("coverage", "0")
    md.append(f"| **Coverage** | {coverage}% | {'✅' if float(coverage) >= 80 else '⚠️'} |")
    
    bugs_count = measures.get("bugs", "0")
    md.append(f"| **Bugs** | {bugs_count} | {'✅' if int(bugs_count) == 0 else '❌'} |")
    
    vulnerabilities_count = measures.get("vulnerabilities", "0")
    md.append(f"| **Vulnerabilities** | {vulnerabilities_count} | {'✅' if int(vulnerabilities_count) == 0 else '❌'} |")
    
    code_smells_count = measures.get("code_smells", "0")
    md.append(f"| **Code Smells** | {code_smells_count} | {'✅' if int(code_smells_count) == 0 else '⚠️'} |")
    
    duplicated = measures.get("duplicated_lines_density", "0")
    md.append(f"| **Duplicated Lines** | {duplicated}% | {'✅' if float(duplicated) < 3 else '⚠️'} |")
    
    debt = measures.get("sqale_index", "0")
    debt_hours = int(debt) / 60 if debt != "N/A" else 0
    md.append(f"| **Technical Debt** | {debt_hours:.1f}h | ℹ️ |")
    
    ncloc = measures.get("ncloc", "N/A")
    md.append(f"| **Lines of Code** | {ncloc} | ℹ️ |")
    
    complexity = measures.get("complexity", "N/A")
    md.append(f"| **Complexity** | {complexity} | ℹ️ |")
    
    md.append("")
    
    # Ratings
    md.append("### Quality Ratings")
    md.append("")
    md.append("| Category | Rating |")
    md.append("|----------|--------|")
    
    reliability = measures.get("reliability_rating", "N/A")
    md.append(f"| **Reliability** | {get_rating_badge(reliability)} |")
    
    security = measures.get("security_rating", "N/A")
    md.append(f"| **Security** | {get_rating_badge(security)} |")
    
    maintainability = measures.get("sqale_rating", "N/A")
    md.append(f"| **Maintainability** | {get_rating_badge(maintainability)} |")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # Issues Summary
    md.append("## 🐛 Issues Summary")
    md.append("")
    md.append(f"- **Total Issues:** {len(all_issues)}")
    md.append(f"- **Bugs:** {len(bugs)}")
    md.append(f"- **Vulnerabilities:** {len(vulnerabilities)}")
    md.append(f"- **Code Smells:** {len(code_smells)}")
    md.append("")
    
    # Bugs Section
    if bug_files:
        md.append("---")
        md.append("")
        md.append(f"## 🐛 Bugs ({len(bugs)})")
        md.append("")
        md.append(f"**Files Affected:** {len(bug_files)}")
        md.append("")
        
        for file_path, issues in sorted(bug_files.items(), key=lambda x: len(x[1]), reverse=True):
            md.append(f"### 📁 `{file_path}`")
            md.append("")
            md.append(f"**Issues:** {len(issues)}")
            md.append("")
            
            for issue in sorted(issues, key=lambda x: x["line"] if isinstance(x["line"], int) else 0):
                severity_icon = get_severity_badge(issue["severity"])
                line = issue["line"]
                message = issue["message"]
                rule = issue["rule"]
                
                md.append(f"- {severity_icon} **Line {line}:** {message}")
                md.append(f"  - *Rule:* `{rule}`")
                md.append("")
    else:
        md.append("---")
        md.append("")
        md.append("## 🐛 Bugs")
        md.append("")
        md.append("✅ **No bugs found!**")
        md.append("")
    
    # Vulnerabilities Section
    if vulnerability_files:
        md.append("---")
        md.append("")
        md.append(f"## 🔒 Vulnerabilities ({len(vulnerabilities)})")
        md.append("")
        md.append(f"**Files Affected:** {len(vulnerability_files)}")
        md.append("")
        
        for file_path, issues in sorted(vulnerability_files.items(), key=lambda x: len(x[1]), reverse=True):
            md.append(f"### 📁 `{file_path}`")
            md.append("")
            md.append(f"**Issues:** {len(issues)}")
            md.append("")
            
            for issue in sorted(issues, key=lambda x: x["line"] if isinstance(x["line"], int) else 0):
                severity_icon = get_severity_badge(issue["severity"])
                line = issue["line"]
                message = issue["message"]
                rule = issue["rule"]
                
                md.append(f"- {severity_icon} **Line {line}:** {message}")
                md.append(f"  - *Rule:* `{rule}`")
                md.append("")
    else:
        md.append("---")
        md.append("")
        md.append("## 🔒 Vulnerabilities")
        md.append("")
        md.append("✅ **No vulnerabilities found!**")
        md.append("")
    
    # Code Smells Section (Top 10 files only)
    if code_smell_files:
        md.append("---")
        md.append("")
        md.append(f"## 🔧 Code Smells ({len(code_smells)})")
        md.append("")
        md.append(f"**Files Affected:** {len(code_smell_files)}")
        md.append("")
        md.append("### Top 10 Files with Most Code Smells")
        md.append("")
        
        sorted_files = sorted(code_smell_files.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        
        for file_path, issues in sorted_files:
            md.append(f"#### 📁 `{file_path}` ({len(issues)} issues)")
            md.append("")
            md.append("<details>")
            md.append("<summary>View Issues</summary>")
            md.append("")
            
            # Group by severity
            by_severity = defaultdict(list)
            for issue in issues:
                by_severity[issue["severity"]].append(issue)
            
            for severity in ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]:
                if severity in by_severity:
                    severity_issues = by_severity[severity]
                    severity_icon = get_severity_badge(severity)
                    md.append(f"**{severity_icon} {severity}** ({len(severity_issues)})")
                    md.append("")
                    
                    for issue in sorted(severity_issues, key=lambda x: x["line"] if isinstance(x["line"], int) else 0):
                        line = issue["line"]
                        message = issue["message"]
                        rule = issue["rule"]
                        
                        md.append(f"- Line {line}: {message}")
                        md.append(f"  - *Rule:* `{rule}`")
                    md.append("")
            
            md.append("</details>")
            md.append("")
        
        if len(code_smell_files) > 10:
            md.append(f"*...and {len(code_smell_files) - 10} more files*")
            md.append("")
    else:
        md.append("---")
        md.append("")
        md.append("## 🔧 Code Smells")
        md.append("")
        md.append("✅ **No code smells found!**")
        md.append("")
    
    # Footer
    md.append("---")
    md.append("")
    md.append("## 📚 Resources")
    md.append("")
    md.append(f"- [View on SonarCloud](https://sonarcloud.io/dashboard?id={PROJECT_KEY})")
    md.append(f"- [Project Issues](https://sonarcloud.io/project/issues?id={PROJECT_KEY})")
    md.append(f"- [Code Coverage](https://sonarcloud.io/component_measures?id={PROJECT_KEY}&metric=coverage)")
    md.append("")
    md.append("---")
    md.append("")
    md.append("*Report generated automatically from SonarCloud API*")
    
    return "\n".join(md)


def main():
    print("🔍 Fetching data from SonarCloud...")
    
    try:
        # Fetch data
        measures = fetch_measures()
        all_issues = fetch_issues()
        
        print(f"✓ Found {len(all_issues)} total issues")
        
        # Generate markdown
        print("📝 Generating markdown report...")
        markdown = generate_markdown(measures, all_issues)
        
        # Save to file
        output_path = Path(__file__).parent / "SONARCLOUD_REPORT.md"
        output_path.write_text(markdown)
        
        print(f"✅ Report saved to: {output_path}")
        print(f"   {len(markdown.splitlines())} lines written")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

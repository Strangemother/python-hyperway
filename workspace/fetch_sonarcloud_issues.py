#!/usr/bin/env python3
"""
Fetch issues and code smells from SonarCloud and create a checklist.

Usage:
    python fetch_sonarcloud_issues.py
"""

import json
import requests
from pathlib import Path
from collections import defaultdict

# Configuration
PROJECT_KEY = "Strangemother_python-hyperway"
ORGANIZATION = "strangemother"
BASE_URL = "https://sonarcloud.io/api"

# Read token from file
token_file = Path(__file__).parent / ".sonarcloud.token"
TOKEN = token_file.read_text().strip()

def fetch_issues(issue_type=None, severity=None):
    """Fetch issues from SonarCloud.
    
    Args:
        issue_type: Filter by type (CODE_SMELL, BUG, VULNERABILITY, SECURITY_HOTSPOT)
        severity: Filter by severity (INFO, MINOR, MAJOR, CRITICAL, BLOCKER)
    
    Returns:
        List of issues
    """
    url = f"{BASE_URL}/issues/search"
    params = {
        "componentKeys": PROJECT_KEY,
        "organization": ORGANIZATION,
        "ps": 500,  # page size
    }
    
    if issue_type:
        params["types"] = issue_type
    if severity:
        params["severities"] = severity
    
    response = requests.get(url, params=params, auth=(TOKEN, ""))
    response.raise_for_status()
    
    data = response.json()
    return data.get("issues", [])


def fetch_measures():
    """Fetch quality metrics from SonarCloud."""
    url = f"{BASE_URL}/measures/component"
    params = {
        "component": PROJECT_KEY,
        "metricKeys": "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_index,reliability_rating,security_rating,sqale_rating"
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
        # Extract file path from component key
        file_path = component.replace(f"{PROJECT_KEY}:", "")
        
        grouped[file_path].append({
            "line": issue.get("line", "N/A"),
            "message": issue.get("message", "No message"),
            "rule": issue.get("rule", ""),
            "severity": issue.get("severity", ""),
            "type": issue.get("type", ""),
        })
    
    return grouped


def print_summary(measures):
    """Print quality metrics summary."""
    print("=" * 80)
    print("SONARCLOUD QUALITY METRICS SUMMARY")
    print("=" * 80)
    print(f"Project: {PROJECT_KEY}")
    print(f"Organization: {ORGANIZATION}")
    print("-" * 80)
    
    metrics = {
        "code_smells": "Code Smells",
        "bugs": "Bugs",
        "vulnerabilities": "Vulnerabilities",
        "coverage": "Coverage (%)",
        "duplicated_lines_density": "Duplicated Lines (%)",
        "sqale_index": "Technical Debt (min)",
        "reliability_rating": "Reliability Rating",
        "security_rating": "Security Rating",
        "sqale_rating": "Maintainability Rating",
    }
    
    for key, label in metrics.items():
        value = measures.get(key, "N/A")
        print(f"{label:.<40} {value}")
    
    print("=" * 80)
    print()


def print_checklist(grouped_issues, issue_type_name):
    """Print a checklist of issues grouped by file."""
    if not grouped_issues:
        print(f"✓ No {issue_type_name} found!\n")
        return
    
    print(f"\n{'=' * 80}")
    print(f"{issue_type_name.upper()} CHECKLIST ({len(grouped_issues)} files)")
    print("=" * 80)
    
    total_issues = sum(len(issues) for issues in grouped_issues.values())
    print(f"Total issues: {total_issues}\n")
    
    # Sort files by number of issues (descending)
    sorted_files = sorted(grouped_issues.items(), key=lambda x: len(x[1]), reverse=True)
    
    for file_path, issues in sorted_files:
        print(f"\n📁 {file_path} ({len(issues)} issues)")
        print("-" * 80)
        
        # Sort issues by line number
        sorted_issues = sorted(issues, key=lambda x: x["line"] if isinstance(x["line"], int) else 0)
        
        for issue in sorted_issues:
            severity_icon = {
                "BLOCKER": "🔴",
                "CRITICAL": "🟠",
                "MAJOR": "🟡",
                "MINOR": "🔵",
                "INFO": "⚪",
            }.get(issue["severity"], "⚫")
            
            line = issue["line"]
            message = issue["message"]
            rule = issue["rule"]
            
            print(f"  {severity_icon} Line {line}: {message}")
            print(f"     Rule: {rule}")


def save_json_report(all_issues, measures, output_file="sonarcloud_report.json"):
    """Save full report as JSON."""
    report = {
        "project": PROJECT_KEY,
        "organization": ORGANIZATION,
        "measures": measures,
        "issues": all_issues,
        "summary": {
            "total_issues": len(all_issues),
            "code_smells": len([i for i in all_issues if i.get("type") == "CODE_SMELL"]),
            "bugs": len([i for i in all_issues if i.get("type") == "BUG"]),
            "vulnerabilities": len([i for i in all_issues if i.get("type") == "VULNERABILITY"]),
        }
    }
    
    output_path = Path(__file__).parent / output_file
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {output_path}")


def main():
    print(f"\n🔍 Fetching issues from SonarCloud...\n")
    
    try:
        # Fetch metrics
        measures = fetch_measures()
        print_summary(measures)
        
        # Fetch all issues
        all_issues = fetch_issues()
        
        # Separate by type
        code_smells = [i for i in all_issues if i.get("type") == "CODE_SMELL"]
        bugs = [i for i in all_issues if i.get("type") == "BUG"]
        vulnerabilities = [i for i in all_issues if i.get("type") == "VULNERABILITY"]
        
        # Group by file
        code_smell_files = group_issues_by_file(code_smells)
        bug_files = group_issues_by_file(bugs)
        vulnerability_files = group_issues_by_file(vulnerabilities)
        
        # Print checklists
        print_checklist(bug_files, "Bugs")
        print_checklist(vulnerability_files, "Vulnerabilities")
        print_checklist(code_smell_files, "Code Smells")
        
        # Save JSON report
        save_json_report(all_issues, measures)
        
        print("\n" + "=" * 80)
        print("✓ Analysis complete!")
        print("=" * 80)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from SonarCloud: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

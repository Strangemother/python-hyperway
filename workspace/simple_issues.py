#!/usr/bin/env python3
"""Simple SonarCloud issues checklist - just files and line numbers."""

import requests
from pathlib import Path
from collections import defaultdict

PROJECT_KEY = "Strangemother_python-hyperway"
ORGANIZATION = "strangemother"
TOKEN = Path(__file__).parent.joinpath(".sonarcloud.token").read_text().strip()

def fetch_issues():
    url = "https://sonarcloud.io/api/issues/search"
    params = {"componentKeys": PROJECT_KEY, "organization": ORGANIZATION, "ps": 500}
    response = requests.get(url, params=params, auth=(TOKEN, ""))
    return response.json().get("issues", [])

def main():
    issues = fetch_issues()
    
    # Group by file
    by_file = defaultdict(list)
    for issue in issues:
        file_path = issue.get("component", "").replace(f"{PROJECT_KEY}:", "")
        line = issue.get("line", "?")
        issue_type = issue.get("type", "")
        severity = issue.get("severity", "")[0]  # First letter
        
        by_file[file_path].append((line, severity, issue_type))
    
    # Print simple checklist
    print(f"\n📋 SonarCloud Issues Checklist ({len(issues)} total)\n")
    
    for file_path in sorted(by_file.keys()):
        lines = by_file[file_path]
        
        # Get line numbers (skip N/A)
        line_numbers = sorted([ln for ln, _, _ in lines if isinstance(ln, int)])
        
        if line_numbers:
            line_str = ", ".join(map(str, line_numbers))
            print(f"[ ] {file_path}")
            print(f"    Lines: {line_str}")
        else:
            print(f"[ ] {file_path}")
            print(f"    ({len(lines)} issues, no specific lines)")
        print()
    
    # Save to simple text file
    output = Path(__file__).parent / "issues_checklist.txt"
    with open(output, "w") as f:
        f.write(f"SonarCloud Issues Checklist - {len(issues)} total issues\n")
        f.write("=" * 60 + "\n\n")
        
        for file_path in sorted(by_file.keys()):
            lines = by_file[file_path]
            line_numbers = sorted([ln for ln, _, _ in lines if isinstance(ln, int)])
            
            f.write(f"[ ] {file_path}\n")
            if line_numbers:
                f.write(f"    Lines: {', '.join(map(str, line_numbers))}\n")
            else:
                f.write(f"    ({len(lines)} issues)\n")
            f.write("\n")
    
    print(f"✓ Saved to: {output}")

if __name__ == "__main__":
    main()

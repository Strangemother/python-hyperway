#!/usr/bin/env python3
"""Update version in sonar-project.properties from package version."""

import re
import sys
from pathlib import Path

# Get the project root (parent of scripts directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Add src to path to import hyperway
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hyperway import __version__


def get_package_version():
    """Read version from hyperway package."""
    return __version__


def update_sonar_properties(version):
    """Update version in sonar-project.properties."""
    sonar_file = PROJECT_ROOT / "sonar-project.properties"
    
    with open(sonar_file) as f:
        content = f.read()
    
    # Replace the version line
    new_content = re.sub(
        r'sonar\.projectVersion=.*',
        f'sonar.projectVersion={version}',
        content
    )
    
    with open(sonar_file, 'w') as f:
        f.write(new_content)
    
    print(f"✓ Updated sonar-project.properties to version {version}")


if __name__ == "__main__":
    version = get_package_version()
    print(f"Package version: {version}")
    update_sonar_properties(version)

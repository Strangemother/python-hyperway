#!/bin/bash
# Generate coverage report for SonarQube
# Usage: ./scripts/generate_coverage.sh [tox-environment]
#
# Examples:
#   ./scripts/generate_coverage.sh          # Run all available Python versions
#   ./scripts/generate_coverage.sh py312    # Run only Python 3.12

set -e

VENV_PYTHON="/workspaces/python-hyperway/.venv/bin/python"
TOX_BIN="/workspaces/python-hyperway/.venv/bin/tox"

# Check if we're using venv or system tox
if [ -f "$TOX_BIN" ]; then
    TOX_CMD="$TOX_BIN"
elif command -v tox &> /dev/null; then
    TOX_CMD="tox"
else
    echo "Error: tox is not installed"
    echo "Install with: pip install tox"
    exit 1
fi

echo "================================================"
echo "Generating coverage report for SonarQube"
echo "================================================"
echo ""

# Run tox with optional environment argument
if [ -n "$1" ]; then
    echo "Running tox for environment: $1"
    $TOX_CMD -e "$1"
else
    echo "Running tox for all configured environments"
    $TOX_CMD
fi

echo ""
echo "================================================"
echo "Coverage report generated successfully!"
echo "================================================"
echo ""

# Check if coverage.xml was created
if [ -f "coverage.xml" ]; then
    echo "✓ coverage.xml created: $(du -h coverage.xml | cut -f1)"
    echo ""
    echo "Next steps:"
    echo "  1. Review coverage report above"
    echo "  2. Run sonar-scanner to upload to SonarQube"
    echo "  3. Check SonarQube dashboard for results"
else
    echo "✗ Warning: coverage.xml was not created"
    exit 1
fi

#!/bin/bash
# Test runner script for chordSequence project

set -e  # Exit on error

echo "========================================="
echo "Running chordSequence Unit Tests"
echo "========================================="
echo ""

# Run tests with coverage if available
if command -v coverage &> /dev/null; then
    echo "Running with coverage..."
    coverage run --source=chordSequenceGenerator test_chordSequenceGenerator.py
    echo ""
    echo "Coverage Report:"
    coverage report -m
    echo ""
    echo "Generating HTML coverage report..."
    coverage html
    echo "✓ HTML coverage report generated in htmlcov/"
else
    echo "Running tests (install 'coverage' for coverage reports)..."
    python3 test_chordSequenceGenerator.py
fi

echo ""
echo "========================================="
echo "✓ All tests passed!"
echo "========================================="

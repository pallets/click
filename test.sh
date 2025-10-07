#!/bin/bash
set -e

# Test runner for Click issue #3084 - Optional value not optional anymore

# Try python first, fallback to python3
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "Error: Python not found"
    exit 1
fi

echo "Using: $PYTHON_CMD ($(${PYTHON_CMD} --version 2>&1))"
echo "Testing Click issue #3084: Optional value bug"
echo "================================================"

case "$1" in
  base)
    # Run existing tests that should still pass after our fix
    echo "Running existing Click option tests..."
    $PYTHON_CMD -m pytest tests/test_options.py::test_counting -v
    $PYTHON_CMD -m pytest tests/test_options.py::test_multiple_default_help -v
    $PYTHON_CMD -m pytest tests/test_options.py::test_good_defaults_for_multiple -v
    ;;
  new)
    # Run newly added tests that demonstrate and verify the fix
    echo "Running new tests for optional value bug..."
    $PYTHON_CMD -m pytest tests/test_optional_value_bug.py -v
    ;;
  all)
    # Run both base and new tests
    echo "=== Running BASE tests (verifying no regression) ==="
    $PYTHON_CMD -m pytest tests/test_options.py::test_counting -v
    $PYTHON_CMD -m pytest tests/test_options.py::test_multiple_default_help -v
    $PYTHON_CMD -m pytest tests/test_options.py::test_good_defaults_for_multiple -v
    echo ""
    echo "=== Running NEW tests (verifying the fix) ==="
    $PYTHON_CMD -m pytest tests/test_optional_value_bug.py -v
    ;;
  full)
    # Run the entire test suite to ensure nothing is broken
    echo "Running full test suite..."
    $PYTHON_CMD -m pytest tests/test_options.py -v
    ;;
  *)
    echo "Usage: ./test.sh {base|new|all|full}"
    echo "  base - Run a few existing tests to check for regressions"
    echo "  new  - Run new tests for the bug fix"
    echo "  all  - Run both base and new tests"
    echo "  full - Run the entire test_options.py test suite"
    exit 1
    ;;
esac

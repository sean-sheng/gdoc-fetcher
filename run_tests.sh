#!/bin/bash
# Comprehensive test runner for gdoc-fetch and gdoc-upload

set -e

echo "========================================="
echo "gdoc-fetch & gdoc-upload Test Suite"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if running unit or integration tests
TEST_TYPE=${1:-"unit"}

case $TEST_TYPE in
    unit)
        print_step "Running Unit Tests (Fast)"
        echo "These tests run without authentication and don't hit Google APIs"
        echo ""
        pytest tests/unit/ -v
        print_success "Unit tests passed!"
        echo ""
        echo "Run 'bash run_tests.sh integration' to run integration tests"
        ;;

    integration)
        print_step "Running Integration Tests (Requires Auth)"
        echo "These tests require authentication and create real Google Docs"
        echo ""

        # Check authentication
        if ! gcloud auth print-access-token &> /dev/null; then
            print_warning "Authentication not available!"
            echo "Please run: gcloud auth login --enable-gdrive-access"
            exit 1
        fi

        print_success "Authentication verified"
        echo ""

        pytest tests/integration/ -v -m integration

        print_success "Integration tests passed!"
        print_warning "Note: Created test documents may need manual cleanup from Google Drive"
        ;;

    all)
        print_step "Running All Tests (Unit + Integration)"
        echo ""

        # Run unit tests first
        print_step "1/2: Unit Tests"
        pytest tests/unit/ -v
        print_success "Unit tests passed!"
        echo ""

        # Run integration tests
        print_step "2/2: Integration Tests"

        if ! gcloud auth print-access-token &> /dev/null; then
            print_warning "Skipping integration tests (authentication not available)"
            exit 0
        fi

        pytest tests/integration/ -v -m integration
        print_success "Integration tests passed!"
        ;;

    *)
        echo "Usage: bash run_tests.sh [unit|integration|all]"
        echo ""
        echo "Options:"
        echo "  unit         - Run unit tests only (default, fast)"
        echo "  integration  - Run integration tests only (requires auth)"
        echo "  all          - Run both unit and integration tests"
        echo ""
        echo "Examples:"
        echo "  bash run_tests.sh"
        echo "  bash run_tests.sh unit"
        echo "  bash run_tests.sh integration"
        echo "  bash run_tests.sh all"
        exit 1
        ;;
esac

echo ""
echo "========================================="
print_success "All tests completed successfully!"
echo "========================================="

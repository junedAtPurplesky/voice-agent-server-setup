#!/usr/bin/env bash
# ==========================================================
# Smart Test Runner
# Automatically handles venv setup and runs tests
# ==========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.test_venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

setup_venv_if_needed() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}📦 Setting up test environment...${NC}"
        python3 -m venv "$VENV_DIR"
        
        echo -e "${YELLOW}⬆️  Installing dependencies...${NC}"
        "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel -q
        "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q
        
        echo -e "${GREEN}✓ Test environment ready${NC}"
    fi
}

# Ensure venv exists
setup_venv_if_needed

# Use venv Python
PYTHON="$VENV_DIR/bin/python3"

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo -e "${BLUE}Smart Test Runner${NC}"
    echo ""
    echo "Usage: $0 <test_script> [options]"
    echo ""
    echo "Examples:"
    echo "  $0 test_client.py"
    echo "  $0 test_stream.py --verbose"
    echo "  $0 load_test.py --requests 100 --concurrent 10"
    echo "  $0 example_usage.py"
    echo ""
    echo "Or run directly:"
    echo "  $0 quick          # Run test_client.py with defaults"
    echo "  $0 stream         # Run test_stream.py"
    echo "  $0 load           # Run load_test.py with defaults"
    echo "  $0 examples       # Run example_usage.py"
    exit 0
fi

# Handle shortcuts
case "$1" in
    quick|client)
        shift
        echo -e "${BLUE}Running comprehensive tests...${NC}"
        exec "$PYTHON" "$SCRIPT_DIR/test_client.py" "$@"
        ;;
    stream)
        shift
        echo -e "${BLUE}Running streaming tests...${NC}"
        exec "$PYTHON" "$SCRIPT_DIR/test_stream.py" "$@"
        ;;
    load)
        shift
        echo -e "${BLUE}Running load tests...${NC}"
        exec "$PYTHON" "$SCRIPT_DIR/load_test.py" "$@"
        ;;
    examples)
        shift
        echo -e "${BLUE}Running examples...${NC}"
        exec "$PYTHON" "$SCRIPT_DIR/example_usage.py" "$@"
        ;;
    *)
        # Run the specified script
        TEST_SCRIPT="$1"
        shift
        
        # Add .py if not present
        if [[ ! "$TEST_SCRIPT" =~ \.py$ ]]; then
            TEST_SCRIPT="${TEST_SCRIPT}.py"
        fi
        
        # Check if script exists
        if [ ! -f "$SCRIPT_DIR/$TEST_SCRIPT" ]; then
            echo "Error: Test script not found: $TEST_SCRIPT"
            exit 1
        fi
        
        echo -e "${BLUE}Running $TEST_SCRIPT...${NC}"
        exec "$PYTHON" "$SCRIPT_DIR/$TEST_SCRIPT" "$@"
        ;;
esac


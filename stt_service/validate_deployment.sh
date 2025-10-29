#!/bin/bash
# Validate deployment structure and configuration

# Don't exit on error - we want to collect all validation results
set +e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================"
echo "STT Service Deployment Validation"
echo "============================================"
echo ""

# Track validation status
PASSED=0
FAILED=0

validate() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $1${NC}"
        ((FAILED++))
    fi
}

# Check directory structure
echo "🔍 Checking directory structure..."
[ -d "app" ]; validate "app directory exists"
mkdir -p logs 2>/dev/null; [ -d "logs" ]; validate "logs directory"
mkdir -p tmp 2>/dev/null; [ -d "tmp" ]; validate "tmp directory"

echo ""
echo "🔍 Checking Python files..."
for file in app/__init__.py app/main.py app/config.py app/models.py app/auth.py app/utils.py app/vad.py app/http_endpoints.py app/websocket_endpoints.py; do
    [ -f "$file" ] && validate "$file" || validate "$file missing"
done

echo ""
echo "🔍 Checking configuration files..."
[ -f "requirements.txt" ] && validate "requirements.txt" || validate "requirements.txt missing"
[ -f ".env.example" ] && validate ".env.example" || validate ".env.example missing"

echo ""
echo "🔍 Checking shell scripts..."
for script in setup.sh start.sh stop.sh restart.sh status.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            validate "$script (executable)"
        else
            echo -e "${YELLOW}⚠️  $script not executable${NC}"
            chmod +x "$script" 2>/dev/null && echo -e "${GREEN}  Fixed!${NC}"
        fi
    else
        validate "$script missing"
    fi
done

echo ""
echo "🔍 Checking documentation..."
[ -f "RUNPOD_DEPLOYMENT.md" ] && validate "RUNPOD_DEPLOYMENT.md" || validate "RUNPOD_DEPLOYMENT.md missing"

echo ""
echo "🔍 Syntax checking Python files..."
python3 -m py_compile app/*.py 2>/dev/null && validate "Python syntax" || validate "Python syntax errors"

echo ""
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" && validate "Python 3.8+" || validate "Python 3.8+ required"

echo ""
echo "🔍 Checking required commands..."
for cmd in python3 pip3; do
    command -v $cmd > /dev/null 2>&1 && validate "$cmd command" || validate "$cmd command missing"
done

echo ""
echo "🔍 Checking optional commands..."
for cmd in curl git ffmpeg; do
    if command -v $cmd > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $cmd (optional)${NC}"
    else
        echo -e "${YELLOW}⚠️  $cmd not found (optional but recommended)${NC}"
    fi
done

echo ""
echo "============================================"
echo "Validation Results"
echo "============================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All validations passed!${NC}"
    echo "Ready for deployment. Next steps:"
    echo "  1. Run ./setup.sh to install dependencies"
    echo "  2. Configure .env file"
    echo "  3. Run ./start.sh to start the service"
    exit 0
else
    echo -e "${RED}❌ Some validations failed${NC}"
    echo "Please fix the issues above before deployment"
    exit 1
fi


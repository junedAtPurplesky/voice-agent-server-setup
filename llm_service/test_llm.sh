#!/usr/bin/env bash
# ==========================================================
# Quick LLM Service Testing Script
# ==========================================================
# Simple script for quick testing without Python dependencies

set -e

# Configuration
LLM_URL="${LLM_URL:-http://127.0.0.1:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# -------------------------------
# Helper Functions
# -------------------------------

print_header() {
    echo -e "${BLUE}$1${NC}"
    echo "======================================"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# -------------------------------
# Test Functions
# -------------------------------

test_health() {
    print_header "Testing Health Endpoint"
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$LLM_URL/v1/models" 2>&1)
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')
    
    if [ "$http_code" = "200" ]; then
        print_success "Service is healthy"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 0
    else
        print_error "Health check failed (HTTP $http_code)"
        return 1
    fi
}

test_completion() {
    print_header "Testing Completion Endpoint"
    
    local prompt="${1:-What is AI?}"
    local max_tokens="${2:-50}"
    
    print_info "Prompt: $prompt"
    print_info "Max tokens: $max_tokens"
    
    start_time=$(date +%s.%N)
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST "$LLM_URL/v1/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"default\",
            \"prompt\": \"$prompt\",
            \"max_tokens\": $max_tokens,
            \"temperature\": 0.7
        }" 2>&1)
    
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')
    
    if [ "$http_code" = "200" ]; then
        print_success "Completion successful (${elapsed}s)"
        
        # Extract and display response
        text=$(echo "$body" | jq -r '.choices[0].text' 2>/dev/null)
        if [ -n "$text" ] && [ "$text" != "null" ]; then
            echo ""
            echo "Response:"
            echo "─────────────────────────────────────"
            echo "$text"
            echo "─────────────────────────────────────"
        fi
        
        # Show usage stats if available
        usage=$(echo "$body" | jq -r '.usage' 2>/dev/null)
        if [ -n "$usage" ] && [ "$usage" != "null" ]; then
            echo ""
            echo "Usage: $usage"
        fi
        
        return 0
    else
        print_error "Completion failed (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

test_streaming() {
    print_header "Testing Streaming Endpoint"
    
    local prompt="${1:-Tell me a short story.}"
    local max_tokens="${2:-100}"
    
    print_info "Prompt: $prompt"
    print_info "Max tokens: $max_tokens"
    echo ""
    echo "Streaming response:"
    echo "─────────────────────────────────────"
    
    # Use curl with --no-buffer for streaming
    curl -s --no-buffer \
        -X POST "$LLM_URL/v1/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"default\",
            \"prompt\": \"$prompt\",
            \"max_tokens\": $max_tokens,
            \"temperature\": 0.7,
            \"stream\": true
        }" | while read -r line; do
            if [[ $line == data:* ]]; then
                data="${line#data: }"
                if [ "$data" != "[DONE]" ]; then
                    # Extract text from JSON (simple grep approach)
                    text=$(echo "$data" | jq -r '.choices[0].text' 2>/dev/null)
                    if [ -n "$text" ] && [ "$text" != "null" ]; then
                        echo -n "$text"
                    fi
                fi
            fi
        done
    
    echo ""
    echo "─────────────────────────────────────"
    print_success "Streaming test completed"
}

test_chat() {
    print_header "Testing Chat Completion Endpoint"
    
    local message="${1:-Explain machine learning briefly.}"
    local max_tokens="${2:-100}"
    
    print_info "Message: $message"
    print_info "Max tokens: $max_tokens"
    
    start_time=$(date +%s.%N)
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST "$LLM_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"default\",
            \"messages\": [
                {\"role\": \"user\", \"content\": \"$message\"}
            ],
            \"max_tokens\": $max_tokens,
            \"temperature\": 0.7
        }" 2>&1)
    
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')
    
    if [ "$http_code" = "200" ]; then
        print_success "Chat completion successful (${elapsed}s)"
        
        # Extract and display response
        content=$(echo "$body" | jq -r '.choices[0].message.content' 2>/dev/null)
        if [ -n "$content" ] && [ "$content" != "null" ]; then
            echo ""
            echo "Response:"
            echo "─────────────────────────────────────"
            echo "$content"
            echo "─────────────────────────────────────"
        fi
        
        # Show usage stats
        usage=$(echo "$body" | jq -r '.usage' 2>/dev/null)
        if [ -n "$usage" ] && [ "$usage" != "null" ]; then
            echo ""
            echo "Usage: $usage"
        fi
        
        return 0
    else
        print_error "Chat completion failed (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

run_quick_test() {
    print_header "Running Quick Test Suite"
    echo ""
    
    local passed=0
    local failed=0
    
    # Test 1: Health
    if test_health; then
        ((passed++))
    else
        ((failed++))
        echo ""
        print_error "Health check failed. Is the service running?"
        return 1
    fi
    
    echo ""
    
    # Test 2: Basic completion
    if test_completion "What is 2+2?" 20; then
        ((passed++))
    else
        ((failed++))
    fi
    
    echo ""
    
    # Test 3: Chat
    if test_chat "Say hello!" 20; then
        ((passed++))
    else
        ((failed++))
    fi
    
    echo ""
    print_header "Test Summary"
    echo "Passed: $passed"
    echo "Failed: $failed"
    
    if [ $failed -eq 0 ]; then
        print_success "All tests passed!"
        return 0
    else
        print_error "Some tests failed"
        return 1
    fi
}

run_load_test() {
    print_header "Running Load Test (Python Required)"
    
    if [ ! -f "$SCRIPT_DIR/load_test.py" ]; then
        print_error "load_test.py not found"
        return 1
    fi
    
    python3 "$SCRIPT_DIR/load_test.py" --url "$LLM_URL" "$@"
}

show_usage() {
    cat << EOF
LLM Service Test Script

Usage: $0 <command> [options]

Commands:
    health              Test health endpoint
    completion          Test completion endpoint
    chat                Test chat completion endpoint
    stream              Test streaming endpoint
    quick               Run quick test suite
    load                Run load test (requires Python)

Options:
    --url URL           LLM service URL (default: http://127.0.0.1:8000)
    --prompt TEXT       Custom prompt for completion test
    --message TEXT      Custom message for chat test
    --max-tokens N      Maximum tokens to generate

Examples:
    # Quick test
    $0 quick

    # Test with custom URL
    $0 --url http://192.168.1.100:8000 health

    # Test completion with custom prompt
    $0 completion --prompt "What is the meaning of life?" --max-tokens 100

    # Test streaming
    $0 stream --prompt "Write a poem"

    # Run load test
    $0 load --requests 100 --concurrent 10

Environment Variables:
    LLM_URL             Base URL of LLM service (default: http://127.0.0.1:8000)

EOF
}

# -------------------------------
# Command Dispatcher
# -------------------------------

# Parse options
COMMAND=""
PROMPT=""
MESSAGE=""
MAX_TOKENS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            LLM_URL="$2"
            shift 2
            ;;
        --prompt)
            PROMPT="$2"
            shift 2
            ;;
        --message)
            MESSAGE="$2"
            shift 2
            ;;
        --max-tokens)
            MAX_TOKENS="$2"
            shift 2
            ;;
        health|completion|chat|stream|quick|load|help)
            COMMAND="$1"
            shift
            break
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Execute command
case "$COMMAND" in
    health)
        test_health
        ;;
    completion)
        test_completion "${PROMPT:-What is AI?}" "${MAX_TOKENS:-50}"
        ;;
    chat)
        test_chat "${MESSAGE:-Hello!}" "${MAX_TOKENS:-100}"
        ;;
    stream)
        test_streaming "${PROMPT:-Tell me a story.}" "${MAX_TOKENS:-100}"
        ;;
    quick)
        run_quick_test
        ;;
    load)
        run_load_test "$@"
        ;;
    help|"")
        show_usage
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac


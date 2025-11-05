# Automatic Virtual Environment Setup

All Python test scripts automatically handle their own dependencies with zero manual setup required!

## How It Works

### First Run
When you run any test script for the first time:

```bash
python3 test_client.py
```

**What happens automatically:**
1. 🔍 Script detects that `httpx` (dependency) is not available
2. 📦 Creates `.test_venv` directory in the same folder
3. ⬆️ Installs pip and required packages from `requirements.txt`
4. 🔄 Restarts itself using the new virtual environment
5. ✅ Runs your test

**Output you'll see:**
```
📦 Setting up test environment...
⬆️  Installing dependencies...
✅ Test environment ready

🏥 Testing Service Health...
✅ Service is healthy (Response time: 0.123s)
...
```

### Subsequent Runs
All future runs are instant because they detect and use the existing environment:

```bash
python3 test_client.py
```

**What happens:**
1. 🔍 Script detects `httpx` is available (from `.test_venv`)
2. ✅ Immediately runs your test (no setup)

## Features

### ✅ Zero Configuration
- No need to run `pip install`
- No need to create venv manually
- No need to activate anything
- Just run the script!

### ✅ Isolated Environment
- Uses `.test_venv` separate from LLM service venv
- Doesn't interfere with system Python packages
- Clean, reproducible environment

### ✅ Smart Detection
- Checks if dependencies are already available
- Only creates venv if needed
- Works whether you run from system Python or existing venv

### ✅ Works Everywhere
Every test script has auto-setup:
- `test_client.py` ✓
- `test_stream.py` ✓
- `load_test.py` ✓
- `example_usage.py` ✓

## Usage Examples

### Just Run Any Test
```bash
# First time - auto setup
python3 test_client.py
# 📦 Setting up test environment...
# ⬆️  Installing dependencies...
# ✅ Test environment ready
# [test runs]

# Second time - instant
python3 test_client.py
# [test runs immediately]
```

### With Arguments
```bash
# First run with custom parameters
python3 load_test.py --requests 100 --concurrent 10
# [auto setup happens]
# [test runs]

# Subsequent runs
python3 load_test.py --requests 500 --concurrent 25
# [runs immediately]
```

### Different Scripts
```bash
# Each script shares the same .test_venv
python3 test_client.py      # Creates venv if needed
python3 test_stream.py      # Uses existing venv
python3 load_test.py        # Uses existing venv
python3 example_usage.py    # Uses existing venv
```

## Alternative: Smart Runner

Use `run_test.sh` for shortcuts and explicit venv management:

```bash
# Ensures venv exists and runs test
./run_test.sh quick                    # test_client.py
./run_test.sh stream                   # test_stream.py
./run_test.sh load                     # load_test.py
./run_test.sh examples                 # example_usage.py

# With full script names
./run_test.sh test_client.py --requests 50
./run_test.sh load_test.py --requests 1000 --concurrent 50
```

## Manual Setup (Optional)

If you prefer to setup manually:

```bash
# Create venv manually
python3 -m venv .test_venv
source .test_venv/bin/activate
pip install -r requirements.txt

# Then run tests normally
python3 test_client.py
```

The auto-setup will detect the activated venv and use it.

## Troubleshooting

### Clear and Recreate Environment
```bash
# Remove the venv
rm -rf .test_venv

# Next run will recreate it
python3 test_client.py
```

### Use System Python Instead
If you don't want auto-setup and have system-wide packages:

```bash
# Install dependencies globally
pip install httpx

# Run tests - auto-setup will detect httpx and skip venv creation
python3 test_client.py
```

### Check What Python Is Being Used
```bash
# After auto-setup activates venv
./run_test.sh quick
# Shows: Python: /path/to/.test_venv/bin/python3
```

## Technical Details

### Implementation
Each test script includes this at the top:

```python
def ensure_venv():
    """Ensure we're running in a virtual environment with dependencies"""
    script_dir = Path(__file__).parent
    venv_dir = script_dir / ".test_venv"
    
    # If dependencies available, continue
    try:
        import httpx
        return
    except ImportError:
        pass
    
    # Create venv if needed
    if not venv_dir.exists():
        print("📦 Setting up test environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
        
        # Install dependencies
        pip_path = venv_dir / "bin" / "pip"
        subprocess.run([str(pip_path), "install", "-q", "-r", "requirements.txt"])
    
    # Restart script in venv
    python_path = venv_dir / "bin" / "python3"
    subprocess.run([str(python_path), __file__] + sys.argv[1:])
    sys.exit(0)

ensure_venv()  # Called before any imports
```

### Why It Works
1. **Early detection**: Runs before importing test dependencies
2. **Self-restart**: Script restarts itself in the venv
3. **Transparent**: User doesn't see the restart, just the setup message
4. **Idempotent**: Safe to run multiple times

## Environment Location

### Directory Structure
```
llm_service/
├── test_client.py
├── test_stream.py
├── load_test.py
├── requirements.txt
└── .test_venv/          # Auto-created
    ├── bin/
    │   ├── python3
    │   └── pip
    ├── lib/
    │   └── python3.x/
    │       └── site-packages/
    │           ├── httpx/
    │           └── ...
    └── pyvenv.cfg
```

### .gitignore
The `.test_venv` directory is automatically ignored:
```gitignore
# Test virtual environment
.test_venv/
```

## Benefits

### For Users
- 🚀 **Instant productivity**: No setup time
- 💯 **Zero errors**: Can't forget to install dependencies
- 🔧 **No maintenance**: Environment is self-managing

### For Teams
- 📝 **Simpler docs**: No installation instructions needed
- 🤝 **Onboarding**: New team members can test immediately
- ✅ **Consistency**: Everyone uses same environment

### For CI/CD
- ⚡ **Fast**: Setup only once, cached for subsequent runs
- 🔒 **Isolated**: Each test run is reproducible
- 📦 **Portable**: Works on any system with Python 3.7+

## Comparison

### Before (Manual Setup)
```bash
# User has to remember these steps
python3 -m venv .test_venv
source .test_venv/bin/activate
pip install -r requirements.txt
python3 test_client.py
```

### After (Auto Setup)
```bash
# Just run it!
python3 test_client.py
```

**80% less work, 100% more reliable!** 🎉

## Summary

The automatic virtual environment setup makes testing effortless:

✅ **Zero manual setup** - Just run the script  
✅ **Smart detection** - Uses existing environment if available  
✅ **Isolated dependencies** - Doesn't affect system packages  
✅ **Fast subsequent runs** - Only setup once  
✅ **Works everywhere** - All test scripts included  
✅ **Optional manual control** - Can override if needed  

**Bottom line:** You can go from zero to testing in a single command! 🚀


# Changelog - CosyVoice TTS Service

## Latest Updates

### 🔧 Smart Conda Detection (Latest Fix)

**Date:** November 2024

**What's Fixed:**
- ✅ **Smart Existing Installation Detection** - Handles existing Miniconda installations
- ✅ **Automatic TOS Acceptance** - Fixes "Terms of Service have not been accepted" error
- ✅ **PATH Management** - Automatically adds existing Conda to PATH if needed
- No manual interaction required during setup

**Technical Details:**
The script now:
1. Checks if conda command is available in PATH
2. If not, checks if Miniconda is already installed at `$HOME/miniconda3`
3. If existing installation found:
   - Adds it to PATH for the current session
   - Re-initializes conda for bash
   - Sources conda setup scripts
4. If no installation found, proceeds with fresh install
5. Configures Conda settings for non-interactive use
6. Detects if `conda tos` command is available
7. Automatically accepts TOS for `pkgs/main` and `pkgs/r` channels

**Fixed Issues:**
- "File or directory already exists: '/root/miniconda3'" error
- "CondaToSNonInteractiveError: Terms of Service have not been accepted" error
- Conda command not available in PATH after installation

**Migration:**
Just re-run the setup script:
```bash
./setup.sh
```

The script will automatically detect and use your existing Conda installation!

---

### ✨ Auto-Install Conda

**Date:** November 2024

**What's New:**
- 🎉 **Automatic Conda Installation** - No manual Conda setup required!
- The `setup.sh` script now automatically detects and installs Miniconda if not present
- Supports multiple platforms automatically

**Supported Platforms:**
- ✅ Linux x86_64 (Intel/AMD processors)
- ✅ Linux aarch64 (ARM64 processors)
- ✅ macOS x86_64 (Intel Macs)
- ✅ macOS arm64 (Apple Silicon M1/M2/M3 Macs)

**How It Works:**
```bash
# Just run setup - Conda installs automatically if needed!
./setup.sh
```

The script will:
1. Check if Conda is installed
2. If not found:
   - Detect your OS and architecture automatically
   - Download the appropriate Miniconda installer
   - Install Miniconda to `$HOME/miniconda3`
   - Initialize Conda for your shell
3. Continue with the rest of the setup

**Benefits:**
- 🚀 One-command setup - truly automated
- 🌐 Cross-platform support
- 📦 No manual downloads needed
- ✅ Works on fresh servers out of the box

**Migration:**
If you previously installed Conda manually, no changes needed! The script will detect your existing installation and use it.

---

## Previous Updates

### 🔄 Complete Refactor - Official CosyVoice Implementation

**Date:** November 2024

**Major Changes:**
- Complete rewrite to follow official CosyVoice installation guide
- Switched from Python venv to Conda (official requirement)
- Fixed Python version to 3.8 (official requirement)
- Official CosyVoice repository clone with submodules
- Official API usage for model loading and synthesis
- Proper import path configuration

**What Was Fixed:**
- ✅ All configuration issues
- ✅ All linking problems
- ✅ Import errors
- ✅ Model loading failures
- ✅ Dependency conflicts

**Files Changed:**
- `setup.sh` - Complete rewrite for Conda
- `synthesis.py` - Official API usage
- `config.py` - Proper model paths
- `start_service.sh` - Conda activation
- `requirements.txt` - Service dependencies only

**New Documentation:**
- `START_HERE.md` - Quick start guide
- `INSTALLATION.md` - Detailed installation
- `SERVER_SETUP_GUIDE.md` - Server deployment
- `SETUP_SUMMARY.md` - Technical changes
- `REFACTOR_SUMMARY.md` - Complete refactor docs
- `QUICK_REFERENCE.md` - Command reference

---

## Before vs After

### Installation Process

**Before (Manual):**
```bash
# 1. Install Conda manually
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 2. Restart shell
exec bash

# 3. Run setup
./setup.sh

# 4. Start service
./start_service.sh
```

**After (Automated):**
```bash
# 1. Run setup (Conda auto-installs if needed)
./setup.sh

# 2. Start service
./start_service.sh
```

### Key Improvements

| Feature | Before | After |
|---------|--------|-------|
| **Conda Installation** | ❌ Manual | ✅ Automatic |
| **Platform Detection** | ❌ Manual selection | ✅ Auto-detected |
| **Environment Setup** | ❌ Python venv | ✅ Conda |
| **CosyVoice Install** | ❌ Custom | ✅ Official |
| **Dependencies** | ❌ Custom list | ✅ Official requirements.txt |
| **Model Loading** | ❌ Custom code | ✅ Official API |
| **Import Paths** | ❌ PYTHONPATH hacks | ✅ sitecustomize.py |

---

## Upgrade Guide

### From Old Setup to New

If you have the old setup:

```bash
# 1. Remove old environment
rm -rf venv/

# 2. Run new setup (handles everything)
./setup.sh

# Done! Conda installs automatically if needed
```

### From Previous New Setup (Before Auto-Install)

If you already have the refactored version but without auto-install:

```bash
# No changes needed!
# Your existing Conda installation will be detected and used
# Next setup will just work automatically
```

---

## Technical Details

### Auto-Install Implementation

The setup script now includes:

1. **OS Detection**
   ```bash
   OS_TYPE=$(uname -s)  # Linux or Darwin
   ARCH_TYPE=$(uname -m)  # x86_64, aarch64, arm64
   ```

2. **Platform-Specific URLs**
   - Linux x86_64: `Miniconda3-latest-Linux-x86_64.sh`
   - Linux aarch64: `Miniconda3-latest-Linux-aarch64.sh`
   - macOS x86_64: `Miniconda3-latest-MacOSX-x86_64.sh`
   - macOS arm64: `Miniconda3-latest-MacOSX-arm64.sh`

3. **Automatic Download**
   - Uses `wget` or `curl` (whichever is available)
   - Shows progress during download
   - Validates download success

4. **Silent Installation**
   ```bash
   bash installer.sh -b -p $HOME/miniconda3
   ```
   - `-b`: Batch mode (no prompts)
   - `-p`: Install path

5. **Shell Integration**
   ```bash
   $HOME/miniconda3/bin/conda init bash
   ```
   - Initializes Conda for future shell sessions
   - Adds to PATH for current script

---

## Compatibility

### Operating Systems

✅ **Supported:**
- Ubuntu 20.04+
- Debian 10+
- CentOS 7+
- macOS 10.15+ (Catalina and later)
- Other Linux distributions with bash

⚠️ **Not Tested:**
- Windows (use WSL2)
- Very old Linux distributions

### Architectures

✅ **Fully Supported:**
- x86_64 (Intel/AMD 64-bit)
- aarch64 / arm64 (ARM 64-bit)

❌ **Not Supported:**
- 32-bit systems
- Other architectures

### Shell Compatibility

✅ **Tested:**
- bash
- zsh (via conda init bash compatibility)

⚠️ **Limited:**
- fish, csh (may need manual conda init)

---

## Future Plans

### Planned Features
- [ ] Docker container support
- [ ] One-click cloud deployment scripts
- [ ] Web UI for configuration
- [ ] Model management interface
- [ ] Multi-model support

### Potential Improvements
- [ ] Progress bar for model download
- [ ] Disk space check before installation
- [ ] Network connectivity check
- [ ] Automatic GPU detection and optimization
- [ ] Health monitoring dashboard

---

## Support

### Getting Help

If you encounter issues:

1. **Check logs:** `cat tts_service.log`
2. **Read docs:** See `START_HERE.md`
3. **Troubleshooting:** See `SERVER_SETUP_GUIDE.md`
4. **GitHub Issues:** Report bugs on GitHub

### Common Issues

**Conda installation fails:**
- Check internet connection
- Ensure wget or curl is installed
- Check disk space (need ~500MB)

**Setup script fails:**
- Check system requirements
- Read error messages in terminal
- Check logs for details

---

## Acknowledgments

- **FunAudioLLM Team** - For the excellent CosyVoice model
- **Conda Team** - For the package management system
- **Community** - For feedback and testing

---

**Last Updated:** November 2024
**Current Version:** 2.0 (Auto-install Conda)
**Previous Version:** 1.0 (Manual Conda)


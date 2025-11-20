# LLM Service Manager

A flexible script to manage VLLM model deployments with configurable settings.

## Quick Start

1. **Install dependencies:**
   ```bash
   ./llm_manager.sh install
   ```

2. **Setup Python environment:**
   ```bash
   ./llm_manager.sh setup
   ```

3. **Configure your model:**
   Edit `llm_config.sh` to set your desired model and parameters.

4. **Start the service:**
   ```bash
   ./llm_manager.sh start
   ```

## Configuration

All configuration is done through `llm_config.sh`. This file contains:
- **Active settings** at the top (currently in use)
- **All supported flags** below as comments (reference/documentation)

### Changing Models

To deploy a different model, simply edit `llm_config.sh`:

```bash
# Example: Switch to Llama 3 8B
MODEL_NAME="meta-llama/Meta-Llama-3-8B-Instruct"
QUANTIZATION=""
GPU_MEMORY_UTILIZATION="0.9"
MAX_NUM_SEQS="256"
```

### Example Configurations

The `llm_config.sh` file includes commented examples at the bottom for popular models:
- Llama 3 8B
- Mistral 7B
- Phi-3 Mini
- Qwen (default)

### Enabling Additional Flags

1. Find the flag you want in the commented section of `llm_config.sh`
2. Uncomment it and set your desired value
3. Restart the service

```bash
# Example: Enable trust remote code
TRUST_REMOTE_CODE="--trust-remote-code"
```

## Commands

| Command | Description |
|---------|-------------|
| `./llm_manager.sh install` | Install system dependencies |
| `./llm_manager.sh setup` | Setup Python virtual environment |
| `./llm_manager.sh start` | Start the LLM service |
| `./llm_manager.sh stop` | Stop the LLM service |
| `./llm_manager.sh restart` | Restart the LLM service |
| `./llm_manager.sh status` | Check service status |
| `./llm_manager.sh logs` | View service logs (tail -f) |
| `./llm_manager.sh test` | Run basic performance test |

## Testing

The LLM service includes comprehensive testing tools with **automatic environment setup**. See [TESTING.md](TESTING.md) for detailed documentation.

### Quick Testing

**Shell-based tests (no dependencies):**
```bash
# Run quick test suite
./test_llm.sh quick

# Test individual endpoints
./test_llm.sh health
./test_llm.sh completion
./test_llm.sh stream
```

**Python-based tests (auto-setup, recommended):**
```bash
# No installation needed - automatically creates venv and installs dependencies!
python3 test_client.py              # Comprehensive tests
python3 test_stream.py              # Streaming tests
python3 load_test.py --requests 100 # Load tests

# Or use the smart runner with shortcuts
./run_test.sh quick                 # Run comprehensive tests
./run_test.sh stream --verbose      # Streaming with output
./run_test.sh load --requests 500   # Load test
```

**First run:** Automatically sets up environment (~30 seconds)  
**Subsequent runs:** Uses existing environment (instant)

### Test Clients

| Client | Purpose | Key Features |
|--------|---------|--------------|
| `test_llm.sh` | Quick shell tests | No dependencies, fast health checks, resource monitoring |
| `test_client.py` | Comprehensive testing | All endpoints, metrics, concurrency, resource tracking |
| `test_stream.py` | Streaming focus | Time to first token, chunk analysis, resource monitoring |
| `load_test.py` | Load & performance | High volume, latency metrics (P95, P99), resource tracking |

### 📊 Resource Monitoring

All test clients now display system resources:
- **🎮 GPU/VRAM**: Memory usage, utilization, temperature
- **💾 RAM**: System memory usage and available
- **⚙️ CPU**: Utilization and core count

See [RESOURCE_MONITORING.md](RESOURCE_MONITORING.md) for details.

**Example outputs:**
```bash
# Quick performance check
python3 test_client.py --requests 20 --concurrent 5

# Streaming performance
python3 test_stream.py --num-tests 10 --verbose

# Load test with ramp-up
python3 load_test.py --requests 500 --concurrent 25 --ramp-up 10
```

## Multiple Model Deployments

To run multiple models simultaneously:

1. Create separate config files:
   ```bash
   cp llm_config.sh qwen_config.sh
   cp llm_config.sh llama_config.sh
   ```

2. Edit each config with different models and **ports**

3. Modify the script to use different config files or create wrapper scripts

## Tips

- **Disabling flags**: Set to empty string `""` or comment out
- **Adding custom flags**: Use the `EXTRA_FLAGS` variable
- **Logs location**: `~/llm_service/llm_service.log`
- **Check what's running**: Use `status` command

## Troubleshooting

**Service won't start:**
- Check logs: `./llm_manager.sh logs`
- Verify GPU availability: `nvidia-smi`
- Ensure port is not in use: `lsof -i :8000`

**Out of memory:**
- Reduce `GPU_MEMORY_UTILIZATION` (e.g., from 0.9 to 0.7)
- Reduce `MAX_NUM_SEQS`
- Enable quantization (AWQ, GPTQ)

**Model not found:**
- Check model name is correct
- Verify HuggingFace access (for gated models)
- Set `DOWNLOAD_DIR` if needed


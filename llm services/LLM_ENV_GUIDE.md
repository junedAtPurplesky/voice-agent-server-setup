# LLM Docker Image Environment Variables Guide

This guide details all the environment variables you can use to configure the generic LLM Docker image. These variables allow you to deploy *any* LLM supported by vLLM with custom configurations at runtime.

## Core Configuration

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MODEL_NAME` | `Qwen/Qwen2.5-7B-Instruct-AWQ` | The Hugging Face model ID to load. Can be any model supported by vLLM. |
| `API_KEY` | `default-key` | The API key to protect the server. Clients must provide this key in the `Authorization` header. |
| `PORT` | `8000` | The port on which the vLLM server will listen. |
| `HF_HOME` | `/runpod-volume/huggingface_cache` | Directory to cache downloaded models. Map this to a persistent volume for faster startups. |
| `HUGGING_FACE_HUB_TOKEN` | *(None)* | Your Hugging Face User Access Token. Required for accessing gated or private models (e.g., Llama 3). |

## vLLM Engine Configuration

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MAX_MODEL_LEN` | `32768` | Maximum context length (tokens) for the model. Lower this if you run out of GPU memory. |
| `GPU_MEMORY_UTILIZATION` | `0.95` | Fraction of GPU memory to allocate for the model and KV cache. |
| `DTYPE` | `auto` | Data type for model weights. Options: `auto`, `half`, `float16`, `bfloat16`, `float32`. |
| `QUANTIZATION` | *(Empty)* | Quantization method to use. Options: `awq`, `gptq`, `squeezellm`, or leave empty for none/auto-detect. |
| `TRUST_REMOTE_CODE` | `true` | Whether to trust remote code from the model repository. Set to `false` to disable. |

## Tool Use & Parsing

| Variable | Default | Description |
| :--- | :--- | :--- |
| `ENABLE_AUTO_TOOL_CHOICE` | `true` | Enables automatic tool choice capabilities if the model supports it. |
| `TOOL_CALL_PARSER` | `hermes` | The parser to use for tool calls. Options depend on vLLM version (e.g., `hermes`, `mistral`, `generic`). |

## Advanced Configuration

The following environment variables map directly to vLLM command-line arguments.

### Distributed Inference
| Variable | vLLM Flag | Description |
| :--- | :--- | :--- |
| `TENSOR_PARALLEL_SIZE` | `--tensor-parallel-size` | Number of GPUs for tensor parallelism. |
| `PIPELINE_PARALLEL_SIZE` | `--pipeline-parallel-size` | Number of GPUs for pipeline parallelism. |

### LoRA Adapters
| Variable | vLLM Flag | Description |
| :--- | :--- | :--- |
| `ENABLE_LORA` | `--enable-lora` | Set to `true` to enable LoRA support. |
| `MAX_LORAS` | `--max-loras` | Max number of LoRAs to run in parallel. |
| `MAX_LORA_RANK` | `--max-lora-rank` | Max LoRA rank. |
| `LORA_MODULES` | `--lora-modules` | List of LoRA modules (e.g., `name=path`). |

### Model & Tokenizer
| Variable | vLLM Flag | Description |
| :--- | :--- | :--- |
| `TRUST_REMOTE_CODE` | `--trust-remote-code` | Set to `true` to trust remote code (default: true). |
| `TOKENIZER` | `--tokenizer` | Custom tokenizer path/ID. |
| `TOKENIZER_MODE` | `--tokenizer-mode` | Tokenizer mode (`auto`, `slow`). |
| `REVISION` | `--revision` | Model revision (branch/tag/commit). |
| `TOKENIZER_REVISION` | `--tokenizer-revision` | Tokenizer revision. |

### Scheduling & Memory
| Variable | vLLM Flag | Description |
| :--- | :--- | :--- |
| `MAX_NUM_SEQS` | `--max-num-seqs` | Max number of sequences per iteration. |
| `MAX_NUM_BATCHED_TOKENS` | `--max-num-batched-tokens` | Max number of batched tokens per iteration. |
| `SWAP_SPACE` | `--swap-space` | CPU swap space size (GiB). |
| `ENFORCE_EAGER` | `--enforce-eager` | Set to `true` to enforce eager execution. |
| `KV_CACHE_DTYPE` | `--kv-cache-dtype` | Data type for KV cache (e.g., `auto`, `fp8`). |

### Server & API
| Variable | vLLM Flag | Description |
| :--- | :--- | :--- |
| `SERVED_MODEL_NAME` | `--served-model-name` | Override the model name returned by the API. |
| `CHAT_TEMPLATE` | `--chat-template` | Path to a custom chat template file. |
| `UV_LOOP` | `--uv-loop` | UV loop implementation (`uvloop`, `asyncio`). |
| `LOG_LEVEL` | `--log-level` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

### Manual Override
| Variable | Default | Description |
| :--- | :--- | :--- |
| `EXTRA_ARGS` | *(Empty)* | Pass *any* additional flags directly to the vLLM server string. This is useful for flags that are not explicitly covered above. |

---

## Usage Examples

### 1. Deploying Llama 3 8B (Gated Model)
```bash
docker run -d \
  --gpus all \
  -e MODEL_NAME="meta-llama/Meta-Llama-3-8B-Instruct" \
  -e HUGGING_FACE_HUB_TOKEN="hf_..." \
  -e MAX_MODEL_LEN=8192 \
  -p 8000:8000 \
  my-llm-image
```

### 2. Deploying a Quantized Model (AWQ)
```bash
docker run -d \
  --gpus all \
  -e MODEL_NAME="TheBloke/Mistral-7B-Instruct-v0.2-AWQ" \
  -e QUANTIZATION="awq" \
  -p 8000:8000 \
  my-llm-image
```

### 3. Using Extra Arguments
```bash
docker run -d \
  --gpus all \
  -e MODEL_NAME="Qwen/Qwen2.5-7B-Instruct" \
  -e EXTRA_ARGS="--enable-prefix-caching --disable-log-requests" \
  -p 8000:8000 \
  my-llm-image
```

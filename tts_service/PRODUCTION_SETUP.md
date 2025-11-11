# Production Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Install python-dotenv for .env file support
pip install python-dotenv

# Or install all requirements
pip install -r requirements.txt
```

### 2. Create Environment File

```bash
# Copy the example file
cp example.env .env

# Edit with your production values
nano .env  # or vim .env
```

### 3. Configure .env File

Edit `.env` file with your production settings:

```bash
# Enable authentication (REQUIRED for production)
TTS_REQUIRE_AUTH=true

# Set your API keys (comma-separated)
TTS_API_KEYS="sk-prod-key1-abc123xyz789,sk-prod-key2-def456uvw012"

# Other settings...
TTS_HOST=0.0.0.0
TTS_PORT=8002
TTS_LOG_LEVEL=info
```

### 4. Start the Service

```bash
# The service will automatically load from .env file
python tts_server.py
```

## Environment Variables

### Required for Production

```bash
# Enable authentication
TTS_REQUIRE_AUTH=true

# API keys (comma-separated, generate strong random keys)
TTS_API_KEYS="sk-prod-your-key-1,sk-prod-your-key-2"
```

### Optional Configuration

```bash
# Server settings
TTS_HOST=0.0.0.0
TTS_PORT=8002
TTS_LOG_LEVEL=info
TTS_MAX_TEXT_LENGTH=5000

# Model settings
TTS_MODEL_NAME=CosyVoice-300M-SFT
TTS_MODEL_PATH=pretrained_models/CosyVoice-300M-SFT
TTS_DEVICE=auto
```

## Generate Secure API Keys

### Python
```python
import secrets
# Generate a secure random key
key = f"sk-prod-{secrets.token_urlsafe(32)}"
print(key)
```

### OpenSSL
```bash
openssl rand -hex 32
```

### Node.js
```javascript
const crypto = require('crypto');
const key = `sk-prod-${crypto.randomBytes(32).toString('hex')}`;
console.log(key);
```

### Bash
```bash
# Generate a secure key
echo "sk-prod-$(openssl rand -hex 32)"
```

## Example Production Setup

### Using .env file (Recommended)

```bash
# .env file content
TTS_REQUIRE_AUTH=true
TTS_API_KEYS="sk-prod-client1-abc123xyz789def456uvw012ghi789rst345,sk-prod-client2-jkl012mno345pqr678stu901vwx234yza567"
TTS_HOST=0.0.0.0
TTS_PORT=8002
TTS_LOG_LEVEL=info
TTS_MAX_TEXT_LENGTH=5000
TTS_MODEL_NAME=CosyVoice-300M-SFT
TTS_MODEL_PATH=pretrained_models/CosyVoice-300M-SFT
TTS_DEVICE=auto
```

The service automatically loads from `.env` file when it starts.

### Using Environment Variables Directly (Alternative)

If you prefer not to use `.env` file:

```bash
export TTS_REQUIRE_AUTH=true
export TTS_API_KEYS="sk-prod-key1-abc123,sk-prod-key2-def456"
python tts_server.py
```

**Note:** Environment variables take precedence over `.env` file values.

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

ENV TTS_REQUIRE_AUTH=true
ENV TTS_API_KEYS="sk-prod-key1,sk-prod-key2"

EXPOSE 8002
CMD ["python", "tts_server.py"]
```

```bash
# docker-compose.yml
version: '3.8'
services:
  tts-service:
    build: .
    ports:
      - "8002:8002"
    environment:
      - TTS_REQUIRE_AUTH=true
      - TTS_API_KEYS=${TTS_API_KEYS}
    env_file:
      - .env.production
```

### Systemd Service

```ini
# /etc/systemd/system/tts-service.service
[Unit]
Description=TTS Service
After=network.target

[Service]
Type=simple
User=tts
WorkingDirectory=/opt/tts-service
Environment="TTS_REQUIRE_AUTH=true"
Environment="TTS_API_KEYS=sk-prod-key1,sk-prod-key2"
ExecStart=/usr/bin/python3 /opt/tts-service/tts_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Testing Production Setup

### 1. Test with Valid API Key

```bash
curl -X GET "http://localhost:8002/v1/voices" \
  -H "xi-api-key: sk-prod-key1-abc123"
```

### 2. Test without API Key (Should Fail)

```bash
curl -X GET "http://localhost:8002/v1/voices"
# Expected: {"detail": "Invalid or missing API key"}
```

### 3. Test with Invalid API Key (Should Fail)

```bash
curl -X GET "http://localhost:8002/v1/voices" \
  -H "xi-api-key: invalid-key"
# Expected: {"detail": "Invalid or missing API key"}
```

## Security Checklist

- [ ] `TTS_REQUIRE_AUTH=true` is set
- [ ] Strong API keys generated (32+ characters)
- [ ] `.env` file is in `.gitignore`
- [ ] File permissions set: `chmod 600 .env`
- [ ] Different keys for different environments
- [ ] Keys rotated regularly
- [ ] Keys stored securely (not in code)
- [ ] HTTPS enabled in production
- [ ] Rate limiting configured
- [ ] Monitoring/logging enabled

## Client Usage Examples

### Python Client

```python
import requests

API_KEY = "sk-prod-key1-abc123"
BASE_URL = "https://your-tts-service.com"

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

# List voices
response = requests.get(f"{BASE_URL}/v1/voices", headers=headers)
voices = response.json()

# Text to speech
response = requests.post(
    f"{BASE_URL}/v1/text-to-speech/default",
    headers=headers,
    json={
        "text": "Hello, world!",
        "model_id": "eleven_multilingual_v2"
    }
)
audio = response.content
```

### JavaScript/TypeScript

```typescript
const API_KEY = "sk-prod-key1-abc123";
const BASE_URL = "https://your-tts-service.com";

async function textToSpeech(text: string, voiceId: string) {
  const response = await fetch(`${BASE_URL}/v1/text-to-speech/${voiceId}`, {
    method: "POST",
    headers: {
      "xi-api-key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      text,
      model_id: "eleven_multilingual_v2"
    })
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  
  return await response.blob();
}
```

## Troubleshooting

### Authentication Not Working

1. Check environment variables are set:
   ```bash
   echo $TTS_REQUIRE_AUTH
   echo $TTS_API_KEYS
   ```

2. Check service logs for auth initialization:
   ```
   ✓ Authentication initialized: require_auth=True, 2 key(s) loaded
   ```

3. Verify API key format matches exactly (no extra spaces)

### Service Won't Start

1. Check if auth is required but no keys provided:
   ```
   WARNING: Authentication is required but no API keys provided!
   ```

2. Ensure environment variables are exported before starting

3. Check logs for initialization errors


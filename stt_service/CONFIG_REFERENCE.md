# Configuration Reference

Complete reference for all configuration options in the STT service.

## Configuration Structure

The service accepts three configuration sections:
1. **audio** - Audio format settings
2. **vad** - Voice Activity Detection settings
3. **transcription** - Transcription engine settings

## Audio Configuration

Configure audio input format. The service automatically converts to the required format (PCM16, mono, 16kHz) for Whisper.

```json
{
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "encoding": "pcm_s16le",
    "chunk_size": null
  }
}
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `sample_rate` | int | 16000 | 8000-48000 | Audio sample rate in Hz |
| `channels` | int | 1 | 1-2 | Number of audio channels (1=mono, 2=stereo) |
| `encoding` | string | "pcm_s16le" | See below | Audio encoding format |
| `chunk_size` | int\|null | null | - | Expected chunk size in bytes (optional) |

### Supported Encodings

| Encoding | Description | Bits per Sample |
|----------|-------------|-----------------|
| `pcm_s16le` | 16-bit signed PCM, little-endian | 16 |
| `pcm_f32le` | 32-bit float PCM, little-endian | 32 |
| `mulaw` | μ-law compression (telephony) | 8 |
| `alaw` | A-law compression (telephony) | 8 |

### Common Configurations

**Standard (16kHz mono)**
```json
{"sample_rate": 16000, "channels": 1, "encoding": "pcm_s16le"}
```

**High quality (48kHz stereo)**
```json
{"sample_rate": 48000, "channels": 2, "encoding": "pcm_s16le"}
```

**Telephone (8kHz mu-law)**
```json
{"sample_rate": 8000, "channels": 1, "encoding": "mulaw"}
```

## VAD Configuration

Configure Voice Activity Detection for automatic utterance detection.

```json
{
  "vad": {
    "enabled": true,
    "mode": 3,
    "silence_duration": 1.0,
    "min_speech_duration": 0.3,
    "frame_duration": 30,
    "speech_threshold": 0.5
  }
}
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `enabled` | bool | true | - | Enable/disable VAD |
| `mode` | int | 3 | 0-3 | VAD aggressiveness (0=quality, 3=aggressive) |
| `silence_duration` | float | 1.0 | 0.1-5.0 | Seconds of silence to trigger end-of-utterance |
| `min_speech_duration` | float | 0.3 | 0.1-2.0 | Minimum speech duration in seconds to process |
| `frame_duration` | int | 30 | 10,20,30 | Frame duration in milliseconds |
| `speech_threshold` | float | 0.5 | 0.0-1.0 | Ratio of speech frames to trigger speech detection |

### VAD Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| 0 | Quality mode | Clean audio, low noise |
| 1 | Low-bitrate | Compressed audio |
| 2 | Aggressive | Moderate noise |
| 3 | Very aggressive | High noise environments |

### Usage Scenarios

**Quiet environment (responsive)**
```json
{
  "mode": 1,
  "silence_duration": 0.5,
  "min_speech_duration": 0.2
}
```

**Noisy environment (robust)**
```json
{
  "mode": 3,
  "silence_duration": 1.5,
  "min_speech_duration": 0.5
}
```

**Conversation (natural pauses)**
```json
{
  "mode": 2,
  "silence_duration": 0.8,
  "min_speech_duration": 0.3
}
```

**Manual control (VAD disabled)**
```json
{
  "enabled": false
}
```

## Transcription Configuration

Configure the Whisper transcription engine.

```json
{
  "transcription": {
    "language": "en",
    "task": "transcribe",
    "beam_size": 5,
    "best_of": 5,
    "temperature": 0.0,
    "vad_filter": false,
    "condition_on_previous_text": false,
    "no_speech_threshold": 0.6,
    "enable_partial_transcripts": true,
    "partial_interval": 0.5
  }
}
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `language` | string\|null | null | ISO 639-1 | Language code (null=auto-detect) |
| `task` | string | "transcribe" | transcribe/translate | Task type |
| `beam_size` | int | 5 | 1-10 | Beam size for decoding (higher=better quality, slower) |
| `best_of` | int | 5 | 1-10 | Number of candidates when sampling |
| `temperature` | float | 0.0 | 0.0-1.0 | Sampling temperature (0=greedy, >0=random) |
| `vad_filter` | bool | false | - | Use Whisper's internal VAD |
| `condition_on_previous_text` | bool | false | - | Use previous text as context |
| `no_speech_threshold` | float | 0.6 | 0.0-1.0 | Threshold for no-speech detection |
| `enable_partial_transcripts` | bool | true | - | Send partial transcripts while speaking |
| `partial_interval` | float | 0.5 | 0.1-2.0 | Interval in seconds between partial transcripts |

### Language Codes

Common language codes (ISO 639-1):

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `es` | Spanish |
| `fr` | French | `de` | German |
| `it` | Italian | `pt` | Portuguese |
| `ru` | Russian | `zh` | Chinese |
| `ja` | Japanese | `ko` | Korean |
| `ar` | Arabic | `hi` | Hindi |

**Auto-detect**: Set to `null` for automatic language detection.

### Task Types

| Task | Description |
|------|-------------|
| `transcribe` | Transcribe audio in original language |
| `translate` | Transcribe and translate to English |

### Quality vs Speed Trade-offs

**Maximum quality (slow)**
```json
{
  "beam_size": 10,
  "best_of": 10,
  "temperature": 0.0
}
```

**Balanced (default)**
```json
{
  "beam_size": 5,
  "best_of": 5,
  "temperature": 0.0
}
```

**Maximum speed (lower quality)**
```json
{
  "beam_size": 1,
  "best_of": 1,
  "temperature": 0.0
}
```

### Partial Transcripts

Control real-time partial transcription behavior:

**Responsive (frequent updates)**
```json
{
  "enable_partial_transcripts": true,
  "partial_interval": 0.3
}
```

**Balanced**
```json
{
  "enable_partial_transcripts": true,
  "partial_interval": 0.5
}
```

**Conservative (less frequent)**
```json
{
  "enable_partial_transcripts": true,
  "partial_interval": 1.0
}
```

**Disabled**
```json
{
  "enable_partial_transcripts": false
}
```

## Complete Examples

### Example 1: Voice Assistant (High Responsiveness)

```json
{
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "encoding": "pcm_s16le"
  },
  "vad": {
    "enabled": true,
    "mode": 3,
    "silence_duration": 0.8,
    "min_speech_duration": 0.2
  },
  "transcription": {
    "language": "en",
    "beam_size": 5,
    "enable_partial_transcripts": true,
    "partial_interval": 0.3
  }
}
```

### Example 2: Call Center (Quality, Noisy)

```json
{
  "audio": {
    "sample_rate": 8000,
    "channels": 1,
    "encoding": "mulaw"
  },
  "vad": {
    "enabled": true,
    "mode": 3,
    "silence_duration": 1.5,
    "min_speech_duration": 0.5
  },
  "transcription": {
    "language": null,
    "beam_size": 7,
    "enable_partial_transcripts": false
  }
}
```

### Example 3: Meeting Transcription (Multilingual)

```json
{
  "audio": {
    "sample_rate": 48000,
    "channels": 2,
    "encoding": "pcm_s16le"
  },
  "vad": {
    "enabled": true,
    "mode": 2,
    "silence_duration": 1.2,
    "min_speech_duration": 0.4
  },
  "transcription": {
    "language": null,
    "beam_size": 8,
    "enable_partial_transcripts": true,
    "partial_interval": 1.0
  }
}
```

### Example 4: Podcast Transcription (Quality)

```json
{
  "audio": {
    "sample_rate": 44100,
    "channels": 1,
    "encoding": "pcm_s16le"
  },
  "vad": {
    "enabled": false
  },
  "transcription": {
    "language": "en",
    "beam_size": 10,
    "temperature": 0.0,
    "enable_partial_transcripts": false
  }
}
```

## Performance Tips

1. **Sample Rate**: 16kHz is optimal for Whisper. Higher rates will be downsampled.

2. **Beam Size**: Higher = better quality but slower. Use 5 for real-time, 10 for offline.

3. **VAD Mode**: Higher mode filters noise better but may clip speech. Test in your environment.

4. **Partial Interval**: Lower = more responsive but more CPU. Balance based on needs.

5. **Language**: Specify language if known for faster processing. Auto-detect adds overhead.

6. **Channels**: Convert to mono before sending if possible to reduce bandwidth.

## Default Configuration

If no configuration is sent, the service uses:

```json
{
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "encoding": "pcm_s16le"
  },
  "vad": {
    "enabled": true,
    "mode": 3,
    "silence_duration": 1.0,
    "min_speech_duration": 0.3,
    "frame_duration": 30,
    "speech_threshold": 0.5
  },
  "transcription": {
    "language": null,
    "task": "transcribe",
    "beam_size": 5,
    "enable_partial_transcripts": true,
    "partial_interval": 0.5
  }
}
```

## Retrieving Default Configuration

```bash
curl http://localhost:8001/config/defaults
```

Or via WebSocket, the service will use defaults if no config is sent.


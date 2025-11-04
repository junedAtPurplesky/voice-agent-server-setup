# Configuration Reference

Complete guide to all configuration options in the CosyVoice2 TTS Service.

## 📋 Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Service Configuration](#service-configuration)
3. [Audio Configuration](#audio-configuration)
4. [Voice Configuration](#voice-configuration)
5. [Streaming Configuration](#streaming-configuration)
6. [Synthesis Configuration](#synthesis-configuration)
7. [Text Processing Configuration](#text-processing-configuration)
8. [Session Configuration](#session-configuration)
9. [Configuration Examples](#configuration-examples)
10. [Performance Tuning](#performance-tuning)

---

## Configuration Overview

### Configuration Levels

1. **Service Configuration** - Set at server startup (config.py)
2. **Session Configuration** - Set per client session (HTTP/WebSocket)
3. **Request Configuration** - Set per request (HTTP only)

### Configuration Hierarchy

```
Service Config (Server)
  └── Session Config (Client)
       └── Request Config (Per-request overrides)
```

Client configurations **override** service defaults.

---

## Service Configuration

Server-level configuration set in `config.py` or environment variables.

### ServiceConfig

```python
class ServiceConfig(BaseModel):
    model_name: str = "CosyVoice2-0.5B"
    model_path: str = "FunAudioLLM/CosyVoice2-0.5B"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    host: str = "0.0.0.0"
    port: int = 8002
    model_cache_dir: str = "./models"
    log_level: str = "info"
    max_text_length: int = 5000
```

### Parameters

#### `model_name`
- **Type**: string
- **Default**: `"CosyVoice2-0.5B"`
- **Description**: Name of the TTS model
- **Options**: 
  - `"CosyVoice2-0.5B"` - Fast, good quality
  - Custom model names (if supported)

#### `model_path`
- **Type**: string
- **Default**: `"FunAudioLLM/CosyVoice2-0.5B"`
- **Description**: Hugging Face model path or local path
- **Examples**:
  - `"FunAudioLLM/CosyVoice2-0.5B"` - Download from HF
  - `"/path/to/local/model"` - Load from disk

#### `device`
- **Type**: string
- **Default**: `"cuda"` if available, else `"cpu"`
- **Options**:
  - `"cuda"` - Use GPU (NVIDIA)
  - `"cuda:0"` - Specific GPU
  - `"cpu"` - Use CPU only
- **Performance Impact**: GPU is 10-30x faster

#### `host`
- **Type**: string
- **Default**: `"0.0.0.0"`
- **Description**: Server bind address
- **Examples**:
  - `"0.0.0.0"` - Listen on all interfaces
  - `"127.0.0.1"` - Local only

#### `port`
- **Type**: integer
- **Default**: `8002`
- **Description**: Server port number
- **Range**: 1024-65535

#### `model_cache_dir`
- **Type**: string
- **Default**: `"./models"`
- **Description**: Directory for cached models
- **Note**: Requires ~500MB-2GB disk space

#### `log_level`
- **Type**: string
- **Default**: `"info"`
- **Options**: `"debug"`, `"info"`, `"warning"`, `"error"`, `"critical"`

#### `max_text_length`
- **Type**: integer
- **Default**: `5000`
- **Description**: Maximum characters per request
- **Recommendation**: Keep under 5000 for best performance

### Environment Variables

Override service config with environment variables:

```bash
export TTS_PORT=8002
export TTS_DEVICE=cuda
export TTS_LOG_LEVEL=debug
export TTS_MAX_TEXT_LENGTH=5000
```

---

## Audio Configuration

Control output audio format and quality.

### AudioConfig

```python
class AudioConfig(BaseModel):
    sample_rate: int = 24000
    channels: int = 1
    encoding: Literal["pcm_s16le", "pcm_f32le", "mp3", "opus", "wav"] = "pcm_s16le"
    bitrate: Optional[int] = 128
```

### Parameters

#### `sample_rate`
- **Type**: integer
- **Default**: `24000`
- **Description**: Output audio sample rate in Hz
- **Options**:
  - `16000` - Lower quality, smaller size
  - `22050` - Medium quality
  - `24000` - High quality (CosyVoice native)
  - `44100` - CD quality
  - `48000` - Professional quality
- **Trade-off**: Higher = better quality but larger files
- **Recommendation**: Use `24000` (native model rate)

#### `channels`
- **Type**: integer
- **Default**: `1`
- **Options**:
  - `1` - Mono (recommended for TTS)
  - `2` - Stereo
- **Note**: TTS models typically generate mono; stereo duplicates channel

#### `encoding`
- **Type**: string (enum)
- **Default**: `"pcm_s16le"`
- **Options**:

| Encoding | Description | Quality | Size | CPU |
|----------|-------------|---------|------|-----|
| `pcm_s16le` | 16-bit PCM | High | Large | Low |
| `pcm_f32le` | 32-bit float PCM | Highest | Largest | Low |
| `wav` | WAV container | High | Large | Low |
| `mp3` | MP3 compressed | Good | Small | Medium |
| `opus` | Opus compressed | Good | Smallest | Medium |

**Recommendations**:
- Real-time streaming: `pcm_s16le`
- File storage: `mp3` or `opus`
- Maximum quality: `pcm_f32le`

#### `bitrate`
- **Type**: integer (optional)
- **Default**: `128`
- **Description**: Bitrate for lossy formats (kbps)
- **Range**: 64-320
- **Only applies to**: MP3, Opus
- **Examples**:
  - `64` - Low quality, small size
  - `128` - Good quality (recommended)
  - `192` - High quality
  - `256-320` - Maximum quality

### Examples

**High Quality**:
```json
{
  "audio": {
    "sample_rate": 24000,
    "channels": 1,
    "encoding": "pcm_s16le"
  }
}
```

**Small File Size**:
```json
{
  "audio": {
    "sample_rate": 22050,
    "channels": 1,
    "encoding": "opus",
    "bitrate": 96
  }
}
```

---

## Voice Configuration

Control voice characteristics and speaking style.

### VoiceConfig

```python
class VoiceConfig(BaseModel):
    speaker: str = "default"
    style: Optional[str] = None
    speed: float = 1.0  # 0.5-2.0
    pitch: float = 1.0  # 0.5-2.0
    energy: float = 1.0  # 0.5-2.0
```

### Parameters

#### `speaker`
- **Type**: string
- **Default**: `"default"`
- **Description**: Voice speaker/character ID
- **Available Voices**: Use `GET /voices` endpoint to list
- **Examples**:
  - `"default"` - Neutral voice
  - `"female_calm"` - Calm female voice
  - `"male_energetic"` - Energetic male voice
  - `"female_friendly"` - Friendly female voice
  - `"male_professional"` - Professional male voice

#### `style`
- **Type**: string (optional)
- **Default**: `null`
- **Description**: Speaking style or emotion
- **Options** (model-dependent):
  - `"cheerful"` - Happy, upbeat
  - `"sad"` - Somber, melancholic
  - `"angry"` - Intense, forceful
  - `"neutral"` - Balanced, professional
  - `"excited"` - Energetic, enthusiastic
- **Note**: Not all models support style control

#### `speed`
- **Type**: float
- **Default**: `1.0`
- **Range**: `0.5` - `2.0`
- **Description**: Speech rate multiplier

**Speed Guide**:
- `0.5` - Half speed (very slow, clear enunciation)
- `0.7` - Slow (learning, emphasis)
- `0.8` - Slightly slow (clear)
- `1.0` - Normal speed
- `1.2` - Slightly fast (energetic)
- `1.5` - Fast (excited, urgent)
- `2.0` - Double speed (maximum)

**Use Cases**:
- `0.7-0.8` - Educational content, accessibility
- `1.0` - Most applications
- `1.2-1.4` - Podcasts, energetic content
- `1.5+` - Quick summaries, time-constrained

#### `pitch`
- **Type**: float
- **Default**: `1.0`
- **Range**: `0.5` - `2.0`
- **Description**: Pitch/frequency multiplier

**Pitch Guide**:
- `0.5` - Very low (deep, bass)
- `0.7` - Low (masculine, authoritative)
- `0.9` - Slightly low
- `1.0` - Normal pitch
- `1.1` - Slightly high
- `1.3` - High (bright, youthful)
- `2.0` - Very high (chipmunk effect)

**Use Cases**:
- `0.7-0.9` - Authoritative narration, announcements
- `1.0` - Most applications
- `1.1-1.3` - Friendly, approachable content
- Extreme values - Special effects

#### `energy`
- **Type**: float
- **Default**: `1.0`
- **Range**: `0.5` - `2.0`
- **Description**: Volume/intensity multiplier

**Energy Guide**:
- `0.5` - Quiet, subdued
- `0.7` - Soft, intimate
- `1.0` - Normal energy
- `1.2` - Elevated, enthusiastic
- `1.5` - High energy, excited
- `2.0` - Maximum intensity

### Voice Combination Examples

**Calm Narrator**:
```json
{
  "voice": {
    "speaker": "male_professional",
    "speed": 0.9,
    "pitch": 0.95,
    "energy": 0.9
  }
}
```

**Energetic Presenter**:
```json
{
  "voice": {
    "speaker": "female_friendly",
    "speed": 1.2,
    "pitch": 1.1,
    "energy": 1.3
  }
}
```

**Serious Announcement**:
```json
{
  "voice": {
    "speaker": "male_professional",
    "speed": 0.85,
    "pitch": 0.9,
    "energy": 1.1
  }
}
```

---

## Streaming Configuration

ElevenLabs-style streaming controls for real-time synthesis.

### StreamingConfig

```python
class StreamingConfig(BaseModel):
    enabled: bool = True
    chunk_size: int = 1024
    flush_threshold: int = 3
    optimize_streaming_latency: int = 2
    enable_ssml_parsing: bool = False
    buffer_size: int = 3
    sentence_silence_duration: float = 0.3
```

### Parameters

#### `enabled`
- **Type**: boolean
- **Default**: `true`
- **Description**: Enable/disable streaming mode
- **Effect**: 
  - `true` - Stream audio chunks as generated
  - `false` - Wait for complete audio before sending

#### `chunk_size`
- **Type**: integer
- **Default**: `1024`
- **Range**: `256` - `4096`
- **Description**: Audio samples per streaming chunk
- **Trade-off**: 
  - Smaller = lower latency, more overhead
  - Larger = higher latency, less overhead
- **Recommendations**:
  - `512` - Ultra-low latency
  - `1024` - Balanced (recommended)
  - `2048` - Lower overhead

#### `flush_threshold`
- **Type**: integer
- **Default**: `3`
- **Range**: `1` - `10`
- **Description**: Number of sentences to buffer before auto-flushing
- **Impact**: **Critical for latency**

**Flush Threshold Guide**:

| Value | Latency | Quality | Use Case |
|-------|---------|---------|----------|
| `1` | Lowest | Good | Real-time chat, voice assistants |
| `2` | Low | Good+ | Interactive applications |
| `3` | Medium | Best | Balanced (default) |
| `4-5` | Higher | Best+ | Audiobooks, narration |
| `6-10` | Highest | Optimal | Batch processing |

**Example Impact**:
```
Text: "First sentence. Second sentence. Third sentence."

flush_threshold=1: Synth → Send → Synth → Send → Synth → Send
flush_threshold=3: Synth all → Send all (fewer interruptions)
```

#### `optimize_streaming_latency`
- **Type**: integer
- **Default**: `2`
- **Range**: `0` - `4`
- **Description**: Latency optimization level (ElevenLabs-style)

**Latency Levels**:

| Level | Latency | Quality | Processing | Use Case |
|-------|---------|---------|------------|----------|
| `0` | Highest | Best | Slowest | Maximum quality |
| `1` | High | Great | Slow | High-quality narration |
| `2` | Medium | Good | Balanced | General use (default) |
| `3` | Low | Acceptable | Fast | Interactive apps |
| `4` | Lowest | Acceptable | Fastest | Real-time chat |

**Technical Details**:
- Affects model inference parameters
- Controls buffer sizes and processing priorities
- Higher values may skip some quality checks

#### `enable_ssml_parsing`
- **Type**: boolean
- **Default**: `false`
- **Description**: Parse SSML markup in input text
- **Note**: Basic SSML support (full implementation in progress)
- **Example SSML**:
```xml
<speak>
  <prosody rate="slow">Hello</prosody>
  <break time="500ms"/>
  <prosody pitch="high">World</prosody>
</speak>
```

#### `buffer_size`
- **Type**: integer
- **Default**: `3`
- **Range**: `1` - `10`
- **Description**: Number of audio chunks to pre-buffer
- **Trade-off**:
  - `1` - Immediate streaming, potential stuttering
  - `3-5` - Smooth streaming (recommended)
  - `10` - Very smooth, higher initial latency

#### `sentence_silence_duration`
- **Type**: float
- **Default**: `0.3`
- **Range**: `0.0` - `2.0`
- **Description**: Silence duration between sentences (seconds)
- **Examples**:
  - `0.0` - No pause (continuous speech)
  - `0.2` - Quick pause
  - `0.3` - Natural pause (default)
  - `0.5` - Clear pause
  - `1.0` - Long pause (dramatic effect)

### Streaming Presets

**Real-Time Chat** (Lowest Latency):
```json
{
  "streaming": {
    "enabled": true,
    "chunk_size": 512,
    "flush_threshold": 1,
    "optimize_streaming_latency": 4,
    "buffer_size": 1,
    "sentence_silence_duration": 0.2
  }
}
```

**Interactive App** (Balanced):
```json
{
  "streaming": {
    "enabled": true,
    "chunk_size": 1024,
    "flush_threshold": 2,
    "optimize_streaming_latency": 2,
    "buffer_size": 3,
    "sentence_silence_duration": 0.3
  }
}
```

**Audiobook** (High Quality):
```json
{
  "streaming": {
    "enabled": true,
    "chunk_size": 2048,
    "flush_threshold": 5,
    "optimize_streaming_latency": 0,
    "buffer_size": 5,
    "sentence_silence_duration": 0.4
  }
}
```

---

## Synthesis Configuration

Control synthesis quality and model behavior.

### SynthesisConfig

```python
class SynthesisConfig(BaseModel):
    stability: float = 0.5
    similarity_boost: float = 0.75
    use_speaker_boost: bool = True
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    repetition_penalty: float = 1.0
    max_new_tokens: int = 2048
```

### Parameters

#### `stability`
- **Type**: float
- **Default**: `0.5`
- **Range**: `0.0` - `1.0`
- **Description**: Voice consistency/stability (ElevenLabs-inspired)

**Stability Guide**:

| Value | Behavior | Use Case |
|-------|----------|----------|
| `0.0-0.3` | Highly variable, expressive | Dramatic reading, character voices |
| `0.4-0.6` | Balanced (default range) | Most applications |
| `0.7-1.0` | Very consistent, predictable | Professional narration, news |

**Effect**:
- Low: More prosody variation, emotional expression
- High: Smoother, more monotone delivery

#### `similarity_boost`
- **Type**: float
- **Default**: `0.75`
- **Range**: `0.0` - `1.0`
- **Description**: Voice similarity to target speaker (ElevenLabs-style)

**Similarity Boost Guide**:

| Value | Behavior | Use Case |
|-------|----------|----------|
| `0.0-0.4` | Creative interpretation | Experimental, varied content |
| `0.5-0.8` | Balanced (recommended) | General use |
| `0.8-1.0` | Maximum similarity | Voice cloning, consistency |

**Effect**:
- Low: More creative, may deviate from target voice
- High: Closer match to speaker characteristics

#### `use_speaker_boost`
- **Type**: boolean
- **Default**: `true`
- **Description**: Enhance speaker-specific characteristics
- **Effect**: Emphasizes unique voice qualities
- **Recommendation**: Keep enabled for better voice distinction

#### `temperature`
- **Type**: float
- **Default**: `0.7`
- **Range**: `0.0` - `2.0`
- **Description**: Sampling randomness

**Temperature Guide**:

| Value | Behavior | Quality | Use Case |
|-------|----------|---------|----------|
| `0.0-0.3` | Very deterministic | Consistent | Repeated synthesis |
| `0.4-0.6` | Slightly varied | High | Professional content |
| `0.7-0.9` | Varied (natural) | Good | General use |
| `1.0-1.5` | Highly varied | Acceptable | Creative content |
| `1.6-2.0` | Chaotic | Lower | Experimental |

**Technical**: Controls softmax temperature in sampling

#### `top_k`
- **Type**: integer
- **Default**: `50`
- **Range**: `0` - `100`
- **Description**: Top-K sampling - consider top K tokens
- **Effect**:
  - Lower = More focused, deterministic
  - Higher = More diverse output
- **Recommendation**: `40-60` for speech

#### `top_p`
- **Type**: float
- **Default**: `0.9`
- **Range**: `0.0` - `1.0`
- **Description**: Nucleus sampling - cumulative probability threshold
- **Effect**:
  - Lower (0.7-0.8) = More focused
  - Higher (0.9-1.0) = More diverse
- **Recommendation**: `0.85-0.95` for natural speech

#### `repetition_penalty`
- **Type**: float
- **Default**: `1.0`
- **Range**: `1.0` - `2.0`
- **Description**: Penalty for repeating tokens
- **Effect**:
  - `1.0` = No penalty
  - `1.2-1.5` = Moderate penalty (recommended)
  - `1.5+` = Strong penalty (may sound unnatural)
- **Use**: Prevent audio artifacts and repetitions

#### `max_new_tokens`
- **Type**: integer
- **Default**: `2048`
- **Range**: `256` - `4096`
- **Description**: Maximum tokens to generate
- **Note**: Typically don't need to change
- **Effect**: Limits generation length (safety measure)

### Synthesis Presets

**Maximum Quality**:
```json
{
  "synthesis": {
    "stability": 0.7,
    "similarity_boost": 0.85,
    "use_speaker_boost": true,
    "temperature": 0.5,
    "top_k": 40,
    "top_p": 0.85,
    "repetition_penalty": 1.2
  }
}
```

**Natural & Expressive**:
```json
{
  "synthesis": {
    "stability": 0.4,
    "similarity_boost": 0.7,
    "use_speaker_boost": true,
    "temperature": 0.8,
    "top_k": 50,
    "top_p": 0.9,
    "repetition_penalty": 1.0
  }
}
```

**Consistent & Professional**:
```json
{
  "synthesis": {
    "stability": 0.8,
    "similarity_boost": 0.8,
    "use_speaker_boost": true,
    "temperature": 0.6,
    "top_k": 40,
    "top_p": 0.85,
    "repetition_penalty": 1.3
  }
}
```

---

## Text Processing Configuration

Control text preprocessing and normalization.

### TextProcessingConfig

```python
class TextProcessingConfig(BaseModel):
    normalize_text: bool = True
    split_sentences: bool = True
    remove_special_chars: bool = False
    max_sentence_length: int = 500
```

### Parameters

#### `normalize_text`
- **Type**: boolean
- **Default**: `true`
- **Description**: Apply text normalization
- **Operations**:
  - Expand numbers: `42` → `forty-two`
  - Expand abbreviations: `Dr.` → `Doctor`
  - Normalize punctuation
  - Convert symbols: `$50` → `fifty dollars`

**Example**:
```
Input:  "Dr. Smith earned $1,234 last yr."
Output: "Doctor Smith earned one thousand two hundred thirty-four dollars last year."
```

#### `split_sentences`
- **Type**: boolean
- **Default**: `true`
- **Description**: Automatically split text into sentences
- **Benefits**:
  - Better prosody (natural pauses)
  - Enables sentence-level streaming
  - More natural intonation
- **Sentence Boundaries**: `. ! ? ; :`

#### `remove_special_chars`
- **Type**: boolean
- **Default**: `false`
- **Description**: Remove special characters
- **Keeps**: Letters, numbers, basic punctuation
- **Removes**: Emojis, special symbols, formatting
- **Use Case**: Clean noisy input text

#### `max_sentence_length`
- **Type**: integer
- **Default**: `500`
- **Range**: `50` - `2000`
- **Description**: Maximum characters per sentence
- **Effect**: Long sentences are split at commas/semicolons
- **Recommendation**: `300-500` for best quality

### Text Processing Examples

**Default (Recommended)**:
```json
{
  "text_processing": {
    "normalize_text": true,
    "split_sentences": true,
    "remove_special_chars": false,
    "max_sentence_length": 500
  }
}
```

**Raw Text (Minimal Processing)**:
```json
{
  "text_processing": {
    "normalize_text": false,
    "split_sentences": false,
    "remove_special_chars": false,
    "max_sentence_length": 2000
  }
}
```

**Clean Input**:
```json
{
  "text_processing": {
    "normalize_text": true,
    "split_sentences": true,
    "remove_special_chars": true,
    "max_sentence_length": 300
  }
}
```

---

## Session Configuration

Complete session configuration combining all configs.

### SessionConfig

```python
class SessionConfig(BaseModel):
    audio: AudioConfig = AudioConfig()
    voice: VoiceConfig = VoiceConfig()
    streaming: StreamingConfig = StreamingConfig()
    synthesis: SynthesisConfig = SynthesisConfig()
    text_processing: TextProcessingConfig = TextProcessingConfig()
```

### Complete Example

```json
{
  "audio": {
    "sample_rate": 24000,
    "channels": 1,
    "encoding": "pcm_s16le"
  },
  "voice": {
    "speaker": "female_calm",
    "speed": 1.0,
    "pitch": 1.0,
    "energy": 1.0
  },
  "streaming": {
    "enabled": true,
    "chunk_size": 1024,
    "flush_threshold": 2,
    "optimize_streaming_latency": 2,
    "buffer_size": 3,
    "sentence_silence_duration": 0.3
  },
  "synthesis": {
    "stability": 0.6,
    "similarity_boost": 0.75,
    "use_speaker_boost": true,
    "temperature": 0.7,
    "top_k": 50,
    "top_p": 0.9,
    "repetition_penalty": 1.0
  },
  "text_processing": {
    "normalize_text": true,
    "split_sentences": true,
    "remove_special_chars": false,
    "max_sentence_length": 500
  }
}
```

---

## Configuration Examples

### Use Case Presets

#### 1. Real-Time Voice Assistant

**Requirements**: Lowest latency, acceptable quality

```json
{
  "audio": {
    "sample_rate": 22050,
    "encoding": "opus",
    "bitrate": 96
  },
  "voice": {
    "speaker": "female_friendly",
    "speed": 1.1
  },
  "streaming": {
    "flush_threshold": 1,
    "optimize_streaming_latency": 4,
    "chunk_size": 512,
    "buffer_size": 1
  },
  "synthesis": {
    "stability": 0.6,
    "temperature": 0.8
  }
}
```

#### 2. Audiobook Narration

**Requirements**: Maximum quality, consistency

```json
{
  "audio": {
    "sample_rate": 24000,
    "encoding": "pcm_s16le"
  },
  "voice": {
    "speaker": "male_professional",
    "speed": 0.95,
    "pitch": 0.95,
    "energy": 0.9
  },
  "streaming": {
    "flush_threshold": 5,
    "optimize_streaming_latency": 0,
    "sentence_silence_duration": 0.4
  },
  "synthesis": {
    "stability": 0.8,
    "similarity_boost": 0.85,
    "temperature": 0.5,
    "repetition_penalty": 1.3
  },
  "text_processing": {
    "normalize_text": true,
    "split_sentences": true,
    "max_sentence_length": 600
  }
}
```

#### 3. Customer Service Bot

**Requirements**: Clear, professional, moderate latency

```json
{
  "audio": {
    "sample_rate": 24000,
    "encoding": "opus",
    "bitrate": 128
  },
  "voice": {
    "speaker": "female_friendly",
    "speed": 1.0,
    "energy": 1.1
  },
  "streaming": {
    "flush_threshold": 2,
    "optimize_streaming_latency": 3,
    "sentence_silence_duration": 0.3
  },
  "synthesis": {
    "stability": 0.7,
    "similarity_boost": 0.8,
    "temperature": 0.6
  }
}
```

#### 4. Podcast Production

**Requirements**: Expressive, high quality, file output

```json
{
  "audio": {
    "sample_rate": 24000,
    "encoding": "mp3",
    "bitrate": 192
  },
  "voice": {
    "speaker": "male_energetic",
    "speed": 1.15,
    "pitch": 1.05,
    "energy": 1.2
  },
  "streaming": {
    "flush_threshold": 3,
    "optimize_streaming_latency": 1,
    "sentence_silence_duration": 0.35
  },
  "synthesis": {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "temperature": 0.75
  }
}
```

#### 5. Learning/Educational Content

**Requirements**: Clear, slower, well-paced

```json
{
  "audio": {
    "sample_rate": 24000,
    "encoding": "pcm_s16le"
  },
  "voice": {
    "speaker": "female_calm",
    "speed": 0.85,
    "pitch": 1.0,
    "energy": 1.0
  },
  "streaming": {
    "flush_threshold": 2,
    "optimize_streaming_latency": 1,
    "sentence_silence_duration": 0.5
  },
  "synthesis": {
    "stability": 0.75,
    "similarity_boost": 0.8,
    "temperature": 0.6
  },
  "text_processing": {
    "normalize_text": true,
    "max_sentence_length": 400
  }
}
```

---

## Performance Tuning

### Latency Optimization

**Priority: Minimize first-byte latency**

```json
{
  "streaming": {
    "flush_threshold": 1,
    "optimize_streaming_latency": 4,
    "chunk_size": 512,
    "buffer_size": 1
  },
  "synthesis": {
    "temperature": 0.8,
    "top_k": 30
  }
}
```

**Expected**: 100-200ms first chunk

### Quality Optimization

**Priority: Maximum audio quality**

```json
{
  "audio": {
    "sample_rate": 24000,
    "encoding": "pcm_s16le"
  },
  "streaming": {
    "optimize_streaming_latency": 0,
    "flush_threshold": 5
  },
  "synthesis": {
    "stability": 0.8,
    "similarity_boost": 0.85,
    "temperature": 0.5,
    "top_p": 0.85,
    "repetition_penalty": 1.3
  }
}
```

### Bandwidth Optimization

**Priority: Minimize network usage**

```json
{
  "audio": {
    "sample_rate": 16000,
    "encoding": "opus",
    "bitrate": 64
  },
  "streaming": {
    "chunk_size": 2048
  }
}
```

**Bandwidth**: ~64 kbps

### CPU Optimization

**Priority: Minimize CPU usage**

```json
{
  "streaming": {
    "optimize_streaming_latency": 3,
    "chunk_size": 2048
  },
  "synthesis": {
    "temperature": 0.9,
    "top_k": 30
  }
}
```

### GPU Memory Optimization

```python
# Force CPU mode
SERVICE_CONFIG.device = "cpu"

# Or reduce batch processing
streaming.flush_threshold = 1
```

---

## Configuration Validation

### Validation Rules

The service validates all configurations:

1. **Range Checks**: Values must be within specified ranges
2. **Type Checks**: Correct data types enforced
3. **Enum Checks**: String values must match allowed options
4. **Dependency Checks**: Some options depend on others

### Error Examples

**Invalid Range**:
```json
{
  "voice": {
    "speed": 3.0  // ❌ Max is 2.0
  }
}
```
Error: `speed must be between 0.5 and 2.0`

**Invalid Enum**:
```json
{
  "audio": {
    "encoding": "flac"  // ❌ Not supported
  }
}
```
Error: `encoding must be one of: pcm_s16le, pcm_f32le, mp3, opus, wav`

### Best Practice: Validate Before Sending

```python
from pydantic import ValidationError
from config import SessionConfig

try:
    config = SessionConfig(
        voice={"speed": 1.5},
        streaming={"flush_threshold": 2}
    )
    # Valid config
except ValidationError as e:
    print(f"Invalid config: {e}")
```

---

## Summary Table

### Quick Reference

| Feature | Config Section | Key Parameter | Default | Range |
|---------|---------------|---------------|---------|-------|
| Output Quality | `audio` | `sample_rate` | 24000 | 16000-48000 |
| Speech Speed | `voice` | `speed` | 1.0 | 0.5-2.0 |
| Latency | `streaming` | `flush_threshold` | 3 | 1-10 |
| Latency | `streaming` | `optimize_streaming_latency` | 2 | 0-4 |
| Consistency | `synthesis` | `stability` | 0.5 | 0.0-1.0 |
| Voice Match | `synthesis` | `similarity_boost` | 0.75 | 0.0-1.0 |
| Randomness | `synthesis` | `temperature` | 0.7 | 0.0-2.0 |

---

## Additional Resources

- [README.md](README.md) - Service overview
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [CLIENT_API_GUIDE.md](CLIENT_API_GUIDE.md) - API reference with examples

---

**Need help choosing settings?** Start with defaults and adjust based on your specific needs!


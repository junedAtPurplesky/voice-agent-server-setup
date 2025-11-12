"""
Custom LiveKit plugins matching ElevenLabs TTS and Speechmatics STT interfaces
These plugins are drop-in replacements for the official plugins
"""

import os
import asyncio
import base64
import json
import logging
from typing import Optional, AsyncIterator
import numpy as np
import aiohttp
import websockets
from livekit import rtc
from livekit.agents import stt, llm, tts

logger = logging.getLogger(__name__)


# Configuration from environment variables
STT_BASE_URL = os.getenv("STT_BASE_URL", "http://localhost:8001")
TTS_BASE_URL = os.getenv("TTS_BASE_URL", "http://localhost:8002")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8080")
STT_API_KEY = os.getenv("STT_API_KEY", "")
TTS_API_KEY = os.getenv("TTS_API_KEY", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")


# ============================================================================
# Speechmatics STT Plugin (matching official interface)
# ============================================================================

class STT(stt.STT):
    """
    Speechmatics-compatible STT plugin
    Matches the interface of livekit.plugins.speechmatics.STT
    """
    
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        language: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Speechmatics-compatible STT
        
        Args:
            api_key: API key for authentication (uses STT_API_KEY env var if not provided)
            language: Language code (e.g., 'en', 'en-US')
            base_url: Base URL of STT service (uses STT_BASE_URL env var if not provided)
        """
        super().__init__()
        self._api_key = api_key or STT_API_KEY
        self._language = language
        self._base_url = (base_url or STT_BASE_URL).rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def aclose(self):
        """Close the plugin"""
        if self._session:
            await self._session.close()
            self._session = None
    
    def stream(
        self,
        *,
        sample_rate: int,
        num_channels: int,
    ) -> "STTStream":
        """
        Create a streaming STT instance
        
        Args:
            sample_rate: Audio sample rate
            num_channels: Number of audio channels
        """
        return STTStream(
            api_key=self._api_key,
            language=self._language,
            base_url=self._base_url,
            sample_rate=sample_rate,
            num_channels=num_channels,
        )


class STTStream(stt.STTStream):
    """
    Streaming STT implementation matching Speechmatics protocol
    """
    
    def __init__(
        self,
        *,
        api_key: str,
        language: Optional[str],
        base_url: str,
        sample_rate: int,
        num_channels: int,
    ):
        super().__init__(sample_rate=sample_rate, num_channels=num_channels)
        self._api_key = api_key
        self._language = language
        self._base_url = base_url
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._audio_buffer = bytearray()
        self._task: Optional[asyncio.Task] = None
        self._session_started = False
    
    async def aclose(self):
        """Close the stream"""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            try:
                # Send EndOfStream message (Speechmatics protocol)
                await self._ws.send(json.dumps({"message": "EndOfStream"}))
            except Exception:
                pass
            await self._ws.close()
            self._ws = None
    
    async def push_frame(self, frame: rtc.AudioFrame):
        """Push audio frame for transcription"""
        if not self._ws:
            await self._start_session()
        
        # Convert frame to bytes (PCM16)
        audio_data = frame.data.tobytes()
        self._audio_buffer.extend(audio_data)
        
        # Send binary audio chunks (Speechmatics expects binary data)
        # Recommended chunk size: ~200ms at 16kHz mono PCM16 = 6400 bytes
        chunk_size = (self.sample_rate * 2 * 2) // 10  # 200ms
        if len(self._audio_buffer) >= chunk_size:
            await self._send_audio_chunk()
    
    async def flush(self):
        """Flush remaining audio"""
        if self._audio_buffer and self._ws:
            await self._send_audio_chunk()
            # Signal end of stream
            await self._ws.send(json.dumps({"message": "EndOfStream"}))
    
    async def _start_session(self):
        """Start Speechmatics WebSocket session"""
        ws_url = self._base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/v1/realtime"
        
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        
        self._ws = await websockets.connect(ws_url, extra_headers=headers)
        
        # Send StartRecognition message (Speechmatics protocol)
        config = {
            "message": "StartRecognition",
            "config": {
                "language": self._language or "en",
                "output_format": "json",
                "enable_partials": True,
                "max_delay": 0.0
            }
        }
        await self._ws.send(json.dumps(config))
        self._session_started = True
        
        # Start receiving task
        self._task = asyncio.create_task(self._receive_loop())
    
    async def _send_audio_chunk(self):
        """Send audio chunk as binary (Speechmatics protocol)"""
        if not self._ws or not self._audio_buffer:
            return
        
        chunk = bytes(self._audio_buffer)
        self._audio_buffer.clear()
        await self._ws.send(chunk)
    
    async def _receive_loop(self):
        """Receive transcription results (Speechmatics protocol)"""
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    continue
                
                try:
                    data = json.loads(message)
                    msg_type = data.get("message")
                    
                    if msg_type == "AddPartialTranscript":
                        # Partial transcript (interim)
                        results = data.get("results", [])
                        text = self._extract_text_from_results(results)
                        if text:
                            await self.on_event.emit(stt.SpeechEvent(
                                type=stt.SpeechEventType.INTERIM_TRANSCRIPT,
                                alternatives=[stt.SpeechData(text=text)]
                            ))
                    
                    elif msg_type == "AddTranscript":
                        # Final transcript
                        results = data.get("results", [])
                        text = self._extract_text_from_results(results)
                        if text:
                            await self.on_event.emit(stt.SpeechEvent(
                                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                                alternatives=[stt.SpeechData(
                                    text=text,
                                    language=data.get("language", self._language or "en")
                                )]
                            ))
                    
                    elif msg_type == "EndOfTranscript":
                        # End of utterance
                        await self.on_event.emit(stt.SpeechEvent(
                            type=stt.SpeechEventType.END_OF_SPEECH,
                            alternatives=[]
                        ))
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing STT message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("STT WebSocket connection closed")
        except Exception as e:
            logger.error(f"STT stream receive error: {e}")
            await self.on_event.emit(stt.SpeechEvent(
                type=stt.SpeechEventType.ERROR,
                alternatives=[stt.SpeechData(text=f"Error: {str(e)}")]
            ))
    
    def _extract_text_from_results(self, results: list) -> str:
        """Extract text from Speechmatics results format"""
        text_parts = []
        for result in results:
            if "alternatives" in result:
                for alt in result["alternatives"]:
                    # Speechmatics uses 'transcript' key (not 'content')
                    transcript = alt.get("transcript", "")
                    if not transcript:
                        # Fallback to 'content' for compatibility
                        transcript = alt.get("content", "")
                    if transcript:
                        text_parts.append(transcript)
        return " ".join(text_parts).strip()


# ============================================================================
# ElevenLabs TTS Plugin (matching official interface)
# ============================================================================

class TTS(tts.TTS):
    """
    ElevenLabs-compatible TTS plugin
    Matches the interface of livekit.plugins.elevenlabs.TTS
    """
    
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        voice: str = "default",
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize ElevenLabs-compatible TTS
        
        Args:
            api_key: API key for authentication (uses TTS_API_KEY env var if not provided)
            voice: Voice ID to use
            model: Model ID (optional, uses default if not provided)
            base_url: Base URL of TTS service (uses TTS_BASE_URL env var if not provided)
        """
        super().__init__()
        self._api_key = api_key or TTS_API_KEY
        self._voice = voice
        self._model = model
        self._base_url = (base_url or TTS_BASE_URL).rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def aclose(self):
        """Close the plugin"""
        if self._session:
            await self._session.close()
            self._session = None
    
    def synthesize(
        self,
        *,
        text: str,
    ) -> "TTSStream":
        """
        Synthesize text to speech
        
        Args:
            text: Text to synthesize
        """
        return TTSStream(
            api_key=self._api_key,
            voice=self._voice,
            model=self._model,
            base_url=self._base_url,
            text=text,
        )


class TTSStream(tts.TTSStream):
    """
    Streaming TTS implementation matching ElevenLabs protocol
    """
    
    def __init__(
        self,
        *,
        api_key: str,
        voice: str,
        model: Optional[str],
        base_url: str,
        text: str,
    ):
        super().__init__()
        self._api_key = api_key
        self._voice = voice
        self._model = model
        self._base_url = base_url
        self._text = text
        self._session: Optional[aiohttp.ClientSession] = None
        self._sample_rate = 24000  # Default for ElevenLabs/CosyVoice
    
    async def aclose(self):
        """Close the stream"""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            headers = {
                "Content-Type": "application/json",
            }
            if self._api_key:
                # ElevenLabs uses 'xi-api-key' header
                headers["xi-api-key"] = self._api_key
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session
    
    async def __aiter__(self) -> AsyncIterator[tts.SynthesizedEvent]:
        """Stream synthesized audio (ElevenLabs protocol)"""
        session = self._get_session()
        
        # ElevenLabs API format
        request_data = {
            "text": self._text,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "use_speaker_boost": True
            },
            "output_format": "pcm_24000"  # ElevenLabs format
        }
        
        if self._model:
            request_data["model_id"] = self._model
        
        try:
            async with session.post(
                f"{self._base_url}/v1/text-to-speech/{self._voice}/stream",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"TTS API error {resp.status}: {error_text}")
                
                # Stream audio chunks (ElevenLabs returns PCM16 audio)
                async for chunk in resp.content.iter_chunked(4096):
                    if chunk:
                        # Convert bytes to numpy array (PCM16, 16-bit signed integers)
                        audio_array = np.frombuffer(chunk, dtype=np.int16)
                        samples_per_channel = len(audio_array)
                        
                        yield tts.SynthesizedEvent(
                            type=tts.SynthesizedEventType.AUDIO,
                            audio=rtc.AudioFrame(
                                data=audio_array,
                                sample_rate=self._sample_rate,
                                num_channels=1,
                                samples_per_channel=samples_per_channel
                            )
                        )
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise


# ============================================================================
# Custom LLM Plugin (OpenAI-compatible)
# ============================================================================

class LLM(llm.LLM):
    """
    OpenAI-compatible LLM plugin
    """
    
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: str = "default",
        temperature: float = 0.7,
        base_url: Optional[str] = None,
    ):
        """
        Initialize LLM plugin
        
        Args:
            api_key: API key for authentication (uses LLM_API_KEY env var if not provided)
            model: Model name
            temperature: Sampling temperature
            base_url: Base URL of LLM gateway (uses LLM_BASE_URL env var if not provided)
        """
        super().__init__()
        self._api_key = api_key or LLM_API_KEY
        self._model = model
        self._temperature = temperature
        self._base_url = (base_url or LLM_BASE_URL).rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def aclose(self):
        """Close the plugin"""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            headers = {
                "Content-Type": "application/json",
            }
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session
    
    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        fnc_ctx: Optional[llm.FunctionContext] = None,
    ) -> "LLMStream":
        """Create chat stream"""
        return LLMStream(
            api_key=self._api_key,
            model=self._model,
            temperature=self._temperature,
            base_url=self._base_url,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
        )


class LLMStream(llm.LLMStream):
    """Streaming LLM implementation"""
    
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        temperature: float,
        base_url: str,
        chat_ctx: llm.ChatContext,
        fnc_ctx: Optional[llm.FunctionContext],
    ):
        super().__init__(chat_ctx=chat_ctx, fnc_ctx=fnc_ctx)
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def aclose(self):
        """Close the stream"""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            headers = {
                "Content-Type": "application/json",
            }
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session
    
    async def __aiter__(self) -> AsyncIterator[llm.ChunkEvent]:
        """Stream chat completion (OpenAI protocol)"""
        session = self._get_session()
        
        # Convert chat context to OpenAI format
        messages = []
        for msg in self.chat_ctx.messages:
            role = "user" if msg.role == llm.ChatRole.USER else "assistant"
            messages.append({
                "role": role,
                "content": msg.content
            })
        
        # Add system message if present
        if self.chat_ctx.instructions:
            messages.insert(0, {
                "role": "system",
                "content": self.chat_ctx.instructions
            })
        
        # Prepare functions if available
        functions = None
        if self.fnc_ctx and self.fnc_ctx.definitions:
            functions = []
            for fn_def in self.fnc_ctx.definitions:
                fn_schema = {
                    "name": fn_def.name,
                    "description": fn_def.description,
                    "parameters": fn_def.parameters
                }
                functions.append(fn_schema)
        
        request_data = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "stream": True,
        }
        
        if functions:
            request_data["functions"] = functions
        
        try:
            async with session.post(
                f"{self._base_url}/v1/chat/completions",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"LLM API error {resp.status}: {error_text}")
                
                # Parse SSE stream (OpenAI format)
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line or line == "data: [DONE]":
                        continue
                    
                    if line.startswith("data: "):
                        line = line[6:]
                    
                    try:
                        data = json.loads(line)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            
                            if content:
                                yield llm.ChunkEvent(
                                    type=llm.ChunkEventType.CONTENT,
                                    content=content
                                )
                            
                            # Handle function calls
                            if "function_call" in delta:
                                fn_call = delta["function_call"]
                                if "name" in fn_call:
                                    yield llm.ChunkEvent(
                                        type=llm.ChunkEventType.FUNCTION_CALL,
                                        function_call=llm.FunctionCall(
                                            name=fn_call.get("name", ""),
                                            arguments=fn_call.get("arguments", "")
                                        )
                                    )
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            raise

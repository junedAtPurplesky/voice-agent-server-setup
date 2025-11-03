#!/usr/bin/env python3
"""
Integration example: How to use the configurable STT service in your voice agent
Demonstrates client-side configuration like Speechmatics
"""

import asyncio
import json
from typing import Optional, Callable, Dict, Any

import websockets


class STTClient:
    """
    Configurable client for Faster Whisper STT Service
    Similar to Speechmatics API with client-side configuration
    """
    
    def __init__(
        self,
        url: str = "ws://localhost:8001/stream",
        audio_config: Optional[Dict[str, Any]] = None,
        vad_config: Optional[Dict[str, Any]] = None,
        transcription_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize STT client
        
        Args:
            url: WebSocket URL
            audio_config: Audio format configuration
            vad_config: VAD configuration
            transcription_config: Transcription configuration
        """
        self.url = url
        self.websocket = None
        
        # Configuration
        self.audio_config = audio_config or {
            "sample_rate": 16000,
            "channels": 1,
            "encoding": "pcm_s16le"
        }
        
        self.vad_config = vad_config or {
            "enabled": True,
            "mode": 3,
            "silence_duration": 1.0,
            "min_speech_duration": 0.3,
            "frame_duration": 30
        }
        
        self.transcription_config = transcription_config or {
            "language": "en",
            "enable_partial_transcripts": True,
            "partial_interval": 0.5
        }
        
        # Callbacks
        self.on_partial: Optional[Callable[[str, Dict], None]] = None
        self.on_final: Optional[Callable[[str, Dict], None]] = None
        self.on_end_of_utterance: Optional[Callable[[], None]] = None
        self.on_status: Optional[Callable[[Dict], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
    async def connect(self):
        """Connect to STT service and send configuration"""
        self.websocket = await websockets.connect(self.url)
        print("[STT] Connected")
        
        # Send configuration
        config_message = {
            "type": "config",
            "audio": self.audio_config,
            "vad": self.vad_config,
            "transcription": self.transcription_config
        }
        
        await self.websocket.send(json.dumps(config_message))
        
        # Wait for ready confirmation
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get('type') == 'ready':
            print(f"[STT] {data.get('message')}")
        else:
            raise Exception(f"Failed to configure: {data}")
            
    async def disconnect(self):
        """Disconnect from STT service"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            print("[STT] Disconnected")
            
    async def send_audio(self, audio_chunk: bytes):
        """
        Send audio chunk to STT service
        
        Args:
            audio_chunk: Raw audio in configured format
        """
        if self.websocket:
            await self.websocket.send(audio_chunk)
    
    async def receive_messages(self):
        """
        Receive and process messages from STT service
        Call this in a separate task
        """
        try:
            while self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                msg_type = data.get('type')
                
                if msg_type == 'partial':
                    # Partial transcript while user is speaking
                    if self.on_partial:
                        self.on_partial(data.get('text', ''), data)
                        
                elif msg_type == 'final':
                    # Final transcript of complete utterance
                    if self.on_final:
                        self.on_final(data.get('text', ''), data)
                        
                elif msg_type == 'end_of_utterance':
                    # User stopped speaking
                    if self.on_end_of_utterance:
                        self.on_end_of_utterance()
                        
                elif msg_type == 'status':
                    # Status update
                    if self.on_status:
                        self.on_status(data)
                        
                elif msg_type == 'error':
                    # Error occurred
                    if self.on_error:
                        self.on_error(data.get('message', 'Unknown error'))
                        
        except websockets.exceptions.ConnectionClosed:
            print("[STT] Connection closed")
        except Exception as e:
            print(f"[STT] Error receiving messages: {e}")
            if self.on_error:
                self.on_error(str(e))
    
    async def reset(self):
        """Reset the audio buffer"""
        if self.websocket:
            await self.websocket.send(json.dumps({"type": "reset"}))
    
    async def force_end(self):
        """Force end current utterance"""
        if self.websocket:
            await self.websocket.send(json.dumps({"type": "force_end"}))
    
    async def get_stats(self):
        """Request buffer statistics"""
        if self.websocket:
            await self.websocket.send(json.dumps({"type": "get_stats"}))


# Example 1: Basic usage with default configuration
async def basic_example():
    """Basic usage example"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Usage (Default Config)")
    print("=" * 60)
    
    # Create client with defaults
    stt = STTClient()
    
    # Set up callbacks
    def handle_partial(text: str, metadata: Dict):
        print(f"[USER SPEAKING] {text}")
    
    def handle_final(text: str, metadata: Dict):
        print(f"[USER SAID] {text}")
        print(f"  Processing time: {metadata.get('processing_time', 0):.3f}s")
    
    def handle_end_of_utterance():
        print("[USER FINISHED]")
    
    stt.on_partial = handle_partial
    stt.on_final = handle_final
    stt.on_end_of_utterance = handle_end_of_utterance
    
    # Connect
    await stt.connect()
    
    # Start receiving in background
    receive_task = asyncio.create_task(stt.receive_messages())
    
    # Send audio (your implementation here)
    # while True:
    #     audio_chunk = await get_audio_from_microphone()
    #     await stt.send_audio(audio_chunk)
    
    # Cleanup
    receive_task.cancel()
    await stt.disconnect()


# Example 2: Custom configuration (like Speechmatics)
async def custom_config_example():
    """Custom configuration example"""
    print("\n" + "=" * 60)
    print("Example 2: Custom Configuration")
    print("=" * 60)
    
    # Create client with custom config
    stt = STTClient(
        audio_config={
            "sample_rate": 16000,
            "channels": 1,
            "encoding": "pcm_s16le"
        },
        vad_config={
            "enabled": True,
            "mode": 2,  # Less aggressive VAD
            "silence_duration": 0.8,  # Shorter silence threshold
            "min_speech_duration": 0.2
        },
        transcription_config={
            "language": "en",
            "beam_size": 5,
            "enable_partial_transcripts": True,
            "partial_interval": 0.3  # More frequent partials
        }
    )
    
    # Set callbacks
    stt.on_partial = lambda text, meta: print(f"Partial: {text}")
    stt.on_final = lambda text, meta: print(f"Final: {text}")
    stt.on_end_of_utterance = lambda: print("End of utterance")
    
    await stt.connect()
    
    # Use the client...
    
    await stt.disconnect()


# Example 3: Voice agent integration
class VoiceAgent:
    """Example voice agent using STT service"""
    
    def __init__(self):
        # Configure STT for voice agent use case
        self.stt = STTClient(
            vad_config={
                "enabled": True,
                "mode": 3,
                "silence_duration": 1.0,
                "min_speech_duration": 0.3
            },
            transcription_config={
                "language": None,  # Auto-detect
                "enable_partial_transcripts": True,
                "partial_interval": 0.5
            }
        )
        
        # Set up STT callbacks
        self.stt.on_partial = self.on_partial_transcript
        self.stt.on_final = self.on_final_transcript
        self.stt.on_end_of_utterance = self.on_user_finished_speaking
        self.stt.on_error = self.on_stt_error
        
        self.current_transcript = ""
        
    def on_partial_transcript(self, text: str, metadata: Dict):
        """Handle partial transcript - update UI"""
        self.current_transcript = text
        print(f"[UI UPDATE] User: {text}")
        # Update your UI to show what user is saying in real-time
    
    def on_final_transcript(self, text: str, metadata: Dict):
        """Handle final transcript - process user input"""
        print(f"[USER INPUT] {text}")
        
        # Process the user's complete sentence
        asyncio.create_task(self.process_user_input(text))
    
    def on_user_finished_speaking(self):
        """Handle end of utterance - prepare for response"""
        print("[READY] User finished speaking, preparing response...")
        # This is a good time to stop audio playback if agent was speaking
        # or to prepare to generate a response
    
    def on_stt_error(self, error: str):
        """Handle STT errors"""
        print(f"[ERROR] STT error: {error}")
        # Handle error gracefully
    
    async def process_user_input(self, text: str):
        """Process user input and generate response"""
        # 1. Send to your LLM
        # llm_response = await self.llm_gateway.generate(text)
        
        # 2. Send to TTS
        # audio = await self.tts_service.synthesize(llm_response)
        
        # 3. Play audio
        # await self.audio_player.play(audio)
        
        print(f"[AGENT] Processing: {text}")
    
    async def start(self):
        """Start the voice agent"""
        print("Starting voice agent...")
        
        # Connect to STT
        await self.stt.connect()
        
        # Start receiving STT messages
        receive_task = asyncio.create_task(self.stt.receive_messages())
        
        # Main loop - receive audio from microphone and send to STT
        try:
            while True:
                # Get audio from microphone
                audio_chunk = await self.get_audio_from_microphone()
                
                # Send to STT
                await self.stt.send_audio(audio_chunk)
                
        except KeyboardInterrupt:
            print("\nStopping voice agent...")
        finally:
            receive_task.cancel()
            await self.stt.disconnect()
    
    async def get_audio_from_microphone(self) -> bytes:
        """Get audio from microphone - implement this"""
        # TODO: Implement actual microphone capture
        await asyncio.sleep(0.1)
        return b'\x00' * 3200


# Example 4: Different audio formats
async def audio_format_examples():
    """Examples with different audio formats"""
    print("\n" + "=" * 60)
    print("Example 4: Different Audio Formats")
    print("=" * 60)
    
    # Example 1: 8kHz telephone audio
    stt_telephone = STTClient(
        audio_config={
            "sample_rate": 8000,
            "channels": 1,
            "encoding": "pcm_s16le"
        }
    )
    
    # Example 2: 48kHz stereo high quality
    stt_hifi = STTClient(
        audio_config={
            "sample_rate": 48000,
            "channels": 2,
            "encoding": "pcm_s16le"
        }
    )
    
    # Example 3: mu-law encoded (common in telephony)
    stt_mulaw = STTClient(
        audio_config={
            "sample_rate": 8000,
            "channels": 1,
            "encoding": "mulaw"
        }
    )
    
    print("✓ Created clients for different audio formats")
    print("  - Telephone: 8kHz mono PCM")
    print("  - Hi-Fi: 48kHz stereo PCM")
    print("  - Telephony: 8kHz mu-law")


# Example 5: VAD configuration for different use cases
async def vad_config_examples():
    """Examples with different VAD configurations"""
    print("\n" + "=" * 60)
    print("Example 5: VAD Configurations")
    print("=" * 60)
    
    # Very responsive (for quiet environments)
    stt_quiet = STTClient(
        vad_config={
            "enabled": True,
            "mode": 1,  # Less aggressive
            "silence_duration": 0.5,  # Quick response
            "min_speech_duration": 0.2
        }
    )
    
    # Robust (for noisy environments)
    stt_noisy = STTClient(
        vad_config={
            "enabled": True,
            "mode": 3,  # Most aggressive
            "silence_duration": 1.5,  # Wait longer to avoid false triggers
            "min_speech_duration": 0.5
        }
    )
    
    # Disabled VAD (manual control)
    stt_manual = STTClient(
        vad_config={
            "enabled": False
        }
    )
    
    print("✓ Created clients with different VAD configs")
    print("  - Quiet: Responsive, low latency")
    print("  - Noisy: Robust, fewer false triggers")
    print("  - Manual: VAD disabled, manual control")


if __name__ == "__main__":
    print("=" * 60)
    print("STT Service Integration Examples")
    print("=" * 60)
    print("\nThis file demonstrates how to integrate the STT service")
    print("with client-side configuration (like Speechmatics)")
    print("\nSee the examples above for:")
    print("  - Basic usage")
    print("  - Custom configuration")
    print("  - Voice agent integration")
    print("  - Different audio formats")
    print("  - VAD configurations")
    print("\nUncomment the examples below to run them:")
    print()
    
    # Uncomment to run examples:
    # asyncio.run(basic_example())
    # asyncio.run(custom_config_example())
    # asyncio.run(audio_format_examples())
    # asyncio.run(vad_config_examples())
    
    # Run voice agent:
    # agent = VoiceAgent()
    # asyncio.run(agent.start())

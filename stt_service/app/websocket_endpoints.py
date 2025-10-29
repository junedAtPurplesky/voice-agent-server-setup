"""WebSocket endpoints for STT service"""

import logging
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
from .config import config_manager, TranscriptionConfig
from .models import stt_processor
from .auth import auth_manager, request_validator
from .vad import vad_manager
from .utils import response_formatter

logger = logging.getLogger(__name__)
router = APIRouter()


class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        vad_manager.remove_vad_instance(client_id)
        logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                return True
            except:
                return False
        return False


connection_manager = WebSocketConnectionManager()


def generate_client_id(websocket: WebSocket) -> str:
    """Generate unique client ID"""
    data = f"{websocket.client.host}{id(websocket)}{time.time()}"
    return hashlib.md5(data.encode()).hexdigest()[:16]


@router.websocket("/ws/realtime")
async def websocket_realtime_transcription(
    websocket: WebSocket,
    token: Optional[str] = None,
    language: str = "auto"
):
    """Real-time WebSocket transcription"""
    client_id = None
    
    try:
        if not auth_manager.validate_websocket_token(token):
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        client_id = generate_client_id(websocket)
        config = TranscriptionConfig(
            language=request_validator.validate_language(language),
            vad_config=config_manager.get_config().transcription.vad_config
        )
        
        await connection_manager.connect(websocket, client_id)
        
        welcome_msg = response_formatter.format_websocket_message(
            "connection_established",
            {"client_id": client_id},
            client_id
        )
        await connection_manager.send_message(client_id, welcome_msg)
        
        audio_buffer = bytearray()
        chunk_size = config_manager.get_config().chunk_size_bytes
        
        while True:
            data = await websocket.receive()
            
            if data["type"] == "websocket.receive" and "bytes" in data:
                audio_data = data["bytes"]
                audio_buffer.extend(audio_data)
                
                if len(audio_buffer) >= chunk_size:
                    try:
                        result = await stt_processor.process_stream(bytes(audio_buffer), config)
                        partial_msg = response_formatter.format_partial_transcript(
                            result.full_text,
                            result.segments[0].confidence if result.segments else 0.0,
                            client_id
                        )
                        await connection_manager.send_message(client_id, partial_msg)
                        audio_buffer.clear()
                    except Exception as e:
                        logger.error(f"Transcription error: {e}")
                        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if client_id:
            connection_manager.disconnect(client_id)


@router.websocket("/ws/fullduplex")
async def websocket_fullduplex_transcription(
    websocket: WebSocket,
    token: Optional[str] = None,
    language: str = "auto"
):
    """Full-duplex WebSocket with VAD"""
    client_id = None
    
    try:
        if not auth_manager.validate_websocket_token(token):
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        client_id = generate_client_id(websocket)
        config = TranscriptionConfig(
            language=request_validator.validate_language(language),
            vad_config=config_manager.get_config().transcription.vad_config
        )
        
        vad_instance = vad_manager.create_vad_instance(client_id, config.vad_config)
        await connection_manager.connect(websocket, client_id)
        
        audio_buffer = bytearray()
        chunk_size = config_manager.get_config().chunk_size_bytes
        
        while True:
            data = await websocket.receive()
            
            if data["type"] == "websocket.receive" and "bytes" in data:
                audio_data = data["bytes"]
                audio_buffer.extend(audio_data)
                
                # Process VAD
                vad_result = await vad_instance.process_audio_chunk(audio_data)
                if vad_result and vad_result.get("state") in ["speech_start", "speech_end"]:
                    vad_msg = response_formatter.format_vad_event(
                        vad_result["state"],
                        vad_result,
                        client_id
                    )
                    await connection_manager.send_message(client_id, vad_msg)
                
                if len(audio_buffer) >= chunk_size:
                    try:
                        result = await stt_processor.process_stream(bytes(audio_buffer), config)
                        if result.full_text.strip():
                            partial_msg = response_formatter.format_partial_transcript(
                                result.full_text,
                                result.segments[0].confidence if result.segments else 0.0,
                                client_id
                            )
                            await connection_manager.send_message(client_id, partial_msg)
                        audio_buffer.clear()
                    except Exception as e:
                        logger.error(f"Transcription error: {e}")
                        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if client_id:
            connection_manager.disconnect(client_id)


"""Utility functions"""

from datetime import datetime
from typing import Dict, Any


class ResponseFormatter:
    @staticmethod
    def format_transcription_response(result, config, processing_time, request_id=None):
        return {
            "success": True,
            "text": result.full_text if hasattr(result, 'full_text') else str(result),
            "language": config.language.value,
            "segments": result.segments_data if hasattr(result, 'segments_data') else [],
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def format_websocket_message(message_type: str, data: Dict, client_id=None):
        return {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id
        }
    
    @staticmethod
    def format_vad_event(event_type: str, vad_result: Dict, client_id=None):
        return {
            "type": "vad_event",
            "event": event_type,
            "vad_result": vad_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def format_partial_transcript(text: str, confidence: float = 0.0, client_id=None):
        return {
            "type": "partial_transcript",
            "text": text,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def format_final_transcript(text: str, segments: list, confidence: float = 0.0, client_id=None):
        return {
            "type": "final_transcript",
            "text": text,
            "segments": segments,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }


response_formatter = ResponseFormatter()


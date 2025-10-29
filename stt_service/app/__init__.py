"""STT Service Package"""

__version__ = "2.0.0"

from .main import app
from .config import config_manager
from .models import stt_processor
from .auth import auth_manager
from .vad import vad_manager

__all__ = [
    "app",
    "config_manager",
    "stt_processor",
    "auth_manager",
    "vad_manager"
]


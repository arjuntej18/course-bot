# Defines the automation states and stores current runtime status.

from dataclasses import dataclass, asdict
from enum import Enum
from threading import Lock
from typing import Optional


class BotState(str, Enum):
    IDLE = "IDLE"
    WAITING_FOR_CHROME = "WAITING_FOR_CHROME"
    CONNECTED = "CONNECTED"
    LOADING_VIDEO = "LOADING_VIDEO"
    PLAYING = "PLAYING"
    PAUSED_BY_NETWORK = "PAUSED_BY_NETWORK"
    RECOVERING = "RECOVERING"
    VIDEO_COMPLETED = "VIDEO_COMPLETED"
    BREAK = "BREAK"
    NEXT_VIDEO = "NEXT_VIDEO"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


@dataclass
class RuntimeStatus:
    state: BotState = BotState.IDLE
    message: str = "Idle"
    current_url: str = ""
    position: float = 0.0
    duration: float = 0.0
    internet_connected: bool = True
    browser_connected: bool = False
    last_checkpoint: float = 0.0
    error: Optional[str] = None


class StatusStore:
    def __init__(self):
        self._status = RuntimeStatus()
        self._lock = Lock()

    def update(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self._status, key):
                    setattr(self._status, key, value)

    def snapshot(self):
        with self._lock:
            data = asdict(self._status)
            data["state"] = self._status.state.value
            return data

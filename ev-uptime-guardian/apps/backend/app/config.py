from __future__ import annotations

import os
from pydantic import BaseModel, Field, field_validator

class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    GEMINI_API_KEY: str | None = None
    OSRM_BASE: str = "http://localhost:5000"
    USE_LIVE_APIS: bool = False
    DB_PATH: str = "apps/backend/app/db/demo.sqlite3"
    COLOR_BANDS: str = "10,25"  # green<=10, amber<=25 else red
    
    # Routing settings
    OSRM_TIMEOUT_S: float = 2.5
    OSRM_FALLBACK_ENABLED: bool = True
    DEFAULT_HIGHWAY_KMPH: float = 50.0
    DEFAULT_URBAN_KMPH: float = 25.0
    CORRIDOR_WIDTH_KM: float = 5.0
    CORRIDOR_TOPK: int = 4
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create Settings from environment variables."""
        def parse_bool(key: str, default: bool) -> bool:
            val = os.getenv(key, "").lower()
            return val in ("true", "1") if val else default
            
        def parse_float(key: str, default: float) -> float:
            try:
                return float(os.getenv(key, default))
            except (ValueError, TypeError):
                return default
                
        def parse_int(key: str, default: int) -> int:
            try:
                return int(os.getenv(key, default))
            except (ValueError, TypeError):
                return default
        
        return cls(
            GEMINI_API_KEY=os.getenv("GEMINI_API_KEY"),
            OSRM_BASE=os.getenv("OSRM_BASE", cls.model_fields["OSRM_BASE"].default),
            USE_LIVE_APIS=parse_bool("USE_LIVE_APIS", cls.model_fields["USE_LIVE_APIS"].default),
            DB_PATH=os.getenv("DB_PATH", cls.model_fields["DB_PATH"].default),
            COLOR_BANDS=os.getenv("COLOR_BANDS", cls.model_fields["COLOR_BANDS"].default),
            
            # Routing settings
            OSRM_TIMEOUT_S=parse_float("OSRM_TIMEOUT_S", cls.model_fields["OSRM_TIMEOUT_S"].default),
            OSRM_FALLBACK_ENABLED=parse_bool("OSRM_FALLBACK_ENABLED", cls.model_fields["OSRM_FALLBACK_ENABLED"].default),
            DEFAULT_HIGHWAY_KMPH=parse_float("DEFAULT_HIGHWAY_KMPH", cls.model_fields["DEFAULT_HIGHWAY_KMPH"].default),
            DEFAULT_URBAN_KMPH=parse_float("DEFAULT_URBAN_KMPH", cls.model_fields["DEFAULT_URBAN_KMPH"].default),
            CORRIDOR_WIDTH_KM=parse_float("CORRIDOR_WIDTH_KM", cls.model_fields["CORRIDOR_WIDTH_KM"].default),
            CORRIDOR_TOPK=parse_int("CORRIDOR_TOPK", cls.model_fields["CORRIDOR_TOPK"].default)
        )

# Global settings instance
SETTINGS = Settings.from_env()
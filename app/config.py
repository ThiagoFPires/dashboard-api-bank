import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "monitor_data.sqlite3"

class Settings:
    PROJECT_NAME: str = "Monitor de APIs Bancárias"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Intervalo de checagem automática em segundos
    CHECK_INTERVAL_SECONDS: int = 30
    
    # Limiares de latência em milissegundos
    LATENCY_NORMAL_THRESHOLD_MS: int = 600
    LATENCY_DEGRADED_THRESHOLD_MS: int = 1800
    
    # Timeout de requisição HTTP (em segundos)
    REQUEST_TIMEOUT_SECONDS: float = 6.0
    
    # Modo de operação: 'hybrid', 'simulation_only', ou 'live_only'
    MONITOR_MODE: str = os.getenv("MONITOR_MODE", "hybrid")

settings = Settings()

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from datetime import datetime, timezone, timedelta

# No ambiente Serverless da Vercel, apenas /tmp é gravável
if os.getenv("VERCEL"):
    DB_PATH = Path("/tmp/monitor_data.sqlite3")
else:
    DB_PATH = BASE_DIR / "monitor_data.sqlite3"

# Configuração Oficial do Fuso Horário de Brasília (UTC-3)
try:
    from zoneinfo import ZoneInfo
    BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    BRASILIA_TZ = timezone(timedelta(hours=-3))

def get_brasilia_now() -> datetime:
    """Retorna datetime atual com o fuso horário oficial de Brasília (America/Sao_Paulo / UTC-3)."""
    try:
        return datetime.now(BRASILIA_TZ)
    except Exception:
        return datetime.now(timezone(timedelta(hours=-3)))

class Settings:
    PROJECT_NAME: str = "Monitor de APIs Bancárias"
    VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    TIMEZONE: str = "America/Sao_Paulo"
    
    # Intervalo de checagem automática em segundos
    CHECK_INTERVAL_SECONDS: int = 60
    
    # Limiares de latência em milissegundos
    LATENCY_NORMAL_THRESHOLD_MS: int = 600
    LATENCY_DEGRADED_THRESHOLD_MS: int = 1800
    
    # Timeout de requisição HTTP (em segundos)
    REQUEST_TIMEOUT_SECONDS: float = 6.0
    
    # Modo de operação: 'hybrid', 'simulation_only', ou 'live_only'
    MONITOR_MODE: str = os.getenv("MONITOR_MODE", "hybrid")
    
    # Arquitetura Desacoplada (Serverless Vercel)
    # Tempo mínimo entre checagens externas para proteção de IP e rate limit (em segundos)
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", 60))
    # Chave de segurança para acionar cron externo
    CRON_SECRET_TOKEN: str = os.getenv("CRON_SECRET_TOKEN", "bank_monitor_cron_secret_2026")

settings = Settings()


"""
Módulo de Monitoramento e Sondas de Rede (HTTP Probing & Telemetria).
Realiza checagens assíncronas com HTTPX, medindo tempo de resposta, códigos HTTP e status.
"""

import asyncio
import time
import random
import logging
from typing import List, Dict, Any, Optional
import httpx

from app.config import settings
from app.banks_catalog import BANKS_CATALOG, get_bank_by_id
from app.database import record_check, get_setting

logger = logging.getLogger("bank_monitor")

# Perfis de latência para simulação realista
BASE_LATENCY_PROFILES = {
    "itau": {"min": 65, "max": 190, "jitter": 25},
    "sicredi": {"min": 90, "max": 240, "jitter": 30},
    "sicoob": {"min": 85, "max": 220, "jitter": 30},
    "bb": {"min": 60, "max": 180, "jitter": 20},
    "bradesco": {"min": 75, "max": 210, "jitter": 25}
}

class BankMonitorEngine:
    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def probe_single_service(self, client: httpx.AsyncClient, bank: Dict[str, Any], svc: Dict[str, Any]) -> Dict[str, Any]:
        """Testa um serviço individual de um banco via HTTP ou simulação inteligente."""
        mode = get_setting("monitor_mode", settings.MONITOR_MODE)
        b_id = bank["id"]
        s_id = svc["id"]
        url = svc["endpoint_url"]
        
        # Modo estritamente simulado
        if mode == "simulation_only":
            return self._simulate_check(bank, svc)
            
        start_time = time.perf_counter()
        try:
            # Sonda HTTP real com timeout configurado
            timeout = settings.REQUEST_TIMEOUT_SECONDS
            headers = {
                "User-Agent": "BankApiMonitor/1.0 (+https://github.com/bank-api-monitor)",
                "Accept": "application/json, text/plain, */*"
            }
            
            resp = await client.get(url, headers=headers, timeout=timeout, follow_redirects=True)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
            code = resp.status_code
            
            # Avaliação do status:
            # Em APIs financeiras, códigos 200, 201, 204 ou 400/401/403/404/405 confirmam que o gateway bancário está de pé
            if code in [200, 201, 204, 301, 302, 400, 401, 403, 404, 405]:
                if elapsed_ms > settings.LATENCY_DEGRADED_THRESHOLD_MS:
                    status = "degraded"
                    msg = f"Latência elevada ({elapsed_ms}ms)"
                else:
                    status = "operational"
                    msg = f"Gateway bancário ativo (HTTP {code})"
            elif code in [500, 502, 503, 504]:
                status = "outage"
                msg = f"Erro no servidor bancário (HTTP {code})"
            else:
                status = "degraded"
                msg = f"Código HTTP inesperado ({code})"
                
            record_check(b_id, s_id, code, elapsed_ms, status, msg, is_simulated=False)
            return {
                "bank_id": b_id,
                "service_id": s_id,
                "status": status,
                "latency_ms": elapsed_ms,
                "status_code": code,
                "message": msg
            }

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
            
            # Se for modo híbrido e o endpoint for sandbox/fictício sem DNS, usamos a telemetria simulada realista
            if mode == "hybrid":
                return self._simulate_check(bank, svc)
                
            status = "outage"
            msg = f"Falha de conexão / Timeout: {str(e)[:100]}"
            record_check(b_id, s_id, 0, elapsed_ms, status, msg, is_simulated=False)
            return {
                "bank_id": b_id,
                "service_id": s_id,
                "status": status,
                "latency_ms": elapsed_ms,
                "status_code": 0,
                "message": msg
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
            if mode == "hybrid":
                return self._simulate_check(bank, svc)
            status = "outage"
            msg = f"Erro inesperado: {str(e)[:100]}"
            record_check(b_id, s_id, 0, elapsed_ms, status, msg, is_simulated=False)
            return {
                "bank_id": b_id,
                "service_id": s_id,
                "status": status,
                "latency_ms": elapsed_ms,
                "status_code": 0,
                "message": msg
            }

    def _simulate_check(self, bank: Dict[str, Any], svc: Dict[str, Any]) -> Dict[str, Any]:
        """Gera telemetria realista para endpoints de sandbox/demonstração."""
        b_id = bank["id"]
        s_id = svc["id"]
        profile = BASE_LATENCY_PROFILES.get(b_id, {"min": 80, "max": 200, "jitter": 20})
        
        base = random.uniform(profile["min"], profile["max"])
        jitter = random.uniform(-profile["jitter"], profile["jitter"])
        latency = max(25.0, round(base + jitter, 1))
        
        # 97% das vezes operacional, 2.5% degradado, 0.5% outage pontual
        dice = random.random()
        if dice > 0.975:
            # Instabilidade temporária
            latency = round(random.uniform(270, 340), 1)
            status = "degraded"
            code = 200
            msg = "Latência ligeiramente acima do limite de SLA"
        elif dice > 0.998:
            latency = round(random.uniform(360, 420), 1)
            status = "outage"
            code = 503
            msg = "503 Service Unavailable (contingência)"
        else:
            status = "operational"
            code = 200
            msg = "Serviço operacional e responsivo"
            
        record_check(b_id, s_id, code, latency, status, msg if status != 'operational' else None, is_simulated=True)
        return {
            "bank_id": b_id,
            "service_id": s_id,
            "status": status,
            "latency_ms": latency,
            "status_code": code,
            "message": msg
        }

    async def check_all_banks(self) -> List[Dict[str, Any]]:
        """Verifica concorrentemente todos os serviços de todos os bancos."""
        tasks = []
        async with httpx.AsyncClient(verify=False) as client:
            for bank in BANKS_CATALOG:
                for svc in bank["services"]:
                    tasks.append(self.probe_single_service(client, bank, svc))
            results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    async def check_bank_services(self, bank_id: str) -> List[Dict[str, Any]]:
        """Verifica todos os serviços de um único banco."""
        bank = get_bank_by_id(bank_id)
        if not bank:
            return []
        tasks = []
        async with httpx.AsyncClient(verify=False) as client:
            for svc in bank["services"]:
                tasks.append(self.probe_single_service(client, bank, svc))
            results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    async def _background_loop(self):
        """Loop contínuo de verificação periódica."""
        logger.info("Iniciando background worker do monitor bancário...")
        while self.is_running:
            try:
                interval = int(get_setting("check_interval", settings.CHECK_INTERVAL_SECONDS))
                await self.check_all_banks()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no ciclo de monitoramento: {e}")
                await asyncio.sleep(10)

    def start_background_worker(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._background_loop())

    def stop_background_worker(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()

# Instância singleton do monitor
monitor_engine = BankMonitorEngine()

# Controle de Concorrência & Cache Lock para Arquitetura Desacoplada (Serverless / Vercel)
_last_probe_timestamp: float = 0.0
_probe_lock = asyncio.Lock()

async def run_decoupled_probe_if_needed(force: bool = False) -> bool:
    """
    Executa um ciclo de probes assíncrono em segundo plano (Background Task)
    apenas se o tempo decorrido desde a última sondagem for maior que o CACHE_TTL_SECONDS.
    Possui trava de concorrência (Mutex Lock) para que múltiplos acessos simultâneos
    não gerem requisições duplicadas aos bancos.
    """
    global _last_probe_timestamp
    now = time.time()
    ttl = settings.CACHE_TTL_SECONDS

    # 1. Checagem rápida de TTL (sem lock)
    if not force and (now - _last_probe_timestamp < ttl):
        return False

    # 2. Se já houver um probe sendo executado por outra requisição, ignora
    if _probe_lock.locked():
        return False

    async with _probe_lock:
        # Re-avaliação dentro do lock
        now = time.time()
        if not force and (now - _last_probe_timestamp < ttl):
            return False

        logger.info(f"⚡ [Desacoplado] Disparando sondagem assíncrona nos bancos (TTL: {ttl}s)...")
        try:
            await monitor_engine.check_all_banks()
            _last_probe_timestamp = time.time()
            return True
        except Exception as e:
            logger.error(f"Erro na sondagem desacoplada: {e}")
            return False


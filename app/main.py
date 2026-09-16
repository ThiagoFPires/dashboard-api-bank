"""
Aplicação Principal FastAPI para o Monitor de APIs Bancárias.
Rotas de UI (Jinja2) e endpoints de API RESTful assíncrona.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
import io
import csv

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.banks_catalog import BANKS_CATALOG, get_bank_by_id
from app.database import (
    init_db, get_latest_bank_status, get_system_summary,
    get_latency_chart_data, get_incidents, resolve_incident,
    get_setting, set_setting, simulate_bank_state
)
from app.monitor import monitor_engine
from app.models import (
    SystemSummaryModel, BankStatusModel, LatencyChartResponse,
    PingRequest, PingResponse, UpdateSettingsRequest
)

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicializar DB
    init_db()
    if not os.getenv("VERCEL"):
        monitor_engine.start_background_worker()
    yield
    # Shutdown: parar worker
    if not os.getenv("VERCEL"):
        monitor_engine.stop_background_worker()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema de Monitoramento em Tempo Real das APIs Bancárias do Itaú, Sicredi, Sicoob, Banco do Brasil e Bradesco com Indicador de Calor (Verde, Amarelo, Vermelho).",
    lifespan=lifespan
)

# Servir arquivos estáticos e templates Jinja2
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ============================================================================
# ROTAS HTML (INTERFACE WEB)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Página principal do Dashboard."""
    summary = get_system_summary()
    banks = get_latest_bank_status()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "active_page": "dashboard",
            "summary": summary,
            "banks": banks
        }
    )

@app.get("/banks/{bank_id}", response_class=HTMLResponse)
async def bank_detail_page(request: Request, bank_id: str):
    """Página de visão aprofundada de um banco individual."""
    banks = get_latest_bank_status()
    selected_bank = None
    for b in banks:
        if b["bank_id"] == bank_id:
            selected_bank = b
            break
            
    if not selected_bank:
        raise HTTPException(status_code=404, detail="Banco não encontrado no catálogo.")
        
    return templates.TemplateResponse(
        request=request,
        name="bank_detail.html",
        context={
            "active_page": "banks",
            "bank": selected_bank
        }
    )

@app.get("/incidents", response_class=HTMLResponse)
async def incidents_page(request: Request):
    """Página de gestão e histórico de incidentes."""
    incidents = get_incidents()
    return templates.TemplateResponse(
        request=request,
        name="incidents.html",
        context={
            "active_page": "incidents",
            "incidents": incidents
        }
    )

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Página de configurações e parâmetros do monitor."""
    current_mode = get_setting("monitor_mode", settings.MONITOR_MODE)
    check_interval = get_setting("check_interval", settings.CHECK_INTERVAL_SECONDS)
    latency_normal = get_setting("latency_normal_threshold", settings.LATENCY_NORMAL_THRESHOLD_MS)
    latency_degraded = get_setting("latency_degraded_threshold", settings.LATENCY_DEGRADED_THRESHOLD_MS)
    webhook_url = get_setting("webhook_url", "")
    
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "active_page": "settings",
            "current_mode": current_mode,
            "check_interval": check_interval,
            "latency_normal": latency_normal,
            "latency_degraded": latency_degraded,
            "webhook_url": webhook_url
        }
    )

# ============================================================================
# ENDPOINTS REST API
# ============================================================================

@app.get("/api/summary", response_model=SystemSummaryModel)
async def api_summary():
    """Retorna métricas executivas consolidadas (KPIs)."""
    return get_system_summary()

@app.get("/api/status")
async def api_status():
    """Retorna o status em tempo real de todos os 5 bancos e seus serviços."""
    return get_latest_bank_status()

@app.get("/api/banks/{bank_id}")
async def api_bank_detail(bank_id: str):
    """Retorna o status detalhado de um banco específico."""
    banks = get_latest_bank_status()
    for b in banks:
        if b["bank_id"] == bank_id:
            return b
    raise HTTPException(status_code=404, detail="Banco não encontrado")

@app.post("/api/banks/{bank_id}/simulate")
async def api_simulate_bank(bank_id: str, payload: dict):
    """Permite simular imediatamente um estado (outage=vermelho, degraded=amarelo, operational=verde)."""
    state = payload.get("state", "operational")
    simulate_bank_state(bank_id, state)
    return {"message": f"Estado de {bank_id} alterado para {state}", "bank_id": bank_id, "state": state}

@app.get("/api/chart-data")
async def api_chart_data():
    """Retorna séries temporais de latência dos bancos para o Chart.js."""
    return get_latency_chart_data(limit_per_bank=20)

@app.post("/api/check-now")
async def api_check_now(payload: PingRequest = None):
    """Dispara uma verificação imediata para todos os bancos ou banco específico."""
    bank_id = payload.bank_id if payload else None
    
    if bank_id:
        results = await monitor_engine.check_bank_services(bank_id)
    else:
        results = await monitor_engine.check_all_banks()
        
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "checked_count": len(results),
        "results": results
    }

@app.get("/api/incidents")
async def api_get_incidents(status: str = None):
    """Retorna a lista de incidentes registrados."""
    return get_incidents(status_filter=status)

@app.post("/api/incidents/{incident_id}/resolve")
async def api_resolve_incident(incident_id: int):
    """Marca um incidente como resolvido."""
    resolve_incident(incident_id)
    return {"message": "Incidente resolvido com sucesso", "incident_id": incident_id}

@app.get("/api/settings")
async def api_get_settings():
    """Retorna as configurações atuais do monitor."""
    return {
        "monitor_mode": get_setting("monitor_mode", settings.MONITOR_MODE),
        "check_interval": get_setting("check_interval", settings.CHECK_INTERVAL_SECONDS),
        "latency_normal_threshold": get_setting("latency_normal_threshold", settings.LATENCY_NORMAL_THRESHOLD_MS),
        "latency_degraded_threshold": get_setting("latency_degraded_threshold", settings.LATENCY_DEGRADED_THRESHOLD_MS),
        "webhook_url": get_setting("webhook_url", "")
    }

@app.post("/api/settings")
async def api_update_settings(req: UpdateSettingsRequest):
    """Atualiza as configurações de monitoramento."""
    if req.monitor_mode is not None:
        set_setting("monitor_mode", req.monitor_mode)
    if req.check_interval is not None:
        set_setting("check_interval", req.check_interval)
    if req.latency_normal_threshold is not None:
        set_setting("latency_normal_threshold", req.latency_normal_threshold)
    if req.latency_degraded_threshold is not None:
        set_setting("latency_degraded_threshold", req.latency_degraded_threshold)
    if req.webhook_url is not None:
        set_setting("webhook_url", req.webhook_url)
    return {"status": "success", "message": "Configurações atualizadas"}

@app.get("/api/export/csv")
async def export_csv():
    """Exporta o status atual dos serviços em formato CSV."""
    banks = get_latest_bank_status()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Banco", "Codigo", "Servico", "Endpoint", "Status", "Latencia_ms", "Ultimo_Update"])
    
    for bank in banks:
        for svc in bank["services"]:
            writer.writerow([
                bank["name"],
                bank["code"],
                svc["name"],
                svc["endpoint_url"],
                svc["status"],
                svc["latency_ms"],
                svc["last_update"]
            ])
            
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_apis_bancarias.csv"}
    )

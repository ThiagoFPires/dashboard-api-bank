"""
Modelos de dados e schemas Pydantic para a API REST.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ServiceStatusModel(BaseModel):
    id: str
    name: str
    description: str
    importance: str
    status: str
    latency_ms: float
    status_code: Optional[int] = None
    last_update: str
    error_message: Optional[str] = None
    endpoint_url: str

class BankStatusModel(BaseModel):
    bank_id: str
    name: str
    short_name: str
    code: str
    color: str
    bg_soft: str
    border_color: str
    text_color: str
    badge_color: str
    icon: str
    tagline: str
    developer_portal: str
    status: str
    avg_latency_ms: float
    uptime_24h: float
    blocks: List[str]
    services: List[ServiceStatusModel]

class SystemSummaryModel(BaseModel):
    global_status: str
    global_message: str
    operational_banks: int
    degraded_banks: int
    outage_banks: int
    total_banks: int
    avg_latency_ms: float
    overall_uptime: float
    active_incidents: int
    total_checks: int
    last_checked_at: str

class LatencyChartDataset(BaseModel):
    bank_id: str
    label: str
    color: str
    data: List[Optional[float]]

class LatencyChartResponse(BaseModel):
    labels: List[str]
    datasets: List[LatencyChartDataset]

class IncidentModel(BaseModel):
    id: int
    bank_id: str
    service_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    started_at: str
    resolved_at: Optional[str] = None

class PingRequest(BaseModel):
    bank_id: Optional[str] = None
    service_id: Optional[str] = None

class PingResultItem(BaseModel):
    bank_id: str
    service_id: str
    status: str
    latency_ms: float
    status_code: Optional[int]
    message: str

class PingResponse(BaseModel):
    timestamp: str
    checked_count: int
    results: List[PingResultItem]

class UpdateSettingsRequest(BaseModel):
    check_interval: Optional[int] = Field(None, ge=5, le=3600)
    latency_normal_threshold: Optional[int] = Field(None, ge=100, le=5000)
    latency_degraded_threshold: Optional[int] = Field(None, ge=200, le=10000)
    monitor_mode: Optional[str] = None
    webhook_url: Optional[str] = None

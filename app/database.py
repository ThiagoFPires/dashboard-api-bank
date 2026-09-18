"""
Módulo de Banco de Dados SQLite para o Monitor de APIs Bancárias.
Gerencia histórico de checagens, incidentes e métricas de disponibilidade.
Indicadores de calor em cores sólidas:
  - Verde (#22c55e): Bom estado (Operacional)
  - Amarelo (#eab308): Oscilando (Lentidão / Degradação)
  - Vermelho (#ef4444): Caiu (Indisponível / Outage)
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.config import DB_PATH, get_brasilia_now
from app.banks_catalog import BANKS_CATALOG

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de checagens de serviços
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id TEXT NOT NULL,
            service_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status_code INTEGER,
            latency_ms REAL NOT NULL,
            status TEXT NOT NULL, /* operational, degraded, outage */
            error_message TEXT,
            is_simulated INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_checks_bank_ts 
        ON service_checks (bank_id, timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_checks_svc_ts 
        ON service_checks (service_id, timestamp)
    """)
    
    # Tabela de incidentes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id TEXT NOT NULL,
            service_id TEXT,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT NOT NULL, /* low, medium, high, critical */
            status TEXT NOT NULL, /* active, investigating, resolved */
            started_at TEXT NOT NULL,
            resolved_at TEXT
        )
    """)
    
    # Tabela de configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    conn.commit()
    
    # Se o banco tiver poucas checagens, repovoar com demonstração visual rica de calor
    cursor.execute("SELECT COUNT(*) as count FROM service_checks")
    row = cursor.fetchone()
    if row["count"] < 50:
        seed_initial_history(conn)
        
    conn.close()

def seed_initial_history(conn: sqlite3.Connection):
    """Alimenta o histórico com dados realistas incluindo verde (bom estado), amarelo (oscilação) e vermelho (queda)."""
    cursor = conn.cursor()
    now = get_brasilia_now()
    
    bank_latency_profile = {
        "itau": (85, 150),
        "sicredi": (110, 180),
        "sicoob": (95, 165),
        "bb": (70, 135),
        "bradesco": (90, 160)
    }
    
    # Criar 70 pontos recentes por banco (espaçados a cada 2 minutos) para curva contínua e rica
    for i in range(70, -1, -1):
        check_time = (now - timedelta(minutes=i * 2)).strftime("%Y-%m-%d %H:%M:%S")
        
        for bank in BANKS_CATALOG:
            b_id = bank["id"]
            min_l, max_l = bank_latency_profile.get(b_id, (90, 160))
            
            for svc in bank["services"]:
                s_id = svc["id"]
                
                # Simular padrão de calor variado com variações de latência realistas:
                if (b_id in ["itau", "sicredi"] and i in [14, 15]) or (b_id == "bradesco" and i in [6, 7]):
                    # Amarelo: Oscilando com leve pico de latência
                    latency = random.uniform(270, 340)
                    status = "degraded"
                    code = 200
                    err = "Tempo de resposta acima do SLA"
                elif (b_id == "sicoob" and i in [32, 33]) or (b_id == "bb" and i == 45):
                    # Vermelho: Falha pontual
                    latency = random.uniform(360, 420)
                    status = "outage"
                    code = 503
                    err = "503 Service Unavailable (Falha de Conexão)"
                else:
                    # Verde: Bom estado
                    latency = random.uniform(min_l, max_l)
                    status = "operational"
                    code = 200
                    err = None
                    
                cursor.execute("""
                    INSERT INTO service_checks 
                    (bank_id, service_id, timestamp, status_code, latency_ms, status, error_message, is_simulated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (b_id, s_id, check_time, code, round(latency, 1), status, err))
    
    cursor.execute("""
        INSERT INTO incidents (bank_id, service_id, title, description, severity, status, started_at, resolved_at)
        VALUES 
        ('sicoob', 'sicoob-pix', 'Instabilidade temporária no gateway Pix', 'Detectada falha de resposta HTTP 503 no gateway Pix. Restabelecido em 10 minutos.', 'critical', 'resolved', ?, ?),
        ('itau', 'itau-boletos', 'Oscilação de latência na emissão de boletos', 'Latência média superou 950ms momentaneamente durante pico operacional.', 'medium', 'resolved', ?, ?)
    """, (
        (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        (now - timedelta(hours=1, minutes=50)).strftime("%Y-%m-%d %H:%M:%S"),
        (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
        (now - timedelta(hours=3, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")
    ))
    
    conn.commit()

def record_check(bank_id: str, service_id: str, status_code: Optional[int], 
                 latency_ms: float, status: str, error_message: Optional[str] = None, 
                 is_simulated: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = get_brasilia_now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO service_checks 
        (bank_id, service_id, timestamp, status_code, latency_ms, status, error_message, is_simulated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (bank_id, service_id, now_str, status_code, round(latency_ms, 1), status, error_message, 1 if is_simulated else 0))
    
    if status == "outage":
        cursor.execute("""
            SELECT id FROM incidents 
            WHERE bank_id = ? AND service_id = ? AND status = 'active'
        """, (bank_id, service_id))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO incidents (bank_id, service_id, title, description, severity, status, started_at)
                VALUES (?, ?, ?, ?, 'critical', 'active', ?)
            """, (
                bank_id, service_id,
                f"API Indisponível (Queda): {service_id}",
                f"Falha de resposta: {error_message or 'HTTP 5xx ou Timeout'}",
                now_str
            ))
    elif status == "operational":
        cursor.execute("""
            UPDATE incidents 
            SET status = 'resolved', resolved_at = ?
            WHERE bank_id = ? AND service_id = ? AND status = 'active'
        """, (now_str, bank_id, service_id))
        
    conn.commit()
    conn.close()

def get_latest_bank_status() -> List[Dict[str, Any]]:
    """Retorna o status mais recente consolidado de cada um dos 5 bancos com mapa de calor detalhado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    for bank in BANKS_CATALOG:
        b_id = bank["id"]
        
        services_status = []
        bank_statuses = []
        latencies = []
        
        for svc in bank["services"]:
            s_id = svc["id"]
            cursor.execute("""
                SELECT * FROM service_checks 
                WHERE bank_id = ? AND service_id = ? 
                ORDER BY id DESC LIMIT 1
            """, (b_id, s_id))
            row = cursor.fetchone()
            
            if row:
                svc_status = row["status"]
                svc_lat = row["latency_ms"]
                svc_code = row["status_code"]
                last_update = row["timestamp"]
                err = row["error_message"]
            else:
                svc_status = "operational"
                svc_lat = 120.0
                svc_code = 200
                last_update = get_brasilia_now().strftime("%Y-%m-%d %H:%M:%S")
                err = None
                
            services_status.append({
                "id": s_id,
                "name": svc["name"],
                "description": svc["description"],
                "importance": svc["importance"],
                "status": svc_status,
                "latency_ms": svc_lat,
                "status_code": svc_code,
                "last_update": last_update,
                "error_message": err,
                "endpoint_url": svc["endpoint_url"]
            })
            bank_statuses.append(svc_status)
            latencies.append(svc_lat)
            
        if "outage" in bank_statuses:
            overall_status = "outage"
        elif "degraded" in bank_statuses:
            overall_status = "degraded"
        else:
            overall_status = "operational"
            
        avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
        
        cutoff_24h = (get_brasilia_now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status != 'outage' THEN 1 ELSE 0 END) as successful
            FROM service_checks 
            WHERE bank_id = ? AND timestamp >= ?
        """, (b_id, cutoff_24h))
        stats = cursor.fetchone()
        
        total = stats["total"] if stats and stats["total"] else 1
        successful = stats["successful"] if stats and stats["successful"] else 1
        uptime_pct = round((successful / total) * 100, 2) if total > 0 else 100.0
        
        # Histórico recente para o INDICADOR DE CALOR (1 bloco = 1 minuto exato no tempo)
        num_minutes = 24
        now_dt = get_brasilia_now()
        cutoff_minutes = (now_dt - timedelta(minutes=num_minutes)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            SELECT 
                strftime('%Y-%m-%d %H:%M', timestamp) as minute_key,
                CASE 
                    WHEN SUM(CASE WHEN status = 'outage' THEN 1 ELSE 0 END) > 0 THEN 'outage'
                    WHEN SUM(CASE WHEN status = 'degraded' THEN 1 ELSE 0 END) > 0 THEN 'degraded'
                    ELSE 'operational'
                END as minute_status,
                ROUND(AVG(latency_ms), 1) as avg_lat
            FROM service_checks
            WHERE bank_id = ? AND timestamp >= ?
            GROUP BY minute_key
        """, (b_id, cutoff_minutes))
        
        minute_map = {row["minute_key"]: (row["minute_status"], row["avg_lat"]) for row in cursor.fetchall()}
        
        heat_blocks = []
        for i in range(num_minutes - 1, -1, -1):
            m_dt = now_dt - timedelta(minutes=i)
            m_key = m_dt.strftime("%Y-%m-%d %H:%M")
            m_time = m_dt.strftime("%H:%M")
            
            if m_key in minute_map:
                st, lat = minute_map[m_key]
            else:
                st, lat = "operational", 120.0
                
            if st == "operational":
                color = "#22c55e" # Verde: Bom estado
                label = "Bom Estado"
                css_class = "heat-green"
            elif st == "degraded":
                color = "#eab308" # Amarelo: Oscilando
                label = "Oscilando"
                css_class = "heat-yellow"
            else:
                color = "#ef4444" # Vermelho: Caiu
                label = "Caiu (Indisponível)"
                css_class = "heat-red"
                
            heat_blocks.append({
                "status": st,
                "latency_ms": lat,
                "time": m_time,
                "color": color,
                "label": label,
                "css_class": css_class
            })

            
        results.append({
            "bank_id": b_id,
            "name": bank["name"],
            "short_name": bank["short_name"],
            "code": bank["code"],
            "color": bank["color"],
            "logo_url": bank.get("logo_url", ""),
            "bg_soft": bank["bg_soft"],
            "border_color": bank["border_color"],
            "text_color": bank["text_color"],
            "badge_color": bank["badge_color"],
            "icon": bank["icon"],
            "tagline": bank["tagline"],
            "developer_portal": bank["developer_portal"],
            "status": overall_status,
            "avg_latency_ms": avg_latency,
            "uptime_24h": uptime_pct,
            "blocks": heat_blocks,
            "services": services_status
        })
        
    conn.close()
    return results

def get_system_summary() -> Dict[str, Any]:
    """Retorna o sumário executivo com KPIs gerais."""
    banks = get_latest_bank_status()
    total_banks = len(banks)
    
    operational_banks = sum(1 for b in banks if b["status"] == "operational")
    degraded_banks = sum(1 for b in banks if b["status"] == "degraded")
    outage_banks = sum(1 for b in banks if b["status"] == "outage")
    
    avg_latency = round(sum(b["avg_latency_ms"] for b in banks) / total_banks, 1) if total_banks else 0.0
    overall_uptime = round(sum(b["uptime_24h"] for b in banks) / total_banks, 2) if total_banks else 100.0
    
    if outage_banks > 0:
        global_status = "outage"
        global_message = f"{outage_banks} banco(s) com APIs fora do ar (Caiu)"
    elif degraded_banks > 0:
        global_status = "degraded"
        global_message = f"{degraded_banks} banco(s) oscilando com lentidão"
    else:
        global_status = "operational"
        global_message = "Todos os bancos operando em bom estado"
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM incidents WHERE status = 'active'")
    active_incidents = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM service_checks")
    total_checks = cursor.fetchone()["count"]
    conn.close()
    
    return {
        "global_status": global_status,
        "global_message": global_message,
        "operational_banks": operational_banks,
        "degraded_banks": degraded_banks,
        "outage_banks": outage_banks,
        "total_banks": total_banks,
        "avg_latency_ms": avg_latency,
        "overall_uptime": overall_uptime,
        "active_incidents": active_incidents,
        "total_checks": total_checks,
        "last_checked_at": get_brasilia_now().strftime("%H:%M:%S")
    }

def get_latency_chart_data(limit_per_bank: int = 100) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    datasets = []
    cutoff = (get_brasilia_now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        SELECT strftime('%H:%M', timestamp) as time_label, MAX(timestamp) as max_ts
        FROM service_checks
        WHERE timestamp >= ?
        GROUP BY time_label
        ORDER BY max_ts DESC
        LIMIT ?
    """, (cutoff, limit_per_bank))
    time_rows = list(reversed(cursor.fetchall()))
    labels = [r["time_label"] for r in time_rows]
    
    if not labels:
        conn.close()
        return {"labels": [], "datasets": []}

    placeholders = ",".join(["?"] * len(labels))
    cursor.execute(f"""
        SELECT 
            bank_id,
            strftime('%H:%M', timestamp) as time_label,
            ROUND(AVG(latency_ms), 1) as avg_lat
        FROM service_checks
        WHERE timestamp >= ? AND strftime('%H:%M', timestamp) IN ({placeholders})
        GROUP BY bank_id, time_label
    """, [cutoff] + labels)
    
    data_map = {(r["bank_id"], r["time_label"]): r["avg_lat"] for r in cursor.fetchall()}
    
    for bank in BANKS_CATALOG:
        b_id = bank["id"]
        points = [data_map.get((b_id, t)) for t in labels]
        datasets.append({
            "bank_id": b_id,
            "label": bank["short_name"],
            "color": bank["color"],
            "data": points
        })
        
    conn.close()
    return {
        "labels": labels,
        "datasets": datasets
    }

def get_incidents(status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status_filter:
        cursor.execute("""
            SELECT * FROM incidents 
            WHERE status = ? 
            ORDER BY started_at DESC LIMIT ?
        """, (status_filter, limit))
    else:
        cursor.execute("""
            SELECT * FROM incidents 
            ORDER BY CASE WHEN status = 'active' THEN 0 ELSE 1 END, started_at DESC 
            LIMIT ?
        """, (limit,))
        
    rows = cursor.fetchall()
    incidents = [dict(r) for r in rows]
    conn.close()
    return incidents

def resolve_incident(incident_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = get_brasilia_now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE incidents 
        SET status = 'resolved', resolved_at = ?
        WHERE id = ?
    """, (now_str, incident_id))
    conn.commit()
    conn.close()

def simulate_bank_state(bank_id: str, state: str):
    """Permite testar e simular imediatamente o estado de um banco (caiu / oscilando / bom estado)."""
    bank = next((b for b in BANKS_CATALOG if b["id"] == bank_id), None)
    if not bank:
        return
        
    for svc in bank["services"]:
        s_id = svc["id"]
        if state == "outage": # Vermelho: Caiu
            record_check(bank_id, s_id, 503, 3200.0, "outage", "Falha de Conexão (503 Service Unavailable)", is_simulated=True)
        elif state == "degraded": # Amarelo: Oscilando
            record_check(bank_id, s_id, 200, 1450.0, "degraded", "Tempo de resposta acima do normal (Oscilação)", is_simulated=True)
        else: # Verde: Bom Estado
            record_check(bank_id, s_id, 200, 95.0, "operational", "Serviço Operacional em Bom Estado", is_simulated=True)

def get_setting(key: str, default: Any = None) -> Any:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]
    return default

def set_setting(key: str, value: Any):
    conn = get_db_connection()
    cursor = conn.cursor()
    val_str = json.dumps(value) if not isinstance(value, str) else value
    cursor.execute("""
        INSERT INTO settings (key, value) 
        VALUES (?, ?) 
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, val_str))
    conn.commit()
    conn.close()

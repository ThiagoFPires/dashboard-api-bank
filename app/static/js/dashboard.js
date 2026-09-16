/**
 * Bank API Monitor - Dashboard Interativo
 * Indicador de calor em cores sólidas:
 *   - Verde (#22c55e): Bom Estado
 *   - Amarelo (#eab308): Oscilando
 *   - Vermelho (#ef4444): Caiu
 */

let latencyChart = null;
let isAutoRefreshActive = true;
let refreshIntervalTimer = null;

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
    initChart();
    loadDashboardData();
    setupAutoRefresh();
});

// Estilos monocromáticos sólidos de linha para os 5 bancos
const MONO_BANK_STYLES = {
    "itau": { color: "#ffffff", dash: [] },
    "sicredi": { color: "#e4e4e7", dash: [6, 4] },
    "sicoob": { color: "#a1a1aa", dash: [] },
    "bb": { color: "#71717a", dash: [4, 4] },
    "bradesco": { color: "#52525b", dash: [2, 2] }
};

// Inicialização do Gráfico Chart.js
function initChart() {
    const ctx = document.getElementById("latencyChart");
    if (!ctx) return;

    const gridColor = "rgba(255, 255, 255, 0.08)";
    const textColor = "#a1a1aa";

    latencyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        color: "#ffffff",
                        usePointStyle: true,
                        boxWidth: 8,
                        font: { size: 11, family: "Inter, sans-serif", weight: "bold" }
                    }
                },
                tooltip: {
                    backgroundColor: "#000000",
                    titleColor: "#ffffff",
                    bodyColor: "#d4d4d8",
                    borderColor: "#3f3f46",
                    borderWidth: 1,
                    padding: 10,
                    cornerRadius: 4,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} ms`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 11, family: "JetBrains Mono, monospace" } }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: { 
                        color: textColor, 
                        font: { size: 11, family: "JetBrains Mono, monospace" },
                        callback: function(value) { return value + " ms"; }
                    },
                    suggestedMin: 0
                }
            }
        }
    });

    loadChartData();
}

// Carregar Dados do Gráfico
async function loadChartData() {
    if (!latencyChart) return;
    try {
        const response = await fetch("/api/chart-data");
        if (!response.ok) return;
        const data = await response.json();

        latencyChart.data.labels = data.labels;
        latencyChart.data.datasets = data.datasets.map(ds => {
            const style = MONO_BANK_STYLES[ds.bank_id] || { color: "#a1a1aa", dash: [] };
            return {
                label: ds.label,
                data: ds.data,
                borderColor: style.color,
                borderDash: style.dash,
                borderWidth: 2,
                pointRadius: 2.5,
                pointHoverRadius: 5,
                pointBackgroundColor: style.color,
                tension: 0.2,
                fill: false
            };
        });
        latencyChart.update();
    } catch (err) {
        console.error("Erro ao carregar dados do gráfico:", err);
    }
}

// Carregar Dados Consolidados do Dashboard
async function loadDashboardData() {
    try {
        const [summaryRes, banksRes] = await Promise.all([
            fetch("/api/summary"),
            fetch("/api/status")
        ]);

        if (summaryRes.ok) {
            const summary = await summaryRes.json();
            updateSummaryUI(summary);
        }

        if (banksRes.ok) {
            const banks = await banksRes.json();
            updateBanksUI(banks);
        }
    } catch (err) {
        console.error("Erro na atualização do dashboard:", err);
    }
}

// Atualizar Elementos de Resumo / KPIs
function updateSummaryUI(summary) {
    const statusPill = document.getElementById("globalStatusPill");
    const statusText = document.getElementById("globalStatusText");
    const avgLat = document.getElementById("kpiAvgLatency");
    const uptime = document.getElementById("kpiOverallUptime");
    const activeIncidents = document.getElementById("kpiActiveIncidents");
    const totalChecks = document.getElementById("kpiTotalChecks");
    const lastChecked = document.getElementById("kpiLastChecked");

    if (statusText) statusText.innerText = summary.global_message;
    if (avgLat) avgLat.innerText = `${summary.avg_latency_ms} ms`;
    if (uptime) uptime.innerText = `${summary.overall_uptime}%`;
    if (activeIncidents) activeIncidents.innerText = summary.active_incidents;
    if (totalChecks) totalChecks.innerText = summary.total_checks.toLocaleString();
    if (lastChecked) lastChecked.innerText = `Atualizado às ${summary.last_checked_at}`;

    if (statusPill) {
        if (summary.global_status === "operational") {
            statusPill.className = "px-3 py-1 rounded text-xs font-semibold flex items-center gap-2 border bg-zinc-950 text-emerald-400 border-emerald-500/40";
            statusPill.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-[#22c55e]"></span> Bom Estado`;
        } else if (summary.global_status === "degraded") {
            statusPill.className = "px-3 py-1 rounded text-xs font-semibold flex items-center gap-2 border bg-zinc-950 text-yellow-400 border-yellow-500/40";
            statusPill.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-[#eab308]"></span> Oscilando`;
        } else {
            statusPill.className = "px-3 py-1 rounded text-xs font-semibold flex items-center gap-2 border bg-zinc-950 text-red-400 border-red-500/40";
            statusPill.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-[#ef4444]"></span> Caiu (Fora)`;
        }
    }
}

// Atualizar Cards dos Bancos com Indicador de Calor
function updateBanksUI(banks) {
    banks.forEach(bank => {
        const cardLat = document.getElementById(`bank-lat-${bank.bank_id}`);
        const cardBadge = document.getElementById(`bank-badge-${bank.bank_id}`);
        const cardUptime = document.getElementById(`bank-uptime-${bank.bank_id}`);
        const cardStripe = document.getElementById(`stripe-${bank.bank_id}`);
        const heatBar = document.getElementById(`heat-bar-${bank.bank_id}`);
        
        if (cardLat) cardLat.innerText = `${bank.avg_latency_ms} ms`;
        if (cardUptime) cardUptime.innerText = `${bank.uptime_24h}% SLA`;

        // Atualizar listra superior sólida do card
        if (cardStripe) {
            cardStripe.className = `h-1 w-full ${bank.status === 'operational' ? 'bg-[#22c55e]' : (bank.status === 'degraded' ? 'bg-[#eab308]' : 'bg-[#ef4444]')}`;
        }

        // Atualizar Badge de Status
        if (cardBadge) {
            let badgeHtml = "";
            if (bank.status === "operational") {
                badgeHtml = `<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-zinc-950 text-emerald-400 border border-emerald-500/40"><span class="w-2 h-2 rounded-full bg-[#22c55e]"></span> Bom Estado</span>`;
            } else if (bank.status === "degraded") {
                badgeHtml = `<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-zinc-950 text-yellow-400 border border-yellow-500/40"><span class="w-2 h-2 rounded-full bg-[#eab308]"></span> Oscilando</span>`;
            } else {
                badgeHtml = `<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-zinc-950 text-red-400 border border-red-500/40"><span class="w-2 h-2 rounded-full bg-[#ef4444]"></span> Caiu</span>`;
            }
            cardBadge.innerHTML = badgeHtml;
        }

        // Atualizar Barra de Calor com os blocos verde, amarelo e vermelho
        if (heatBar && bank.blocks) {
            heatBar.innerHTML = bank.blocks.map(b => {
                let css = b.css_class || (b.status === 'operational' ? 'heat-green' : (b.status === 'degraded' ? 'heat-yellow' : 'heat-red'));
                let label = b.label || (b.status === 'operational' ? 'Bom Estado' : (b.status === 'degraded' ? 'Oscilando' : 'Caiu'));
                let lat = b.latency_ms || 100;
                let t = b.time || '--:--';
                return `<div class="heat-block ${css}" title="${t} • ${label} (${lat}ms)"></div>`;
            }).join("");
        }

        // Atualizar mini-linhas de serviços dentro do card
        bank.services.forEach(svc => {
            const svcStatusEl = document.getElementById(`svc-status-${svc.id}`);
            const svcLatEl = document.getElementById(`svc-lat-${svc.id}`);
            if (svcStatusEl) {
                let bgClass = svc.status === 'operational' ? 'bg-[#22c55e]' : (svc.status === 'degraded' ? 'bg-[#eab308]' : 'bg-[#ef4444]');
                svcStatusEl.className = `w-2 h-2 rounded-full ${bgClass}`;
            }
            if (svcLatEl) {
                svcLatEl.innerText = `${svc.latency_ms}ms`;
            }
        });
    });
}

// Disparo Manual de Checagem Geral
async function triggerCheckAll() {
    const btn = document.getElementById("btnCheckAll");
    const icon = document.getElementById("checkAllIcon");
    
    if (btn) btn.disabled = true;
    if (icon) icon.classList.add("animate-spin");
    
    showToast("Disparando testes em tempo real para os 5 bancos...", "info");

    try {
        const res = await fetch("/api/check-now", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });

        if (res.ok) {
            const result = await res.json();
            showToast(`Concluído! ${result.checked_count} serviços testados com sucesso.`, "success");
            await loadDashboardData();
            await loadChartData();
        } else {
            showToast("Falha ao executar checagens.", "error");
        }
    } catch (err) {
        showToast("Erro na comunicação com o servidor.", "error");
    } finally {
        if (btn) btn.disabled = false;
        if (icon) icon.classList.remove("animate-spin");
    }
}

// Disparo Manual para um Banco Específico
async function triggerCheckBank(bankId, event) {
    if (event) event.stopPropagation();
    const btn = document.getElementById(`btn-ping-${bankId}`);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<svg class="animate-spin h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>`;
    }

    try {
        const res = await fetch("/api/check-now", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ bank_id: bankId })
        });
        if (res.ok) {
            showToast(`Banco ${bankId.toUpperCase()} testado com sucesso!`, "success");
            await loadDashboardData();
            await loadChartData();
        }
    } catch (e) {
        showToast("Erro ao testar banco.", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg class="w-3.5 h-3.5 text-zinc-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Ping`;
        }
    }
}

// Auto Refresh em Background
function setupAutoRefresh() {
    refreshIntervalTimer = setInterval(() => {
        if (isAutoRefreshActive) {
            loadDashboardData();
            loadChartData();
        }
    }, 15000);
}

function toggleAutoRefresh() {
    isAutoRefreshActive = !isAutoRefreshActive;
    const toggleBtn = document.getElementById("autoRefreshToggle");
    if (toggleBtn) {
        if (isAutoRefreshActive) {
            toggleBtn.className = "px-3 py-1.5 rounded text-xs font-semibold border bg-zinc-800 text-white border-zinc-600 transition-all flex items-center gap-2";
            showToast("Atualização automática ativada (15s)", "info");
        } else {
            toggleBtn.className = "px-3 py-1.5 rounded text-xs font-semibold border bg-zinc-950 text-zinc-500 border-zinc-800 transition-all flex items-center gap-2";
            showToast("Atualização automática pausada", "warning");
        }
    }
}

// Sistema de Notificações Toast
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    let bg = "bg-zinc-900 text-white border-zinc-700";
    if (type === "success") bg = "bg-zinc-900 text-emerald-400 border-emerald-500/50";
    if (type === "warning") bg = "bg-zinc-900 text-yellow-400 border-yellow-500/50";
    if (type === "error") bg = "bg-zinc-950 text-red-400 border-red-500/50";

    toast.className = `flex items-center gap-2.5 px-4 py-2.5 rounded text-xs font-medium border shadow-2xl transition-all duration-200 transform translate-y-2 opacity-0 ${bg}`;
    toast.innerHTML = `<span>${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove("translate-y-2", "opacity-0");
    }, 20);

    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => toast.remove(), 250);
    }, 3500);
}

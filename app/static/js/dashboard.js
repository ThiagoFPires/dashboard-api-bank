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
    initTheme();
    initChart();
    loadDashboardData();
    setupAutoRefresh();
});

// Cores oficiais dos bancos para o gráfico de latência
const OFFICIAL_BANK_COLORS = {
    "itau": "#EC7000",      // Laranja Itaú
    "sicredi": "#00933B",   // Verde Sicredi
    "sicoob": "#00AE9D",    // Turquesa Sicoob
    "bb": "#FEE100",        // Amarelo Ouro BB
    "bradesco": "#CC092F"   // Vermelho Bradesco
};

let currentChartFilter = "all";

// Controle de Tema (Claro / Escuro)
function initTheme() {
    const isLight = document.documentElement.classList.contains("light");
    updateThemeIcons(isLight ? "light" : "dark");
}

function updateThemeIcons(theme) {
    const sunIcon = document.getElementById("sunIcon");
    const moonIcon = document.getElementById("moonIcon");
    if (sunIcon && moonIcon) {
        if (theme === "light") {
            sunIcon.classList.add("hidden");
            moonIcon.classList.remove("hidden");
        } else {
            sunIcon.classList.remove("hidden");
            moonIcon.classList.add("hidden");
        }
    }
}

function toggleTheme() {
    const isDark = document.documentElement.classList.contains("dark");
    if (isDark) {
        document.documentElement.classList.remove("dark");
        document.documentElement.classList.add("light");
        localStorage.setItem("bank_monitor_theme", "light");
        updateThemeIcons("light");
        showToast("Tema claro ativado", "info");
    } else {
        document.documentElement.classList.remove("light");
        document.documentElement.classList.add("dark");
        localStorage.setItem("bank_monitor_theme", "dark");
        updateThemeIcons("dark");
        showToast("Tema escuro ativado", "info");
    }
    updateChartTheme();
    applyChartFilter();
}

function updateChartTheme() {
    if (!latencyChart) return;
    const isDark = document.documentElement.classList.contains("dark");
    const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)";
    const textColor = isDark ? "#a1a1aa" : "#64748b";

    if (latencyChart.options.scales.x) {
        latencyChart.options.scales.x.grid.color = gridColor;
        latencyChart.options.scales.x.ticks.color = textColor;
    }
    if (latencyChart.options.scales.y) {
        latencyChart.options.scales.y.grid.color = gridColor;
        latencyChart.options.scales.y.ticks.color = textColor;
    }

    if (latencyChart.options.plugins && latencyChart.options.plugins.tooltip) {
        latencyChart.options.plugins.tooltip.backgroundColor = isDark ? "#09090b" : "#ffffff";
        latencyChart.options.plugins.tooltip.titleColor = isDark ? "#ffffff" : "#0f172a";
        latencyChart.options.plugins.tooltip.bodyColor = isDark ? "#d4d4d8" : "#334155";
        latencyChart.options.plugins.tooltip.borderColor = isDark ? "#27272a" : "#e2e8f0";
    }

    latencyChart.update();
}

// Controle de Paginação e Arrastar no Histórico do Gráfico
const DEFAULT_VISIBLE_POINTS = 20;
let userHasInteractedWithChart = false;

// Resetar Pan e Zoom do Gráfico para os dados mais recentes
function resetChartZoom() {
    if (!latencyChart) return;
    if (typeof latencyChart.resetZoom === "function") {
        latencyChart.resetZoom();
    }
    userHasInteractedWithChart = false;
    const total = latencyChart.data.labels ? latencyChart.data.labels.length : 0;
    if (total > DEFAULT_VISIBLE_POINTS) {
        latencyChart.options.scales.x.min = total - DEFAULT_VISIBLE_POINTS;
        latencyChart.options.scales.x.max = total - 1;
    } else {
        latencyChart.options.scales.x.min = 0;
        latencyChart.options.scales.x.max = Math.max(0, total - 1);
    }
    latencyChart.update();
    showToast("Visão do gráfico redefinida para os pontos mais recentes", "info");
}

// Navegação por botões de passo (Anterior / Recente)
function panChartStep(direction) {
    if (!latencyChart || !latencyChart.scales.x) return;
    const total = latencyChart.data.labels ? latencyChart.data.labels.length : 0;
    if (total <= 1) return;

    const scale = latencyChart.scales.x;
    const currentMin = typeof scale.min === "number" ? scale.min : 0;
    const currentMax = typeof scale.max === "number" ? scale.max : total - 1;
    const windowSize = Math.max(1, currentMax - currentMin);
    const step = Math.max(1, Math.round(windowSize / 3));

    userHasInteractedWithChart = true;

    if (direction === "left") {
        // Ir para o passado (mais antigo)
        const newMin = Math.max(0, currentMin - step);
        const newMax = Math.min(total - 1, newMin + windowSize);
        latencyChart.options.scales.x.min = newMin;
        latencyChart.options.scales.x.max = newMax;
    } else {
        // Ir para o presente (mais recente)
        const newMax = Math.min(total - 1, currentMax + step);
        const newMin = Math.max(0, newMax - windowSize);
        latencyChart.options.scales.x.min = newMin;
        latencyChart.options.scales.x.max = newMax;
        if (newMax >= total - 1) {
            userHasInteractedWithChart = false;
        }
    }

    latencyChart.update('none');
}

// Arrastar interativo via Mouse / Touch / Pointer no Canvas
function setupChartDragNavigation(canvas) {
    let isDragging = false;
    let startX = 0;
    let initialMin = 0;
    let initialMax = 0;
    let hasMoved = false;

    canvas.addEventListener("pointerdown", (e) => {
        if (!latencyChart || !latencyChart.scales.x) return;
        if (e.button !== 0 && e.pointerType === "mouse") return;
        
        const total = latencyChart.data.labels ? latencyChart.data.labels.length : 0;
        if (total <= 1) return;

        const scale = latencyChart.scales.x;
        isDragging = true;
        hasMoved = false;
        startX = e.clientX;
        
        initialMin = typeof scale.min === "number" ? scale.min : 0;
        initialMax = typeof scale.max === "number" ? scale.max : total - 1;

        canvas.classList.add("grabbing");
        try {
            canvas.setPointerCapture(e.pointerId);
        } catch (_) {}
    });

    canvas.addEventListener("pointermove", (e) => {
        if (!isDragging || !latencyChart || !latencyChart.scales.x) return;

        const deltaX = e.clientX - startX;
        if (Math.abs(deltaX) > 3) {
            hasMoved = true;
            userHasInteractedWithChart = true;
        }
        if (!hasMoved) return;

        const total = latencyChart.data.labels.length;
        const windowSize = Math.max(1, initialMax - initialMin);
        
        if (windowSize >= total - 1 && initialMin === 0 && initialMax === total - 1) {
            return;
        }

        const scaleWidth = latencyChart.scales.x.width || canvas.clientWidth || 600;
        const pixelsPerIndex = Math.max(1, scaleWidth / windowSize);
        
        // Puxar para a direita (deltaX > 0) revela dados anteriores (diminui índices)
        // Puxar para a esquerda (deltaX < 0) revela dados recentes (aumenta índices)
        const indexShift = Math.round(deltaX / pixelsPerIndex);
        
        let newMin = initialMin - indexShift;
        let newMax = initialMax - indexShift;

        if (newMin < 0) {
            newMin = 0;
            newMax = Math.min(total - 1, newMin + windowSize);
        } else if (newMax > total - 1) {
            newMax = total - 1;
            newMin = Math.max(0, newMax - windowSize);
        }

        latencyChart.options.scales.x.min = newMin;
        latencyChart.options.scales.x.max = newMax;
        latencyChart.update('none');
    });

    const endDrag = (e) => {
        if (isDragging) {
            isDragging = false;
            canvas.classList.remove("grabbing");
            try {
                canvas.releasePointerCapture(e.pointerId);
            } catch (_) {}
            
            if (latencyChart && latencyChart.scales.x) {
                const total = latencyChart.data.labels ? latencyChart.data.labels.length : 0;
                if (latencyChart.scales.x.max >= total - 1) {
                    userHasInteractedWithChart = false;
                }
            }
        }
    };

    canvas.addEventListener("pointerup", endDrag);
    canvas.addEventListener("pointercancel", endDrag);
}

// Inicialização do Gráfico Chart.js
function initChart() {
    const ctx = document.getElementById("latencyChart");
    if (!ctx) return;

    const isDark = document.documentElement.classList.contains("dark");
    const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)";
    const textColor = isDark ? "#a1a1aa" : "#64748b";

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
                    display: false
                },
                zoom: {
                    pan: {
                        enabled: false // Arraste interativo implementado nativamente via setupChartDragNavigation
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                            speed: 0.05,
                        },
                        pinch: {
                            enabled: true,
                        },
                        mode: 'x',
                        onZoomComplete: () => {
                            userHasInteractedWithChart = true;
                        }
                    },
                    limits: {
                        x: { min: 0, max: 'original', minRange: 4 }
                    }
                },
                tooltip: {
                    backgroundColor: isDark ? "#09090b" : "#ffffff",
                    titleColor: isDark ? "#ffffff" : "#0f172a",
                    bodyColor: isDark ? "#d4d4d8" : "#334155",
                    borderColor: isDark ? "#27272a" : "#e2e8f0",
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 6,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.dataset.label}: ${context.parsed.y} ms`;
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

    setupChartDragNavigation(ctx);
    loadChartData();
}

// Carregar Dados do Gráfico com Cores Oficiais e Ajuste de Janela de Histórico
async function loadChartData() {
    if (!latencyChart) return;
    try {
        const response = await fetch("/api/chart-data");
        if (!response.ok) return;
        const data = await response.json();

        latencyChart.data.labels = data.labels;
        latencyChart.data.datasets = data.datasets.map(ds => {
            const color = OFFICIAL_BANK_COLORS[ds.bank_id] || ds.color || "#ffffff";
            return {
                bank_id: ds.bank_id,
                label: ds.label,
                data: ds.data,
                borderColor: color,
                backgroundColor: color,
                borderWidth: 2.5,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: color,
                tension: 0.3,
                fill: false,
                hidden: (currentChartFilter !== "all" && ds.bank_id !== currentChartFilter)
            };
        });

        const total = data.labels.length;
        if (total > 0) {
            // Se o usuário não está navegando no passado, foca nos últimos 20 pontos
            if (!userHasInteractedWithChart) {
                if (total > DEFAULT_VISIBLE_POINTS) {
                    latencyChart.options.scales.x.min = total - DEFAULT_VISIBLE_POINTS;
                    latencyChart.options.scales.x.max = total - 1;
                } else {
                    latencyChart.options.scales.x.min = 0;
                    latencyChart.options.scales.x.max = total - 1;
                }
            }
            // Atualiza limites de zoom para cobrir todo o histórico
            if (latencyChart.options.plugins && latencyChart.options.plugins.zoom && latencyChart.options.plugins.zoom.limits) {
                latencyChart.options.plugins.zoom.limits.x = {
                    min: 0,
                    max: total - 1,
                    minRange: 4
                };
            }
        }

        latencyChart.update(userHasInteractedWithChart ? 'none' : undefined);
    } catch (err) {
        console.error("Erro ao carregar dados do gráfico:", err);
    }
}

// Filtro de Bancos no Gráfico de Histórico Comparativo
function filterChart(bankId) {
    if (currentChartFilter === bankId && bankId !== "all") {
        currentChartFilter = "all";
    } else {
        currentChartFilter = bankId;
    }
    applyChartFilter();
}

function applyChartFilter() {
    const buttons = document.querySelectorAll(".chart-filter-btn");
    buttons.forEach(btn => {
        const filter = btn.getAttribute("data-filter");
        const bankColor = btn.getAttribute("data-color");
        if (filter === currentChartFilter) {
            if (filter === "all") {
                btn.className = "chart-filter-btn px-3 py-1.5 rounded font-semibold bg-white text-black border border-white transition-all flex items-center gap-1.5 shadow-sm";
                btn.style.borderColor = "";
                btn.style.boxShadow = "";
            } else {
                btn.className = "chart-filter-btn px-2.5 py-1.5 rounded font-semibold bg-zinc-800 text-white transition-all flex items-center gap-1.5 shadow-sm";
                btn.style.borderColor = bankColor || "#ffffff";
                btn.style.boxShadow = `0 0 12px ${bankColor}40`;
            }
        } else {
            btn.className = "chart-filter-btn px-2.5 py-1.5 rounded font-semibold bg-zinc-950 text-zinc-400 border border-zinc-800 hover:text-white hover:bg-zinc-900 transition-all flex items-center gap-1.5";
            btn.style.borderColor = "";
            btn.style.boxShadow = "";
        }
    });

    if (!latencyChart) return;

    latencyChart.data.datasets.forEach(ds => {
        if (currentChartFilter === "all") {
            ds.hidden = false;
        } else {
            ds.hidden = (ds.bank_id !== currentChartFilter);
        }
    });

    latencyChart.update();
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
    }, 60000);
}

function toggleAutoRefresh() {
    isAutoRefreshActive = !isAutoRefreshActive;
    const toggleBtn = document.getElementById("autoRefreshToggle");
    if (toggleBtn) {
        if (isAutoRefreshActive) {
            toggleBtn.className = "px-3 py-1.5 rounded text-xs font-semibold border bg-zinc-800 text-white border-zinc-600 transition-all flex items-center gap-2";
            showToast("Atualização automática ativada (60s)", "info");
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

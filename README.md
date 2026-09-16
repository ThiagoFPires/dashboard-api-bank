# 🏦 Monitor de APIs Bancárias (Brasil)

Plataforma em **Python** de alta performance para monitoramento contínuo em tempo real da disponibilidade, latência e conformidade de SLAs das APIs dos principais bancos brasileiros: **Itaú**, **Sicredi**, **Sicoob**, **Banco do Brasil** e **Bradesco**.

---

## 📋 Funcionalidades Principais

- **Painel Executivo em Tempo Real:** Status geral da rede bancária, SLAs médios das últimas 24h, tempo de resposta (ms) e incidentes ativos.
- **Identidade Visual Dedicada por Banco:**
  - 🟧 **Itaú Unibanco (341):** Pix, Boletos & Cobrança, Extrato, OAuth2/STS.
  - 🟩 **Sicredi (748):** Pix Sicredi, Cobrança Híbrida, Extrato Cooperado, Auth Gateway.
  - 🟦 **Sicoob (756):** Pix CobV, Cobrança Bancária, Saldo/Extrato, Keycloak/OAuth2.
  - 🟨 **Banco do Brasil (001):** Pix BB, Cobrança de Boletos, Pagamentos em Lote, OAuth2 BB.
  - 🟥 **Bradesco (237):** Pix Bradesco, Boletos Registrados, Extratos, OAuth2 Bradesco.
- **Gráfico Comparativo de Latência:** Séries temporais em tempo real geradas com **Chart.js** comparando a performance dos 5 bancos.
- **Visão Granular de Microserviços:** Monitoramento detalhado dos endpoints de Pix, Cobrança, Extratos e Autenticação.
- **Central de Incidentes:** Registro automático e manual de degradações, timeouts e recuperação de serviços.
- **Disparo Manual (Instant Ping):** Teste imediato de um único banco ou de todos os 20 serviços com feedback visual e notificações Toast.
- **Persistência Integrada:** Banco de dados SQLite local com histórico e cálculos automáticos de uptime.
- **Exportação de Dados:** Exportação de relatórios de status em CSV e API REST completa com Swagger em `/docs`.

---

## 🚀 Como Executar

### 1. Pré-requisitos
- Python 3.10 ou superior instalado.

### 2. Instalação das Dependências
No terminal, dentro da pasta do projeto:
```bash
pip install -r requirements.txt
```

### 3. Iniciar o Servidor
Você pode iniciar simplesmente dando um **duplo clique** no arquivo:
```
iniciar_monitor.bat
```
Ele irá verificar as dependências, abrir o navegador em `http://127.0.0.1:8000` automaticamente e iniciar o servidor!

Ou, se preferir pelo terminal:
```bash
python run.py
```
Ou diretamente com o Uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Abra seu navegador em:
- **Dashboard Web:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentação Interativa (Swagger API):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ⚙️ Modos de Operação

Na aba **Configurações** (`/settings`), você pode ajustar:
1. **Modo Híbrido (Recomendado):** Dispara requisições HTTP reais. Se o banco exigir certificados mTLS corporativos restritos, aciona telemetria de contingência para manter a interface e métricas ativas.
2. **Modo Simulação Contínua:** Gera telemetria estocástica com curvas e perfis de latência realistas para os 5 bancos (ideal para desenvolvimento).
3. **Modo Apenas HTTP Real:** Efetua estritamente sondas de rede contra os endpoints cadastrados.

---

## 📁 Estrutura do Projeto

```
bank-api-monitor/
├── app/
│   ├── __init__.py
│   ├── config.py             # Configurações gerais e limiares de latência
│   ├── banks_catalog.py      # Catálogo e metadados dos 5 bancos e seus serviços
│   ├── database.py           # Persistência SQLite, métricas de SLA e incidentes
│   ├── models.py             # Schemas Pydantic para validação e documentação
│   ├── monitor.py            # Motor assíncrono com HTTPX e Background Worker
│   ├── main.py               # Servidor FastAPI com rotas HTML e API REST
│   ├── static/
│   │   ├── css/custom.css    # Animações de status e estilização dos cards
│   │   └── js/dashboard.js   # Atualização em tempo real e gráficos Chart.js
│   └── templates/
│       ├── base.html         # Layout base responsivo com Tailwind CSS
│       ├── index.html        # Dashboard principal com KPIs e cards dos bancos
│       ├── bank_detail.html  # Visão aprofundada de um banco individual
│       ├── incidents.html    # Histórico de incidentes e resolução
│       └── settings.html     # Painel de configurações operacionais
├── requirements.txt          # Dependências do projeto
├── run.py                    # Script de inicialização simplificado
└── README.md                 # Documentação
```

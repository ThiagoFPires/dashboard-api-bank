"""
Catálogo dos Bancos e Serviços Monitorados.
Contém metadados de marca, cores oficiais dos bancos para o gráfico e URLs das logos SVG.
"""

BANKS_CATALOG = [
    {
        "id": "itau",
        "name": "Itaú Unibanco",
        "short_name": "Itaú",
        "code": "341",
        "color": "#EC7000",
        "logo_url": "/static/img/itau.svg",
        "bg_soft": "#27272a",
        "border_color": "#52525b",
        "text_color": "#ffffff",
        "badge_color": "bg-zinc-800 text-zinc-100 border-zinc-700",
        "icon": "building-2",
        "tagline": "Maior banco privado do Brasil",
        "developer_portal": "https://developer.itau.com.br",
        "services": [
            {
                "id": "itau-pix",
                "name": "Pix API",
                "description": "Emissão de cobrança imediata (QR Code dinâmico) e webhooks de recebimento",
                "endpoint_url": "https://api.itau.com.br/sandbox/pix/v2",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            },
            {
                "id": "itau-boletos",
                "name": "Boletos & Cobrança",
                "description": "Emissão, alteração de vencimento, cancelamento e consulta de boletos",
                "endpoint_url": "https://api.itau.com.br/sandbox/boletos/v2",
                "method": "GET",
                "expected_status": 200,
                "importance": "high"
            },
            {
                "id": "itau-extrato",
                "name": "Extrato & Conciliação",
                "description": "Consulta de extratos por período e conciliação bancária automatizada",
                "endpoint_url": "https://api.itau.com.br/sandbox/extrato/v1",
                "method": "GET",
                "expected_status": 200,
                "importance": "medium"
            },
            {
                "id": "itau-auth",
                "name": "OAuth2 / STS",
                "description": "Serviço de geração e validação de tokens mTLS e credenciais de acesso",
                "endpoint_url": "https://sts.itau.com.br/as/token.oauth2",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            }
        ]
    },
    {
        "id": "sicredi",
        "name": "Sicredi",
        "short_name": "Sicredi",
        "code": "748",
        "color": "#00933B",
        "logo_url": "/static/img/sicredi.svg",
        "bg_soft": "#27272a",
        "border_color": "#52525b",
        "text_color": "#ffffff",
        "badge_color": "bg-zinc-800 text-zinc-100 border-zinc-700",
        "icon": "trees",
        "tagline": "Sistema de Crédito Cooperativo",
        "developer_portal": "https://developer.sicredi.com.br",
        "services": [
            {
                "id": "sicredi-pix",
                "name": "Pix Sicredi",
                "description": "Liquidação instantânea, gestão de chaves Pix e webhooks",
                "endpoint_url": "https://api-parceiro.sicredi.com.br/sb/pix/v2",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            },
            {
                "id": "sicredi-boletos",
                "name": "Cobrança Híbrida",
                "description": "Boletos com código de barras tradicional e Pix QR Code acoplado",
                "endpoint_url": "https://api-parceiro.sicredi.com.br/sb/cobranca/v3/boletos",
                "method": "GET",
                "expected_status": 200,
                "importance": "high"
            },
            {
                "id": "sicredi-extrato",
                "name": "Extrato Cooperado",
                "description": "Consulta de extratos e saldos em contas correntes do Sicredi",
                "endpoint_url": "https://api-parceiro.sicredi.com.br/sb/extrato/v1",
                "method": "GET",
                "expected_status": 200,
                "importance": "medium"
            },
            {
                "id": "sicredi-auth",
                "name": "Auth Gateway (OAuth2)",
                "description": "Emissão de Bearer tokens para APIs parceiras e corporativas",
                "endpoint_url": "https://api-parceiro.sicredi.com.br/auth/openapi/v1/token",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            }
        ]
    },
    {
        "id": "sicoob",
        "name": "Sicoob",
        "short_name": "Sicoob",
        "code": "756",
        "color": "#00AE9D",
        "logo_url": "/static/img/sicoob.svg",
        "bg_soft": "#27272a",
        "border_color": "#52525b",
        "text_color": "#ffffff",
        "badge_color": "bg-zinc-800 text-zinc-100 border-zinc-700",
        "icon": "shield-check",
        "tagline": "Sistema de Cooperativas de Crédito do Brasil",
        "developer_portal": "https://developers.sicoob.com.br",
        "services": [
            {
                "id": "sicoob-pix",
                "name": "Pix CobV & Imediato",
                "description": "Cobrança com vencimento, juros, multas e QR Code Pix Sicoob",
                "endpoint_url": "https://api.sicoob.com.br/pix/api/v2",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            },
            {
                "id": "sicoob-boletos",
                "name": "Cobrança Bancária",
                "description": "Emissão, consulta de títulos e instrução de desconto/baixa",
                "endpoint_url": "https://api.sicoob.com.br/cobranca-bancaria/v3/boletos",
                "method": "GET",
                "expected_status": 200,
                "importance": "high"
            },
            {
                "id": "sicoob-extrato",
                "name": "Conta Corrente / Saldo",
                "description": "Saldos consolidados e extratos em formato estruturado",
                "endpoint_url": "https://api.sicoob.com.br/conta-corrente/v2/extrato",
                "method": "GET",
                "expected_status": 200,
                "importance": "medium"
            },
            {
                "id": "sicoob-auth",
                "name": "Keycloak / OAuth2",
                "description": "Autenticação corporativa com mTLS e certificados digitais",
                "endpoint_url": "https://auth.sicoob.com.br/auth/realms/cooperado/protocol/openid-connect/token",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            }
        ]
    },
    {
        "id": "bb",
        "name": "Banco do Brasil",
        "short_name": "Banco do Brasil",
        "code": "001",
        "color": "#FEE100",
        "logo_url": "/static/img/bb.svg",
        "bg_soft": "#27272a",
        "border_color": "#52525b",
        "text_color": "#ffffff",
        "badge_color": "bg-zinc-800 text-zinc-100 border-zinc-700",
        "icon": "landmark",
        "tagline": "Maior banco público e pioneiro em APIs financeiras",
        "developer_portal": "https://developers.bb.com.br",
        "services": [
            {
                "id": "bb-pix",
                "name": "Pix BB",
                "description": "Soluções Pix Cobrança, Pix Saque/Troco e conciliação em lote",
                "endpoint_url": "https://api.bb.com.br/pix/v1",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            },
            {
                "id": "bb-boletos",
                "name": "Cobrança de Boletos",
                "description": "Registro instantâneo de boletos com convênio e impressão online",
                "endpoint_url": "https://api.bb.com.br/cobrancas/v2/boletos",
                "method": "GET",
                "expected_status": 200,
                "importance": "high"
            },
            {
                "id": "bb-pagamentos",
                "name": "Pagamentos em Lote",
                "description": "Pagamento de contas, tributos e transferências massivas",
                "endpoint_url": "https://api.bb.com.br/pagamentos-lote/v1",
                "method": "GET",
                "expected_status": 200,
                "importance": "high"
            },
            {
                "id": "bb-auth",
                "name": "OAuth2 BB Gateway",
                "description": "Validação de App Key e Client Secret via OAuth2 do Banco do Brasil",
                "endpoint_url": "https://oauth.bb.com.br/oauth/v2/token",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            }
        ]
    },
    {
        "id": "bradesco",
        "name": "Banco Bradesco",
        "short_name": "Bradesco",
        "code": "237",
        "color": "#CC092F",
        "logo_url": "/static/img/bradesco.svg",
        "bg_soft": "#27272a",
        "border_color": "#52525b",
        "text_color": "#ffffff",
        "badge_color": "bg-zinc-800 text-zinc-100 border-zinc-700",
        "icon": "wallet",
        "tagline": "Líder em transações comerciais e cartões",
        "developer_portal": "https://developers.bradesco.com.br",
        "services": [
            {
                "id": "bradesco-pix",
                "name": "Pix Bradesco",
                "description": "Processamento de cobrança imediata e notificações de eventos Pix",
                "endpoint_url": "https://api.bradesco.com.br/v1/pix",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            },
            {
                "id": "bradesco-boletos",
                "name": "Boleto Registrado",
                "description": "Emissão de boletos com registro imediato no CIP e conciliação",
                "endpoint_url": "https://api.bradesco.com.br/v1/boletos-registrados",
                "method": "GET",
                "expected_status": 200,
                "importance": "high"
            },
            {
                "id": "bradesco-extrato",
                "name": "Extrato & Conciliação",
                "description": "Exportação de movimentações e lançamentos futuros",
                "endpoint_url": "https://api.bradesco.com.br/v1/extrato",
                "method": "GET",
                "expected_status": 200,
                "importance": "medium"
            },
            {
                "id": "bradesco-auth",
                "name": "OAuth2 Bradesco",
                "description": "Serviço de autenticação corporativa com validação de certificados",
                "endpoint_url": "https://auth.bradesco.com.br/oauth/token",
                "method": "GET",
                "expected_status": 200,
                "importance": "critical"
            }
        ]
    }
]

def get_bank_by_id(bank_id: str):
    for bank in BANKS_CATALOG:
        if bank["id"] == bank_id:
            return bank
    return None

def get_service_by_id(service_id: str):
    for bank in BANKS_CATALOG:
        for svc in bank["services"]:
            if svc["id"] == service_id:
                return svc, bank
    return None, None

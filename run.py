"""
Script de inicialização do Monitor de APIs Bancárias.
Executa o servidor Uvicorn compatível com ambiente local e nuvem (Render, Railway, etc.).
"""

import sys
import os
import uvicorn

# Configurar encoding UTF-8 no terminal Windows se necessário
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Configurar fuso horário padrão para Horário de Brasília
os.environ.setdefault("TZ", "America/Sao_Paulo")
try:
    import time
    if hasattr(time, "tzset"):
        time.tzset()
except Exception:
    pass


# Garantir que a raiz do projeto esteja no sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    print("\n" + "=" * 65)
    print("  [+] MONITOR DE APIS BANCARIAS - BRASIL")
    print("  Bancos Monitorados:")
    print("    - Itau Unibanco (341)")
    print("    - Sicredi (748)")
    print("    - Sicoob (756)")
    print("    - Banco do Brasil (001)")
    print("    - Bradesco (237)")
    print("=" * 65)
    print(f"  * Servidor Ativo em: http://{host}:{port}")
    print(f"  * Swagger API Docs: http://{host}:{port}/docs")
    print("=" * 65 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()

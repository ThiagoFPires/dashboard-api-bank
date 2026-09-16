"""
Script de inicialização do Monitor de APIs Bancárias.
Executa o servidor local Uvicorn na porta 8000.
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

# Garantir que a raiz do projeto esteja no sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def main():
    print("\n" + "=" * 65)
    print("  [+] MONITOR DE APIS BANCARIAS - BRASIL")
    print("  Bancos Monitorados:")
    print("    - Itau Unibanco (341)")
    print("    - Sicredi (748)")
    print("    - Sicoob (756)")
    print("    - Banco do Brasil (001)")
    print("    - Bradesco (237)")
    print("=" * 65)
    print("  * Dashboard Web: http://127.0.0.1:8000")
    print("  * Swagger API Docs: http://127.0.0.1:8000/docs")
    print("=" * 65 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()

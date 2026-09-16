@echo off
title Monitor de APIs Bancarias - Brasil
chcp 65001 >nul
cls

echo =====================================================================
echo    INICIALIZANDO MONITOR DE APIS BANCARIAS
echo    (Itau, Sicredi, Sicoob, Banco do Brasil, Bradesco)
echo =====================================================================
echo.

:: Navega para o diretorio onde o arquivo .bat esta localizado
cd /d "%~dp0"

:: Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao foi encontrado no PATH do sistema.
    echo Por favor, instale o Python 3.10+ ou adicione-o ao PATH.
    echo.
    pause
    exit /b 1
)

:: Verifica e instala dependencias se necessario
echo [*] Verificando dependencias necessarias...
pip install -r requirements.txt --quiet

echo.
echo [*] Abrindo o Dashboard no seu navegador...
start http://127.0.0.1:8000

echo.
echo [*] Iniciando o servidor Uvicorn...
echo     Pressione CTRL+C na janela para encerrar o servidor.
echo.

python run.py

if %errorlevel% neq 0 (
    echo.
    echo [AVISO] O servidor foi encerrado.
    pause
)

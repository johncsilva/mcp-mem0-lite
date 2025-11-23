@echo off
REM Script para iniciar o servidor MCP no WSL automaticamente
REM Este script é chamado pelo Windows na inicialização

echo Iniciando MCP Mem0-Lite no WSL...

REM Obter o diretório do script (funciona mesmo se executado de outro lugar)
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM Converter caminho Windows para WSL (C:\Users\... -> /mnt/c/Users/...)
REM Assumindo que está em algum lugar acessível pelo WSL
set WSL_SCRIPT_PATH=/home/john/projetos/Pessoal/mcp-mem0-lite/mcp-mem0-lite-global.sh

REM Iniciar o servidor MCP no WSL em background
wsl -d Ubuntu -e bash -c "nohup %WSL_SCRIPT_PATH% > /dev/null 2>&1 &"

REM Aguardar alguns segundos para dar tempo do servidor iniciar
timeout /t 5 /nobreak >nul

REM Verificar se o servidor está rodando
curl -s http://127.0.0.1:8050/ >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Servidor MCP iniciado com sucesso!
) else (
    echo [AVISO] Servidor pode ainda estar iniciando...
)

echo.
echo Servidor MCP Mem0-Lite em execucao no WSL
echo URL: http://127.0.0.1:8050

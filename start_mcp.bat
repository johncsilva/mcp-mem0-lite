@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   MCP Mem0-Lite Startup Script
echo ========================================
echo.

REM Limpar processos orfaos do servidor MCP
echo [1/4] Limpando processos orfaos...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /C:"PID:"') do (
    for /f "tokens=*" %%b in ('wmic process where "ProcessId=%%a" get CommandLine /format:list 2^>nul ^| findstr "server.py"') do (
        echo   [KILL] Encerrando processo Python server.py (PID: %%a^)
        taskkill /F /PID %%a >nul 2>&1
    )
)

REM Limpar processos usando porta 8050
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8050 ^| findstr LISTENING') do (
    echo   [KILL] Encerrando processo na porta 8050 (PID: %%a^)
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul
echo   [OK] Limpeza concluida
echo.

REM Verificar se Ollama esta rodando
echo [2/4] Verificando Ollama...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Ollama ja esta rodando
    goto ollama_ready
)

echo   [INICIANDO] Ollama nao encontrado, iniciando...
start "Ollama" ollama serve
timeout /t 3 /nobreak >nul

REM Aguardar Ollama ficar online (max 30s)
set OLLAMA_TIMEOUT=30
set OLLAMA_ELAPSED=0
:wait_ollama
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Ollama iniciado com sucesso
    goto ollama_ready
)
timeout /t 1 /nobreak >nul
set /a OLLAMA_ELAPSED+=1
if !OLLAMA_ELAPSED! geq !OLLAMA_TIMEOUT! (
    echo   [ERRO] Timeout aguardando Ollama
    exit /b 1
)
goto wait_ollama

:ollama_ready
echo.

REM Verificar se servidor MCP esta rodando
echo [3/4] Verificando servidor MCP...
curl -s http://127.0.0.1:8050/ >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Servidor MCP ja esta rodando
    goto mcp_ready
)

echo   [INICIANDO] Servidor MCP nao encontrado, iniciando...
cd /d C:\Dev\mcp-mem0-lite
start "MCP Mem0-Lite Server" cmd /k ".venv\Scripts\python.exe server.py"

REM Aguardar servidor MCP ficar online (max 60s)
set MCP_TIMEOUT=60
set MCP_ELAPSED=0
:wait_mcp
curl -s http://127.0.0.1:8050/ >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Servidor MCP iniciado com sucesso
    goto mcp_ready
)
timeout /t 1 /nobreak >nul
set /a MCP_ELAPSED+=1
if !MCP_ELAPSED! geq !MCP_TIMEOUT! (
    echo   [ERRO] Timeout aguardando servidor MCP
    exit /b 1
)
goto wait_mcp

:mcp_ready
echo.

echo [4/4] Validando integracao...
curl -s --max-time 2 http://127.0.0.1:8050/mcp/sse >nul 2>&1
if %errorlevel% lss 28 (
    echo   [OK] Endpoint SSE acessivel
) else (
    echo   [AVISO] Endpoint SSE nao respondeu
)
echo.

echo ========================================
echo   TUDO OK!
echo ========================================
echo   Ollama:      http://127.0.0.1:11434
echo   MCP Server:  http://127.0.0.1:8050
echo   SSE:         http://127.0.0.1:8050/mcp/sse
echo ========================================
echo.
echo Pressione qualquer tecla para fechar...
pause >nul

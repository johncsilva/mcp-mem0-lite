@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   MCP Mem0-Lite - Startup Interativo
echo ========================================
echo.

REM Mostrar menu de selecao de LLM
:menu
echo Selecione o provedor LLM:
echo.
echo   [1] Ollama Local - llama3.2:latest (Gratuito, ~35s/memoria)
echo   [2] Ollama Local - llama3.1:8b (Gratuito, ~60s/memoria, mais confiavel)
echo   [3] Ollama Local - tinyllama (Gratuito, ~10s/memoria, pode falhar)
echo   [4] OpenAI - gpt-4o-mini (Pago, ~1-3s/memoria, muito confiavel)
echo   [5] OpenAI - gpt-4o (Pago, ~1-3s/memoria, melhor qualidade)
echo   [Q] Cancelar
echo.
set /p choice="Escolha uma opcao: "

if /i "%choice%"=="Q" (
    echo Operacao cancelada.
    pause
    exit /b 0
)

REM Configurar LLM baseado na escolha
if "%choice%"=="1" (
    set LLM_PROVIDER=ollama
    set LLM_MODEL=llama3.2:latest
    set LLM_DESC=Ollama llama3.2:latest
    set USE_OLLAMA=1
)
if "%choice%"=="2" (
    set LLM_PROVIDER=ollama
    set LLM_MODEL=llama3.1:8b
    set LLM_DESC=Ollama llama3.1:8b
    set USE_OLLAMA=1
)
if "%choice%"=="3" (
    set LLM_PROVIDER=ollama
    set LLM_MODEL=tinyllama
    set LLM_DESC=Ollama tinyllama
    set USE_OLLAMA=1
)
if "%choice%"=="4" (
    set LLM_PROVIDER=openai
    set LLM_MODEL=gpt-4o-mini
    set LLM_DESC=OpenAI gpt-4o-mini
    set USE_OLLAMA=0
)
if "%choice%"=="5" (
    set LLM_PROVIDER=openai
    set LLM_MODEL=gpt-4o
    set LLM_DESC=OpenAI gpt-4o
    set USE_OLLAMA=0
)

if not defined LLM_PROVIDER (
    echo Opcao invalida!
    echo.
    goto menu
)

echo.
echo Configuracao selecionada: %LLM_DESC%
echo.

REM Atualizar arquivo .env
echo [CONFIG] Atualizando .env...
powershell -NoProfile -Command "(Get-Content .env) -replace '^LLM_PROVIDER=.*', 'LLM_PROVIDER=%LLM_PROVIDER%' | Set-Content .env"
powershell -NoProfile -Command "(Get-Content .env) -replace '^LLM_MODEL=.*', 'LLM_MODEL=%LLM_MODEL%' | Set-Content .env"
echo   [OK] Configuracao atualizada
echo.

REM Limpar processos orfaos do servidor MCP
echo [1/3] Limpando processos orfaos...
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
if "%USE_OLLAMA%"=="1" (
    echo [2/3] Verificando Ollama...
    curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        goto start_ollama
    ) else (
        echo   [OK] Ollama ja esta rodando
        goto after_ollama
    )
) else (
    echo [2/3] Verificando OpenAI...
    echo   [OK] Usando OpenAI API (chave configurada no .env^)
    goto after_ollama
)

:start_ollama
echo   [INICIANDO] Ollama nao encontrado, iniciando...
start "Ollama" ollama serve
timeout /t 3 /nobreak >nul

set OLLAMA_TIMEOUT=30
set OLLAMA_ELAPSED=0

:wait_ollama
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if not errorlevel 1 goto ollama_started
timeout /t 1 /nobreak >nul
set /a OLLAMA_ELAPSED+=1
if !OLLAMA_ELAPSED! geq !OLLAMA_TIMEOUT! (
    echo   [ERRO] Timeout aguardando Ollama
    pause
    exit /b 1
)
goto wait_ollama

:ollama_started
echo   [OK] Ollama iniciado com sucesso

:after_ollama
echo.

REM Iniciar servidor MCP
echo [3/3] Iniciando servidor MCP com %LLM_DESC%...
cd /d C:\Dev\mcp-mem0-lite
start "MCP Mem0-Lite Server - %LLM_DESC%" cmd /k ".venv\Scripts\python.exe server.py"

REM Aguardar servidor MCP ficar online
set MCP_TIMEOUT=60
set MCP_ELAPSED=0
:wait_mcp
curl -s http://127.0.0.1:8050/ >nul 2>&1
if not errorlevel 1 goto mcp_started
timeout /t 1 /nobreak >nul
set /a MCP_ELAPSED+=1
if !MCP_ELAPSED! geq !MCP_TIMEOUT! (
    echo   [ERRO] Timeout aguardando servidor MCP
    pause
    exit /b 1
)
goto wait_mcp

:mcp_started
echo   [OK] Servidor MCP iniciado com sucesso
echo.

echo ========================================
echo   TUDO OK!
echo ========================================
echo   LLM:         %LLM_DESC%
echo   Ollama:      http://127.0.0.1:11434
echo   MCP Server:  http://127.0.0.1:8050
echo   SSE:         http://127.0.0.1:8050/mcp/sse
echo ========================================
echo.
echo Servidor iniciado em janela separada.
echo Nao feche a janela do servidor!
echo.
pause

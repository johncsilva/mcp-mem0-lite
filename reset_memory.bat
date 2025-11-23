@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   MCP Mem0-Lite - Reset Memory
echo ========================================
echo.
echo AVISO: Isso vai apagar TODAS as memorias!
echo.
set /p confirm="Tem certeza? (S/N): "
if /i not "%confirm%"=="S" (
    echo Operacao cancelada.
    pause
    exit /b 0
)
echo.

REM Parar todos os processos Python que estao usando server.py
echo [1/3] Parando servidor MCP...
curl -s --max-time 1 http://127.0.0.1:8050/ >nul 2>&1
if %errorlevel% equ 0 (
    echo   [INFO] Servidor detectado, parando...

    REM Tentar parar pela janela
    taskkill /F /FI "WINDOWTITLE eq MCP Mem0-Lite Server*" >nul 2>&1

    REM Parar todos os python.exe que estejam usando a porta 8050
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8050') do (
        taskkill /F /PID %%a >nul 2>&1
    )

    REM Aguardar processos fecharem
    timeout /t 3 /nobreak >nul
    echo   [OK] Servidor parado
) else (
    echo   [OK] Servidor nao esta rodando
)
echo.

REM Apagar ChromaDB
echo [2/3] Apagando ChromaDB...
if exist "C:\Dev\mcp-mem0-lite\chroma_db" (
    rmdir /s /q "C:\Dev\mcp-mem0-lite\chroma_db"
    echo   [OK] ChromaDB apagado
) else (
    echo   [INFO] ChromaDB nao existe
)

REM Apagar SQLite
echo [3/3] Apagando SQLite...
if exist "C:\Dev\mcp-mem0-lite\mem0.db" (
    del /f /q "C:\Dev\mcp-mem0-lite\mem0.db"
    echo   [OK] SQLite apagado
) else (
    echo   [INFO] SQLite nao existe
)
echo.

echo ========================================
echo   RESET COMPLETO!
echo ========================================
echo   Todas as memorias foram apagadas.
echo   Na proxima inicializacao, os bancos
echo   serao recriados vazios.
echo ========================================
echo.
pause

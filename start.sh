#!/bin/bash
echo "🚀 Iniciando servidor MCP Mem0-Lite..."

# Verifica se já está rodando (por porta)
if lsof -ti:8050 > /dev/null 2>&1; then
    echo "⚠️  Servidor já está rodando na porta 8050!"
    PID=$(lsof -ti:8050)
    echo "📋 PID: $PID"
    ps -p $PID -o args= 2>/dev/null | head -1
    exit 1
fi

# Ativa venv e inicia servidor
cd "$(dirname "$0")"
source .venv/bin/activate
nohup python server.py > server.log 2>&1 &

# Aguarda inicialização
sleep 3

# Verifica se iniciou
if curl -s http://127.0.0.1:8050/ > /dev/null; then
    echo "✅ Servidor iniciado com sucesso!"
    echo "📍 URL: http://127.0.0.1:8050"
    echo "📍 MCP: http://127.0.0.1:8050/mcp/sse"
    echo "📋 PID: $(pgrep -f 'python.*server.py')"
else
    echo "❌ Erro ao iniciar servidor"
    echo "📋 Últimas linhas do log:"
    tail -20 server.log
    exit 1
fi

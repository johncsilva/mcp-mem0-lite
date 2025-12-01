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
FORCE_HTTP_MODE=true nohup python server.py > server.log 2>&1 &
SERVER_PID=$!
echo "Servidor iniciado com PID: $SERVER_PID"

# Aguarda inicialização
sleep 5

# Verifica se iniciou
echo "Testando conectividade..."
RESPONSE=$(curl -s --max-time 5 http://127.0.0.1:8050/ 2>/dev/null)
if [ $? -eq 0 ] && echo "$RESPONSE" | grep -q "running"; then
    echo "✅ Servidor iniciado com sucesso!"
    echo "📍 URL: http://127.0.0.1:8050"
    echo "📍 MCP: http://127.0.0.1:8050/mcp/sse"
    echo "📋 PID: $(pgrep -f 'python.*server.py')"
else
    echo "❌ Erro ao iniciar servidor"
    echo "📋 Código de saída do curl: $?"
    echo "📋 Resposta recebida: ${#RESPONSE} caracteres"
    echo "📋 Últimas linhas do log:"
    tail -20 server.log 2>/dev/null || echo "Log vazio"
    exit 1
fi

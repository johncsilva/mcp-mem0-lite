#!/bin/bash
echo "📊 Status do Servidor MCP Mem0-Lite"
echo "======================================"

# Verifica processo (pega apenas o processo LISTEN, não conexões)
PID=$(lsof -ti:8050 -sTCP:LISTEN 2>/dev/null | head -1)
if [ -n "$PID" ]; then
    echo "✅ Processo: RODANDO"
    echo "📋 PID: $PID"

    # Tempo de execução
    UPTIME=$(ps -p $PID -o etime= 2>/dev/null | xargs)
    echo "⏱️  Uptime: $UPTIME"

    # Memória
    MEM=$(ps -p $PID -o rss= 2>/dev/null | awk '{printf "%.2f MB", $1/1024}')
    echo "💾 Memória: $MEM"

    # Comando
    CMD=$(ps -p $PID -o args= 2>/dev/null | cut -c1-70)
    echo "📝 Comando: $CMD"
else
    echo "❌ Processo: PARADO"
fi

# Verifica porta
if lsof -i:8050 > /dev/null 2>&1; then
    echo "✅ Porta 8050: EM USO"
else
    echo "❌ Porta 8050: LIVRE"
fi

# Testa endpoint
echo ""
echo "Testando endpoints..."
if curl -s --max-time 2 http://127.0.0.1:8050/ > /dev/null; then
    echo "✅ HTTP: RESPONDENDO"

    # Informações do servidor
    curl -s http://127.0.0.1:8050/ | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"📌 Nome: {data.get('name', 'N/A')}\")
    print(f\"📌 Versão: {data.get('version', 'N/A')}\")
    config = data.get('configuration', {}).get('current', {})
    print(f\"📌 LLM: {config.get('llm_provider', 'N/A')}/{config.get('llm_model', 'N/A')}\")
    tools = data.get('mcp_tools', {})
    print(f\"📌 Tools: {len(tools)} disponíveis\")
except:
    pass
"
else
    echo "❌ HTTP: NÃO RESPONDENDO"
fi

echo ""
echo "======================================"

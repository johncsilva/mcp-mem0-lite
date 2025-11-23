#!/bin/bash
echo "🔄 Reiniciando servidor MCP Mem0-Lite..."

# Para o servidor
bash "$(dirname "$0")/stop.sh"

# Aguarda
sleep 2

# Inicia o servidor
bash "$(dirname "$0")/start.sh"

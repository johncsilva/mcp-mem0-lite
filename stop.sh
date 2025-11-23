#!/bin/bash
echo "🛑 Parando servidor MCP Mem0-Lite..."

# Tenta encontrar processo por diferentes padrões
if pgrep -f "python.*server" > /dev/null || lsof -ti:8050 > /dev/null 2>&1; then
    echo "📋 Parando processo..."

    # Método 1: Por nome
    pkill -f "python.*server" 2>/dev/null

    # Método 2: Por porta
    lsof -ti:8050 | xargs kill 2>/dev/null

    # Aguarda parar
    sleep 2

    # Verifica se parou
    if lsof -ti:8050 > /dev/null 2>&1; then
        echo "⚠️  Servidor não respondeu, forçando..."
        lsof -ti:8050 | xargs kill -9 2>/dev/null
        sleep 1
    fi

    # Verifica status final
    if ! lsof -ti:8050 > /dev/null 2>&1; then
        echo "✅ Servidor parado com sucesso!"
    else
        echo "❌ Erro ao parar servidor"
        exit 1
    fi
else
    echo "⚠️  Servidor não está rodando"
    exit 0
fi

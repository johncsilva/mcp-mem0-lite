#!/bin/bash

# MCP Mem0-Lite Global Launcher
# Este script permite executar o servidor MCP de qualquer diretório

# Caminho absoluto para o projeto (ajuste conforme necessário)
PROJECT_DIR="/home/john/projetos/Pessoal/mcp-mem0-lite"

# Verificar se o diretório do projeto existe
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Erro: Diretório do projeto não encontrado: $PROJECT_DIR"
    echo "Ajuste o caminho PROJECT_DIR neste script."
    exit 1
fi

# Verificar se estamos no diretório correto e ativar ambiente virtual
cd "$PROJECT_DIR" || exit 1

# Verificar se o ambiente virtual existe
if [ ! -d ".venv" ]; then
    echo "Erro: Ambiente virtual não encontrado em $PROJECT_DIR/.venv"
    echo "Execute a instalação completa primeiro."
    exit 1
fi

# Ativar ambiente virtual
source .venv/bin/activate

# Verificar se o Ollama está rodando
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "Aviso: Ollama não está rodando. Iniciando..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Iniciar o servidor MCP
echo "Iniciando servidor MCP Mem0-Lite..."
exec python server.py
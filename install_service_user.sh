#!/bin/bash

# Script alternativo para instalar serviço MCP sem sudo
# Cria um serviço usuário que roda na sessão do usuário

echo "Instalando serviço MCP Mem0-Lite (modo usuário)..."

# Criar diretório para serviços do usuário
mkdir -p ~/.config/systemd/user/

# Copiar arquivo de serviço
cp mcp-mem0-lite.service ~/.config/systemd/user/

# Recarregar configurações do systemd do usuário
systemctl --user daemon-reload

# Habilitar serviço para iniciar no login
systemctl --user enable mcp-mem0-lite

# Iniciar serviço
systemctl --user start mcp-mem0-lite

echo "Serviço instalado e iniciado!"
echo ""
echo "Comandos úteis:"
echo "  systemctl --user status mcp-mem0-lite    # Ver status"
echo "  systemctl --user stop mcp-mem0-lite      # Parar serviço"
echo "  systemctl --user start mcp-mem0-lite     # Iniciar serviço"
echo "  systemctl --user restart mcp-mem0-lite   # Reiniciar serviço"
echo "  journalctl --user -u mcp-mem0-lite -f    # Ver logs em tempo real"
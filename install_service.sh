#!/bin/bash

# Script de instalação do serviço MCP Mem0-Lite
# Execute com: sudo ./install_service.sh

echo "Instalando serviço MCP Mem0-Lite..."

# Copiar arquivo de serviço
cp mcp-mem0-lite.service /etc/systemd/system/

# Recarregar configurações do systemd
systemctl daemon-reload

# Habilitar serviço para iniciar no boot
systemctl enable mcp-mem0-lite

# Iniciar serviço
systemctl start mcp-mem0-lite

echo "Serviço instalado e iniciado!"
echo ""
echo "Comandos úteis:"
echo "  systemctl status mcp-mem0-lite    # Ver status"
echo "  systemctl stop mcp-mem0-lite      # Parar serviço"
echo "  systemctl start mcp-mem0-lite     # Iniciar serviço"
echo "  systemctl restart mcp-mem0-lite   # Reiniciar serviço"
echo "  journalctl -u mcp-mem0-lite -f    # Ver logs em tempo real"
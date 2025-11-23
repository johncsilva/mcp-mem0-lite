# 🔧 Como Gerenciar o Servidor MCP Mem0-Lite

## 🛑 Parar o Servidor

### Opção 1: Matar processo por nome (recomendado)
```bash
pkill -f "python.*server.py"
```

### Opção 2: Encontrar PID e matar
```bash
# Encontrar o PID do servidor
ps aux | grep "python.*server.py" | grep -v grep

# Matar pelo PID (substitua XXXX pelo PID encontrado)
kill XXXX

# Se não responder, force:
kill -9 XXXX
```

### Opção 3: Verificar porta 8050 e matar processo
```bash
# Linux/WSL
lsof -ti:8050 | xargs kill -9

# Alternativa
netstat -tlnp | grep 8050
# Anote o PID e: kill -9 PID
```

## ▶️ Iniciar o Servidor

### Modo 1: Interativo (para debug)
```bash
# Ativa ambiente virtual
source .venv/bin/activate

# Inicia servidor (Ctrl+C para parar)
python server.py
```

### Modo 2: Background (daemon)
```bash
# Ativa ambiente virtual e roda em background
source .venv/bin/activate && nohup python server.py > server.log 2>&1 &

# Verificar se está rodando
ps aux | grep "python.*server.py"

# Ver logs em tempo real
tail -f server.log
```

### Modo 3: Usando screen (recomendado para WSL)
```bash
# Instalar screen (se não tiver)
sudo apt-get install screen

# Criar sessão
screen -S mcp-server

# Dentro da sessão:
source .venv/bin/activate
python server.py

# Sair da sessão (servidor continua rodando): Ctrl+A depois D

# Voltar para a sessão
screen -r mcp-server

# Listar sessões
screen -ls
```

### Modo 4: Usando tmux
```bash
# Instalar tmux (se não tiver)
sudo apt-get install tmux

# Criar sessão
tmux new -s mcp-server

# Dentro da sessão:
source .venv/bin/activate
python server.py

# Sair da sessão: Ctrl+B depois D

# Voltar para a sessão
tmux attach -t mcp-server
```

## 🔄 Reiniciar o Servidor

```bash
# Parar e iniciar em um comando
pkill -f "python.*server.py" && sleep 2 && source .venv/bin/activate && nohup python server.py > server.log 2>&1 &
```

## ✅ Verificar Status do Servidor

### Verificar se está rodando
```bash
# Por processo
ps aux | grep "python.*server.py" | grep -v grep

# Por porta
lsof -i:8050
# ou
netstat -tlnp | grep 8050
```

### Testar endpoint
```bash
# Status do servidor
curl http://127.0.0.1:8050/

# Verificar se responde
curl -s http://127.0.0.1:8050/ | grep "status"
```

## 📋 Scripts Úteis

### Script de Start (criar: start.sh)
```bash
#!/bin/bash
echo "🚀 Iniciando servidor MCP Mem0-Lite..."

# Verifica se já está rodando
if pgrep -f "python.*server.py" > /dev/null; then
    echo "⚠️  Servidor já está rodando!"
    ps aux | grep "python.*server.py" | grep -v grep
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
```

### Script de Stop (criar: stop.sh)
```bash
#!/bin/bash
echo "🛑 Parando servidor MCP Mem0-Lite..."

if ! pgrep -f "python.*server.py" > /dev/null; then
    echo "⚠️  Servidor não está rodando"
    exit 0
fi

# Para o servidor
pkill -f "python.*server.py"

# Aguarda parar
sleep 2

# Verifica se parou
if pgrep -f "python.*server.py" > /dev/null; then
    echo "⚠️  Servidor não respondeu, forçando..."
    pkill -9 -f "python.*server.py"
    sleep 1
fi

if ! pgrep -f "python.*server.py" > /dev/null; then
    echo "✅ Servidor parado com sucesso!"
else
    echo "❌ Erro ao parar servidor"
    exit 1
fi
```

### Script de Restart (criar: restart.sh)
```bash
#!/bin/bash
echo "🔄 Reiniciando servidor MCP Mem0-Lite..."

# Para o servidor
bash stop.sh

# Aguarda
sleep 2

# Inicia o servidor
bash start.sh
```

### Script de Status (criar: status.sh)
```bash
#!/bin/bash
echo "📊 Status do Servidor MCP Mem0-Lite"
echo "======================================"

# Verifica processo
if pgrep -f "python.*server.py" > /dev/null; then
    echo "✅ Processo: RODANDO"
    PID=$(pgrep -f "python.*server.py")
    echo "📋 PID: $PID"

    # Tempo de execução
    ps -p $PID -o etime= | xargs echo "⏱️  Uptime:"

    # Memória
    ps -p $PID -o rss= | awk '{printf "💾 Memória: %.2f MB\n", $1/1024}'
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
    print(f\"📌 LLM: {data.get('configuration', {}).get('current', {}).get('llm_model', 'N/A')}\")
except:
    pass
"
else
    echo "❌ HTTP: NÃO RESPONDENDO"
fi

echo ""
echo "======================================"
```

## 🔧 Tornar scripts executáveis

```bash
chmod +x start.sh stop.sh restart.sh status.sh
```

## 📖 Uso dos Scripts

```bash
# Iniciar servidor
./start.sh

# Parar servidor
./stop.sh

# Reiniciar servidor
./restart.sh

# Ver status
./status.sh
```

## 🐛 Troubleshooting

### Erro: "Port already in use"
```bash
# Encontrar e matar processo na porta 8050
lsof -ti:8050 | xargs kill -9
```

### Erro: "Virtual environment not found"
```bash
# Criar virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Servidor não inicia
```bash
# Ver logs de erro
cat server.log

# Iniciar em modo debug
source .venv/bin/activate
python server.py
# (observe os erros no terminal)
```

### Verificar se Ollama está rodando
```bash
# Testar Ollama
curl http://127.0.0.1:11434/api/tags

# Se não responder, iniciar Ollama
ollama serve &
```

## 📁 Arquivos Importantes

- **server.py**: Código principal do servidor
- **server.log**: Logs do servidor (quando em background)
- **.env**: Configurações (DATABASE_URL, LLM_MODEL, etc.)
- **mem0.db**: Banco de dados SQLite
- **chroma_db/**: Vector store do ChromaDB

## 🔄 Quando Reiniciar

Reinicie o servidor após:
- ✅ Modificar server.py
- ✅ Modificar .env
- ✅ Atualizar dependências (pip install)
- ✅ Trocar modelo LLM manualmente no .env
- ❌ Adicionar/deletar memórias (não precisa)
- ❌ Fazer buscas (não precisa)

## 📊 Monitoramento

### Ver logs em tempo real
```bash
tail -f server.log
```

### Ver últimas 50 linhas
```bash
tail -50 server.log
```

### Buscar erros nos logs
```bash
grep -i error server.log
grep -i exception server.log
```

## 🚀 Autostart no Boot (Opcional)

### Systemd Service (Linux)
Criar arquivo `/etc/systemd/system/mcp-mem0-lite.service`:

```ini
[Unit]
Description=MCP Mem0-Lite Server
After=network.target

[Service]
Type=simple
User=john
WorkingDirectory=/home/john/projetos/Pessoal/mcp-mem0-lite
ExecStart=/home/john/projetos/Pessoal/mcp-mem0-lite/.venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-mem0-lite
sudo systemctl start mcp-mem0-lite
sudo systemctl status mcp-mem0-lite
```

---

**📚 Ver também**:
- README.md - Instalação e configuração
- GUIA_RAPIDO_REGRAS.md - Como usar regras de programação
- IMPLEMENTACAO_CONCLUIDA.md - Novas funcionalidades

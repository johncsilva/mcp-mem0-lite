# mcp-mem0-lite

Servidor MCP (FastAPI + FastMCP + Mem0) com embeddings/LLM via Ollama ou OpenAI, pronto para rodar no WSL.

## Instalação no WSL
1) Pré-requisitos: `python3-venv`, `python3-pip`, Git, e Ollama instalado no WSL (não no Windows).  
   ```bash
   sudo apt update && sudo apt install -y python3-venv python3-pip git
   ```
2) Ambiente Python:
   ```bash
   cd /home/john/projetos/Pessoal/mcp-mem0-lite
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3) Modelos (Ollama dentro do WSL):
   ```bash
   ollama pull llama3.2:latest
   ollama pull nomic-embed-text
   # se o serviço não estiver ativo: ollama serve
   ```
4) `.env` (paths Linux):
   ```env
   HOST=127.0.0.1
   PORT=8050
   DATABASE_URL=sqlite:///./mem0.db
   VECTOR_STORE_PROVIDER=chroma
   CHROMA_PERSIST_DIR=./chroma_db
   EMBEDDING_PROVIDER=ollama
   EMBEDDING_MODEL=nomic-embed-text
   EMBEDDING_DIMS=768
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.2:latest
   # se usar OpenAI, troque provider/model e defina OPENAI_API_KEY
   ```
5) Rodar:
   ```bash
   source .venv/bin/activate
   python server.py
   ```

## Smoke test rápido
Com o servidor rodando e o venv ativo:
```bash
python test_mcp_tools.py
```
Ele adiciona/busca/lista uma memória de teste.

## Integrar com Codex CLI (MCP)
Adicione o servidor MCP no Codex:
```bash
codex mcp add mem0-lite -- npx -y mcp-remote@latest http://127.0.0.1:8050/mcp/sse
codex mcp list
```
Ou configure em `~/.config/codex/codex_config.toml`:
```toml
[features]
rmcp_client = true

[mcp_servers.mem0-lite]
command = "npx"
args = ["-y", "mcp-remote@latest", "http://127.0.0.1:8050/mcp/sse"]
```

## Integrar com Claude Code CLI (MCP)

### 1. Verificar se o servidor está rodando
```bash
curl http://127.0.0.1:8050/mcp/sse
```

### 2. Configurar o Claude Code
Edite `~/.claude.json` (crie se não existir):
```bash
nano ~/.claude.json
```

Adicione:
```json
{
  "mcpServers": {
    "mem0-lite": {
      "type": "sse",
      "url": "http://127.0.0.1:8050/mcp/sse"
    }
  }
}
```

### 3. Verificar conexão
```bash
claude mcp list
# Deve mostrar: mem0-lite [connected]
```

### 4. Testar os tools
```bash
# Listar usuários
claude "Use o tool list_all_user_ids"

# Adicionar memória
claude "Adicione uma memória de teste: 'Configuração do MCP concluída'"
```

### Troubleshooting
```bash
# Validar JSON
cat ~/.claude.json | python -m json.tool

# Verificar servidor
curl -v http://127.0.0.1:8050/

# Ver logs do servidor (na janela onde está rodando)
```

## Integrar com OpenCode CLI (MCP)

O OpenCode suporta servidores MCP remotos via SSE.

### 1. Verificar se o servidor está rodando
```bash
curl http://127.0.0.1:8050/mcp/sse
```

### 2. Configurar o OpenCode
Edite ou crie `~/.opencode/opencode.jsonc` (ou o arquivo de config do OpenCode):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "mem0-lite": {
      "type": "remote",
      "url": "http://127.0.0.1:8050/mcp/sse",
      "enabled": true
    }
  }
}
```

### 3. Verificar conexão
Inicie o OpenCode no diretório do projeto:
```bash
opencode
```

E teste os tools:
```bash
# Listar usuários
Use o tool list_all_user_ids

# Adicionar memória
Adicione uma memória de teste: 'Configuração do MCP concluída no OpenCode'
```

### Troubleshooting
- Certifique-se de que o servidor está rodando antes de iniciar o OpenCode
- Verifique se a URL está correta: `http://127.0.0.1:8050/mcp/sse`
- O arquivo de exemplo `opencode.jsonc` neste repositório pode ser usado como referência

## Integrar com Gemini CLI (MCP)

Devido a um comportamento inesperado do `gemini-cli` com o comando `mcp add` para servidores SSE, a configuração precisa ser feita editando-se manualmente o arquivo de configurações do Gemini CLI.

### 1. Localize e Abra o Arquivo de Configuração:
O arquivo de configuração do Gemini CLI para o usuário geralmente está localizado em `~/.gemini/settings.json` (ou `/home/seu_usuario/.gemini/settings.json` no Linux).

Abra este arquivo em seu editor de texto preferido.

### 2. Edite a Seção `mcpServers`:
Dentro do arquivo `settings.json`, localize ou adicione a chave `"mcpServers"`. Dentro dela, adicione ou modifique a entrada para `"mem0-lite"` para que fique exatamente como no exemplo abaixo.

**Exemplo de estrutura no `settings.json`:**

```json
{
  // ... outras configurações do Gemini CLI ...

  "mcpServers": {
    "mem0-lite": {
      "type": "sse",
      "url": "http://127.0.0.1:8050/mcp/sse"
    }
    // ... outros servidores MCP, se houver, garantindo vírgulas corretas ...
  }

  // ... outras configurações do Gemini CLI ...
}
```

**Observações importantes:**
*   Substitua as seções `// ... outras configurações ...` pelo conteúdo já existente no seu arquivo.
*   **Atenção às vírgulas:** Certifique-se de que a sintaxe JSON esteja correta. Se houver outras chaves antes ou depois de `mcpServers`, ou outros servidores MCP dentro de `mcpServers`, use vírgulas para separá-los.
*   Salve e feche o arquivo `settings.json`.

### 3. Verifique a Conexão:
Com o seu servidor `server.py` já em execução em outro terminal, abra um **novo** terminal e execute:

```powershell
gemini mcp list
```

✅ **Deve mostrar**: `mem0-lite` como `✓ Connected`.

## Claude Desktop (Linux/WSL)
Copie `claude_desktop_config.json` para `~/.config/Claude/claude_desktop_config.json` e reinicie o app. O comando deve apontar para `python` e o caminho do `server.py` no WSL.
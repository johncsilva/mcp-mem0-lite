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
   python3 server.py
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
# MCP Server como serviço do Windows (WinSW + WSL)

Roda `python server.py` no WSL (distro `Ubuntu-24.04`) ativando o venv Linux `.venv`.

## Arquivos
- `run-mcp.bat`: chama o WSL e roda o servidor.
- `mcpserver-service.xml`: configuração do WinSW (nome/id do serviço, logs, auto start).

## Ajustes necessários
1) Baixe o WinSW (release mais recente) de https://github.com/winsw/winsw/releases e coloque o `.exe` na mesma pasta destes arquivos, renomeando para `mcpserver-service.exe`.
2) Edite caminhos:
   - `run-mcp.bat`:
     - `DISTRO=Ubuntu-24.04` (troque se o nome for diferente, veja com `wsl -l -q`).
     - `APP=/home/john/projetos/Pessoal/mcp-mem0-lite` (ajuste se o projeto estiver em outro lugar).
   - `mcpserver-service.xml`:
     - `<arguments>/c "C:\Path\To\run-mcp.bat"</arguments>` → coloque o caminho Windows onde o `.bat` ficará.
     - `<logpath>C:\Path\To\logs</logpath>` → crie essa pasta ou ajuste.
3) (Opcional) Ajuste `<id>` e `<name>` no XML se quiser outro nome de serviço.

## Instalar e testar
No Prompt/PowerShell **como Administrador**, na pasta do `mcpserver-service.exe`:
```bat
mcpserver-service.exe install
mcpserver-service.exe start
mcpserver-service.exe status
```
Teste o servidor (ex.: `curl http://localhost:11434/api/tags` ou endpoint do MCP) para confirmar que subiu.

## Parar, reiniciar, remover
```bat
mcpserver-service.exe stop
mcpserver-service.exe restart
mcpserver-service.exe uninstall
```

## Notas
- O serviço chama `wsl -d <DISTRO> -- bash -lc "cd <APP> && source .venv/bin/activate && python server.py"`.
- O Windows acessa `\\wsl$\\<DISTRO>` quando o WSL está ativo; geralmente o comando já acorda a distro. Se quiser garantir, crie uma tarefa simples no Agendador rodando `wsl -d <DISTRO> -- true` no boot.
- Se mudar o caminho do projeto/venv, atualize o `.bat`. Se editar o XML, reinicie o serviço (`stop`/`start` ou `restart`).***

# Para o Ollama no WSL iniciar com o Windows, use estes comandos/ajustes:

- Garantir systemd ativo no WSL (faça uma vez, dentro do WSL):

  sudo systemctl enable --now ollama
  systemctl status ollama
  No windows, se ainda não tiver a configuraçao, em /etc/wsl.conf: 
  ```
  [boot]
    nsystemd=true
  ```
  depois wsl --shutdown no Windows, reabrir a distro. 
- Fazer o WSL acordar no boot do Windows:
    - Crie uma tarefa no Agendador (“Ao iniciar o computador”) com ação:
      wsl -d Ubuntu-24.04 -- true
      Isso apenas acorda a distro; o systemd sobe e o serviço ollama inicia porque está enabled.
- Alternativa (mais explícito):
      wsl -d Ubuntu-24.04 -- systemctl start ollama
      como ação da tarefa.
- Testar após reboot:
    - Dentro do WSL: curl http://localhost:11434/api/tags
    - Do Windows: curl http://localhost:11434/api/tags (porta 11434 deve responder).

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

## Integrar com Claude Desktop (SSE)

Claude Desktop pode se conectar ao servidor que já está rodando via SSE, compartilhando a mesma instância com Claude Code CLI.

### Windows

#### 1. Verificar se o servidor está rodando
```powershell
curl http://127.0.0.1:8050/mcp/sse
```

#### 2. Abrir arquivo de configuração
```powershell
notepad %APPDATA%\Claude\claude_desktop_config.json
```

#### 3. Adicionar configuração (SSE)
```json
{
  "mcpServers": {
    "mem0-lite": {
      "command": "wsl",
      "args": [
        "bash",
        "-c",
        "npx -y mcp-remote@latest http://localhost:8050/mcp/sse"
      ]
    }
  }
}
```

#### 4. Reiniciar Claude Desktop
Feche completamente o Claude Desktop e abra novamente.
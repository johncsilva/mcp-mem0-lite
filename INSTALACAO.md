# Guia de Instalação - MCP Mem0-Lite

> **Guia completo para instalação do servidor MCP Mem0-Lite em uma máquina Windows limpa**

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Instalação do Python](#1-instalação-do-python)
3. [Instalação do Ollama](#2-instalação-do-ollama)
4. [Download dos Modelos LLM](#3-download-dos-modelos-llm)
5. [Configuração do Projeto](#4-configuração-do-projeto)
6. [Instalação das Dependências Python](#5-instalação-das-dependências-python)
7. [Configuração do Ambiente](#6-configuração-do-ambiente)
8. [Configuração dos Clientes MCP](#7-configuração-dos-clientes-mcp)
9. [Iniciando o Servidor](#8-iniciando-o-servidor)
10. [Verificação da Instalação](#9-verificação-da-instalação)
11. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

### Hardware Mínimo Recomendado
- **CPU**: 4 cores (Intel i5/AMD Ryzen 5 ou superior)
- **RAM**: 16 GB (mínimo 8 GB)
- **Disco**: 20 GB de espaço livre
- **GPU** (opcional): NVIDIA RTX para aceleração (10-30x mais rápido)

### Software
- Windows 10/11 (64-bit)
- Conexão com internet (para download inicial)
- Privilégios de administrador (para instalação)

### Verificação do Sistema

Abra o PowerShell e verifique:

```powershell
# Verificar versão do Windows
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"

# Verificar memória RAM
systeminfo | findstr /C:"Total Physical Memory"

# Verificar espaço em disco (unidade C:)
wmic logicaldisk where "DeviceID='C:'" get Size,FreeSpace
```

---

## 1. Instalação do Python

### 1.1 Download do Python 3.12

1. Acesse: https://www.python.org/downloads/
2. Baixe **Python 3.12.x** (versão mais recente da série 3.12)
3. Execute o instalador `python-3.12.x-amd64.exe`

### 1.2 Instalação

⚠️ **IMPORTANTE**: Durante a instalação:

✅ **MARQUE** a opção: **"Add Python 3.12 to PATH"**
✅ Selecione: **"Install Now"** ou **"Customize installation"**

Se escolher "Customize installation":
- ✅ Marque todas as opções em "Optional Features"
- ✅ Em "Advanced Options", marque:
  - "Install for all users"
  - "Add Python to environment variables"
  - "Precompile standard library"

### 1.3 Verificação

Abra um **novo** PowerShell e execute:

```powershell
python --version
# Deve retornar: Python 3.12.x

pip --version
# Deve retornar: pip 24.x.x from ...
```

❌ **Se não funcionar**:
- Feche e reabra o PowerShell
- Se ainda não funcionar, reinicie o computador

---

## 2. Instalação do Ollama

### 2.1 Download

1. Acesse: https://ollama.com/download
2. Clique em **"Download for Windows"**
3. Baixe o arquivo `OllamaSetup.exe`

### 2.2 Instalação

1. Execute `OllamaSetup.exe`
2. Siga o assistente de instalação (Next → Install → Finish)
3. Ollama será instalado e iniciado automaticamente

### 2.3 Verificação

Abra um **novo** PowerShell e execute:

```powershell
ollama --version
# Deve retornar: ollama version x.x.x
```

Para verificar se o servidor Ollama está rodando:

```powershell
curl http://127.0.0.1:11434/api/tags
```

✅ **Se retornar JSON** → Ollama está rodando
❌ **Se falhar** → Execute: `ollama serve` em um terminal separado

---

## 3. Download dos Modelos LLM

Os modelos são necessários para o funcionamento do Mem0-Lite.

### 3.1 Modelo LLM (Processamento de Memórias)

**Modelo recomendado**: `llama3.2:latest` (3B parâmetros, ~2GB)

```powershell
ollama pull llama3.2:latest
```

⏱️ **Tempo estimado**: 5-15 minutos (depende da conexão)

> **Nota**: `tinyllama` é mais rápido (~10s por memória) mas pode falhar ao gerar IDs estruturados. Use `llama3.2:latest` (~35s por memória) para maior confiabilidade.

### 3.2 Modelo de Embeddings (Busca Vetorial)

**Modelo obrigatório**: `nomic-embed-text` (768 dimensões, ~274MB)

```powershell
ollama pull nomic-embed-text
```

⏱️ **Tempo estimado**: 1-3 minutos

### 3.3 Verificação dos Modelos

```powershell
ollama list
```

✅ **Deve listar**:
```
NAME                    ID              SIZE    MODIFIED
llama3.2:latest         a80c4f17acd5    2.0 GB  X minutes ago
nomic-embed-text:latest 0a109f422b47    274 MB  X minutes ago
```

---

## 4. Configuração do Projeto

### 4.1 Escolha do Diretório

Escolha onde instalar o projeto. Exemplo: `C:\Dev\mcp-mem0-lite`

```powershell
# Criar diretório
mkdir C:\Dev\mcp-mem0-lite
cd C:\Dev\mcp-mem0-lite
```

### 4.2 Copiar Arquivos do Projeto

**Opção A: Se você tem os arquivos em outra máquina**

1. Copie toda a pasta `mcp-mem0-lite` da máquina de origem
2. Cole em `C:\Dev\` na máquina de destino
3. **Exclua** as seguintes pastas (se existirem):
   - `.venv/` (ambiente virtual - será recriado)
   - `chroma_db/` (banco de dados - será recriado)
   - `mem0.db` (banco de dados - será recriado)

**Opção B: Se você tem os arquivos compactados**

1. Extraia o arquivo `.zip` em `C:\Dev\`
2. Certifique-se de que a estrutura seja: `C:\Dev\mcp-mem0-lite\server.py`

### 4.3 Estrutura de Arquivos Necessária

Verifique se você tem os seguintes arquivos:

```
C:\Dev\mcp-mem0-lite\
├── server.py              ✅ (Servidor MCP principal)
├── .env                   ✅ (Configurações)
├── start_mcp.bat          ✅ (Script de inicialização)
├── reset_memory.bat       ✅ (Script para limpar memórias)
├── benchmark_speed.py     ⭕ (Opcional - testes de performance)
├── test_mcp_tools.py      ⭕ (Opcional - testes)
├── validate_mcp.py        ⭕ (Opcional - validação)
└── README.md              ⭕ (Opcional - documentação)
```

✅ = Obrigatório | ⭕ = Opcional

---

## 5. Instalação das Dependências Python

### 5.1 Criar Ambiente Virtual

```powershell
cd C:\Dev\mcp-mem0-lite
python -m venv .venv
```

### 5.2 Ativar Ambiente Virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

⚠️ **Se aparecer erro de política de execução**:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois execute novamente: `.\.venv\Scripts\Activate.ps1`

✅ **Ambiente ativado**: O prompt deve mostrar `(.venv)` no início

### 5.3 Atualizar pip

```powershell
python -m pip install --upgrade pip
```

### 5.4 Instalar Dependências

```powershell
pip install fastapi uvicorn python-dotenv pydantic
pip install mem0ai
pip install mcp
pip install chromadb
pip install ollama
```

⏱️ **Tempo estimado**: 2-5 minutos

### 5.5 Verificação

```powershell
pip list | findstr -i "fastapi mem0 mcp chroma ollama"
```

✅ **Deve listar todas as bibliotecas instaladas**

---

## 6. Configuração do Ambiente

### 6.1 Editar o Arquivo `.env`

Abra o arquivo `.env` com o Bloco de Notas:

```powershell
notepad .env
```

### 6.2 Configurar Caminhos

**IMPORTANTE**: Ajuste os caminhos para o seu computador.

Se você instalou em `C:\Dev\mcp-mem0-lite`, mantenha assim:

```env
# MCP
HOST=127.0.0.1
PORT=8050

# Metadados (leve)
DATABASE_URL=sqlite:///C:/Dev/mcp-mem0-lite/mem0.db

# Vector store local: CHROMA
VECTOR_STORE_PROVIDER=chroma
CHROMA_PERSIST_DIR=C:/Dev/mcp-mem0-lite/chroma_db

# Embeddings via Ollama
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMS=768

# LLM local para processamento de memorias
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:latest
```

⚠️ **Se instalou em outro local** (ex: `D:\Projetos\mcp-mem0-lite`):
- Substitua `C:/Dev/mcp-mem0-lite` por `D:/Projetos/mcp-mem0-lite`
- **Use `/` (barra) ao invés de `\` (contrabarra)** nos caminhos

### 6.3 Salvar e Fechar

1. Salve: `Ctrl+S`
2. Feche o Bloco de Notas

---

## 7. Configuração dos Clientes MCP

Os clientes MCP (Claude Code, Gemini CLI, Codex) precisam saber onde está o servidor.

### 7.1 Claude Code (Obrigatório)

Claude Code usa o arquivo `~/.claude.json` para configuração.

#### Windows

```powershell
# Abrir arquivo de configuração
notepad "$env:USERPROFILE\.claude.json"
```

Se o arquivo não existir, crie-o.

#### Adicionar Configuração

Adicione ou edite a seção `mcpServers`:

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

Salve e feche.

#### Verificar Conexão

Após iniciar o servidor (próximos passos), no Claude Code execute:

```
claude mcp list
```

✅ **Deve mostrar**: `mem0-lite` conectado

---

### 7.2 Gemini CLI (Opcional)

Se você usa o Gemini CLI:

```powershell
# Adicionar servidor MCP
gemini mcp add mem0-lite --scope user --command "npx" --args "-y" --args "mcp-remote@latest" --args "http://127.0.0.1:8050/mcp/sse"
```

#### Verificar

```powershell
gemini mcp list
```

✅ **Deve mostrar**: `mem0-lite` (pode aparecer "Disconnected" até o servidor iniciar)

---

### 7.3 OpenAI Codex (Opcional)

Se você usa o Codex:

```powershell
# Adicionar servidor MCP
codex mcp add mem0-lite -- npx -y mcp-remote@latest http://127.0.0.1:8050/mcp/sse
```

#### Verificar

```powershell
codex mcp list
```

✅ **Deve mostrar**: `mem0-lite` configurado

---

## 8. Iniciando o Servidor

### 8.1 Primeiro Início (Manual)

Para entender o processo, vamos iniciar manualmente:

```powershell
# Ativar ambiente virtual (se ainda não estiver ativado)
.\.venv\Scripts\Activate.ps1

# Iniciar servidor
python server.py
```

✅ **Servidor iniciado com sucesso** se você ver:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8050 (Press CTRL+C to quit)
```

⏱️ **Tempo de inicialização**: 5-10 segundos

Para parar o servidor: `Ctrl+C`

---

### 8.2 Usando o Script de Inicialização (Recomendado)

O script `start_mcp.bat` automatiza o processo:

1. Verifica se Ollama está rodando (inicia se necessário)
2. Verifica se servidor MCP está rodando (inicia se necessário)
3. Aguarda tudo ficar online
4. Mostra "TUDO OK!" quando pronto

#### Executar Script

```powershell
cd C:\Dev\mcp-mem0-lite
.\start_mcp.bat
```

#### O que esperar

```
========================================
  MCP Mem0-Lite Startup Script
========================================

[1/3] Verificando Ollama...
  [OK] Ollama ja esta rodando

[2/3] Verificando servidor MCP...
  [INICIANDO] Servidor MCP nao encontrado, iniciando...
  [OK] Servidor MCP iniciado com sucesso

[3/3] Validando integracao...
  [OK] Endpoint SSE acessivel

========================================
  TUDO OK!
========================================
  Ollama:      http://127.0.0.1:11434
  MCP Server:  http://127.0.0.1:8050
  SSE:         http://127.0.0.1:8050/mcp/sse
========================================

Pressione qualquer tecla para fechar...
```

⚠️ **Não feche a janela do servidor** - ele precisa ficar rodando em segundo plano.

---

## 9. Verificação da Instalação

### 9.1 Testar Servidor MCP

Em um **novo** PowerShell:

```powershell
# Testar endpoint raiz
curl http://127.0.0.1:8050/

# Testar endpoint SSE
curl --max-time 2 http://127.0.0.1:8050/mcp/sse
```

✅ **Se funcionar**: Servidor está respondendo

### 9.2 Testar no Claude Code

No Claude Code, execute:

```
Use o tool list_all_user_ids para listar todos os usuários
```

✅ **Se funcionar**: MCP está integrado corretamente

### 9.3 Adicionar Primeira Memória

No Claude Code:

```
Adicione uma memória de teste: "Instalação do MCP Mem0-Lite concluída com sucesso!"
```

⏱️ **Tempo esperado**: 30-40 segundos (primeira vez pode ser mais lento)

✅ **Sucesso**: Claude deve confirmar que a memória foi salva

### 9.4 Listar Memórias

```
Liste minhas memórias
```

✅ **Deve retornar**: A memória de teste que você acabou de criar

---

## Troubleshooting

### ❌ Problema: Python não é reconhecido

**Erro**: `'python' is not recognized as an internal or external command`

**Solução**:
1. Feche e reabra o PowerShell
2. Se ainda não funcionar, reinicie o computador
3. Verifique se o Python está no PATH:
   ```powershell
   $env:PATH -split ';' | Select-String -Pattern 'Python'
   ```
4. Se não aparecer, reinstale o Python marcando "Add to PATH"

---

### ❌ Problema: Ollama não está respondendo

**Erro**: `Connection refused` ou `Failed to connect to Ollama`

**Solução**:
1. Verifique se Ollama está rodando:
   ```powershell
   curl http://127.0.0.1:11434/api/tags
   ```
2. Se não responder, inicie manualmente:
   ```powershell
   ollama serve
   ```
3. Deixe essa janela aberta e tente novamente

---

### ❌ Problema: Porta 8050 já está em uso

**Erro**: `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8050)`

**Solução**:
1. Encontre o processo usando a porta:
   ```powershell
   netstat -ano | findstr :8050
   ```
2. Mate o processo (substitua `<PID>` pelo número da última coluna):
   ```powershell
   taskkill /F /PID <PID>
   ```

---

### ❌ Problema: Memórias não são salvas (erro de ID)

**Erro**: `Error processing memory action: ... Error: '<ID of the memory>'`

**Causa**: Modelo LLM (`tinyllama`) muito pequeno para gerar IDs estruturados

**Solução**:
1. Edite `.env` e mude para modelo maior:
   ```env
   LLM_MODEL=llama3.2:latest
   ```
2. Reinicie o servidor
3. Limpe memórias corrompidas:
   ```powershell
   .\reset_memory.bat
   ```

---

### ❌ Problema: add_memory muito lento (60+ segundos)

**Causa**: Modelo LLM grande (`llama3.1:8b`) sem GPU

**Soluções**:

**Opção 1**: Usar modelo menor (aceitar trade-off de qualidade)
```env
LLM_MODEL=llama3.2:latest  # ~35s por memória
```

**Opção 2**: Usar GPU (se disponível)
- Ollama usa GPU automaticamente se detectar NVIDIA GPU
- Reduz tempo de 60s para 2-5s

**Opção 3**: Usar API externa (requer chave API)
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-3-haiku-20240307
```

---

### ❌ Problema: Claude Code não vê o servidor MCP

**Sintomas**: `claude mcp list` não mostra `mem0-lite` ou mostra "Failed to connect"

**Soluções**:

1. Verifique se servidor está rodando:
   ```powershell
   curl http://127.0.0.1:8050/mcp/sse
   ```

2. Verifique configuração do Claude:
   ```powershell
   notepad "$env:USERPROFILE\.claude.json"
   ```

   Deve ter:
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

3. Reinicie o Claude Code

---

### ❌ Problema: Erro de importação `ModuleNotFoundError`

**Erro**: `ModuleNotFoundError: No module named 'mem0'` (ou outro módulo)

**Solução**:
1. Certifique-se de que o ambiente virtual está ativado:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   (deve mostrar `(.venv)` no prompt)

2. Reinstale dependências:
   ```powershell
   pip install --force-reinstall mem0ai mcp fastapi uvicorn chromadb ollama python-dotenv pydantic
   ```

---

### ❌ Problema: Executar scripts .bat falha

**Erro**: Não pode executar `.bat` no PowerShell

**Solução**:
Use `cmd` ou `.\`:
```powershell
# Opção 1: Via cmd
cmd /c start_mcp.bat

# Opção 2: Com .\
.\start_mcp.bat
```

---

### 🆘 Resetar Tudo

Se algo der muito errado e quiser recomeçar do zero:

```powershell
cd C:\Dev\mcp-mem0-lite

# Parar servidor
taskkill /F /IM python.exe

# Limpar bancos de dados
.\reset_memory.bat

# Recriar ambiente virtual
rmdir /s /q .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Reinstalar dependências
pip install --upgrade pip
pip install fastapi uvicorn python-dotenv pydantic mem0ai mcp chromadb ollama

# Reiniciar
.\start_mcp.bat
```

---

## 📚 Recursos Adicionais

### Documentação Oficial

- **Mem0**: https://docs.mem0.ai/
- **MCP (Model Context Protocol)**: https://modelcontextprotocol.io/
- **Ollama**: https://ollama.com/
- **ChromaDB**: https://docs.trychroma.com/

### Comandos Úteis

```powershell
# Listar modelos Ollama instalados
ollama list

# Remover modelo não usado
ollama rm <model_name>

# Ver logs do servidor (se rodando em background)
# (abrir a janela do servidor)

# Verificar uso de memória do Ollama
tasklist /FI "IMAGENAME eq ollama.exe"

# Verificar processos Python rodando
tasklist /FI "IMAGENAME eq python.exe"
```

### Scripts Auxiliares

- `start_mcp.bat` - Iniciar Ollama + Servidor MCP (com verificações)
- `reset_memory.bat` - Limpar todas as memórias (apaga bancos de dados)
- `benchmark_speed.py` - Testar velocidade do add_memory
- `test_mcp_tools.py` - Testar todos os tools MCP

---

## ✅ Checklist Final

Antes de considerar a instalação completa, verifique:

- [ ] Python 3.12+ instalado e no PATH
- [ ] Ollama instalado e rodando
- [ ] Modelo `llama3.2:latest` baixado
- [ ] Modelo `nomic-embed-text` baixado
- [ ] Projeto copiado para `C:\Dev\mcp-mem0-lite`
- [ ] Ambiente virtual criado (`.venv/`)
- [ ] Dependências instaladas (mem0, mcp, fastapi, etc)
- [ ] Arquivo `.env` configurado com caminhos corretos
- [ ] Claude Code configurado (`~/.claude.json`)
- [ ] Servidor inicia sem erros (`.\start_mcp.bat`)
- [ ] Claude Code conecta ao servidor (`claude mcp list`)
- [ ] Consegue adicionar e listar memórias
- [ ] `list_all_user_ids` retorna seu username do Windows

Se todos os itens estiverem ✅, a instalação está completa!

---

## 🎉 Próximos Passos

Agora que o servidor está instalado:

1. **Explorar os Tools MCP**:
   - `add_memory` - Adicionar memórias
   - `search_memory` - Busca semântica
   - `list_memories` - Listar todas as memórias
   - `list_all_user_ids` - Ver usuários com memórias
   - `delete_memory` - Apagar memória específica

2. **Usar no Claude Code**:
   - Peça ao Claude para salvar informações importantes
   - Use busca semântica para recuperar contexto
   - Memórias persistem entre sessões

3. **Integrar com Gemini/Codex** (opcional):
   - Siga as instruções da seção 7.2 e 7.3
   - Compartilhe memórias entre diferentes AIs

4. **Ajustar Performance**:
   - Se muito lento: use modelo menor ou API externa
   - Se tem GPU: Ollama usará automaticamente
   - Consulte `PERFORMANCE_TUNING.md` para detalhes

---

**Instalação criada em**: 2025-11-12
**Versão do guia**: 1.0
**Testado em**: Windows 10/11, Python 3.12, Ollama 0.5+

Para suporte ou dúvidas, consulte a documentação oficial ou os recursos listados acima.

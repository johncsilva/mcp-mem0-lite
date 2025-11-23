# Iniciar Servidor MCP no WSL Automaticamente com o Windows

Este guia mostra como configurar o servidor MCP Mem0-Lite rodando no WSL para iniciar automaticamente quando o Windows iniciar, **sem precisar abrir manualmente o WSL**.

## Arquivos Criados

- **start_wsl_mcp.bat**: Script que inicia o servidor no WSL
- **start_wsl_mcp_silent.vbs**: Script VBS que executa o .bat sem mostrar janelas

## Pré-requisitos

1. ✅ WSL instalado e configurado
2. ✅ Servidor MCP funcionando no WSL
3. ✅ Distribuição WSL chamada "Ubuntu" (ou ajuste o nome no script)

## Método 1: Agendador de Tarefas do Windows (Recomendado)

### Passos Detalhados:

1. **Abra o Agendador de Tarefas**
   - Pressione `Win + R`
   - Digite `taskschd.msc`
   - Pressione Enter

2. **Crie uma Nova Tarefa**
   - Clique em "Criar Tarefa..." (não "Criar Tarefa Básica")

3. **Aba "Geral"**
   - Nome: `MCP WSL Auto Start`
   - Descrição: `Inicia servidor MCP Mem0-Lite no WSL automaticamente`
   - ✅ Marque: "Executar estando o usuário conectado ou não"
   - Configure para: Windows 10

4. **Aba "Disparadores"**
   - Clique em "Novo..."
   - Iniciar a tarefa: **No logon**
   - Configurações específicas: **Usuário específico** (seu usuário)
   - Atrasar tarefa por: **30 segundos** (dar tempo do WSL estar pronto)
   - ✅ Marque: "Ativado"
   - Clique em "OK"

5. **Aba "Ações"**

   **Opção A - Usando VBScript (sem janelas):**
   - Programa/script: `wscript.exe`
   - Argumentos: `"\\wsl.localhost\Ubuntu\home\john\projetos\Pessoal\mcp-mem0-lite\start_wsl_mcp_silent.vbs"`

   **Opção B - Usando WSL diretamente:**
   - Programa/script: `wsl.exe`
   - Argumentos: `-d Ubuntu -e bash -c "nohup /home/john/projetos/Pessoal/mcp-mem0-lite/mcp-mem0-lite-global.sh > /dev/null 2>&1 &"`

6. **Aba "Condições"**
   - ✅ Marque: "Iniciar somente se a seguinte conexão de rede estiver disponível: Qualquer conexão"
   - ❌ Desmarque: "Iniciar a tarefa apenas se o computador estiver conectado à energia CA"

7. **Aba "Configurações"**
   - ✅ Marque: "Permitir que a tarefa seja executada sob demanda"
   - ✅ Marque: "Executar tarefa o mais breve possível após a execução agendada ser perdida"
   - Se a tarefa já estiver em execução: **Não iniciar uma nova instância**

8. **Finalizar**
   - Clique em "OK"
   - Digite sua senha se solicitado

### Testar Agora:

```cmd
# No PowerShell ou CMD como Administrador
schtasks /run /tn "MCP WSL Auto Start"

# Aguarde alguns segundos e teste
curl http://127.0.0.1:8050/
```

---

## Método 2: Pasta de Inicialização (Mais Simples)

### Passos:

1. **Abra a pasta de inicialização**
   - Pressione `Win + R`
   - Digite: `shell:startup`
   - Pressione Enter

2. **Copie o arquivo VBS**
   - Navegue até seu projeto no WSL via: `\\wsl.localhost\Ubuntu\home\john\projetos\Pessoal\mcp-mem0-lite\`
   - Copie o arquivo `start_wsl_mcp_silent.vbs`
   - Cole na pasta de inicialização

   **OU crie um atalho:**
   - Botão direito → Novo → Atalho
   - Local: `wsl.exe -d Ubuntu -e bash -c "nohup /home/john/projetos/Pessoal/mcp-mem0-lite/mcp-mem0-lite-global.sh > /dev/null 2>&1 &"`
   - Nome: `MCP WSL Server`

3. **Teste**
   - Clique duplo no atalho/arquivo
   - Aguarde alguns segundos
   - Teste: `curl http://127.0.0.1:8050/`

---

## Método 3: Executar como Tarefa ao Iniciar Sistema

Para iniciar antes do logon do usuário (mais avançado):

```cmd
# Abra PowerShell como Administrador

# Crie a tarefa
$action = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d Ubuntu -e bash -c 'nohup /home/john/projetos/Pessoal/mcp-mem0-lite/mcp-mem0-lite-global.sh > /dev/null 2>&1 &'"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings

# Registre a tarefa
Register-ScheduledTask -TaskName "MCP_WSL_System" -InputObject $task
```

---

## Verificar se Está Funcionando

### Após configurar:

1. **Reinicie o Windows**

2. **Após login, verifique no WSL:**
   ```bash
   # No WSL
   ps aux | grep python | grep server.py
   ```

3. **Teste a API:**
   ```bash
   curl http://127.0.0.1:8050/
   curl http://127.0.0.1:8050/mcp/sse
   ```

4. **Verifique se o Ollama também está rodando:**
   ```bash
   curl http://127.0.0.1:11434/api/tags
   ```

---

## Importante: Ajustar Nome da Distribuição WSL

Se sua distribuição WSL não se chama "Ubuntu", ajuste nos scripts:

```bash
# Verificar nome da distribuição
wsl -l -v
```

Se aparecer "Ubuntu-22.04" ou outro nome, edite:
- `start_wsl_mcp.bat`: linha com `wsl -d Ubuntu`
- Nas tarefas agendadas: argumento `-d Ubuntu`

---

## Solução de Problemas

### WSL não inicia automaticamente:

1. **Habilite integração WSL com Windows:**
   ```powershell
   # PowerShell como Admin
   wsl --update
   wsl --set-default-version 2
   ```

2. **Verifique se o WSL está configurado para iniciar:**
   - Abra `C:\Users\{SeuUsuário}\.wslconfig`
   - Adicione:
   ```ini
   [wsl2]
   memory=4GB
   processors=2
   ```

### Servidor não inicia:

1. **Teste manualmente no WSL:**
   ```bash
   cd /home/john/projetos/Pessoal/mcp-mem0-lite
   ./mcp-mem0-lite-global.sh
   ```

2. **Verifique logs:**
   ```bash
   # No WSL
   journalctl --user -u mcp-mem0-lite -f
   ```

### Ollama não está rodando:

O script `mcp-mem0-lite-global.sh` tenta iniciar o Ollama automaticamente, mas se não funcionar:

```bash
# No WSL, adicione ao ~/.bashrc ou configure serviço systemd para Ollama
nohup ollama serve > /dev/null 2>&1 &
```

### Permissão negada:

```bash
# No WSL
chmod +x /home/john/projetos/Pessoal/mcp-mem0-lite/mcp-mem0-lite-global.sh
chmod +x /home/john/projetos/Pessoal/mcp-mem0-lite/start_wsl_mcp.bat
```

---

## Desativar Inicialização Automática

### Método 1 (Agendador de Tarefas):
```cmd
# PowerShell
Disable-ScheduledTask -TaskName "MCP WSL Auto Start"

# Ou remover completamente
Unregister-ScheduledTask -TaskName "MCP WSL Auto Start" -Confirm:$false
```

### Método 2 (Pasta de Inicialização):
1. Pressione `Win + R` → `shell:startup`
2. Delete o arquivo/atalho

---

## Vantagens desta Abordagem

✅ Servidor roda no WSL (Linux nativo)
✅ Inicia automaticamente com o Windows
✅ Não precisa abrir janela WSL manualmente
✅ Execução em background invisível
✅ Usa os scripts Linux existentes
✅ Melhor desempenho (ambiente Linux)

---

## Notas Finais

⚠️ **Caminho WSL**: O caminho `/home/john/projetos/Pessoal/mcp-mem0-lite` deve estar correto no seu sistema.

⚠️ **Delay no Boot**: É normal o servidor levar alguns segundos extras para ficar disponível após o boot do Windows.

⚠️ **Recursos**: O WSL + Ollama + servidor podem consumir recursos significativos ao iniciar.

⚠️ **Rede**: O servidor estará disponível em `127.0.0.1:8050` tanto no Windows quanto no WSL.

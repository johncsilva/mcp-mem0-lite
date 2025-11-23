# Performance Tuning - MCP Mem0-Lite

## Problema
`add_memory` demora 30-60+ segundos devido ao processamento LLM local (CPU).

## Benchmarks (CPU Intel/AMD)

| Modelo | Params | Tempo add_memory | Qualidade |
|--------|--------|------------------|-----------|
| llama3.1:8b | 8B | ~60s | Excelente |
| llama3.2:latest | 3B | ~35s | Muito Boa |
| phi3:mini | 3.8B | ~25s | Boa |
| tinyllama | 1.1B | ~10s | Aceitável |
| qwen2.5:0.5b | 0.5B | ~5s | Básica |

## Soluções Disponíveis

### 🚀 Opção 1: Modelo Menor (Implementada)
**Status**: ✅ Aplicada (llama3.2:latest)
**Ganho**: 60s → 35s (42% mais rápido)

```bash
# Trocar para modelo ainda menor
ollama pull tinyllama  # ~10s
# ou
ollama pull qwen2.5:0.5b  # ~5s
```

Edite `.env`:
```env
LLM_MODEL=tinyllama
```

### 🎮 Opção 2: GPU Acceleration
**Requer**: NVIDIA GPU (GTX 1060+) ou AMD GPU
**Ganho**: 60s → 2-5s (10-30x mais rápido)

Ollama automaticamente usa GPU se disponível. Verifique:
```bash
ollama ps  # deve mostrar GPU sendo usada
nvidia-smi  # verificar uso de GPU
```

### ☁️ Opção 3: API Externa (Claude/OpenAI)
**Requer**: API key + internet
**Ganho**: 60s → 1-3s
**Custo**: ~$0.0001-0.001 por memória

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-3-haiku-20240307

# ou OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

### ⚡ Opção 4: Fast Mode (Sem LLM)
**Implementação**: Criar parâmetro `fast_mode=True` em `add_memory`
**Ganho**: 60s → 3s (somente embedding)
**Trade-off**: Perde processamento inteligente (deduplicação, estruturação)

---

## Recomendações por Caso de Uso

### Desenvolvimento/Testes
✅ **tinyllama** (10s) - bom equilíbrio velocidade/qualidade

### Produção com Alta Qualidade
✅ **llama3.2 + GPU** (2-5s) ou **API externa** (1-3s)

### Prototipagem Rápida
✅ **qwen2.5:0.5b** (5s) ou **fast_mode** (3s)

---

## Aplicar Mudanças

1. Editar `.env`:
   ```env
   LLM_MODEL=tinyllama  # ou outro modelo
   ```

2. Reiniciar servidor:
   ```bash
   # Parar servidor atual
   # Iniciar novamente
   python server.py
   ```

3. Testar:
   ```bash
   python benchmark_speed.py
   ```

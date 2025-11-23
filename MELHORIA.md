# Otimizações para Armazenamento de Regras de Programação

## 📊 Análise do Caso de Uso

Regras de programação têm características únicas:
- **Estruturadas**: Têm padrões (contexto, condição, ação, exceções)
- **Hierárquicas**: Categorias (linguagem → framework → padrão)
- **Versionadas**: Evoluem com o tempo
- **Contextuais**: Aplicam-se a contextos específicos
- **Alta consulta**: Muito mais leituras que escritas
- **Precisão crítica**: Busca precisa retornar regras relevantes

## 🎯 Sugestões de Otimização

### 1. **Schema Estruturado para Regras**
Adicionar campos padronizados no metadata:

```python
# Estrutura sugerida
rule_metadata = {
    "language": "python",           # python, delphi, go, etc.
    "framework": "django",          # django, fastapi, flask, etc.
    "category": "security",         # security, performance, style, architecture
    "severity": "MUST",             # MUST, SHOULD, MAY, DEPRECATED
    "version": "1.0",               # versionamento da regra
    "context": "production",        # dev, production, testing
    "related_rules": ["rule-123"],  # IDs de regras relacionadas
    "replaces": "rule-456",         # Regra que esta substitui
    "author": "john",
    "validated": True               # Se passou por revisão
}
```

### 2. **Sistema de Tags Hierárquicas**
Ao invés de tags planas, usar hierarquia:

```python
# Atual: tags=["python", "django", "security"]
# Melhor: tags=["python.django.security", "python.security", "security"]
```

Permite buscar em diferentes níveis de granularidade.

### 3. **Cache de Consultas Frequentes**
Adicionar cache em memória para regras muito consultadas:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache de 15 minutos para buscas
cache_memory = {}
cache_ttl = timedelta(minutes=15)

def cached_search(query, filters_hash):
    if query in cache_memory:
        entry = cache_memory[query]
        if datetime.now() - entry['timestamp'] < cache_ttl:
            return entry['results']
    return None
```

### 4. **Performance: Desabilitar LLM Processing para Regras**
Regras de programação são estruturadas - não precisam de processamento LLM intensivo:

```python
def add_rule(text: str, skip_llm_processing: bool = True, ...):
    """
    Para regras estruturadas, pular processamento LLM (30-60s → 1-2s)
    """
    if skip_llm_processing:
        # Adiciona direto ao vector store sem processamento LLM
        # Reduz tempo de 30-60s para 1-2s
```

### 5. **Busca Híbrida: Filtros Exatos + Similaridade**
Combinar filtros exatos (language, severity) com busca semântica:

```python
def search_rules(
    query: str,
    language: str = None,       # Filtro exato
    severity: list[str] = None, # ["MUST", "SHOULD"]
    min_score: float = 0.7      # Threshold de similaridade
):
    """
    1. Filtra por language/severity (rápido, exato)
    2. Busca semântica no subset (preciso)
    3. Remove resultados < min_score
    """
```

### 6. **Batch Insert para Importar Regras**
Quando importar múltiplas regras de uma vez:

```python
def add_rules_batch(rules: list[dict], batch_size: int = 10):
    """
    Processa regras em lotes para otimizar embeddings
    """
    for i in range(0, len(rules), batch_size):
        batch = rules[i:i+batch_size]
        # Processa batch em paralelo
```

### 7. **Deduplicação Automática**
Evitar regras duplicadas:

```python
def add_rule(text: str, check_duplicates: bool = True, ...):
    if check_duplicates:
        # Busca por regras similares (score > 0.95)
        similar = search_memory(text, limit=1)
        if similar['results'] and similar['results'][0]['score'] > 0.95:
            return {"status": "duplicate", "existing_id": similar['results'][0]['id']}
```

### 8. **Template de Formato para Regras**
Padronizar formato para facilitar parsing:

```markdown
# REGRA: [Nome da regra]
**Linguagem**: Python
**Framework**: Django
**Severidade**: MUST
**Contexto**: Production

## Descrição
[Descrição clara da regra]

## Exemplo Correto
```python
# código correto
```

## Exemplo Incorreto
```python
# código incorreto
```

## Exceções
- Exceção 1
- Exceção 2
```

### 9. **Índices Especializados por Linguagem**
Criar collections separadas no ChromaDB por linguagem:

```python
# Ao invés de uma collection "mem0_local"
# Criar: "rules_python", "rules_delphi", "rules_go"
# Busca fica mais rápida e focada
```

### 10. **API Específica para Regras**
Adicionar endpoints especializados:

```python
@mcp.tool()
def add_programming_rule(
    rule_text: str,
    language: str,
    category: str,
    severity: str = "SHOULD",
    framework: str = None,
    examples: dict = None,  # {"correct": "...", "incorrect": "..."}
    skip_llm: bool = True   # Regras não precisam de processamento LLM
):
    """Tool específico para adicionar regras de programação"""

@mcp.tool()
def search_rules(
    query: str = None,      # Busca semântica (opcional)
    language: str = None,   # Filtro exato
    category: str = None,   # security, performance, etc.
    severity: list[str] = None,
    framework: str = None,
    min_score: float = 0.6
):
    """Busca otimizada para regras"""
```

## 🚀 Implementação Prioritária

Ordem de implementação recomendada:

1. **Schema estruturado** (30 min) - Adicionar campos padronizados
2. **Skip LLM processing** (20 min) - Ganho imediato de performance
3. **Busca híbrida** (1h) - Melhor precisão nas consultas
4. **Template de formato** (15 min) - Padronizar entrada de dados
5. **API específica para regras** (1h) - Tools especializados
6. **Cache de consultas** (45 min) - Otimizar leituras frequentes
7. **Deduplicação** (30 min) - Evitar regras duplicadas
8. **Batch insert** (45 min) - Importação em massa
9. **Tags hierárquicas** (30 min) - Sistema de categorização avançado
10. **Índices por linguagem** (2h) - Otimização estrutural

## 📝 Notas de Implementação

### Compatibilidade
- Manter backward compatibility com ferramentas existentes
- Adicionar novos tools sem quebrar os antigos
- Migração gradual do schema

### Performance
- Skip LLM deve reduzir tempo de 30-60s para 1-2s
- Cache deve acelerar buscas frequentes em 90%
- Índices por linguagem reduzem espaço de busca

### Testes
- Validar schema antes de adicionar regras
- Testar deduplicação com regras similares
- Benchmark de performance antes/depois

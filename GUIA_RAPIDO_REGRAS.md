# 🚀 Guia Rápido - Regras de Programação

## O que mudou?

O servidor agora está **otimizado para armazenar regras de programação** com:
- ✅ **Schema estruturado** (language, category, severity, framework)
- ✅ **Tags hierárquicas** automáticas (python.django.security → python, django, security)
- ✅ **Cache inteligente** (15 minutos)
- ✅ **Deduplicação** automática
- ✅ **Busca híbrida** (filtros exatos + similaridade semântica)

## Como usar?

### 1. Adicionar uma Regra

#### Opção A: Tool MCP (recomendado)

```python
add_programming_rule(
    rule_text="Always use parameterized queries to prevent SQL injection",
    language="python",
    category="security",
    severity="MUST",
    framework="django",
    examples={
        "correct": "User.objects.filter(id=user_id)",
        "incorrect": "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')"
    }
)
```

#### Opção B: API REST

```bash
curl -X POST http://127.0.0.1:8050/_test/add_json \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Always use parameterized queries",
    "metadata": {
      "language": "python",
      "category": "security",
      "severity": "MUST",
      "framework": "django",
      "rule_type": "programming_rule"
    }
  }'
```

### 2. Buscar Regras

#### Busca Semântica + Filtros

```python
# Encontrar regras de segurança Python
search_rules(
    query="SQL injection prevention",
    language="python",
    category="security"
)

# Regras críticas de Django
search_rules(
    language="python",
    framework="django",
    severity=["MUST", "SHOULD"]
)

# Busca genérica com threshold
search_rules(
    query="memory management",
    min_score=0.7,
    limit=10
)
```

## Parâmetros Disponíveis

### Severities (criticidade)
- `MUST`: Obrigatório
- `SHOULD`: Recomendado
- `MAY`: Opcional
- `DEPRECATED`: Descontinuado

### Categories (categorias)
- `security`: Segurança
- `performance`: Performance
- `style`: Estilo de código
- `architecture`: Arquitetura
- `testing`: Testes
- `documentation`: Documentação
- `general`: Geral

### Contexts (contextos)
- `dev`: Desenvolvimento
- `production`: Produção
- `testing`: Testes
- `staging`: Homologação
- `all`: Todos os ambientes

## Exemplos Práticos

### Regra Python + Django

```python
add_programming_rule(
    rule_text="""
    # REGRA: Usar QuerySets ao invés de SQL direto

    Django ORM fornece proteção automática contra SQL injection.
    Sempre use QuerySets para consultas ao banco de dados.

    ## Correto
    User.objects.filter(username=user_input)

    ## Incorreto
    cursor.execute(f"SELECT * FROM users WHERE username='{user_input}'")
    """,
    language="python",
    framework="django",
    category="security",
    severity="MUST",
    context="all"
)
```

### Regra Delphi

```python
add_programming_rule(
    rule_text="""
    # REGRA: Sempre liberar objetos no mesmo escopo

    Use try-finally para garantir que objetos sejam liberados mesmo em caso de exceção.

    ## Correto
    MyObj := TMyClass.Create;
    try
      // usa MyObj
    finally
      MyObj.Free;
    end;

    ## Incorreto
    MyObj := TMyClass.Create;
    // esqueceu de liberar!
    """,
    language="delphi",
    category="performance",
    severity="MUST",
    context="all"
)
```

### Regra TypeScript + React

```python
add_programming_rule(
    rule_text="""
    # REGRA: Usar useMemo para cálculos pesados

    Evite recalcular valores complexos a cada render.

    ## Correto
    const expensiveValue = useMemo(() =>
      complexCalculation(data),
      [data]
    );

    ## Incorreto
    const expensiveValue = complexCalculation(data); // recalcula todo render!
    """,
    language="typescript",
    framework="react",
    category="performance",
    severity="SHOULD"
)
```

## Buscar Regras

### Por linguagem

```python
# Todas as regras Python
search_rules(language="python")

# Regras Delphi de performance
search_rules(language="delphi", category="performance")
```

### Por framework

```python
# Regras Django
search_rules(framework="django")

# Regras React de performance
search_rules(framework="react", category="performance")
```

### Por severidade

```python
# Apenas regras obrigatórias
search_rules(severity=["MUST"])

# Regras críticas (MUST + SHOULD)
search_rules(severity=["MUST", "SHOULD"])
```

### Busca semântica

```python
# Encontrar regras sobre SQL injection
search_rules(query="SQL injection", language="python")

# Regras sobre gerenciamento de memória
search_rules(query="memory management cleanup")

# Com threshold de similaridade
search_rules(query="authentication security", min_score=0.8)
```

## Tags Hierárquicas

Tags são criadas automaticamente:

```
Regra: Python + Django + Security

Tags geradas:
- python
- python.django
- python.django.security
- django
- security

Você pode buscar por qualquer nível!
```

## Cache Automático

Buscas frequentes são cacheadas por 15 minutos:

```python
# Primeira vez: consulta o banco (2-3s)
search_rules(query="SQL injection", language="python")

# Segunda vez: cache hit (~10ms)
search_rules(query="SQL injection", language="python")
```

Cache é limpo automaticamente quando:
- Adiciona nova regra
- Deleta regra existente
- Após 15 minutos

## Deduplicação

O sistema detecta regras duplicadas:

```python
# Primeira vez: adiciona
add_programming_rule(
    rule_text="Use parameterized queries",
    language="python",
    category="security"
)

# Segunda vez com texto similar (>95%): retorna duplicata
add_programming_rule(
    rule_text="Always use parameterized queries",
    language="python",
    category="security"
)
# Retorna: {"status": "duplicate", "existing_rule": {...}}
```

Para desabilitar:
```python
add_programming_rule(
    rule_text="...",
    check_duplicates=False  # Força adicionar mesmo se duplicado
)
```

## Verificar Servidor

### Status do servidor
```bash
curl http://127.0.0.1:8050/
```

### Listar tools disponíveis
```bash
curl http://127.0.0.1:8050/ | grep mcp_tools
```

Deve incluir:
- `add_programming_rule`
- `search_rules`

## Testes

Execute o script de teste:

```bash
source .venv/bin/activate
python test_rules.py
```

## Troubleshooting

### Servidor não inicia
```bash
# Verificar se Ollama está rodando
curl http://127.0.0.1:11434/api/tags

# Verificar porta
netstat -ano | grep 8050

# Iniciar servidor manualmente
source .venv/bin/activate
python server.py
```

### Erros de validação
```
"Invalid severity 'HIGH'"
```
Use: MUST, SHOULD, MAY, ou DEPRECATED

```
"Invalid category 'bug-fix'"
```
Use: security, performance, style, architecture, testing, documentation, general

### Cache não funciona
O cache só funciona para:
- Buscas com `query` (texto)
- Offset = 0
- Mesmos filtros exatos

## Estrutura de Dados

### Metadados de uma Regra

```json
{
  "id": "uuid-da-regra",
  "memory": "texto da regra",
  "metadata": {
    "language": "python",
    "category": "security",
    "severity": "MUST",
    "framework": "django",
    "version": "1.0",
    "context": "all",
    "rule_type": "programming_rule",
    "created_at": "2025-11-23T10:30:00",
    "author": "Security Team",
    "has_examples": true,
    "example_correct": "código correto",
    "example_incorrect": "código incorreto",
    "tags": "python,python.django,python.django.security,django,security"
  }
}
```

## Endpoints

- **Documentação**: http://127.0.0.1:8050/
- **MCP SSE**: http://127.0.0.1:8050/mcp/sse
- **Test Add**: http://127.0.0.1:8050/_test/add_json (POST)
- **Test Search**: http://127.0.0.1:8050/_test/search?query=...

## Migração de Regras Antigas

Se você tem regras no formato antigo:

```python
# Antigo (ainda funciona)
add_memory(
    text="Use parameterized queries",
    tags=["python", "security"]
)

# Novo (recomendado)
add_programming_rule(
    rule_text="Use parameterized queries",
    language="python",
    category="security",
    severity="MUST"
)
```

Ambos funcionam, mas o novo tem:
- ✅ Validação automática
- ✅ Tags hierárquicas
- ✅ Deduplicação
- ✅ Metadata estruturado

---

**Dúvidas?** Veja a documentação completa em `MELHORIA.md` e `IMPLEMENTACAO_CONCLUIDA.md`

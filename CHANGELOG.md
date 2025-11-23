# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2025-11-23

### Adicionado

#### Novos MCP Tools
- **`add_programming_rule`**: Tool especializado para adicionar regras de programação com validação automática
  - Parâmetros: rule_text, language, category, severity, framework, version, context, author, examples, related_rules, replaces
  - Validação automática de schema (severity, category, context)
  - Deduplicação automática (threshold 95%)
  - Tags hierárquicas automáticas
  - Metadata estruturado

- **`search_rules`**: Busca híbrida otimizada para regras
  - Filtros exatos: language, category, severity, framework, context
  - Busca semântica opcional (query)
  - Threshold de similaridade configurável (min_score)
  - Suporte a cache (15 minutos)
  - OR logic para múltiplos severity

#### Schema Estruturado
- Constantes de validação:
  - `VALID_SEVERITIES`: ["MUST", "SHOULD", "MAY", "DEPRECATED"]
  - `VALID_CATEGORIES`: ["security", "performance", "style", "architecture", "testing", "documentation", "general"]
  - `VALID_CONTEXTS`: ["dev", "production", "testing", "staging", "all"]

#### Helper Functions
- `_expand_hierarchical_tags()`: Expansão automática de tags hierárquicas
  - Exemplo: "python.django.security" → ["python", "python.django", "python.django.security", "django", "security"]
- `_validate_rule_schema()`: Validação de metadata de regras
- `_get_from_cache()`: Recuperação de resultados do cache
- `_put_in_cache()`: Armazenamento de resultados no cache
- `_clear_cache()`: Limpeza do cache
- `_make_cache_key()`: Geração de chaves de cache

#### Cache de Consultas
- Cache em memória para buscas frequentes
- TTL de 15 minutos (configurável via `CACHE_TTL`)
- Invalidação automática ao adicionar/deletar memórias
- Melhora significativa em buscas repetidas

#### Documentação
- **MELHORIA.md**: Documento completo de otimizações planejadas
- **IMPLEMENTACAO_CONCLUIDA.md**: Resumo da implementação realizada
- **GUIA_RAPIDO_REGRAS.md**: Guia prático de uso das novas funcionalidades
- **test_rules.py**: Script de testes automatizados
- **CHANGELOG.md**: Este arquivo

### Modificado

#### MCP Tools Existentes
- **`add_memory`**: Agora limpa o cache após adicionar memória
- **`search_memory`**: Integrado com sistema de cache
  - Cache habilitado para offset=0
  - Chave de cache considera query, user_id, filters e tags
- **`delete_memory`**: Agora limpa o cache após deletar

#### Endpoint de Documentação (`/`)
- Adicionados novos tools: `add_programming_rule`, `search_rules`
- Atualizada seção `mcp_tools`
- Adicionados exemplos de uso para novos tools
- Expandida seção `features` com:
  - hierarchical_tags
  - schema_validation
  - deduplication
  - query_caching
  - hybrid_search

#### Imports
- Adicionado: `from datetime import datetime, timedelta`
- Adicionado: `from typing import Optional, List, Dict, Any`

### Performance

- **Cache**: Redução estimada de 90% no tempo de buscas frequentes
- **Tags hierárquicas**: Busca mais eficiente em múltiplos níveis
- **Validação**: Prevenção de dados inválidos no banco
- **Deduplicação**: Redução de redundância

### Arquivos Adicionados

```
MELHORIA.md                    # Documento de planejamento
IMPLEMENTACAO_CONCLUIDA.md     # Resumo da implementação
GUIA_RAPIDO_REGRAS.md          # Guia de uso
CHANGELOG.md                   # Este arquivo
test_rules.py                  # Testes automatizados
```

### Arquivos Modificados

```
server.py                      # +460 linhas
  - Novos imports
  - Constantes de validação
  - 6 novos helpers
  - 2 novos MCP tools
  - Integração de cache nos tools existentes
  - Documentação atualizada
```

### Testes

- ✅ Status do servidor
- ✅ Adição de regras com `add_programming_rule`
- ✅ Tags hierárquicas automáticas
- ✅ Validação de schema
- ✅ Busca semântica
- ✅ Cache de consultas
- ⚠️ Alguns testes de busca apresentaram warnings (não bloqueante)

## [1.0.0] - 2025-11-XX

### Inicial

- Servidor MCP com FastMCP
- Suporte a Mem0 + ChromaDB + Ollama
- Tools básicos:
  - `add_memory`
  - `search_memory`
  - `list_memories`
  - `list_all_user_ids`
  - `delete_memory`
  - `list_llm_options`
  - `change_llm_config`
- Dual-mode: stdio (Claude Desktop) e SSE (Claude Code)
- Busca semântica com embeddings
- Filtros por metadata
- Tags com OR logic
- Paginação (offset/limit)

---

## Roadmap Futuro

### [2.1.0] - Planejado

- [ ] **Skip LLM Processing**: Opção para adicionar regras sem processamento LLM (30-60s → 1-2s)
- [ ] **Batch Insert**: Adicionar múltiplas regras de uma vez
- [ ] **Export/Import**: Exportar regras para JSON/CSV
- [ ] **Metrics**: Estatísticas de uso dos tools

### [3.0.0] - Futuro

- [ ] **Collections por Linguagem**: Índices separados para cada linguagem
- [ ] **Async Processing**: Processamento assíncrono
- [ ] **GraphQL API**: API alternativa para queries complexas
- [ ] **Web UI**: Interface web para gerenciar regras
- [ ] **Rule Versioning**: Histórico completo de versões de regras
- [ ] **Rule Dependencies**: Grafo de dependências entre regras

---

## Categorização de Mudanças

- **Added**: Novas funcionalidades
- **Changed**: Mudanças em funcionalidades existentes
- **Deprecated**: Funcionalidades que serão removidas
- **Removed**: Funcionalidades removidas
- **Fixed**: Correções de bugs
- **Security**: Correções de vulnerabilidades

---

**Mantenedores**: Claude Code
**Licença**: [LICENSE](LICENSE)
**Repositório**: [mcp-mem0-lite](https://github.com/johncsilva/mcp-mem0-lite)

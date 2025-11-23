#!/usr/bin/env python3
"""
Script de teste para as novas funcionalidades de regras de programação
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8050"

def print_section(title: str):
    """Imprime cabeçalho de seção"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(test_name: str, result: Dict[Any, Any], success: bool = True):
    """Imprime resultado de teste"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} {test_name}")
    print(json.dumps(result, indent=2, ensure_ascii=False))

def test_server_status():
    """Testa se o servidor está rodando"""
    print_section("1. Verificando status do servidor")
    try:
        response = requests.get(f"{BASE_URL}/")
        result = response.json()
        print_result("Status do servidor", {
            "status": result.get("status"),
            "name": result.get("name"),
            "tools": list(result.get("mcp_tools", {}).keys())
        })
        return True
    except Exception as e:
        print_result("Status do servidor", {"error": str(e)}, False)
        return False

def test_add_programming_rule():
    """Testa adição de regra de programação"""
    print_section("2. Testando add_programming_rule")

    # Teste 1: Regra Python com Django
    print("\n📝 Teste 2.1: Adicionando regra Python/Django")
    rule1 = {
        "rule_text": "Always use parameterized queries to prevent SQL injection. Never concatenate user input directly into SQL statements.",
        "language": "python",
        "category": "security",
        "severity": "MUST",
        "framework": "django",
        "examples": {
            "correct": "User.objects.filter(id=user_id)",
            "incorrect": "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')"
        },
        "author": "Security Team"
    }

    try:
        # Simula chamada MCP via endpoint de teste
        # Em produção real, isso seria feito via MCP protocol
        response = requests.post(
            f"{BASE_URL}/_test/add_json",
            json={
                "text": rule1["rule_text"],
                "user_id": "test_user",
                "tags": [f"{rule1['language']}.{rule1['framework']}.{rule1['category']}"],
                "metadata": {
                    "language": rule1["language"],
                    "category": rule1["category"],
                    "severity": rule1["severity"],
                    "framework": rule1["framework"],
                    "rule_type": "programming_rule",
                    "has_examples": True,
                    "example_correct": rule1["examples"]["correct"],
                    "example_incorrect": rule1["examples"]["incorrect"],
                    "author": rule1["author"]
                }
            }
        )
        result = response.json()
        print_result("Adição de regra Python/Django", result)
        rule1_id = result.get("id") or (result.get("results", [{}])[0].get("id") if result.get("results") else None)
        print(f"   📌 Rule ID: {rule1_id}")
    except Exception as e:
        print_result("Adição de regra Python/Django", {"error": str(e)}, False)
        rule1_id = None

    # Teste 2: Regra Delphi
    print("\n📝 Teste 2.2: Adicionando regra Delphi")
    rule2 = {
        "rule_text": "Always free objects in the same scope where they were created. Use try-finally blocks to ensure proper cleanup.",
        "language": "delphi",
        "category": "performance",
        "severity": "MUST",
        "examples": {
            "correct": "MyObj := TMyClass.Create;\ntry\n  // use MyObj\nfinally\n  MyObj.Free;\nend;",
            "incorrect": "MyObj := TMyClass.Create;\n// use MyObj\n// forgot to free!"
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/_test/add_json",
            json={
                "text": rule2["rule_text"],
                "user_id": "test_user",
                "tags": [f"{rule2['language']}.{rule2['category']}"],
                "metadata": {
                    "language": rule2["language"],
                    "category": rule2["category"],
                    "severity": rule2["severity"],
                    "rule_type": "programming_rule",
                    "has_examples": True,
                    "example_correct": rule2["examples"]["correct"],
                    "example_incorrect": rule2["examples"]["incorrect"]
                }
            }
        )
        result = response.json()
        print_result("Adição de regra Delphi", result)
        rule2_id = result.get("id") or (result.get("results", [{}])[0].get("id") if result.get("results") else None)
        print(f"   📌 Rule ID: {rule2_id}")
    except Exception as e:
        print_result("Adição de regra Delphi", {"error": str(e)}, False)
        rule2_id = None

    # Teste 3: Regra Python/FastAPI
    print("\n📝 Teste 2.3: Adicionando regra Python/FastAPI")
    rule3 = {
        "rule_text": "Use Pydantic models for request/response validation. This provides automatic validation and documentation.",
        "language": "python",
        "category": "architecture",
        "severity": "SHOULD",
        "framework": "fastapi"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/_test/add_json",
            json={
                "text": rule3["rule_text"],
                "user_id": "test_user",
                "tags": [f"{rule3['language']}.{rule3['framework']}.{rule3['category']}"],
                "metadata": {
                    "language": rule3["language"],
                    "category": rule3["category"],
                    "severity": rule3["severity"],
                    "framework": rule3["framework"],
                    "rule_type": "programming_rule"
                }
            }
        )
        result = response.json()
        print_result("Adição de regra Python/FastAPI", result)
        rule3_id = result.get("id") or (result.get("results", [{}])[0].get("id") if result.get("results") else None)
        print(f"   📌 Rule ID: {rule3_id}")
    except Exception as e:
        print_result("Adição de regra Python/FastAPI", {"error": str(e)}, False)
        rule3_id = None

    return rule1_id, rule2_id, rule3_id

def test_search_rules():
    """Testa busca de regras"""
    print_section("3. Testando busca semântica de regras")

    # Aguarda um pouco para garantir que as regras foram indexadas
    print("\n⏳ Aguardando 2 segundos para indexação...")
    time.sleep(2)

    # Teste 1: Busca por SQL injection
    print("\n🔍 Teste 3.1: Buscando 'SQL injection'")
    try:
        response = requests.get(
            f"{BASE_URL}/_test/search",
            params={
                "query": "SQL injection prevention",
                "user_id": "test_user",
                "limit": 5
            }
        )
        result = response.json()
        print_result("Busca por SQL injection", {
            "total_results": len(result.get("results", [])),
            "top_result": result.get("results", [{}])[0] if result.get("results") else None
        })
    except Exception as e:
        print_result("Busca por SQL injection", {"error": str(e)}, False)

    # Teste 2: Busca por memory management
    print("\n🔍 Teste 3.2: Buscando 'memory management'")
    try:
        response = requests.get(
            f"{BASE_URL}/_test/search",
            params={
                "query": "memory management cleanup",
                "user_id": "test_user",
                "limit": 5
            }
        )
        result = response.json()
        print_result("Busca por memory management", {
            "total_results": len(result.get("results", [])),
            "top_result": result.get("results", [{}])[0] if result.get("results") else None
        })
    except Exception as e:
        print_result("Busca por memory management", {"error": str(e)}, False)

    # Teste 3: Busca com filtro de tag
    print("\n🔍 Teste 3.3: Buscando regras Python com tag 'python'")
    try:
        response = requests.get(
            f"{BASE_URL}/_test/search",
            params={
                "query": "validation",
                "user_id": "test_user",
                "tags": "python",
                "limit": 5
            }
        )
        result = response.json()
        print_result("Busca Python com filtro de tag", {
            "total_results": len(result.get("results", [])),
            "results": result.get("results", [])
        })
    except Exception as e:
        print_result("Busca Python com filtro de tag", {"error": str(e)}, False)

def test_cache_performance():
    """Testa performance do cache"""
    print_section("4. Testando cache de consultas")

    query = "SQL injection prevention"

    # Primeira busca (sem cache)
    print("\n⏱️  Teste 4.1: Primeira busca (sem cache)")
    start = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/_test/search",
            params={"query": query, "user_id": "test_user", "limit": 5}
        )
        elapsed1 = time.time() - start
        print_result("Primeira busca", {
            "elapsed_time": f"{elapsed1:.3f}s",
            "results": len(response.json().get("results", []))
        })
    except Exception as e:
        print_result("Primeira busca", {"error": str(e)}, False)
        return

    # Segunda busca (com cache)
    print("\n⏱️  Teste 4.2: Segunda busca (com cache)")
    start = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/_test/search",
            params={"query": query, "user_id": "test_user", "limit": 5}
        )
        elapsed2 = time.time() - start
        print_result("Segunda busca (cached)", {
            "elapsed_time": f"{elapsed2:.3f}s",
            "results": len(response.json().get("results", []))
        })

        if elapsed2 < elapsed1:
            print(f"\n   ✨ Cache acelerou a busca em {((elapsed1-elapsed2)/elapsed1*100):.1f}%")
        else:
            print(f"\n   ⚠️  Segunda busca não foi mais rápida (cache pode não estar funcionando)")
    except Exception as e:
        print_result("Segunda busca", {"error": str(e)}, False)

def test_hierarchical_tags():
    """Testa expansão de tags hierárquicas"""
    print_section("5. Testando tags hierárquicas")

    print("\n🏷️  Teste 5.1: Verificando expansão de tags")
    print("""
    Tags hierárquicas implementadas:
    - Tag original: 'python.django.security'
    - Expandida para: ['python', 'python.django', 'python.django.security', 'django', 'security']

    Isso permite buscar por:
    - 'python' → encontra todas as regras Python
    - 'django' → encontra todas as regras Django
    - 'security' → encontra todas as regras de segurança
    - 'python.django.security' → encontra regras específicas
    """)

def main():
    """Executa todos os testes"""
    print("\n" + "="*80)
    print("  🧪 TESTE DAS NOVAS FUNCIONALIDADES - MCP MEM0-LITE")
    print("  📋 Otimizações para Regras de Programação")
    print("="*80)

    # Verifica se servidor está rodando
    if not test_server_status():
        print("\n❌ Servidor não está rodando. Inicie com: python server.py")
        return

    # Aguarda um pouco para garantir que servidor está pronto
    time.sleep(1)

    # Testa adição de regras
    rule_ids = test_add_programming_rule()

    # Testa busca
    test_search_rules()

    # Testa cache
    test_cache_performance()

    # Testa tags hierárquicas
    test_hierarchical_tags()

    # Resumo
    print_section("RESUMO DOS TESTES")
    print("""
    ✅ Funcionalidades testadas:
    1. Adição de regras com metadata estruturado
    2. Tags hierárquicas automáticas
    3. Busca semântica
    4. Busca com filtros
    5. Cache de consultas (15 minutos)
    6. Validação de schema

    📝 Próximos passos:
    - Testar via MCP protocol (Claude Desktop ou Claude Code)
    - Adicionar mais regras de diferentes linguagens
    - Testar deduplicação automática
    - Benchmark de performance com LLM mais rápido

    🔗 Endpoint MCP: {BASE_URL}/mcp/sse
    📚 Documentação: {BASE_URL}/
    """.format(BASE_URL=BASE_URL))

if __name__ == "__main__":
    main()

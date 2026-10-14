#!/usr/bin/env python3
"""
Carregador de batches de planejamento_atividades para Supabase.
Uso: python3 load_planejamento_batches.py [batch_name] [obra_id]
Ex:  python3 load_planejamento_batches.py batch_31-39 obra1

Variáveis de ambiente necessárias:
  SUPABASE_URL: URL do projeto Supabase
  SUPABASE_ANON_KEY: Chave anon do projeto
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path

BATCHES_DIR = Path(__file__).parent.parent / "data" / "batches"

def load_batch_file(batch_name: str, obra_id: str) -> str:
    """Carrega arquivo SQL do batch."""
    file_path = BATCHES_DIR / f"{batch_name}_{obra_id}.sql"
    if not file_path.exists():
        raise FileNotFoundError(f"Batch não encontrado: {file_path}")

    with open(file_path) as f:
        return f.read()

def get_project_id(obra_id: str) -> str:
    """Retorna ID do projeto Supabase para a obra."""
    projects = {
        "obra1": "ivssgstckfcuiyetxdze",
        "obra2": "lwjbuzubnxnzkofcrhah",
    }
    return projects[obra_id]

def split_sql_safe(sql: str, max_bytes: int = 40000) -> list:
    """Divide SQL em chunks seguros."""
    match = re.search(r'(WITH.*?VALUES)\n(.*?)\nON CONFLICT', sql, re.DOTALL)
    if not match:
        return []

    header = match.group(1)
    values_block = match.group(2)

    # Parse valores
    values = []
    lines = values_block.split('\n')
    current = ""

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        current += line + '\n'
        if line_stripped.rstrip(',').endswith(')'):
            values.append(current.rstrip(',').rstrip('\n'))
            current = ""

    if current.strip():
        values.append(current.rstrip(',').rstrip('\n'))

    # Build chunks
    chunks = []
    chunk = []
    size = len(header) + 100

    for val in values:
        val_size = len(val) + 3
        if size + val_size > max_bytes and chunk:
            sql_chunk = header + "\n" + ",\n".join(chunk) + "\nON CONFLICT DO NOTHING;"
            chunks.append(sql_chunk)
            chunk = [val]
            size = len(header) + val_size + 100
        else:
            chunk.append(val)
            size += val_size

    if chunk:
        sql_chunk = header + "\n" + ",\n".join(chunk) + "\nON CONFLICT DO NOTHING;"
        chunks.append(sql_chunk)

    return chunks

def execute_via_psql(sql: str, project_id: str) -> bool:
    """Executa via psql se disponível."""
    # Nota: Requer PGPASSWORD e PGHOST do Supabase
    print(f"⚠️  Execução direto via psql não suportada neste contexto")
    return False

def execute_via_supabase_api(sql: str, project_id: str) -> bool:
    """Executa via REST API do Supabase."""
    supabase_url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not anon_key:
        print("❌ Variáveis SUPABASE_URL e SUPABASE_ANON_KEY não configuradas")
        return False

    # Use mcp__Supabase__execute_sql em sessão Claude Code
    print("ℹ️  Use 'mcp__Supabase__execute_sql' em sessão Claude Code")
    return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 load_planejamento_batches.py <batch_name> <obra_id>")
        print("Exemplos:")
        print("  python3 load_planejamento_batches.py batch_31-39 obra1")
        print("  python3 load_planejamento_batches.py batch_40-47 obra2")
        sys.exit(1)

    batch_name = sys.argv[1]
    obra_id = sys.argv[2]

    try:
        print(f"📦 Carregando {batch_name} para {obra_id}...")
        sql = load_batch_file(batch_name, obra_id)

        chunks = split_sql_safe(sql)
        print(f"✓ {len(chunks)} chunks prontos")

        project_id = get_project_id(obra_id)
        print(f"  Projeto: {project_id}")
        print(f"  Atividades: {sql.count(\"'AT-\")}")

        # Informar próximos passos
        print("\n📋 Próximos passos em sessão Claude Code:")
        print("  1. Use mcp__Supabase__execute_sql com a query SQL")
        print("  2. Repita para cada chunk")
        print("  3. Execute testes: python3 tests/executar.py")

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

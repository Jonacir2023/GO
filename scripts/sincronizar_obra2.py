#!/usr/bin/env python3
"""
Sincronizar dados de Planejamento (EAP, Cronograma, Atividades, Restrições)
de Obra 1 para Obra 2.

Uso:
  python3 scripts/sincronizar_obra2.py

Pré-requisitos:
  - Obra 2 restaurada (não pausada)
  - pip install supabase python-dotenv
  - Arquivo .env com:
    SUPABASE_OBRA1_URL=https://ivssgstckfcuiyetxdze.supabase.co
    SUPABASE_OBRA1_KEY=sb_publishable_...
    SUPABASE_OBRA2_URL=https://lwjbuzubnxnzkofcrhah.supabase.co
    SUPABASE_OBRA2_KEY=sb_publishable_...
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def sincronizar():
    """Sincronizar dados de Obra 1 para Obra 2."""

    try:
        from supabase import create_client
    except ImportError:
        print("❌ Erro: supabase não instalado")
        print("   Instale com: pip install supabase python-dotenv")
        sys.exit(1)

    obra1_url = os.getenv("SUPABASE_OBRA1_URL")
    obra1_key = os.getenv("SUPABASE_OBRA1_KEY")
    obra2_url = os.getenv("SUPABASE_OBRA2_URL")
    obra2_key = os.getenv("SUPABASE_OBRA2_KEY")

    if not all([obra1_url, obra1_key, obra2_url, obra2_key]):
        print("❌ Erro: variáveis de ambiente não configuradas")
        print("   Crie .env com:")
        print("   SUPABASE_OBRA1_URL=...")
        print("   SUPABASE_OBRA1_KEY=...")
        print("   SUPABASE_OBRA2_URL=...")
        print("   SUPABASE_OBRA2_KEY=...")
        sys.exit(1)

    print("Conectando às obras...")
    obra1 = create_client(obra1_url, obra1_key)
    obra2 = create_client(obra2_url, obra2_key)

    tabelas = [
        "planejamento_cronogramas",
        "eap_itens",
        "planejamento_atividades",
        "planejamento_restricoes",
        "pauta_assuntos",
        "checkin_assuntos"
    ]

    for tabela in tabelas:
        print(f"\nSincronizando {tabela}...")

        # Ler de Obra 1
        if tabela in ["pauta_assuntos", "checkin_assuntos"]:
            # Só pegar assuntos Gran Sul (ids com gs-)
            dados = obra1.table(tabela).select("*").eq("obra_id", "obra1").ilike("id", "gs-%").execute()
        else:
            dados = obra1.table(tabela).select("*").eq("obra_id", "obra1").execute()

        if not dados.data:
            print(f"  ℹ️  Nenhum dado em Obra 1 para {tabela}")
            continue

        print(f"  ✓ Lidos {len(dados.data)} registros de Obra 1")

        # Limpar Obra 2
        if tabela in ["pauta_assuntos", "checkin_assuntos"]:
            obra2.table(tabela).delete().eq("obra_id", "obra2").ilike("id", "gs-%").execute()
        else:
            obra2.table(tabela).delete().eq("obra_id", "obra2").execute()

        # Preparar dados (trocar obra_id)
        for r in dados.data:
            r["obra_id"] = "obra2"

        # Inserir em Obra 2
        obra2.table(tabela).insert(dados.data).execute()
        print(f"  ✓ Inseridos {len(dados.data)} registros em Obra 2")

    # Verificar paridade
    print("\n" + "="*60)
    print("Verificando paridade entre as obras:")
    print("="*60)

    for tabela in tabelas:
        o1 = obra1.table(tabela).select("COUNT()", count="exact").eq("obra_id", "obra1").execute()
        if tabela in ["pauta_assuntos", "checkin_assuntos"]:
            o2 = obra2.table(tabela).select("COUNT()", count="exact").eq("obra_id", "obra2").ilike("id", "gs-%").execute()
        else:
            o2 = obra2.table(tabela).select("COUNT()", count="exact").eq("obra_id", "obra2").execute()

        c1 = o1.count or 0
        c2 = o2.count or 0
        status = "✓" if c1 == c2 else "❌"
        print(f"{status} {tabela:40s}: Obra 1 = {c1:4d}, Obra 2 = {c2:4d}")

    print("\n✅ Sincronização concluída!")

if __name__ == "__main__":
    sincronizar()

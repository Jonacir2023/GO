#!/usr/bin/env python3
"""
Aplicar migração: Adicionar coluna 'predecessora' à tabela planejamento_atividades
Funciona em ambas as obras (Obra 1 e Obra 2)
"""
import os
from supabase import create_client, Client

# Dados das duas obras
OBRAS = [
    {
        "nome": "Obra 1",
        "url": "https://ivssgstckfcuiyetxdze.supabase.co",
        "key": os.environ.get("SUPABASE_KEY_1", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2c3Nnc3Rja2ZjdWl5ZXR4emUiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTcwMTk1NzE3OSwiZXhwIjoyMDE3NzE3MTc5fQ.9UBhFbCO5EcC-7KCNz5vkp_BoN9oXFMsgJJvKV3sV88")
    },
    {
        "nome": "Obra 2",
        "url": "https://lwjbuzubnxnzkofcrhah.supabase.co",
        "key": os.environ.get("SUPABASE_KEY_2", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3amJ1enVibnhuemtvZmNyaGFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU2Njc2NDgsImV4cCI6MjA1MTIyNzY0OH0.xZfkEMvLvF_jwhgvzVKzfLOx6QXEVHQkKb5NMhM0qrA")
    }
]

SQL = """
ALTER TABLE planejamento_atividades
ADD COLUMN IF NOT EXISTS predecessora TEXT DEFAULT NULL;

COMMENT ON COLUMN planejamento_atividades.predecessora IS 'Código da atividade predecessora (dependência)';

CREATE INDEX IF NOT EXISTS idx_planejamento_atividades_predecessora
  ON planejamento_atividades(predecessora)
  WHERE predecessora IS NOT NULL;
"""

def aplicar_migracao(obra):
    print(f"\n▶ {obra['nome']}")
    try:
        db = create_client(obra['url'], obra['key'])
        # Executar SQL
        response = db.rpc('exec_sql', {'sql': SQL}).execute()
        print(f"  ✓ Migração aplicada com sucesso")
        return True
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        return False

if __name__ == '__main__':
    print("Aplicando migração: adicionar coluna 'predecessora'")
    print("=" * 50)

    resultados = [aplicar_migracao(obra) for obra in OBRAS]

    print("\n" + "=" * 50)
    if all(resultados):
        print("✓ Todas as obras foram atualizadas com sucesso")
    else:
        print("⚠ Algumas obras falharam. Verifique os logs acima.")

    # Nota: Se o método rpc não existir, tentar via SQL direto
    print("\n💡 Dica: Se isso falhar, execute manualmente no Supabase Dashboard:")
    print("   1. Abra o SQL Editor de cada projeto")
    print("   2. Cole o SQL acima e execute")

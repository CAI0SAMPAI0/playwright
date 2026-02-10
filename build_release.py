#!/usr/bin/env python3
"""
Script automatizado de build e empacotamento.
Gera Study_Practices.zip pronto para distribuição.
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist" / "Study_Practices"
ZIP_NAME = "Study_Practices_v1.0.zip"

def limpar_temporarios():
    """Remove arquivos temporários do desenvolvimento"""
    print("🧹 Limpando arquivos temporários...")
    
    pastas = [
        "build", "logs", "user_data", "perfil_bot_whatsapp",
        "temp_tasks", "scheduled_tasks", "__pycache__"
    ]
    
    for pasta in pastas:
        caminho = BASE_DIR / pasta
        if caminho.exists():
            try:
                shutil.rmtree(caminho)
                print(f"  ✓ {pasta}/")
            except Exception as e:
                print(f"  ✗ {pasta}: {e}")
    
    arquivos = [
        "execution_count.txt", "last_run_path.txt",
        "erro_agendamento.log", "erro_fatal.txt"
    ]
    
    for arquivo in arquivos:
        caminho = BASE_DIR / arquivo
        if caminho.exists():
            try:
                caminho.unlink()
                print(f"  ✓ {arquivo}")
            except Exception as e:
                print(f"  ✗ {arquivo}: {e}")

def compilar():
    """Executa PyInstaller"""
    print("\n📦 Compilando com PyInstaller...")
    
    # Remove dist/build anteriores
    for pasta in ["dist", "build"]:
        caminho = BASE_DIR / pasta
        if caminho.exists():
            shutil.rmtree(caminho)
    
    subprocess.run(
        ["python", "-m", "PyInstaller", "--clean", "app.spec"],
        check=True
    )
    print("  ✓ Compilação concluída")

def criar_zip():
    """Cria ZIP final"""
    print("\n📁 Criando ZIP...")
    
    zip_path = BASE_DIR / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    
    # Arquivos/pastas a incluir
    items = ["Study_Practices.exe", "_internal"]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in items:
            source = DIST_DIR / item
            
            if not source.exists():
                print(f"  ⚠️ {item} não encontrado")
                continue
            
            if source.is_file():
                zipf.write(source, item)
                print(f"  + {item}")
            else:
                # Pasta inteira
                total = 0
                for root, dirs, files in os.walk(source):
                    for file in files:
                        file_path = Path(root) / file
                        arc_path = file_path.relative_to(DIST_DIR)
                        zipf.write(file_path, arc_path)
                        total += 1
                print(f"  + {item}/ ({total} arquivos)")
    
    # Estatísticas
    tamanho_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ {ZIP_NAME} criado ({tamanho_mb:.1f} MB)")

def main():
    print("=" * 70)
    print("BUILD AUTOMATIZADO - Study Practices WhatsApp Bot")
    print("=" * 70)
    
    try:
        limpar_temporarios()
        compilar()
        criar_zip()
        
        print("\n" + "=" * 70)
        print("🎉 BUILD CONCLUÍDO COM SUCESSO!")
        print("=" * 70)
        print(f"\nArquivo pronto: {ZIP_NAME}")
        print("\nPróximos passos:")
        print("  1. Teste o executável em: dist/Study_Practices/")
        print("  2. Faça upload do ZIP para o Google Drive")
        print("  3. Compartilhe o link com os usuários")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERRO na compilação: {e}")
        print("Verifique se app.spec está correto")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")

if __name__ == "__main__":
    main()
import os
import shutil
import subprocess
import zipfile
import sys # garante o uso do executável correto

def realizar_build():
    print("--- Iniciando processo de Build ---")
    
    nome_projeto = "Study_Practices"
    pasta_dist_raiz = "dist"
    arquivo_instrucoes = "Instruções.txt"
    arquivo_zip_final = f"{nome_projeto}.zip"

    # 1. Executa o PyInstaller de forma robusta
    try:
        if os.path.exists(pasta_dist_raiz):
            print(f"--- Limpando pasta {pasta_dist_raiz} anterior ---")
            # ignore_errors=True evita erros se você estiver com a pasta aberta no Windows Explorer
            shutil.rmtree(pasta_dist_raiz, ignore_errors=True) 
            
        print("--- Executando PyInstaller (aguarde...) ---")
        subprocess.run([sys.executable, "-m", "PyInstaller", "--clean", "app.spec"], check=True)
        print("\n[OK] Build concluído com sucesso.")
    except subprocess.CalledProcessError:
        print("\n[ERRO] Falha ao executar o PyInstaller. Verifique se o app.spec está na raiz.")
        return

    # 2. Copia o arquivo Instruções para a raiz do pacote (fora da pasta do App)
    if os.path.exists(arquivo_instrucoes):
        shutil.copy(arquivo_instrucoes, pasta_dist_raiz)
        print(f"[OK] {arquivo_instrucoes} adicionado ao pacote.")
    else:
        print(f"[AVISO] {arquivo_instrucoes} não encontrado. O ZIP será criado sem ele.")

    # 3. Cria o arquivo ZIP
    print(f"--- Criando arquivo ZIP final: {arquivo_zip_final} ---")
    if os.path.exists(arquivo_zip_final):
        os.remove(arquivo_zip_final)

    with zipfile.ZipFile(arquivo_zip_final, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Caminha por tudo que está dentro de 'dist'
        for raiz, pastas, arquivos in os.walk(pasta_dist_raiz):
            for arquivo in arquivos:
                caminho_completo = os.path.join(raiz, arquivo)
                # relpath em relação a pasta_dist_raiz
                # O ZIP conterá a pasta "Study Practices" e o arquivo "Instruções.txt" lado a lado
                caminho_no_zip = os.path.relpath(caminho_completo, pasta_dist_raiz)
                zipf.write(caminho_completo, caminho_no_zip)

    print(f"\n[SUCESSO] O arquivo '{arquivo_zip_final}' está pronto para envio!")

if __name__ == "__main__":
    realizar_build()
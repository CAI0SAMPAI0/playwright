'''import multiprocessing
import sys
import os
import io

# --- 1. BLOQUEIO DE LOOP INFINITO (OBRIGATÓRIO SER O PRIMEIRO) ---
if __name__ == '__main__':
    multiprocessing.freeze_support()

    # --- 2. CONFIGURAÇÃO DE ENCODING ---
    if sys.stdout is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # --- 3. DEFINIÇÃO DE DIRETÓRIOS ---
    import subprocess
    from datetime import datetime
    import json
    import argparse

    if getattr(sys, 'frozen', False):
        from core.paths import get_app_base_dir
        BASE_DIR = get_app_base_dir()
        #BASE_DIR = os.path.dirname(os.path.realpath(sys.executable))
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    os.chdir(BASE_DIR)

    # --- 4. IMPORTS DO PROJETO (DENTRO DO IF MAIN) ---
    from ui.main_window import App 
    from core.automation import executar_envio, contador_execucao
    from core.db import db

    PROFILE_DIR = os.path.normpath(os.path.abspath(os.path.join(BASE_DIR, "perfil_bot_whatsapp")))

    def ensure_profile_dir():
        os.makedirs(PROFILE_DIR, exist_ok=True)

    def garantir_dependencias_playwright():
        """Instala o Chromium no PC da professora se não existir (Mantém o app leve)"""
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=False,
                capture_output=True,
                creationflags=0x08000000 if os.name == 'nt' else 0
            )
        except:
            pass

    # --- 5. LÓGICA DE EXECUÇÃO ---
    #garantir_dependencias_playwright()

    parser = argparse.ArgumentParser(description="WhatsApp Automation App")
    parser.add_argument("--auto", help="Caminho do arquivo JSON de configuração")
    parser.add_argument("--task_id", type=int, help="ID da tarefa no banco de dados")
    args, unknown = parser.parse_known_args()

    if args.auto:
        # MODO AUTOMÁTICO
        task_id = args.task_id
        try:
            with open(args.auto, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if task_id:
                db.atualizar_status(task_id, 'running')

            executar_envio(
                userdir=PROFILE_DIR,
                target=dados["target"],
                mode=dados["mode"],
                message=dados.get("message"),
                file_path=dados.get("file_path"),
                modo_execucao='auto'
            )
            if task_id:
                db.atualizar_status(task_id, 'completed')
            if callable(contador_execucao):
                contador_execucao(True)
            sys.exit(0)
        except Exception as e:
            if task_id:
                db.registrar_erro(task_id, str(e))
            sys.exit(1)
    else:
        # MODO GUI
        ensure_profile_dir()
        app = App()
        app.mainloop()'''

import multiprocessing
import sys
import os
import io
from datetime import datetime

# --- 1. BLOQUEIO OBRIGATÓRIO ---
if __name__ == "__main__":
    multiprocessing.freeze_support()

    # --- 2. STDOUT SEGURO (APENAS CONSOLE) ---
    if sys.stdout and hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        except Exception:
            pass

    # --- 3. IMPORTS BÁSICOS ---
    import json
    import argparse
    from core.paths import get_app_base_dir

    BASE_DIR = os.path.abspath(get_app_base_dir())
    os.chdir(BASE_DIR)

    PROFILE_DIR = os.path.normpath(os.path.join(BASE_DIR, "perfil_bot_whatsapp"))
    os.makedirs(PROFILE_DIR, exist_ok=True)

    # Log de depuração (ajuda a ver se o agendador abriu no lugar certo)
    with open(os.path.join(BASE_DIR, "last_run_path.txt"), "a") as f:
        f.write(f"{datetime.now()}: Rodando em {BASE_DIR} | Perfil: {PROFILE_DIR}\n")

    # --- 4. ARGUMENTOS ---
    parser = argparse.ArgumentParser(description="WhatsApp Automation App")
    parser.add_argument("--auto", help="Arquivo JSON de automação")
    parser.add_argument("--task_id", type=int, help="ID da tarefa")
    args, _ = parser.parse_known_args()

    # --- 5. MODO AUTOMÁTICO ---
    if args.auto:
        from core.automation import executar_envio, contador_execucao
        from core.db import get_db

        db = get_db()
        task_id = args.task_id

        try:
            with open(args.auto, "r", encoding="utf-8") as f:
                dados = json.load(f)

            if task_id:
                db.atualizar_status(task_id, "running")

            executar_envio(
                userdir=PROFILE_DIR,
                target=dados["target"],
                mode=dados["mode"],
                message=dados.get("message"),
                file_path=dados.get("file_path"),
                modo_execucao="auto"
            )

            if task_id:
                db.atualizar_status(task_id, "completed")

            '''try:
                if callable(contador_execucao):
                    contador_execucao(True)
            except Exception:
                pass'''

            sys.exit(0)

        except Exception as e:
            if task_id:
                db.registrar_erro(task_id, str(e))
            sys.exit(1)

    # --- 6. MODO GUI ---
    else:
        try:
            from ui.main_window import App
            app = App()
            app.mainloop()
        except Exception as e:
            # Isso cria um arquivo de erro se o app fechar sozinho
            with open(os.path.join(BASE_DIR, "erro_fatal.txt"), "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] Erro ao abrir GUI: {str(e)}\n")
            raise e


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
    from core.paths import get_app_base_dir, get_whatsapp_profile_dir

    BASE_DIR = get_app_base_dir()
    os.chdir(BASE_DIR)

    PROFILE_DIR = get_whatsapp_profile_dir()

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
        import traceback
        from core.automation import executar_envio, contador_execucao
        from core.db import get_db

        db = get_db()
        task_id = args.task_id
        json_path = os.path.abspath(args.auto)

        try:
            if not os.path.exists(json_path):
                raise FileNotFoundError(f"Arquivo JSON nao encontrado: {json_path}")
            
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

            if callable(contador_execucao):
                contador_execucao(True)

            sys.exit(0)

        except Exception as e:
            erro_detalhado = traceback.format_exc()
            if task_id:
                db.registrar_erro(task_id, str(erro_detalhado))

            # Grava um log físico para ler o que aconteceu
            with open(os.path.join(BASE_DIR, "erro_agendamento.log"), "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] ERRO NA TAREFA {task_id}:\n{erro_detalhado}\n")
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


#!/usr/bin/env python3
"""
EXECUTOR ISOLADO - Roda automação em processo separado.

Chamado por:
- GUI (subprocess manual)
- Task Scheduler (.bat)
"""

import sys
import os
if sys.platform == 'win32':
    # Python 3.7+: Reconfigura stdout/stderr para UTF-8
    if sys.stdout:
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            # Fallback para Python < 3.7
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    if sys.stderr:
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            import io
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import json
from pathlib import Path
from datetime import datetime

# ===== SETUP DE PATHS =====
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from core.db import get_db
from core.automation import executar_envio
from core.logger import get_logger
from core.paths import get_whatsapp_profile_dir

def main(json_path: str):
    """
    Executa uma tarefa a partir de arquivo JSON.
    
    Args:
        json_path: Caminho para task_X.json
    """
    # ===== FORÇA UTF-8 (FIX WINDOWS) =====
    if sys.stdout:
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    # ===== LOGGING =====
    log_dir = BASE_DIR / "logs" / datetime.now().strftime("%Y-%m-%d")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    task_name = Path(json_path).stem
    logger = get_logger(task_name, log_dir / f"{task_name}.log")
    
    logger.info("=" * 70)
    logger.info(f"EXECUTOR INICIADO | JSON: {json_path}")
    
    try:
        # ===== CARREGAR DADOS =====
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        task_id = dados.get("task_id")
        logger.info(f"Task ID: {task_id}")
        modo_execucao = 'manual' if task_id is None else 'auto'
        
        # ===== ATUALIZAR STATUS NO BANCO =====
        db = get_db()
        if task_id:
            db.atualizar_status(task_id, "running")
        
        # ===== EXECUTAR AUTOMAÇÃO (ISOLADA) =====
        profile_dir = get_whatsapp_profile_dir()
        logger.info(f"Perfil: {profile_dir}")
        logger.info(f"Modo: {modo_execucao}")
        
        executar_envio(
            userdir=profile_dir,
            target=dados["target"],
            mode=dados["mode"],
            message=dados.get("message"),
            file_path=dados.get("file_path"),
            logger=logger,
            modo_execucao=modo_execucao
        )
        
        # ===== SUCESSO =====
        if task_id:
            db.atualizar_status(task_id, "completed")
        
        logger.info("[OK] TAREFA CONCLUIDA COM SUCESSO")
        logger.info("=" * 70)
        sys.exit(0)
        
    except Exception as e:
        # ===== FALHA =====
        import traceback
        erro = traceback.format_exc()
        
        logger.error("[ERRO] ERRO NA EXECUCAO:")
        logger.error(erro)
        
        if task_id:
            db.registrar_erro(task_id, str(e))
        
        # Grava arquivo de status para GUI ler
        status_file = Path(json_path).with_suffix('.status')
        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(f"FAILED: {str(e)}")
        
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: executor.py <caminho_para_task.json>")
        sys.exit(2)
    
    main(sys.argv[1])
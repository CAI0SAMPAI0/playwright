import threading
import traceback
from core.db import get_db
# Removemos a importação do PySide6 que causava o conflito

class AutomationWorker(threading.Thread):
    def __init__(self, userdir, target, mode, message=None, file_path=None, task_id=None, 
                 callback_log=None, callback_finished=None):
        """
        Para funcionar com Tkinter, em vez de 'Signals', usamos callbacks.
        Passamos funções que serão chamadas para atualizar a tela.
        """
        super().__init__()
        self.userdir = userdir
        self.target = target
        self.mode = mode
        self.message = message
        self.file_path = file_path
        self.task_id = task_id
        
        # Callbacks para atualizar a UI (substituem os Signals do Qt)
        self.callback_log = callback_log
        self.callback_finished = callback_finished
        self.daemon = True # Garante que a thread morra se fechar o app

    def _emit_log(self, msg):
        if self.callback_log:
            try: self.callback_log(str(msg))
            except: pass
        else:
            print(f"[WORKER] {msg}")

    def _emit_finished(self, success, msg):
        if self.callback_finished:
            try: self.callback_finished(success, str(msg))
            except: pass

    def run(self):
        db = get_db()
        try:
            # Importação local para evitar erros circulares
            from core import automation

            if self.task_id:
                db.atualizar_status(self.task_id, "running")

            # Função local de log para passar para a automação
            def logger_func(msg):
                self._emit_log(msg)

            self._emit_log("🚀 Iniciando thread de automação...")

            automation.executar_envio(
                userdir=self.userdir,
                target=self.target,
                mode=self.mode,
                message=self.message,
                file_path=self.file_path,
                logger=logger_func,
                modo_execucao='manual'
            )

            if self.task_id:
                db.atualizar_status(self.task_id, "completed")

            self._emit_finished(True, "Automação concluída com sucesso!")

        except Exception as e:
            erro_msg = str(e)
            self._emit_log(f"❌ Erro fatal: {erro_msg}")
            
            if self.task_id:
                db.registrar_erro(self.task_id, erro_msg)
            
            self._emit_finished(False, erro_msg)
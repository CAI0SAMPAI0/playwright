import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from core.paths import get_app_base_dir

APP_PATH = Path(get_app_base_dir())

def create_task_bat(task_id, task_name, json_config):
    import sys
    # Usar sempre o diretório real do executável
    app_path = Path(get_app_base_dir()).absolute()
    scheduled_tasks_dir = app_path / "scheduled_tasks"
    scheduled_tasks_dir.mkdir(exist_ok=True)
    
    json_path = scheduled_tasks_dir / f"task_{task_id}.json"
    bat_path = scheduled_tasks_dir / f"task_{task_id}.bat"
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_config, f, indent=2, ensure_ascii=False)
    
    # Pega o caminho do .exe atual
    exe_path = Path(sys.executable).absolute()

    if getattr(sys, 'frozen', False):
        # Se for o EXE compilado: "app.exe --auto..."
        run_command = f'"{exe_path}" --auto "{json_path}" --task_id {task_id}'
    else:
        # Se for rodando via Python: "python.exe app.py --auto..."
        script_path = (app_path / "app.py").absolute()
        run_command = f'"{exe_path}" "{script_path}" --auto "{json_path}" --task_id {task_id}'
    # --------------------------------------
    
    bat_content = f"""@echo off
chcp 65001 >nul
cd /d "{app_path}"
{run_command}
echo Inciando automação...
exit
"""
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    return str(bat_path)

def create_windows_task(task_id, task_name, schedule_time, schedule_date=None):
    bat_path = APP_PATH / "scheduled_tasks" / f"task_{task_id}.bat"

    if not schedule_date:    
        schedule_date = datetime.now().strftime("%d/%m/%Y")

    cmd = (
        f'schtasks /create /tn "AutoMessage_{task_id}" '
        f'/tr "\\"{bat_path}\\"" '
        f'/sc once /st {schedule_time} /sd {schedule_date} '
    )

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr
    return True, "Agendamento criado com sucesso"

def delete_windows_task(task_id):
    """Remove tarefa do Agendador"""
    task_name = f"AutoMessage_{task_id}"
    cmd = f'schtasks /delete /tn "{task_name}" /f'
    subprocess.run(cmd, shell=True, capture_output=True)
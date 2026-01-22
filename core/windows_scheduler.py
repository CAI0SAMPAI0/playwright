import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
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
    vbs_path = scheduled_tasks_dir / f"task_{task_id}.vbs"
    
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
    
    bat_content = f"""@echo off
chcp 65001 >nul
cd /d "{app_path}"
{run_command}
echo Iniciando automação...
exit
"""
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)

    vbs_content = f'CreateObject("Wscript.Shell").Run "{bat_path}", 0, False'
    with open(vbs_path, 'w', encoding='utf-8') as f:
        f.write(vbs_content)
    
    return str(vbs_path)

def create_windows_task(task_id, task_name, schedule_time, schedule_date=None):
    """
    Cria uma tarefa agendada no Windows usando XML
    
    Args:
        task_id: ID único da tarefa
        task_name: Nome da tarefa (não usado, usa AutoMessage_{task_id})
        schedule_time: Horário no formato HH:MM
        schedule_date: Data no formato dd/MM/yyyy (opcional, padrão é hoje)
    
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    vbs_path = APP_PATH / "scheduled_tasks" / f"task_{task_id}.vbs"
    xml_path = APP_PATH / "scheduled_tasks" / f"task_{task_id}.xml"

    # Converte data e hora para o formato ISO
    if not schedule_date:
        schedule_date = datetime.now().strftime("%d/%m/%Y")
    
    try:
        # Combina data e hora
        dt_str = f"{schedule_date} {schedule_time}"
        dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        
        # Formata para o XML (ISO 8601)
        start_boundary = dt.strftime("%Y-%m-%dT%H:%M:%S")
        
        # EndBoundary: 1 hora após o início (pode ajustar conforme necessário)
        end_boundary = (dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        
    except Exception as e:
        return False, f"Erro ao processar data/hora: {str(e)}"

    # Template XML completo e válido
    xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>WhatsApp Automation Task</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>{start_boundary}</StartBoundary>
      <EndBoundary>{end_boundary}</EndBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{vbs_path}</Command>
    </Exec>
  </Actions>
</Task>"""

    # Salva o XML
    try:
        with open(xml_path, 'w', encoding='utf-16') as f:
            f.write(xml_content)
    except Exception as e:
        return False, f"Erro ao criar arquivo XML: {str(e)}"

    # Importa a tarefa usando o XML
    task_full_name = f"AutoMessage_{task_id}"
    cmd = f'schtasks /create /tn "{task_full_name}" /xml "{xml_path}" /f'

    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='cp850',  # Windows console encoding
            errors='replace'
        )
        
        if result.returncode != 0:
            erro = result.stderr if result.stderr else result.stdout
            print(f"[ERRO SCHTASKS] Código: {result.returncode}")
            print(f"[ERRO SCHTASKS] Comando: {cmd}")
            print(f"[ERRO SCHTASKS] Saída: {erro}")
            return False, f"Erro ao criar tarefa: {erro}"
        
        print(f"[OK] Tarefa {task_full_name} criada com sucesso")
        
        # Remove o XML temporário (opcional)
        try:
            xml_path.unlink()
        except:
            pass
            
        return True, "Agendamento criado com sucesso"
        
    except Exception as e:
        print(f"[EXCEÇÃO] Erro ao executar schtasks: {str(e)}")
        return False, f"Exceção ao criar tarefa: {str(e)}"

def delete_windows_task(task_id):
    """
    Remove tarefa do Agendador do Windows
    
    Args:
        task_id: ID da tarefa a ser removida
    """
    task_name = f"AutoMessage_{task_id}"
    cmd = f'schtasks /delete /tn "{task_name}" /f'
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='cp850',
            errors='replace'
        )
        
        if result.returncode == 0:
            print(f"[OK] Tarefa {task_name} removida com sucesso")
        else:
            print(f"[AVISO] Não foi possível remover {task_name}: {result.stderr}")
            
    except Exception as e:
        print(f"[ERRO] Exceção ao deletar tarefa: {str(e)}")
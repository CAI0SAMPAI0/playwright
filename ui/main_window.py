import os
import sys
import customtkinter as ctk
import traceback
import threading
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox
from tkcalendar import Calendar
from core.db import db
from core import automation, windows_scheduler, paths
from core.automation import contador_execucao 
import pyperclip
from core.paths import get_app_base_dir, get_whatsapp_profile_dir


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_DIR = get_whatsapp_profile_dir()
THEME_FILE = os.path.join(BASE_DIR, "data", "theme_pref.txt")
GEOMETRY_FILE = os.path.join(BASE_DIR, "data", "window_pos.txt")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Study Practices - WhatsApp Automation")
        self._restaurar_geometria()
        self._carregar_tema_salvo()

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        icon_path = os.path.join(base_path, "resources", "Taty_s-English-Logo.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass

        self.file_path = None
        self.cards_agendamentos = {}
        self.primary_color = "#b39ddb"
        self.hover_color = "#9575cd"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color=self.primary_color, 
                                      segmented_button_selected_hover_color=self.hover_color)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Novo Envio")
        self.tabview.add("Meus Agendamentos")

        self._setup_envio_tab()
        self._setup_gestao_tab()
        
        self.atualizar_contador_exibicao()
        self._carregar_agendamentos()
        
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        
        # INÍCIO DO LOOP: Atualização a cada 5 segundos
        self.after(5000, self._loop_atualizacao)

    def _restaurar_geometria(self):
        if os.path.exists(GEOMETRY_FILE):
            try:
                with open(GEOMETRY_FILE, "r") as f:
                    geo = f.read().strip()
                    if geo: self.geometry(geo)
            except: self.geometry("500x750")
        else:
            self.geometry("500x750")

    def _ao_fechar(self):
        try:
            os.makedirs(os.path.dirname(GEOMETRY_FILE), exist_ok=True)
            with open(GEOMETRY_FILE, "w") as f:
                f.write(self.geometry())
        except: pass
        self.destroy()

    def _carregar_tema_salvo(self):
        if os.path.exists(THEME_FILE):
            with open(THEME_FILE, "r") as f: ctk.set_appearance_mode(f.read().strip())
        else: ctk.set_appearance_mode("system")

    def _salvar_tema(self, modo):
        os.makedirs(os.path.dirname(THEME_FILE), exist_ok=True)
        with open(THEME_FILE, "w") as f: f.write(modo)

    def _aplicar_mascara_hora(self, event):
        entry = event.widget
        # Ignora teclas de comando para não atrapalhar a navegação
        if event.keysym in ("Left", "Right", "Up", "Down", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return

        texto_atual = entry.get()
        cursor_pos = entry.index("insert")
        
        # Remove tudo que não é número e limita a 4 dígitos
        numeros = "".join([c for c in texto_atual if c.isdigit()])[:4]
        
        # Monta o formato correto
        novo_texto = ""
        if len(numeros) > 0:
            novo_texto += numeros[:2]
        if len(numeros) > 2:
            novo_texto += ":" + numeros[2:]
        
        # SÓ executa a troca se o texto for diferente (evita o "pulo" do cursor)
        if texto_atual != novo_texto:
            entry.delete(0, "end")
            entry.insert(0, novo_texto)
            
            # Ajuste inteligente do cursor
            if event.keysym == "BackSpace":
                entry.icursor(cursor_pos)
            else:
                # Se acabou de digitar o 2º ou 3º número, garante que o cursor avance
                if len(numeros) == 2 and cursor_pos == 2:
                    entry.icursor(3) # Pula para depois do ":"
                elif len(numeros) == 3 and cursor_pos == 3:
                    entry.icursor(4) # Garante que fique após o primeiro dígito dos minutos
                else:
                    entry.icursor(cursor_pos)

    def _validar_campos(self, target, mode, message, file_path):
        if not target:
            messagebox.showerror("Campo Vazio", "Por favor, insira o contato ou número.")
            return False
        msg_limpa = message.strip() if message else ""
        if mode == "text":
            if not msg_limpa:
                messagebox.showerror("Mensagem Vazia", "O modo 'Somente texto' exige uma mensagem.")
                return False
        elif mode == "file":
            if not file_path:
                messagebox.showerror("Arquivo Ausente", "O modo 'Somente arquivo' exige que você selecione ao menos um arquivo.")
                return False
        elif mode == "file_text":
            erros = []
            if not file_path: erros.append("- Selecionar ao menos um arquivo")
            if not msg_limpa: erros.append("- Escrever uma mensagem/legenda")
            if erros:
                msg_erro = "Para o modo 'Arquivo + Texto', você precisa:\n" + "\n".join(erros)
                messagebox.showerror("Dados Insuficientes", msg_erro)
                return False
        return True

    def _loop_atualizacao(self):
        """Loop de atualização silenciosa a cada 5 segundos."""
        try:
            self._carregar_agendamentos()
            self.atualizar_contador_exibicao()
        except Exception as e:
            print(f"Erro no loop: {e}")
        finally:
            self.after(5000, self._loop_atualizacao)

    def _alternar_tema(self):
        mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(mode)
        self._salvar_tema(mode)

    def _setup_envio_tab(self):
        tab = self.tabview.tab("Novo Envio")
        header_frame = ctk.CTkFrame(tab, border_width=1, border_color=("#DBDBDB", "#3d3d3d"))
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.count_label = ctk.CTkLabel(header_frame, text="🚀 Execuções: 0", font=("Roboto", 13, "bold"), text_color=self.primary_color)
        self.count_label.pack(side="left", padx=15, pady=8)
        
        self.theme_btn = ctk.CTkButton(header_frame, text="Alterar tema", width=100, height=28, fg_color=self.primary_color, hover_color=self.hover_color, command=self._alternar_tema)
        self.theme_btn.pack(side="right", padx=15)

        ctk.CTkLabel(tab, text="Contato / Número:", font=("Roboto", 12)).pack(anchor="w", padx=15, pady=(5, 0))
        self.target_input = ctk.CTkEntry(tab, placeholder_text="Ex: 5511999999999 / Tips Basic", height=35)
        self.target_input.pack(fill="x", padx=10, pady=5)

        self.mode_select = ctk.CTkOptionMenu(tab, values=["Somente texto", "Somente arquivo", "Arquivo + texto"], 
                                             command=self._on_mode_change, 
                                             fg_color=self.primary_color, button_color=self.primary_color, 
                                             button_hover_color=self.hover_color)
        self.mode_select.pack(fill="x", padx=10, pady=5)

        self.message_input = ctk.CTkTextbox(tab, height=150, border_width=1)
        self.message_input.pack(fill="both", expand=True, padx=10, pady=5)
        placeholder = "Digite sua mensagem aqui..."
        self.message_input.insert("0.0", placeholder)

        # Função para limpar quando ganhar foco
        def on_focus_in(event):
            if self.message_input.get("1.0", "end-1c") == placeholder:
                self.message_input.delete("1.0", "end")

        # Função para repor se ficar vazio ao perder foco
        def on_focus_out(event):
            if not self.message_input.get("1.0", "end-1c").strip():
                self.message_input.insert("0.0", placeholder)

        # Ligar os eventos
        self.message_input.bind("<FocusIn>", on_focus_in)
        self.message_input.bind("<FocusOut>", on_focus_out)

        action_box = ctk.CTkFrame(tab, border_width=1)
        action_box.pack(fill="x", padx=10, pady=10)

        file_frame = ctk.CTkFrame(action_box, fg_color="transparent")
        file_frame.pack(fill="x", padx=10, pady=10)
        self.file_btn = ctk.CTkButton(file_frame, text="Selecionar Arquivo(s)", state="disabled", 
                                      fg_color="#d3d3d3", hover_color=self.hover_color, command=self._select_file)
        self.file_btn.pack(side="left")
        self.file_label = ctk.CTkLabel(file_frame, text="Nenhum arquivo", font=("Roboto", 10), text_color="gray")
        self.file_label.pack(side="left", padx=10)

        dt_frame = ctk.CTkFrame(action_box, fg_color="transparent")
        dt_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.date_button = ctk.CTkButton(dt_frame, text=datetime.now().strftime("%d/%m/%Y"), 
                                          fg_color=self.primary_color, hover_color=self.hover_color, 
                                          command=lambda: self._abrir_calendario_custom(self.date_button))
        self.date_button.pack(side="left", padx=(0, 10))
        
        self.time_input = ctk.CTkEntry(dt_frame, width=100)
        self.time_input.pack(side="left")
        self.time_input.bind("<KeyRelease>", self._aplicar_mascara_hora)
        self._reset_time()

        actions_frame = ctk.CTkFrame(tab, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(actions_frame, text="Enviar Agora", height=45, fg_color=self.primary_color, hover_color=self.hover_color, command=self._send_now).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(actions_frame, text="Agendar", height=45, fg_color=self.primary_color, hover_color=self.hover_color, command=self._schedule_task).pack(side="left", expand=True, padx=5)

    def _on_mode_change(self, choice):
        state = "normal" if choice != "Somente texto" else "disabled"
        color = self.primary_color if choice != "Somente texto" else "#d3d3d3"
        self.file_btn.configure(state=state, fg_color=color)
        if choice == "Somente arquivo":
            self.message_input.delete("1.0", "end")
            self.message_input.configure(state="disabled")
        else:
            self.message_input.configure(state="normal")

    def _select_file(self):
        paths = filedialog.askopenfilenames()
        if paths:
            self.file_path = "\n".join(paths)
            self.file_label.configure(text=f"{len(paths)} arquivo(s)" if len(paths) > 1 else os.path.basename(paths[0]))

    def _reset_time(self):
        self.time_input.delete(0, 'end')
        self.time_input.insert(0, (datetime.now() + timedelta(minutes=2)).strftime("%H:%M"))

    def _reset_fields(self):
        self.target_input.delete(0, 'end')
        self.message_input.configure(state="normal")
        self.message_input.delete("1.0", "end")
        self.file_path = None
        self.file_label.configure(text="Nenhum arquivo")
        self.mode_select.set("Somente texto")
        self._on_mode_change("Somente texto")
        self._reset_time()
        self.date_button.configure(text=datetime.now().strftime("%d/%m/%Y"))

    def atualizar_contador_exibicao(self):
        try: self.count_label.configure(text=f"🚀 Execuções: {contador_execucao(False)}")
        except: pass

    def _setup_gestao_tab(self):
        tab = self.tabview.tab("Meus Agendamentos")
        self.scrollable_frame = ctk.CTkScrollableFrame(tab, label_text="Histórico")
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _carregar_agendamentos(self):
        """Atualiza a lista de cards de forma inteligente sem 'piscar' a tela."""
        agendamentos = db.listar_todos()
        ids_atuais = [row[0] for row in agendamentos]
        
        # 1. Remover cards que não estão mais no banco
        for t_id in list(self.cards_agendamentos.keys()):
            if t_id not in ids_atuais:
                self.cards_agendamentos[t_id]['frame'].destroy()
                del self.cards_agendamentos[t_id]
        
        status_colors = {"pending": "#808080", "running": "#2196F3", "completed": "#4CAF50", "failed": "#F44336"}

        for row in agendamentos:
            t_id, _, target, _, sched_time, status = row[0], row[1], row[2], row[3], row[4], row[5]
            status_lower = str(status).lower()
            cor = status_colors.get(status_lower, "#808080")
            
            try: dt_amigavel = datetime.fromisoformat(sched_time).strftime("%d/%m/%Y %H:%M")
            except: dt_amigavel = sched_time

            # 2. Atualizar card existente (Flicker-free)
            if t_id in self.cards_agendamentos:
                card_ref = self.cards_agendamentos[t_id]
                
                # Atualiza apenas se os valores mudaram
                if card_ref['status_str'] != status_lower:
                    card_ref['label_status'].configure(text=status_lower.upper(), text_color=cor)
                    card_ref['status_str'] = status_lower
                    state = "normal" if status_lower != "running" else "disabled"
                    card_ref['btn_edit'].configure(state=state)
                    card_ref['btn_del'].configure(state=state)
                
                if card_ref['label_target'].cget("text") != f"📱 {target}":
                    card_ref['label_target'].configure(text=f"📱 {target}")
                
                if card_ref['label_date'].cget("text") != f"📅 {dt_amigavel}":
                    card_ref['label_date'].configure(text=f"📅 {dt_amigavel}")

            # 3. Criar novo card caso não exista
            else:
                card = ctk.CTkFrame(self.scrollable_frame, border_width=1)
                card.pack(fill="x", pady=5, padx=5)
                
                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                
                lbl_target = ctk.CTkLabel(info, text=f"📱 {target}", font=("Roboto", 12, "bold"))
                lbl_target.pack(anchor="w")
                
                lbl_date = ctk.CTkLabel(info, text=f"📅 {dt_amigavel}", font=("Roboto", 10), text_color="gray")
                lbl_date.pack(anchor="w")

                actions = ctk.CTkFrame(card, fg_color="transparent")
                actions.pack(side="right", padx=10)
                
                lbl_status = ctk.CTkLabel(actions, text=status_lower.upper(), text_color=cor, font=("Roboto", 9, "bold"))
                lbl_status.pack()

                btns = ctk.CTkFrame(actions, fg_color="transparent")
                btns.pack()
                
                b_edit = ctk.CTkButton(btns, text="📝", width=30, fg_color=self.primary_color, hover_color=self.hover_color, command=lambda r=row: self._abrir_edicao(r))
                b_edit.pack(side="left", padx=2)
                
                b_del = ctk.CTkButton(btns, text="🗑️", width=30, fg_color="#CF5252", hover_color="#ff0000", command=lambda r=row: self._excluir_agendamento(r))
                b_del.pack(side="left", padx=2)
                
                self.cards_agendamentos[t_id] = {
                    'frame': card, 
                    'label_status': lbl_status, 
                    'label_target': lbl_target,
                    'label_date': lbl_date,
                    'status_str': status_lower, 
                    'btn_edit': b_edit, 
                    'btn_del': b_del
                }

    def _abrir_edicao(self, row):
        task_data = db.obter_por_id(row[0])
        if not task_data: return

        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"Editando Agendamento")
        edit_win.geometry("420x720")

        # --- APLICAÇÃO DO ÍCONE ---
        try:
            if getattr(sys, 'frozen', False):
                # Caminho para quando estiver compilado em .EXE
                base_path = sys._MEIPASS
            else:
                # Caminho para quando estiver rodando o script .PY
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            icon_path = os.path.join(base_path, "resources", "Taty_s-English-Logo.ico")
            
            if os.path.exists(icon_path):
                edit_win.iconbitmap(icon_path)
                edit_win.after(200, lambda: edit_win.iconbitmap(icon_path)) 
            else:
                print(f"Aviso: Ícone não encontrado em {icon_path}")
        except Exception as e:
            print(f"Erro ao carregar ícone na edição: {e}")

        edit_win.transient(self)
        edit_win.lift(); edit_win.focus_force()
        
        
        self.temp_edit_file = task_data['file_path']
        dt_original = datetime.fromisoformat(task_data['scheduled_time'])

        ctk.CTkLabel(edit_win, text="Contato:").pack(pady=(15,0))
        target_ent = ctk.CTkEntry(edit_win, width=320); target_ent.insert(0, task_data['target']); target_ent.pack()

        ctk.CTkLabel(edit_win, text="Forma de Envio:").pack(pady=(10,0))
        map_modos = {"text": "Somente texto", "file": "Somente arquivo", "file_text": "Arquivo + texto"}
        rev_map = {v: k for k, v in map_modos.items()}
        
        msg_txt = ctk.CTkTextbox(edit_win, height=120, width=320)
        btn_alt_file = ctk.CTkButton(edit_win, text="Alterar Arquivo(s)", width=150, height=28, fg_color=self.primary_color, hover_color=self.hover_color)

        def atualizar_campos_edicao(choice):
            if choice == "Somente texto":
                btn_alt_file.configure(state="disabled", fg_color="#d3d3d3")
                msg_txt.configure(state="normal")
            elif choice == "Somente arquivo":
                msg_txt.delete("1.0", "end"); msg_txt.configure(state="disabled")
                btn_alt_file.configure(state="normal", fg_color=self.primary_color, hover_color=self.hover_color)
            else:
                msg_txt.configure(state="normal")
                btn_alt_file.configure(state="normal", fg_color=self.primary_color, hover_color=self.hover_color)

        mode_edit_select = ctk.CTkOptionMenu(edit_win, values=list(map_modos.values()), 
                                             fg_color=self.primary_color, button_color=self.primary_color,
                                             button_hover_color=self.hover_color, 
                                             width=320, command=atualizar_campos_edicao)
        mode_edit_select.set(map_modos.get(task_data['mode'], "Somente texto"))
        mode_edit_select.pack(pady=5)

        ctk.CTkLabel(edit_win, text="Mensagem:").pack(pady=5)
        msg_txt.insert("1.0", task_data['message'] or ""); msg_txt.pack()

        ctk.CTkLabel(edit_win, text="Data e Horário:").pack(pady=5)
        dt_edit_frame = ctk.CTkFrame(edit_win, fg_color="transparent")
        dt_edit_frame.pack()
        
        btn_date_edit = ctk.CTkButton(dt_edit_frame, text=dt_original.strftime("%d/%m/%Y"), width=120, command=lambda: self._abrir_calendario_custom(btn_date_edit), fg_color=self.primary_color, hover_color=self.hover_color)
        btn_date_edit.pack(side="left", padx=5)
        
        time_ent_edit = ctk.CTkEntry(dt_edit_frame, width=80)
        time_ent_edit.insert(0, dt_original.strftime("%H:%M"))
        time_ent_edit.pack(side="left", padx=5)
        time_ent_edit.bind("<KeyRelease>", self._aplicar_mascara_hora)

        lbl_f = ctk.CTkLabel(edit_win, text="Arquivos: " + (str(len(self.temp_edit_file.split('\n'))) if self.temp_edit_file else "0"), font=("Roboto", 10))
        lbl_f.pack()

        def selecionar_arquivos_edicao():
            paths = filedialog.askopenfilenames()
            if paths:
                self.temp_edit_file = "\n".join(paths)
                lbl_f.configure(text=f"Arquivos: {len(paths)}")

        btn_alt_file.configure(command=selecionar_arquivos_edicao)
        btn_alt_file.pack(pady=5)
        atualizar_campos_edicao(mode_edit_select.get())

        def salvar():
            try:
                t_val = target_ent.get().strip()
                m_val = rev_map.get(mode_edit_select.get())
                msg_val = msg_txt.get("1.0", "end-1c").strip()
                f_val = self.temp_edit_file
                h_val = time_ent_edit.get().strip()
                if not self._validar_campos(t_val, m_val, msg_val, f_val): return
                if len(h_val) != 5: return messagebox.showerror("Erro", "Hora incompleta. Use HH:MM")
                nova_dt = datetime.strptime(f"{btn_date_edit.cget('text')} {h_val}", "%d/%m/%Y %H:%M")
                if nova_dt < datetime.now(): return messagebox.showerror("Erro", "O horário deve ser no futuro.")

                windows_scheduler.delete_windows_task(task_data['id'])
                db.atualizar_agendamento_completo(task_data['id'], t_val, m_val, msg_val, f_val, nova_dt)
                
                json_cfg = {"target": t_val, "mode": m_val, "message": msg_val, "file_path": f_val}
                windows_scheduler.create_task_bat(task_data['id'], task_data['task_name'], json_cfg)
                windows_scheduler.create_windows_task(task_data['id'], task_data['task_name'], h_val, btn_date_edit.cget('text'))

                messagebox.showinfo("Sucesso", "Atualizado!"); edit_win.destroy(); self._carregar_agendamentos()
            except Exception as e: messagebox.showerror("Erro", str(e))

        ctk.CTkButton(edit_win, text="Salvar Alterações", fg_color="#4CAF50", hover_color="#277e0f", height=45, command=salvar).pack(pady=25)

    def _excluir_agendamento(self, row):
        if messagebox.askyesno("Excluir", f"Deseja remover {row[2]}?"):
            try:
                windows_scheduler.delete_windows_task(row[0])
                db.deletar(row[0]); self._carregar_agendamentos()
            except Exception as e: messagebox.showerror("Erro", str(e))

    def _get_mode_key(self):
        m = {"Somente texto": "text", "Somente arquivo": "file", "Arquivo + texto": "file_text"}
        return m.get(self.mode_select.get(), "text")

    def _send_now(self):
        target = self.target_input.get().strip()
        message = self.message_input.get("1.0", "end-1c").strip()
        mode = self._get_mode_key()
        if not self._validar_campos(target, mode, message, self.file_path): return
        try:
            automation.executar_envio(userdir=PROFILE_DIR, target=target, mode=mode, message=message, file_path=self.file_path, modo_execucao='manual')
            contador_execucao(True); self.atualizar_contador_exibicao(); messagebox.showinfo("Sucesso", "Enviado"); self._reset_fields()
        except Exception as e: messagebox.showerror("Erro", str(e))

    def _schedule_task(self):
        target = self.target_input.get().strip()
        message = self.message_input.get("1.0", "end-1c").strip()
        mode = self._get_mode_key()
        d, t = self.date_button.cget("text"), self.time_input.get().strip()
        if not self._validar_campos(target, mode, message, self.file_path): return
        if len(t) != 5: return messagebox.showerror("Erro", "Hora incompleta. Use HH:MM")
        try:
            dt = datetime.strptime(f"{d} {t}", "%d/%m/%Y %H:%M")
            if dt < datetime.now(): return messagebox.showerror("Erro", "O horário deve ser no futuro.")
            task_name = f"ZapTask_{int(datetime.now().timestamp())}"

            t_id = db.adicionar(
                task_name=task_name, 
                target=target, 
                mode=mode, 
                message=message, 
                file_path=self.file_path, 
                scheduled_time=dt
            )

            if not t_id or t_id == -1:
                return messagebox.showerror("Erro", "Falha ao salvar no banco de dados")
        
            threading.Thread(
                target=self._criar_tarefa_agendada, 
                args=(t_id, task_name, target, mode, message, self.file_path, t, d),
                daemon=True
            ).start()
        
        except Exception as e: 
            messagebox.showerror("Erro", str(e))

    def _criar_tarefa_agendada(self, t_id, task_name, target, mode, message, file_path, time_str, date_str):
       
        try:
            json_cfg = {
                "target": target, 
                "mode": mode, 
                "message": message, 
                "file_path": file_path
            }
            
            # Cria arquivos JSON e BAT
            windows_scheduler.create_task_bat(t_id, task_name, json_cfg)
            
            # Cria tarefa no Agendador do Windows
            suc, msg = windows_scheduler.create_windows_task(t_id, task_name, time_str, date_str)
            
            if suc: 
                messagebox.showinfo("Agendado", "Tarefa criada com sucesso!")
                self._carregar_agendamentos()
                self._reset_fields()
            else: 
                # Se falhar, remove do banco
                db.deletar(t_id)
                messagebox.showerror("Erro", f"Falha no Agendador do Windows:\n{msg}")
                
        except Exception as e:
            db.deletar(t_id)
            messagebox.showerror("Erro", f"Erro ao criar agendamento:\n{str(e)}")

    def _abrir_calendario_custom(self, target_btn):
        top = ctk.CTkToplevel(self)
        top.title("Data")
        top.attributes("-topmost", True)

        # --- APLICANDO ÍCONE NO CALENDÁRIO ---
        def forcar_icone():
            try:
                # Usa o caminho absoluto direto para evitar erro de localização
                if getattr(sys, 'frozen', False):
                    base = sys._MEIPASS
                else:
                    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                icon_path = os.path.join(base, "resources", "Taty_s-English-Logo.ico")
                
                if os.path.exists(icon_path):
                    # Tenta as duas formas de carregar o ícone
                    top.iconbitmap(icon_path)
                    top.after(200, lambda: top.iconbitmap(icon_path))
            except:
                pass

        # Chama a função quando a janela estiver ociosa (pronta)
        top.after_idle(forcar_icone)

        cal = Calendar(top, selectmode='day', date_pattern='dd/mm/yyyy',background=self.hover_color,      # Cor do cabeçalho
                       selectbackground=self.hover_color,  # COR DO DIA SELECIONADO (O seu roxo)
                       selectforeground='white',           # Cor do texto no dia selecionado
                       normalbackground='#f0f0f0',         # Fundo dos dias normais
                       weekendbackground='#e0e0e0')
        cal.pack(pady=10, padx=10)
        ctk.CTkButton(top, text="Ok", fg_color=self.primary_color, hover_color=self.hover_color, command=lambda: [target_btn.configure(text=cal.get_date()), top.destroy()]).pack(pady=5)

if __name__ == "__main__":
    app = App()
    app.mainloop()
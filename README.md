# 🤖 WhatsApp Automation Tool

<div align="center">
  <h3>📱 Interface Moderna (Modo Claro & Escuro)</h3>
  <div style="display: flex; justify-content: center; gap: 20px;">
    <img src="screenshots/home_light.png" alt="Modo Claro" width="45%"/>
    <img src="screenshots/home_dark.png" alt="Modo Escuro" width="45%"/>
  </div>
  <br>
  <h3>📅 Agendamento Fácil</h3>
  <img src="screenshots/calendario.png" alt="Seletor de Data" width="400"/>
</div>
<br>

---

---

Uma aplicação Desktop robusta para automação e agendamento de mensagens no WhatsApp, desenvolvida com Python, CustomTkinter e Playwright.

![Status](https://img.shields.io/badge/Status-Stable-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)

## ✨ Funcionalidades

* **Envio de Mensagens:** Suporte a Texto, Arquivos (Imagens/Documentos) ou Texto + Arquivo.
* **Agendamento Preciso:** Integração nativa com o **Agendador de Tarefas do Windows** (Task Scheduler) para execuções confiáveis mesmo com o app fechado.
* **Interface Moderna:** GUI construída com `CustomTkinter` (Tema Roxo/Lilás), suportando modo escuro/claro.
* **Gerenciamento de Sessão:** Login persistente (não precisa ler QR Code toda vez).
* **Gestão de Agendamentos:** Visualize, edite ou exclua mensagens programadas.
* **Blindagem contra Erros:**
    * Suporte a usuários do Windows com **espaço no nome** (ex: "CAIO MAXIMUS").
    * Tratamento de processos "zumbis" do Chrome.
    * Forçamento de idioma (PT-BR) para evitar erros de seletores.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Interface:** CustomTkinter
* **Automação:** Playwright (Sync API)
* **Agendamento:** Windows Task Scheduler (via `schtasks`, `.bat` e `.vbs`)
* **Banco de Dados:** SQLite (Armazenamento local de logs e agendamentos)

## 🚀 Como Rodar o Projeto

### Pré-requisitos
* Python 3.10 ou superior
* Google Chrome instalado

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/CAI0SAMPAI0/playwright.git](https://github.com/CAI0SAMPAI0/playwright.git)
    cd playwright
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    # No Windows:
    .\venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Instale os navegadores do Playwright:**
    ```bash
    playwright install chromium
    ```

5.  **Execute a aplicação:**
    ```bash
    # Execute a partir da raiz do projeto
    python app.py
    ```

---

## 📦 Como Gerar o Executável (.exe)

Para distribuir para clientes (sem precisar instalar Python na máquina deles), utilize o **PyInstaller**. Recomenda-se limpar a pasta `dist` e `build` antes de gerar.

```bash
pyinstaller --noconfirm --onedir --windowed --icon="resources/icon.ico" --name "WhatsAppBot" --add-data "ui;ui" --add-data "core;core" --add-data "resources;resources" app.py
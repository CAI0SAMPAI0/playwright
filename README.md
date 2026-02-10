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
* **Portabilidade Total:** Funciona em qualquer pasta do Windows (Desktop, Downloads, HD externo, etc.).
* **Blindagem contra Erros:**
    * Suporte a usuários do Windows com **espaço no nome** (ex: "CAIO MAXIMUS").
    * Tratamento de processos "zumbis" do Chrome.
    * Forçamento de idioma (PT-BR) para evitar erros de seletores.
    * Encoding UTF-8 nativo para compatibilidade universal.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Interface:** CustomTkinter
* **Automação:** Playwright (Sync API)
* **Agendamento:** Windows Task Scheduler (via `schtasks`, `.bat` e `.vbs`)
* **Banco de Dados:** SQLite com WAL mode (Write-Ahead Logging)
* **Empacotamento:** PyInstaller (onedir mode)

---

## 📥 Para Usuários Finais

### **Download e Instalação**

1. **Baixe o arquivo ZIP** do [Google Drive](#) (link fornecido pelo desenvolvedor)

2. **Extraia em qualquer pasta** de sua preferência:
   - ✅ `C:\Users\SeuNome\Desktop\Study_Practices\`
   - ✅ `D:\Aplicativos\Study_Practices\`
   - ✅ `C:\WhatsApp\Study_Practices\`
   - ❌ **NÃO extraia em:** `C:\Program Files\` ou `C:\Windows\` (sem permissão)

3. **Execute:** `Study_Practices.exe`

4. **Primeira vez:**
   - O programa abrirá o Chrome automaticamente
   - Leia o QR Code do WhatsApp no seu celular
   - Aguarde o WhatsApp carregar completamente
   - Pronto! Login salvo permanentemente

### **Requisitos do Sistema**

* Windows 10/11 (64-bit)
* Google Chrome ou Microsoft Edge instalado
* Conexão com a internet
* Mínimo 4GB RAM
* 500MB espaço em disco

### **Onde os Dados Ficam Salvos?**

Todos os dados ficam **dentro da pasta onde você extraiu o programa**:
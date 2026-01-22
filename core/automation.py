import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
import time
import sys
import json
import pyperclip
from playwright.sync_api import sync_playwright
from core.paths import get_chrome_path

def _log(logger, msg):
    if logger:
        try: logger.info(msg) if hasattr(logger, 'info') else logger(msg)
        except: pass
    else: print(f"[LOG] {msg}")

def clicar_primeiro_disponivel(page, lista_seletores, timeout_por_tentativa=300, escrever_texto=None):
    """
    Percorre a lista de seletores rapidamente. 
    Se encontrar, clica. Se houver escrever_texto, ele cola o conteúdo.
    """
    for sel in lista_seletores:
        try:
            elemento = page.locator(sel).last # Usa o último para evitar menus ocultos
            elemento.wait_for(state="visible", timeout=timeout_por_tentativa)
            elemento.scroll_into_view_if_needed()
            elemento.click(force=True)
            
            if escrever_texto:
                time.sleep(0.5)
                pyperclip.copy(escrever_texto)
                page.keyboard.press("Control+V")
            return True
        except:
            continue
    return False

def contador_execucao(incrementar=True):
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    count_file = os.path.join(base_dir, "execution_count.txt")
    count = 0
    if os.path.exists(count_file):
        try:
            with open(count_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                count = int(content) if content else 0
        except: count = 0
    if incrementar:
        count += 1
        with open(count_file, 'w', encoding='utf-8') as f:
            f.write(str(count))
    return count

def iniciar_driver(userdir, modo_execucao='manual', logger=None):
    userdir = os.path.abspath(userdir)
    os.makedirs(userdir, exist_ok=True)

    #if getattr(sys, 'frozen', False) or 'nuitka' in sys.modules:
        # Força o Playwright a usar a pasta padrão de instalação no AppData do Windows
        #os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
    _log(logger, f"Iniciando Playwright | Perfil: {userdir}")
    pw = sync_playwright().start()
    is_auto = modo_execucao in ['auto', 'background']
    
    browser_args = [
        '--disable-notifications', '--no-sandbox', '--disable-setuid-sandbox',
        '--start-maximized', '--force-device-scale-factor=1.25', '--high-dpi-support=1'
    ]
    
    if is_auto:
        browser_args.extend(['--window-position=9999,9999', '--force-device-scale-factor=1.25','--window-size=1366,768', '--high-dpi-support=1'])

    chromium_path = get_chrome_path()

    browser_context = pw.chromium.launch_persistent_context(
        executable_path=str(chromium_path),
        user_data_dir=userdir, headless=False, args=browser_args,
        viewport=None, no_viewport=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    page = browser_context.pages[0]
    page.set_default_timeout(120000)
    page.goto("https://web.whatsapp.com")
    
    try:
        page.wait_for_selector('div[data-tab="3"]', timeout=120000)
        _log(logger, "✓ WhatsApp carregado.")
    except Exception as e:
        if is_auto: page.screenshot(path="erro_login_agendado.png")
        raise e
    return pw, browser_context, page

def enviar_arquivo_com_mensagem(page, file_path, message, logger=None):
    _log(logger, "📎 Preparando anexos...")
    
    # 1. Botão Anexar
    xpath_anexo = '//div[@aria-label="Anexar"] | //span[@data-icon="plus"] | //span[@data-icon="plus-rounded"] | //span[@data-icon="clip"]'
    btn_anexo = page.wait_for_selector(xpath_anexo, state="visible", timeout=120000)
    btn_anexo.click()
    time.sleep(1)

    # 2. Processamento de Caminhos
    if isinstance(file_path, str):
        clean_path = file_path.replace('nC:\\', '\nC:\\')
        lista_arquivos = [os.path.abspath(p.strip()) for p in clean_path.split('\n') if p.strip()]
    else:
        lista_arquivos = [os.path.abspath(str(file_path).strip())]

    ext = os.path.splitext(lista_arquivos[0].lower())[1]
    is_media = ext in ['.jpg', '.jpeg', '.png', '.gif', '.mp4']

    # SEPARAÇÃO DOS SEUS SELETORES DE TIPO (FOTO OU DOCUMENTO)
    if is_media:
        seletores_tipo = [
            "xpath=//div[@aria-label='Fotos e vídeos']",
            "css=#app > div > div > span:nth-child(8) > div > ul > div > div > div:nth-child(2) > li > div > span",
            "xpath=//*[@id='app']/div/div/span[6]/div/ul/div/div/div[2]/li/div/span",
            "xpath=/html/body/div[1]/div/div/div/div/span[6]/div/ul/div/div/div[2]/li/div/span",
            'css=#app > div > div > div:nth-child(11) > div > div > div.xu96u03.xm80bdy.x10l6tqk.x13vifvy.xoz0ns6.x1gslohp > div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl > div > div > div > div > div.x78zum5.xdt5ytf.x1iyjqo2.x1n2onr6 > div:nth-child(2) > div.x6s0dn4.xlr9sxt.xvvg52n.xwd4zgb.xq8v1ta.x78zum5.xu0aao5.xh8yej3 > div.x78zum5.xdt5ytf.x1iyjqo2.xeuugli.x6ikm8r.x10wlt62.xde1mab > span',
            'xpath=//*[@id="app"]/div/div/div[4]/div/div/div[1]/div[1]/div/div/div/div/div[1]/div[2]/div[1]/div[2]/span',
            'xpath=/html/body/div[1]/div/div/div/div/div[4]/div/div/div[1]/div[1]/div/div/div/div/div[1]/div[2]/div[1]/div[2]/span'
        ]
    else:
        seletores_tipo = [
            "xpath=//div[@aria-label='Documento']",
            "css=#app > div > div > span:nth-child(8) > div > ul > div > div > div:nth-child(1) > li > div > span",
            'css=#app > div > div > div:nth-child(11) > div > div > div.xu96u03.xm80bdy.x10l6tqk.x13vifvy.xoz0ns6.x1gslohp > div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl > div > div > div > div > div.x78zum5.xdt5ytf.x1iyjqo2.x1n2onr6 > div:nth-child(1) > div.x6s0dn4.xlr9sxt.xvvg52n.xwd4zgb.xq8v1ta.x78zum5.xu0aao5.xh8yej3 > div.x78zum5.xdt5ytf.x1iyjqo2.xeuugli.x6ikm8r.x10wlt62.xde1mab > span',
            'xpath=//*[@id="app"]/div/div/div[4]/div/div/div[1]/div[1]/div/div/div/div/div[1]/div[1]/div[1]/div[2]/span',
            'xpath=/html/body/div[1]/div/div/div/div/div[4]/div/div/div[1]/div[1]/div/div/div/div/div[1]/div[1]/div[1]/div[2]/span'
            "xpath=//*[@id='app']/div/div/span[6]/div/ul/div/div/div[1]/li/div/span",
            "xpath=/html/body/div[1]/div/div/div/div/span[6]/div/ul/div/div/div[1]/li/div/span"
        ]

    # Tentativa de clique no tipo de arquivo
    clicou_tipo = False
    try:
        page.wait_for_selector(seletores_tipo[0], state="visible", timeout=120000)
    except:
        _log(logger, "⚠️ Menu de tipos demorou, tentando varredura rápida...")

    try:
        for sel in seletores_tipo:
            try:
                with page.expect_file_chooser(timeout=300) as fc_info:
                    page.locator(sel).first.click(force=True, timeout=300)
                file_chooser = fc_info.value
                file_chooser.set_files(lista_arquivos)
                clicou_tipo = True
                _log(logger, f"✅ Arquivo(s) carregados via: {sel}")
                break
            except:
                continue
        
        if not clicou_tipo:
            raise Exception("Nenhum seletor de tipo de arquivo funcionou.")
            
        time.sleep(1) 
    except Exception as e:
        raise Exception(f"Erro ao selecionar arquivos: {e}")

    # 3. Legenda (SEUS SELETORES)
    if message:
        _log(logger, "✍️ Inserindo legenda...")
        seletores_legenda = [
            "css=#app > div > div > div.x78zum5.xdt5ytf.x5yr21d > div > div.x10l6tqk.x13vifvy.x1o0tod.x78zum5.xh8yej3.x5yr21d.x6ikm8r.x10wlt62.x47corl > div.x9f619.x1n2onr6.x5yr21d.x6ikm8r.x10wlt62.x17dzmu4.x1i1dayz.x2ipvbc.xjdofhw.xyyilfv.x1iyjqo2.xpilrb4.x1t7ytsu.x1vb5itz.x12xzwr > div > span > div > div > div > div.x1n2onr6.xupqr0c.x78zum5.x1r8uery.x1iyjqo2.xdt5ytf.x1hc1fzr.x6ikm8r.x10wlt62.x1anedsm > div > div.x1n2onr6.x78zum5.x98rzlu.xdt5ytf.x1qughib.x6ikm8r.x10wlt62 > div.x1n2onr6.x78zum5.x6s0dn4.xl56j7k.xbktkl8.x16ovd2e.xvtqlqk.x12xbjc7.xdx6fka > div > div > div.x1n2onr6.xh8yej3.x1k70j0n.x14z9mp.xzueoph.x1lziwak.xisnujt.x14ug900.x1vvkbs.x126k92a.x1hx0egp.lexical-rich-text-input > div.x1hx0egp.x6ikm8r.x1odjw0f.x1k6rcq7.x1lkfr7t > p",
            "xpath=//*[@id='app']/div/div/div[3]/div/div[3]/div[2]/div/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div[1]/div[1]/p",
            "xpath=/html/body/div[1]/div/div/div/div/div[3]/div/div[3]/div[2]/div/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div[1]/div[1]/p",
            "xpath=//*[@id='app']/div/div/div[3]/div/div[3]/div[2]/div/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div[1]/div[1]/div[1]/p",
            "css=#app > div > div > div.x78zum5.xdt5ytf.x5yr21d > div > div.x10l6tqk.x13vifvy.x1o0tod.x78zum5.xh8yej3.x5yr21d.x6ikm8r.x10wlt62.x47corl > div.x9f619.x1n2onr6.x5yr21d.x6ikm8r.x10wlt62.x17dzmu4.x1i1dayz.x2ipvbc.xjdofhw.xyyilfv.x1iyjqo2.xpilrb4.x1t7ytsu.x1vb5itz.x12xzwr > div > span > div > div > div > div.x1n2onr6.xupqr0c.x78zum5.x1r8uery.x1iyjqo2.xdt5ytf.x1hc1fzr.x6ikm8r.x10wlt62.x1anedsm > div > div.x78zum5.x1iyjqo2.xs83m0k.x1r8uery.xdt5ytf.x1qughib.x6ikm8r.x10wlt62 > div.x1c4vz4f.xs83m0k.xdl72j9.x1g77sc7.x78zum5.xozqiw3.x1oa3qoh.x12fk4p8.xeuugli.x2lwn1j.xl56j7k.x1q0g3np.x6s0dn4.x1n2onr6.xo8q3i6.x1y1aw1k.xwib8y2.x1c1uobl.xyri2b > div > div > div.x1c4vz4f.xs83m0k.xdl72j9.x1g77sc7.x78zum5.xozqiw3.x1oa3qoh.x12fk4p8.xeuugli.x2lwn1j.x1nhvcw1.x1q0g3np.x1cy8zhl.x9f619.xh8yej3.x1ba4aug.x1tiyuxx.xvtqlqk.x1nbhmlj.xdx6fka.x1od0jb8.xyi3aci.xwf5gio.x1p453bz.x1suzm8a > div.x1n2onr6.xh8yej3.x1k70j0n.x14z9mp.xzueoph.x1lziwak.xisnujt.x14ug900.x1vvkbs.x126k92a.x1hx0egp.lexical-rich-text-input > div.x1hx0egp.x6ikm8r.x1odjw0f.x1k6rcq7.x1lkfr7t > p",
            "xpath=//div[contains(@aria-label, 'legenda')]",
            "css=div.lexical-rich-text-input div[contenteditable='true']",
            'css=#app > div > div > div.x78zum5.xdt5ytf.x5yr21d > div > div.x10l6tqk.x13vifvy.x1o0tod.x78zum5.xh8yej3.x5yr21d.x6ikm8r.x10wlt62.x47corl > div.x9f619.x1n2onr6.x5yr21d.x6ikm8r.x10wlt62.x17dzmu4.x1i1dayz.x2ipvbc.xjdofhw.xyyilfv.x1iyjqo2.xpilrb4.x1t7ytsu.x1vb5itz.x12xzxwr > div > span > div > div > div > div.x1n2onr6.xupqr0c.x78zum5.x1r8uery.x1iyjqo2.xdt5ytf.x1hc1fzr.x6ikm8r.x10wlt62.x1anedsm > div > div.x78zum5.x1iyjqo2.xs83m0k.x1r8uery.xdt5ytf.x1qughib.x6ikm8r.x10wlt62 > div.x1c4vz4f.xs83m0k.xdl72j9.x1g77sc7.x78zum5.xozqiw3.x1oa3qoh.x12fk4p8.xeuugli.x2lwn1j.xl56j7k.x1q0g3np.x6s0dn4.x1n2onr6.xo8q3i6.x1y1aw1k.xwib8y2.x1c1uobl.xyri2b > div > div > div > div.x1n2onr6.xh8yej3.x1k70j0n.x14z9mp.xzueoph.x1lziwak.xisnujt.x14ug900.x1vvkbs.x126k92a.x1hx0egp.lexical-rich-text-input > div.x1hx0egp.x6ikm8r.x1odjw0f.x1k6rcq7.x1lkfr7t > p',
            'xpath=//*[@id="app"]/div/div/div[3]/div/div[3]/div[2]/div/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div/div[1]/div[1]/p'
            'xpath=/html/body/div[1]/div/div/div/div/div[3]/div/div[3]/div[2]/div/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div/div[1]/div[1]/p'
        ]
        try:
            page.wait_for_selector(seletores_legenda[0], state="visible", timeout=120000)
        except:
            _log(logger, "⚠️ Aviso: Tela de legenda demorou a aparecer, tentando loop rápido...")

        campo_ok = False
        for sel in seletores_legenda:
            try:
                target = page.locator(sel).last
                target.wait_for(state="visible", timeout=500)
                target.scroll_into_view_if_needed()
                target.click(force=True)
                time.sleep(1)
                pyperclip.copy(message)
                page.keyboard.press("Control+V")
                campo_ok = True
                _log(logger, "✅ Legenda inserida.")
                break
            except: continue
        
        if not campo_ok:
            page.keyboard.press("Tab")
            time.sleep(0.5)
            pyperclip.copy(message)
            page.keyboard.press("Control+V")

    # 4. Enviar 
    _log(logger, "🚀 Enviando...")
    seletores_enviar = [
        "xpath=//span[@data-icon='send']",
        "xpath=//div[@role='button' and @aria-label='Enviar']",
        "xpath=//*[@id='app']/div/div/div[3]/div/div[3]/div[2]/div/span/div/div/div/div[2]/div/div[2]/div[2]/span/div/div/span",
        "xpath=/html/body/div[1]/div/div/div/div/div[3]/div/div[3]/div[2]/div/span/div/div/div/div[2]/div/div[2]/div[2]/span/div/div/span",
        "css=div[aria-label='Enviar'] span[data-icon='send']",
        "css=#app > div > div > div.x78zum5.xdt5ytf.x5yr21d > div > div.x10l6tqk.x13vifvy.x1o0tod.x78zum5.xh8yej3.x5yr21d.x6ikm8r.x10wlt62.x47corl > div.x9f619.x1n2onr6.x5yr21d.x6ikm8r.x10wlt62.x17dzmu4.x1i1dayz.x2ipvbc.xjdofhw.xyyilfv.x1iyjqo2.xpilrb4.x1t7ytsu.x1vb5itz.x12xzwr > div > span > div > div > div > div.x1n2onr6.xupqr0c.x78zum5.x1r8uery.x1iyjqo2.xdt5ytf.x1hc1fzr.x6ikm8r.x10wlt62.x1anedsm > div > div.x78zum5.x1c4vz4f.x2lah0s.x1helyrv.x6s0dn4.x1qughib.x178xt8z.x13fuv20.xx42vgk.x1y1aw1k.xwib8y2.xf7dkkf.xv54qhq > div.x1247r65.xng8ra > span > div > div > span",
        "css=#app > div > div > div.x78zum5.xdt5ytf.x5yr21d > div > div.x10l6tqk.x13vifvy.x1o0tod.x78zum5.xh8yej3.x5yr21d.x6ikm8r.x10wlt62.x47corl > div.x9f619.x1n2onr6.x5yr21d.x6ikm8r.x10wlt62.x17dzmu4.x1i1dayz.x2ipvbc.xjdofhw.xyyilfv.x1iyjqo2.xpilrb4.x1t7ytsu.x1vb5itz.x12xzxwr > div > span > div > div > div > div.x1n2onr6.xupqr0c.x78zum5.x1r8uery.x1iyjqo2.xdt5ytf.x1hc1fzr.x6ikm8r.x10wlt62.x1anedsm > div > div.x78zum5.x1c4vz4f.x2lah0s.x1helyrv.x6s0dn4.x1qughib.x178xt8z.x13fuv20.xx42vgk.x1y1aw1k.xwib8y2.xf7dkkf.xv54qhq > div.x1247r65.xng8ra > span > div > div > span",
        "xpath=//*[@id='app']/div/div/div[3]/div/div[3]/div[2]/div/span/div/div/div/div[2]/div/div[2]/div[2]/span/div/div/span",
    ]
    
    enviou = False
    for sel_env in seletores_enviar:
        try:
            btn = page.locator(sel_env).last
            btn.wait_for(state="visible", timeout=800)
            btn.scroll_into_view_if_needed()
            btn.click(force=True)
            enviou = True
            break
        except: continue

    if enviou:
        time.sleep(15)
        #contador_execucao(incrementar=True)
        _log(logger, "🚀 Concluído!")
    else:
        page.keyboard.press("Enter")

def executar_envio(userdir, target, mode, message=None, file_path=None, logger=None, modo_execucao='manual'):
    pw, context, page = None, None, None
    try:
        pw, context, page = iniciar_driver(userdir, modo_execucao, logger)
        
        search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
        search_box.fill(target)
        time.sleep(2)
        page.keyboard.press("Enter")
        time.sleep(2)

        if mode == "text":
            chat_box = page.locator('div[contenteditable="true"][data-tab="10"]')
            chat_box.wait_for(state="visible")
            chat_box.click(force=True)
            pyperclip.copy(message)
            page.keyboard.press("Control+V")
            page.keyboard.press("Enter")
            time.sleep(2.1)
        else:
            enviar_arquivo_com_mensagem(page, file_path, message, logger)
            
        return True
    except Exception as e:
        _log(logger, f"❌ Falha no processo: {str(e)}")
        raise e
    finally:
        if context: context.close()
        if pw: pw.stop()

def run_auto(json_path):
    if not os.path.exists(json_path): return
    with open(json_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(".")
    current_profile = os.path.join(base_dir, "perfil_bot_whatsapp")

    executar_envio(
        userdir=current_profile,
        target=dados.get("target"),
        mode=dados.get("mode"),
        message=dados.get("message"),
        file_path=dados.get("file_path"),
        logger=lambda m: print(f"[AUTO] {m}"),
        modo_execucao='auto'
    )
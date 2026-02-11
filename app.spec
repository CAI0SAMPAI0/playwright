# -*- mode: python ; coding: utf-8 -*-

import os

# Inclui apenas pastas que EXISTEM (ignora scheduled_tasks que é criada em runtime)
datas_list = []
for folder in ['ui', 'core', 'data', 'resources']:
    if os.path.exists(folder):
        datas_list.append((folder, folder))

# CRÍTICO: Adiciona executor.py (necessário para envios manuais e agendados)
if os.path.exists('executor.py'):
    datas_list.append(('executor.py', '.'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=['playwright.sync_api'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Study_Practices',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=['resources\\Taty_s-English-Logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Study_Practices',
)

# ===== REMOVE NAVEGADORES DO PLAYWRIGHT (REDUZ 300+ MB) =====
import os
import shutil
from pathlib import Path

dist_path = Path('dist/Study_Practices/_internal')
playwright_browsers = dist_path / 'playwright' / 'driver' / 'package' / '.local-browsers'

if playwright_browsers.exists():
    print(f"\n🗑️  REMOVENDO navegadores do Playwright ({playwright_browsers})...")
    try:
        shutil.rmtree(playwright_browsers)
        print("✅ Navegadores removidos com sucesso! (~300MB economizados)")
    except Exception as e:
        print(f"⚠️  Aviso ao remover navegadores: {e}")


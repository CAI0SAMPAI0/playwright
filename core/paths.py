import os
import sys

def get_app_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_user_data_dir():
    base = get_app_base_dir()
    path = os.path.join(base, "user_data")
    os.makedirs(path, exist_ok=True)
    return path

def get_chrome_path():
    caminhos = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in caminhos:
        if os.path.exists(c):
            return c
    raise FileNotFoundError("Chrome/Edge não encontrado no sistema")
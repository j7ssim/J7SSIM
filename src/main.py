import os
import time
import random
import asyncio
import threading
import json
import tempfile
import flet as ft
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError

# --- استخدام المسارات الآمنة ---
BASE_DIR = tempfile.gettempdir()
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')
LOG_FILE = os.path.join(BASE_DIR, 'processed_users.txt')
CONFIG_FILE = os.path.join(SESSIONS_DIR, 'accounts_config.json')

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

def load_accounts_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_all_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# --- تذكير: عند إنشاء الكلاينت داخل أي دالة، استخدم هذا المسار ---
# client = TelegramClient(os.path.join(SESSIONS_DIR, temp_phone), ...)

def main(page: ft.Page):
    page.title = "منظومة أبو الجوج v3.6.1"
    page.rtl = True
    page.scroll = "auto"
    
    # --- تأكد من عدم وجود أي دالة input() هنا أو في أي مكان في الكود ---
    # أي طلب للمستخدم يجب أن يكون عبر ft.TextField() حصراً
    
    # [ضع هنا واجهتك البرمجية بالكامل كما كانت في كودك الأصلي]
    # ...
    
    page.add(ft.Text("تم تشغيل المنظومة بنجاح على أندرويد"))

# --- تشغيل التطبيق بالطريقة المتوافقة مع flet build ---
if __name__ == '__main__':
    ft.app(target=main)

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

# --- تعديل المسارات الذكية لضمان عمل التطبيق على الموبايل ---
BASE_DIR = tempfile.gettempdir()
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')
LOG_FILE = os.path.join(BASE_DIR, 'processed_users.txt')
CONFIG_FILE = os.path.join(SESSIONS_DIR, 'accounts_config.json')

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# --- باقي الكود كما هو ---
def load_accounts_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_all_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def save_account_config(phone, api_id, api_hash):
    config = load_accounts_config()
    config[phone] = {'api_id': int(api_id), 'api_hash': api_hash, 'active': True}
    save_all_config(config)

def load_processed_users():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_user(user_id):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{user_id}\n")

def get_all_sessions():
    sessions = []
    if os.path.exists(SESSIONS_DIR):
        for file in os.listdir(SESSIONS_DIR):
            if file.endswith('.session'):
                sessions.append(file.replace('.session', ''))
    return sessions

def main(page: ft.Page):
    page.title = "منظومة أبو الجوج الاحترافية v3.6.1"
    page.rtl = True
    page.scroll = "auto"
    
    # [باقي الواجهة والوظائف من كودك السابق كما هي بالضبط]
    # تأكد فقط عند استدعاء TelegramClient أن تستخدم os.path.join(SESSIONS_DIR, phone)
    
    # مثال لتصحيح استدعاء الكلاينت داخل الدوال:
    # client = TelegramClient(os.path.join(SESSIONS_DIR, temp_phone), ...)
    
    # أكمل وضع بقية الأكواد الخاصة بك هنا...
    pass

if __name__ == '__main__':
    ft.app(target=main)

import os
import time
import random
import asyncio
import threading
import json
import flet as ft
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError

LOG_FILE = 'processed_users.txt'
SESSIONS_DIR = 'sessions'
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
    for file in os.listdir(SESSIONS_DIR):
        if file.endswith('.session'):
            sessions.append(file.replace('.session', ''))
    return sessions

def main(page: ft.Page):
    page.title = "منظومة أبو الجوج v3.6.1 - الإصدار المستقر والخالي من أخطاء الفوارز"
    page.rtl = True
    page.scroll = "auto"
    
    temp_phone = ""
    temp_api_id = ""
    temp_api_hash = ""
    phone_code_hash = ""
    is_transferring = False
    
    accounts_status = {} 
    config = load_accounts_config()
    for acc in get_all_sessions():
        accounts_status[acc] = config.get(acc, {}).get('active', True)

    phone_input = ft.TextField(label="رقم الهاتف الدولي الكامل (مثال: +964...)", width=250)
    api_id_input = ft.TextField(label="API ID", width=120, value="25609739")
    api_hash_input = ft.TextField(label="API Hash", width=280, value="94f542af3b52c1c05eae67ecf60bd269")
    code_input = ft.TextField(label="رمز التحقق (Telegram Code)", width=200, visible=False)
    status_msg = ft.Text("")
    
    send_code_btn = ft.ElevatedButton("إرسال رمز التحقق")
    verify_code_btn = ft.ElevatedButton("تأكيد الرمز والتفعيل", visible=False)
    
    accounts_list_view = ft.ListView(expand=True, spacing=5, height=160)
    sources_container = ft.Column(spacing=5)
    
    def remove_source_field(field_row):
        sources_container.controls.remove(field_row)
        try: page.update()
        except: pass

    def add_source_field(value=""):
        field = ft.TextField(label=f"رابط المجموعة المصدر #{len(sources_container.controls)+1}", value=value, expand=True)
        row = ft.Row([
            field,
            ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_ACCENT, on_click=lambda e: remove_source_field(row))
        ], spacing=5)
        sources_container.controls.append(row)
        try: page.update()
        except: pass

    add_source_field("https://t.me/Every_11")
    add_source_btn = ft.ElevatedButton("إضافة مجموعة مصدر جديدة (+)", icon=ft.Icons.ADD, on_click=lambda e: add_source_field())
    
    target_input = ft.TextField(label="رابط المجموعة الهدف", value="https://t.me/hjjwkg89")
    delay_input = ft.TextField(label="التأخير بين الإضافات الأساسي (ثانية)", value="120", width=180)
    cooldown_input = ft.TextField(label="الاستراحة الكبرى بعد كل 10 أعضاء (ثانية)", value="600", width=220)
    
    success_counter_text = ft.Text("✅ الإضافات الناجحة: 0", size=16, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)
    failed_counter_text = ft.Text("❌ المحاولات الفاشلة: 0", size=16, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
    timer_display = ft.Text("المنظومة في وضع الاستعداد...", size=14, color=ft.Colors.BLUE_300, weight=ft.FontWeight.BOLD)
    
    def force_refresh_ui(e):
        try: page.update()
        except: pass

    refresh_ui_btn = ft.IconButton(
        icon=ft.Icons.REFRESH, 
        icon_color=ft.Colors.ORANGE_400, 
        tooltip="إنعاش الشاشة والوقت يدوياً",
        on_click=force_refresh_ui
    )
    
    transfer_switch = ft.Switch(label="إيقاف / تشغيل النقل التلقائي", value=False, disabled=True)
    log_box = ft.ListView(expand=True, spacing=5, height=220, auto_scroll=True)
    
    def log_to_ui(text):
        log_box.controls.append(ft.Text(text))
        try: page.update()
        except: pass

    def refresh_accounts_ui():
        accounts_list_view.controls.clear()
        sessions = get_all_sessions()
        current_cfg = load_accounts_config()
        
        if not sessions:
            accounts_list_view.controls.append(ft.Text("لا توجد حسابات مسجلة حالياً."))
            transfer_switch.disabled = True
        else:
            for acc in sessions:
                if acc not in accounts_status:
                    accounts_status[acc] = current_cfg.get(acc, {}).get('active', True)
                status_text = "🟢 نشط بالنقل" if accounts_status[acc] else "🔴 معطل مؤقتاً"
                
                def make_toggle_handler(phone_num): return lambda e: toggle_account_active(phone_num, e.control.value)
                def make_delete_handler(phone_num): return lambda e: delete_account_session(phone_num)

                accounts_list_view.controls.append(
                    ft.Row([
                        ft.Text(f"حساب: {acc} [{status_text}]", expand=True),
                        ft.Switch(value=accounts_status[acc], on_change=make_toggle_handler(acc)),
                        ft.IconButton(icon=ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_600, on_click=make_delete_handler(acc))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            transfer_switch.disabled = False
        try: page.update()
        except: pass

    def toggle_account_active(phone, is_active):
        accounts_status[phone] = is_active
        current_cfg = load_accounts_config()
        if phone in current_cfg:
            current_cfg[phone]['active'] = is_active
            save_all_config(current_cfg)
        refresh_accounts_ui()

    def delete_account_session(phone):
        current_cfg = load_accounts_config()
        if phone in current_cfg: del current_cfg[phone]; save_all_config(current_cfg)
        if phone in accounts_status: del accounts_status[phone]
        try:
            os.remove(os.path.join(SESSIONS_DIR, f"{phone}.session"))
            os.remove(os.path.join(SESSIONS_DIR, f"{phone}.session-journal"))
        except: pass
        refresh_accounts_ui()

    def start_async_send_code():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_send_code())

    async def async_send_code():
        nonlocal phone_code_hash
        client = TelegramClient(os.path.join(SESSIONS_DIR, temp_phone), int(temp_api_id), temp_api_hash)
        try:
            await client.connect()
            res = await client.send_code_request(temp_phone)
            phone_code_hash = res.phone_code_hash
            await client.disconnect()
            status_msg.value = "🎉 كود التفعيل وصل! شيك التلي واكتبه بالأسفل."
            code_input.visible = True; verify_code_btn.visible = True; send_code_btn.visible = False
        except Exception as ex: status_msg.value = f"خطأ بالإرسال: {ex}"
        try: page.update()
        except: pass

    def send_code_wrapper(e):
        nonlocal temp_phone, temp_api_id, temp_api_hash
        temp_phone = phone_input.value.strip()
        temp_api_id = api_id_input.value.strip()
        temp_api_hash = api_hash_input.value.strip()
        if not temp_phone: return
        status_msg.value = "جاري الاتصال وسحب كود الحساب..."
        try: page.update()
        except: pass
        threading.Thread(target=start_async_send_code, daemon=True).start()

    def start_async_verify_code(code_val):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_verify_code(code_val))

    async def async_verify_code(code_val):
        client = TelegramClient(os.path.join(SESSIONS_DIR, temp_phone), int(temp_api_id), temp_api_hash)
        try:
            await client.connect()
            await client.sign_in(temp_phone, code_val, phone_code_hash=phone_code_hash)
            await client.disconnect()
            save_account_config(temp_phone, temp_api_id, temp_api_hash)
            accounts_status[temp_phone] = True
            status_msg.value = f"🎉 تم توثيق الحساب {temp_phone} بنجاح!"
            code_input.visible = False; verify_code_btn.visible = False; send_code_btn.visible = True
            phone_input.value = ""; code_input.value = ""
            refresh_accounts_ui()
        except Exception as ex: status_msg.value = f"خطأ بالرمز: {ex}"
        try: page.update()
        except: pass

    def verify_code_wrapper(e):
        code_val = code_input.value.strip()
        if not code_val: return
        status_msg.value = "جاري الحفظ والتوثيق المباشر للـ Session..."
        try: page.update()
        except: pass
        threading.Thread(target=lambda: start_async_verify_code(code_val), daemon=True).start()

    def start_transfer_manager():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_multi_transfer())

    async def live_countdown(seconds, label_text):
        nonlocal is_transferring
        for remaining in range(seconds, 0, -1):
            if not is_transferring: break
            timer_display.value = f"{label_text}.. متبقي: {remaining} ثانية"
            try: page.update()
            except: pass
            await asyncio.sleep(1)

    async def process_multi_transfer():
        nonlocal is_transferring
        source_urls = [row.controls[0].value.strip() for row in sources_container.controls if row.controls[0].value.strip()]
        target_url = target_input.value.strip()
        user_delay = int(delay_input.value.strip())
        user_cooldown = int(cooldown_input.value.strip())
        
        sessions = get_all_sessions()
        config = load_accounts_config()
        clients = []; active_phones = []
        
        for phone in sessions:
            if not is_transferring: break
            if not accounts_status.get(phone, True): continue
            client = TelegramClient(os.path.join(SESSIONS_DIR, phone), config.get(phone, {}).get('api_id', 25609739), config.get(phone, {}).get('api_hash', '94f542af3b52c1c05eae67ecf60bd269'))
            try:
                await client.connect()
                if await client.is_user_authorized():
                    for s_url in source_urls:
                        try: await client(JoinChannelRequest(s_url))
                        except: pass
                    try: await client(JoinChannelRequest(target_url))
                    except: pass
                    clients.append(client); active_phones.append(phone)
            except: pass

        if not clients:
            log_to_ui("[-] لا توجد حسابات جاهزة للعمل.")
            transfer_switch.value = False
            is_transferring = False
            try: page.update()
            except: pass
            return

        processed_users = load_processed_users()
        all_participants = []; unique_user_ids = set()
        
        log_to_ui("[*] جاري سحب الأعضاء بالخلفية...")
        for s_url in source_urls:
            if not is_transferring: break
            try:
                group_entity = await clients[0].get_entity(s_url)
                users = await clients[0].get_participants(group_entity)
                for u in users:
                    if u.id not in unique_user_ids and not u.bot and not u.is_self:
                        unique_user_ids.add(u.id); all_participants.append(u)
            except Exception as e: log_to_ui(f"[-] خطأ سحب من {s_url}: {e}")

        log_to_ui(f"[+] الإجمالي الجاهز للنقل: {len(all_participants)} عضو")
        
        success_count = 0
        failed_count = 0
        batch_count = 0
        account_index = 0
        
        for user in all_participants:
            if not is_transferring: break
            if str(user.id) in processed_users: continue
            if not clients: 
                log_to_ui("[!] نفدت جميع الحسابات المتاحة.")
                break

            idx = account_index % len(clients)
            current_client = clients[idx]; current_phone = active_phones[idx]
            
            try:
                log_to_ui(f"[>] [{current_phone}] محاولة نقل العضو ID: {user.id}...")
                target_group_active = await current_client.get_entity(target_url)
                
                await current_client(InviteToChannelRequest(target_group_active, [user]))
                
                success_count += 1
                batch_count += 1
                success_counter_text.value = f"✅ الإضافات الناجحة: {success_count}"
                log_to_ui(f"[🟢 إضافة ناجحة] تم إرسال الدعوة بنجاح بواسطة {current_phone}")
                save_processed_user(user.id)
                account_index += 1
                try: page.update()
                except: pass

                if batch_count >= 10:
                    batch_count = 0
                    await live_countdown(user_cooldown, "⏳ استراحة كبرى مكافحة للحظر")
                else:
                    await live_countdown(user_delay, "⏱️ تأخير أمان بين الأعضاء")
            
            except (PeerFloodError, FloodWaitError):
                failed_count += 1
                failed_counter_text.value = f"❌ المحاولات الفاشلة: {failed_count}"
                log_to_ui(f"[⚠️ تقييد] الحساب {current_phone} واجه ضغطاً، جاري التدوير...")
                account_index += 1
                try: page.update()
                except: pass
                await asyncio.sleep(2)
            except UserPrivacyRestrictedError:
                failed_count += 1
                failed_counter_text.value = f"❌ المحاولات الفاشلة: {failed_count}"
                log_to_ui(f"[-] العضو {user.id} خصوصيته مغلقة. تخطي.")
                save_processed_user(user.id)
                try: page.update()
                except: pass
            except Exception as ex:
                failed_count += 1
                failed_counter_text.value = f"❌ المحاولات الفاشلة: {failed_count}"
                log_to_ui(f"[-] فشلت المحاولة بسبب: {ex}")
                save_processed_user(user.id)
                account_index += 1
                try: page.update()
                except: pass

        log_to_ui("[+] انتهت الدورة الحالية للنقل بالكامل.")
        timer_display.value = "المنظومة في وضع الاستعداد..."
        transfer_switch.value = False
        is_transferring = False
        try: page.update()
        except: pass

    def switch_changed(e):
        nonlocal is_transferring
        if transfer_switch.value == True:
            is_transferring = True
            log_box.controls.clear()
            timer_display.value = "⏳ جاري تشغيل المحرك المستمر وبدء التحديث الجبرّي..."
            threading.Thread(target=start_transfer_manager, daemon=True).start()
        else:
            is_transferring = False
            timer_display.value = "🛑 تم إيقاف النقل يدوياً."
            try: page.update()
            except: pass

    send_code_btn.on_click = send_code_wrapper; verify_code_btn.on_click = verify_code_wrapper; transfer_switch.on_change = switch_changed

    page.add(
        ft.Column([
            ft.Text("منظومة أبو الجوج الاحترافية المتكاملة v3.6.1 - النسخة المستقرة", size=22, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("🛠️ إضافة وتوثيق حساب جديد مباشرة بالواجهة:", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([phone_input, api_id_input, api_hash_input]),
            ft.Row([send_code_btn, code_input, verify_code_btn]),
            status_msg,
            ft.Divider(),
            ft.Text("👥 قائمة إدارة وتفعيل/حذف الحسابات المسجلة:", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
            accounts_list_view,
            ft.Divider(),
            ft.Text("🎯 نظام المجموعات المصدر (إضافة ديناميكية مخصصة):", size=15, weight=ft.FontWeight.BOLD),
            sources_container,
            add_source_btn,
            ft.Divider(),
            target_input,
            ft.Divider(),
            
            ft.Text("📊 لوحة الإحصائيات الحية والعدادات الكلية:", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_300),
            ft.Row([success_counter_text, failed_counter_text], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ft.Divider(),
            
            ft.Text("⚙️ إعدادات النقل ومراقبة الوقت الحي التنازلي:", size=15, weight=ft.FontWeight.BOLD),
            ft.Row([delay_input, cooldown_input]),
            ft.Row([transfer_switch, timer_display, refresh_ui_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Text("📊 شاشة مراقبة العمليات والـ Log الحية:", size=14, weight=ft.FontWeight.W_600),
            log_box
        ], scroll=ft.ScrollMode.AUTO)
    )
    refresh_accounts_ui()

if __name__ == '__main__':
    try: ft.run(main)
    except: ft.app(target=main)
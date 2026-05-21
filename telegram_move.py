import time
import random
import sys
import os
import asyncio
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# --- معلومات الحسابات الخاصة بك ---
account_1 = {
    'api_id': 37296397,
    'api_hash': '485f23554447d64e5e98346b4ad958d6',
    'phone': '+9647871370490',
    'session_name': 'session_abu_al_jouj_1'
}

account_2 = {
    'api_id': 25609739,
    'api_hash': '94f542af3b52c1c05eae67ecf60bd269',
    'phone': '+9647502855686',
    'session_name': 'session_abu_al_jouj_2'
}

accounts = [account_1, account_2]
source_group_url = 'https://t.me/Every_11'
target_group_url = 'https://t.me/hjjwkg89'
LOG_FILE = 'processed_users.txt'

def load_processed_users():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_user(user_id):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{user_id}\n")

async def main():
    clients = []
    active_accounts = []
    
    print("=" * 50)
    print("[*] Connecting to all Telegram accounts...")
    print("=" * 50)
    
    for acc in accounts:
        try:
            print(f"[{acc['phone']}] Connecting...")
            client = TelegramClient(acc['session_name'], acc['api_id'], acc['api_hash'])
            await client.start(acc['phone'])
            me = await client.get_me()
            print(f"[+] Successfully logged in as: {me.first_name or 'Account'} ({acc['phone']})")
            
            try:
                await client(JoinChannelRequest(source_group_url))
                await client(JoinChannelRequest(target_group_url))
            except Exception:
                pass
                
            clients.append(client)
            active_accounts.append(acc['phone'])
        except Exception as e:
            print(f"[-] Failed to log in with account {acc['phone']}: {e}")

    print("=" * 50)
    print(f"[⚙️] Total Active Accounts in Rotation: {len(clients)}")
    print(f"[⚙️] Active Phones: {active_accounts}")
    print("=" * 50)

    if not clients:
        print("[-] No active accounts available. Exiting...")
        return

    main_client = clients[0]
    try:
        source_group = await main_client.get_entity(source_group_url)
    except Exception as e:
        print(f"[-] Error accessing source group: {e}")
        return

    processed_users = load_processed_users()
    print(f"\n[*] Loaded {len(processed_users)} previously processed members to skip.")

    print("[*] Fetching participants from source group...")
    participants = await main_client.get_participants(source_group)
    print(f"[+] Found {len(participants)} members in source group.")
    print("[*] Starting multi-account Anti-Ban transfer process...\n")

    added_count = 0
    batch_count = 0 
    account_index = 0
    
    for user in participants:
        if user.bot or user.is_self or str(user.id) in processed_users:
            continue
            
        if not clients:
            print("\n[!] All accounts are restricted. Process stopped.")
            break

        idx = account_index % len(clients)
        current_client = clients[idx]
        current_phone = active_accounts[idx]
        
        try:
            username = f"@{user.username}" if user.username else "[No Username]"
            print(f"[>] [{current_phone}] Trying to add member ID: {user.id} | Username: {username}")
            
            target_group_active = await current_client.get_entity(target_group_url)
            
            # أمر الإضافة المباشر
            await current_client(InviteToChannelRequest(target_group_active, [user]))
            
            added_count += 1
            batch_count += 1
            print(f"[+] Success! Total added in this session: {added_count}")
            save_processed_user(user.id)
            
            # التبديل للحساب التالي فقط عند النجاح المضمون
            account_index += 1
            
            # نظام الاستراحة الطويلة للوجبات لتفادي حظر الـ 24 ساعة
            if batch_count >= 10:
                batch_count = 0
                cooldown = random.randint(600, 900) # استراحة 10 إلى 15 دقيقة
                print(f"\n[☕] Batch reached! Taking a long break for {cooldown // 60} minutes...")
                for remaining in range(cooldown, 0, -1):
                    sys.stdout.write(f"\r[⏱️] Resuming in {remaining} seconds... ")
                    sys.stdout.flush()
                    time.sleep(1)
                print("\n")
            else:
                # مؤقت الأمان الطبيعي بين الإضافات لتمويه الرادار (120 إلى 240 ثانية)
                sleep_time = random.randint(120, 240)
                for remaining in range(sleep_time, 0, -1):
                    sys.stdout.write(f"\r[⏱️] Anti-Ban Delay: Waiting {remaining} seconds... ")
                    sys.stdout.flush()
                    time.sleep(1)
                print("\n")
            
        except PeerFloodError:
            print(f"\n[!] Flood Error: Account {current_phone} restricted temporarily.")
            print(f"[-] Removing account {current_phone} from rotation to protect members...")
            clients.remove(current_client)
            active_accounts.remove(current_phone)
            account_index = 0 
            time.sleep(3)
            
        except UserPrivacyRestrictedError:
            print("[-] Skipped: User privacy settings restriction. Saving to skip list...")
            save_processed_user(user.id)
            # الخصوصية مو ذنب الحساب، فياخذ العضو التالي فوراً وبنفس الحساب بدون حرق وقت ومؤقت طويل
            time.sleep(random.randint(3, 7))
            
        except FloodWaitError as e:
            print(f"\n[!] Flood Wait: Account {current_phone} must wait for {e.seconds} seconds.")
            print(f"[-] Temporary removing from rotation...")
            clients.remove(current_client)
            active_accounts.remove(current_phone)
            account_index = 0
            time.sleep(3)
            
        except Exception as e:
            # هنا السر: إذا الحساب واجه خطأ عام متكرر (مثل حظر مخفي)، نخرجه فوراً حتى ما يحرق الـ list
            print(f"[-] Account {current_phone} encountered an error. Removing from this session to be safe...")
            clients.remove(current_client)
            active_accounts.remove(current_phone)
            account_index = 0
            time.sleep(3)

    print(f"\n[+] Done! Session finished. Total added: {added_count}")

if __name__ == '__main__':
    asyncio.run(main())

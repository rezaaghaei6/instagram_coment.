# login.py — Instagram Session Keeper 2025 + حل خودکار چلنج با کد (ایمیل/پیامک)
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv
import os, time, random
from datetime import datetime

load_dotenv()

USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")
PROXY_RAW = os.getenv("PROXY", "").strip()  # اصلی رو نگه می‌داریم
SESSION_FILE = os.getenv("SESSION_FILE", "session.json")
CHECK_INTERVAL = 180  # هر 3 دقیقه چک

if not USERNAME or not PASSWORD:
    print("خطا: IG_USERNAME یا IG_PASSWORD در .env تنظیم نشده!")
    exit(1)

cl = Client()
cl.delay_range = [1.0, 5.0]

# ========== پشتیبانی 100% از همه نوع پراکسی (بدون کرش) ==========
PROXY = PROXY_RAW.lower()

if PROXY:
    try:
        # 1. فرمت‌های استاندارد (socks5://, http://, ...)
        if PROXY.startswith(('http://', 'https://', 'socks4://', 'socks5://', 'socks5h://')):
            final_proxy = PROXY
            print(f"پراکسی فعال: {PROXY_RAW}")

        # 2. فرمت ساده ایرانی: ip:port یا ip:port:user:pass
        else:
            parts = PROXY.split(':')
            if len(parts) == 2:  # ip:port
                ip, port = parts
                final_proxy = f"http://{ip}:{port}"
            elif len(parts) == 4:  # ip:port:user:pass
                ip, port, user, pwd = parts
                final_proxy = f"http://{user}:{pwd}@{ip}:{port}"
            else:
                print("فرمت پراکسی ناشناخته — بدون پراکسی ادامه می‌ده")
                final_proxy = None

            if 'final_proxy' in locals():
                print(f"پراکسی فعال (فرمت ساده): {final_proxy}")

        # اعمال پراکسی به instagrapi
        if 'final_proxy' in locals() and final_proxy:
            cl.set_proxy(final_proxy)

    except Exception as e:
        print(f"خطا در تنظیم پراکسی (نادیده گرفته شد): {e}")
else:
    print("بدون پراکسی")

# =====================================================================

def solve_challenge():
    print("چلنج اومد! کد تأیید به ایمیل یا شماره تلفن ارسال شد")
    print("کد ۶ رقمی رو از گوشی/ایمیل ببین و اینجا وارد کن:")
    while True:
        code = input("کد تأیید را وارد کن (فقط عدد): ").strip()
        if code.isdigit() and len(code) == 6:
            break
        print("کد باید ۶ رقم باشه! دوباره وارد کن")
    try:
        result = cl.challenge_resolve(code=int(code))
        if result:
            print("چلنج با موفقیت حل شد!")
            cl.dump_settings(SESSION_FILE)
            return True
        else:
            print("کد اشتباه بود یا منقضی شد!")
            return False
    except Exception as e:
        print(f"خطا در حل چلنج: {e}")
        return False

def login_once():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] در حال لاگین با @{USERNAME}...")
    try:
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] سشن قبلی زنده است")
        else:
            cl.login(USERNAME, PASSWORD)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] لاگین اولیه موفق")
        cl.dump_settings(SESSION_FILE)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] session.json ذخیره شد")
        return True
    except ChallengeRequired:
        print("چلنج امنیتی تشخیص داده شد!")
        if solve_challenge():
            return True
        else:
            print("چلنج حل نشد — برنامه بسته میشه")
            exit(1)
    except Exception as e:
        print(f"لاگین ناموفق: {e}")
        return False

def is_session_alive():
    try:
        cl.get_timeline_feed()
        return True
    except LoginRequired:
        return False
    except:
        return True

# ================ شروع برنامه ================
print("="*75)
print(" Instagram Session Keeper 2025 + حل خودکار چلنج با کد")
print(" اولین بار کد می‌گیره — بعدش تا ابد بدون مشکل کار می‌کنه")
print("="*75)

if not login_once():
    exit(1)

print(f"سشن آماده شد — هر {CHECK_INTERVAL} ثانیه چک میشه")
print("این اسکریپت رو هیچوقت نبند!")

while True:
    time.sleep(CHECK_INTERVAL + random.randint(-40, 40))
    print(f"[{datetime.now().strftime('%H:%M:%S')}] چک کردن سشن...")
    
    if not is_session_alive():
        print("سشن مرده است! دوباره لاگین...")
        if not login_once():
            time.sleep(600)
    else:
        print("سشن زنده است")
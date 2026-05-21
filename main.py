import subprocess
import time
import os
import json
import threading

# ================== تنظیمات ==================
UUID = "4ba5ee7f-f9e3-4226-aa59-a84b569297ab"
WORKER_HOST = "wispy-wind-f455.arvin341az.workers.dev"
VLESS_PORT = 2083

def download_xray():
    if not os.path.exists("xray"):
        print("📥 دانلود Xray...")
        os.system("wget -q https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -O xray.zip")
        os.system("unzip -o xray.zip && chmod +x xray && rm xray.zip")
        print("✅ Xray آماده شد.")

def generate_config():
    config = {
        "log": {
            "loglevel": "info",           # info یا debug (برای لاگ خیلی دقیق)
            "access": "none"              # ما خودمان لاگ دسترسی را مدیریت می‌کنیم
        },
        "inbounds": [{
            "port": VLESS_PORT,
            "listen": "0.0.0.0",
            "protocol": "vless",
            "settings": {
                "clients": [{"id": UUID}]
            },
            "streamSettings": {
                "network": "ws",
                "wsSettings": {
                    "path": "/"
                }
            },
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}
        }],
        "outbounds": [{
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": WORKER_HOST,
                    "port": 443,
                    "users": [{"id": UUID, "encryption": "none"}]
                }]
            },
            "streamSettings": {
                "network": "ws",
                "security": "tls",
                "tlsSettings": {
                    "serverName": WORKER_HOST,
                    "fingerprint": "random"
                },
                "wsSettings": {
                    "path": "/?ed=2560",
                    "headers": {"Host": WORKER_HOST}
                }
            }
        }]
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    print(f"✅ کانفیگ با لاگینگ ساخته شد (پورت {VLESS_PORT})")

def run_xray():
    download_xray()
    generate_config()
    
    print("🚀 Xray در حال اجرا است... (ترافیک واقعی نمایش داده می‌شود)")
    print("═" * 70)
    
    try:
        # اجرای Xray با خروجی کامل
        process = subprocess.Popen(
            ["./xray", "run", "-c", "config.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # نمایش زنده لاگ‌ها
        for line in process.stdout:
            line = line.strip()
            if line:
                # فیلتر و نمایش زیباتر
                if "accepted" in line.lower() or "inbound" in line.lower():
                    print(f"📥 [ورودی] {line}")
                elif "outbound" in line.lower() or "dial" in line.lower():
                    print(f"📤 [خروجی] {line}")
                elif "failed" in line.lower() or "error" in line.lower():
                    print(f"❌ [خطا] {line}")
                else:
                    print(line)
                    
    except KeyboardInterrupt:
        print("\n🛑 Xray متوقف شد.")
    except Exception as e:
        print(f"خطا: {e}")

def generate_vless_link(codespace_url):
    link = (
        f"vless://{UUID}@{codespace_url}:{VLESS_PORT}"
        f"?type=ws&security=none&path=/&host={codespace_url}"
        f"#{codespace_url}-Via-Codespace"
    )
    print("\n" + "═"*80)
    print("✅ لینک VLESS شما:")
    print(link)
    print("═"*80)
    print("این لینک را در v2rayNG / Nekobox import کنید.")
    return link

if __name__ == "__main__":
    # اجرای Xray در ترد جدا
    threading.Thread(target=run_xray, daemon=True).start()
    
    time.sleep(8)
    
    # نمایش لینک
    try:
        codespace_url = os.getenv("CODESPACE_NAME") + ".app.github.dev"
        generate_vless_link(codespace_url)
    except:
        print("\n⚠️ آدرس Codespace را وارد کنید:")
        url = input("آدرس: ").strip()
        generate_vless_link(url)
    
    # نگه داشتن برنامه
    try:
        while True:
            time.sleep(300)
    except KeyboardInterrupt:
        print("\nخداحافظ!")

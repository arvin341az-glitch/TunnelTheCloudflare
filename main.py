import subprocess
import time
import os
import requests
import threading

# تنظیمات
VLESS_LINK = "vless://4ba5ee7f-f9e3-4226-aa59-a84b569297ab@wispy-wind-f455.arvin341az.workers.dev:443?encryption=none&security=tls&sni=wispy-wind-f455.arvin341az.workers.dev&fp=random&type=ws&host=wispy-wind-f455.arvin341az.workers.dev&path=%2F%3Fed%3D2560#CF-Worker-VLESS"

XRAY_PORT = 1080  # پورت SOCKS5 محلی
XRAY_CONFIG = "config.json"

def download_xray():
    """دانلود آخرین نسخه Xray برای لینوکس amd64"""
    url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
    if not os.path.exists("xray"):
        print("در حال دانلود Xray...")
        os.system(f"wget -q {url} -O xray.zip")
        os.system("unzip -o xray.zip && chmod +x xray")
        print("Xray دانلود شد.")

def generate_xray_config():
    config = {
        "inbounds": [{
            "port": XRAY_PORT,
            "listen": "0.0.0.0",
            "protocol": "socks",
            "settings": {"udp": True}
        }],
        "outbounds": [{
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": "wispy-wind-f455.arvin341az.workers.dev",
                    "port": 443,
                    "users": [{
                        "id": "4ba5ee7f-f9e3-4226-aa59-a84b569297ab",
                        "encryption": "none",
                        "flow": ""
                    }]
                }]
            },
            "streamSettings": {
                "network": "ws",
                "security": "tls",
                "tlsSettings": {
                    "serverName": "wispy-wind-f455.arvin341az.workers.dev",
                    "fingerprint": "random"
                },
                "wsSettings": {
                    "path": "/?ed=2560",
                    "headers": {
                        "Host": "wispy-wind-f455.arvin341az.workers.dev"
                    }
                }
            }
        }]
    }
    
    import json
    with open(XRAY_CONFIG, "w") as f:
        json.dump(config, f, indent=2)
    print(f"کانفیگ Xray با موفقیت ساخته شد → پورت SOCKS5: {XRAY_PORT}")

def run_xray():
    download_xray()
    generate_xray_config()
    
    print("Xray در حال اجرا... (برای خروج Ctrl+C بزن)")
    try:
        subprocess.run(["./xray", "run", "-c", XRAY_CONFIG])
    except KeyboardInterrupt:
        print("\nXray متوقف شد.")

if __name__ == "__main__":
    # اجرا در ترد جدا برای اینکه بتونی اسکریپت رو ادامه بدی
    threading.Thread(target=run_xray, daemon=True).start()
    
    print(f"\n✅ پروکسی SOCKS5 آماده است: socks5://127.0.0.1:{XRAY_PORT}")
    print("حالا می‌تونی از این پروکسی توی مرورگر، curl، requests و ... استفاده کنی.")
    
    # تست اتصال
    time.sleep(5)
    try:
        proxies = {"http": f"socks5://127.0.0.1:{XRAY_PORT}", "https": f"socks5://127.0.0.1:{XRAY_PORT}"}
        r = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10)
        print("IP فعلی:", r.json())
    except:
        print("تست IP انجام نشد (ممکنه هنوز Xray آماده نشده باشه)")
    
    # نگه داشتن اسکریپت
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("خداحافظ!")

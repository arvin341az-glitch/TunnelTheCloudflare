import subprocess
import time
import os
import json
import threading
import re
import signal

# ================== تنظیمات ==================
UUID = "4ba5ee7f-f9e3-4226-aa59-a84b569297ab"
WORKER_HOST = "wispy-wind-f455.arvin341az.workers.dev"
VLESS_PORT = 2083
CLOUDFLARED_PATH = "./cloudflared"

def download_xray():
    """دانلود Xray اگر موجود نباشد"""
    if not os.path.exists("xray"):
        print("📥 دانلود Xray...")
        os.system("wget -q https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -O xray.zip")
        os.system("unzip -o xray.zip && chmod +x xray && rm xray.zip")
        print("✅ Xray آماده شد.")

def generate_config():
    """ساخت کانفیگ Xray"""
    config = {
        "log": {"loglevel": "info"},
        "inbounds": [{
            "port": VLESS_PORT,
            "listen": "0.0.0.0",
            "protocol": "vless",
            "settings": {
                "decryption": "none",
                "clients": [{"id": UUID, "flow": "", "decryption": "none"}]
            },
            "streamSettings": {
                "network": "ws",
                "wsSettings": {"path": "/"}
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
                "tlsSettings": {"serverName": WORKER_HOST, "fingerprint": "random"},
                "wsSettings": {"path": "/?ed=2560", "headers": {"Host": WORKER_HOST}}
            }
        }]
    }
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    print(f"✅ کانفیگ Xray ساخته شد (پورت {VLESS_PORT})")

def run_xray():
    """اجرای Xray در یک ترد جداگانه"""
    download_xray()
    generate_config()
    
    print("🚀 Xray در حال اجرا است...")
    print("═" * 70)
    
    try:
        process = subprocess.Popen(
            ["./xray", "run", "-c", "config.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            line = line.strip()
            if line:
                if "accepted" in line.lower():
                    print(f"📥 [اتصال] {line}")
                elif "dial" in line.lower():
                    print(f"📤 [ترافیک] {line}")
                elif "error" in line.lower() or "failed" in line.lower():
                    if "decryption" not in line.lower():
                        print(f"❌ [خطا] {line}")
                elif "started" in line.lower():
                    print(f"✅ {line}")
                    
    except Exception as e:
        print(f"خطا در Xray: {e}")

def download_cloudflared():
    """دانلود cloudflared اگر موجود نباشد"""
    if not os.path.exists(CLOUDFLARED_PATH):
        print("📥 دانلود Cloudflared...")
        os.system("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared")
        os.system("chmod +x cloudflared")
        print("✅ Cloudflared آماده شد.")
    else:
        print("✅ Cloudflared از قبل موجود است.")

def get_tunnel_url():
    """اجرای cloudflared و گرفتن آدرس تونل"""
    print("🔗 در حال ایجاد تونل Cloudflare...")
    
    process = subprocess.Popen(
        ["./cloudflared", "tunnel", "--url", f"http://localhost:{VLESS_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    tunnel_url = None
    
    def read_output():
        nonlocal tunnel_url
        for line in process.stdout:
            line = line.strip()
            if "trycloudflare.com" in line and "https://" in line:
                match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                if match and not tunnel_url:
                    tunnel_url = match.group(1)
                    print(f"\n✅ تونل ساخته شد: {tunnel_url}")
                    generate_vless_link(tunnel_url)
            elif "INF" in line and not line.startswith("2026"):
                print(f"   {line}")
    
    thread = threading.Thread(target=read_output, daemon=True)
    thread.start()
    
    return process, thread, lambda: tunnel_url

def generate_vless_link(tunnel_url):
    """ساخت لینک VLESS با آدرس تونل"""
    if not tunnel_url:
        return
    
    host = tunnel_url.replace("https://", "").replace("http://", "")
    
    link = (
        f"vless://{UUID}@{host}:443"
        f"?type=ws&security=tls&sni={host}&fp=random&allowInsecure=1&path=%2F"
        f"#{host}-Via-Codespace"
    )
    
    print("\n" + "═" * 85)
    print("🔗 لینک VLESS برای اتصال از کلاینت:")
    print(link)
    print("═" * 85)
    
    # ذخیره در فایل
    with open("vless_link.txt", "w") as f:
        f.write(link)
    print("📁 لینک همچنین در فایل vless_link.txt ذخیره شد.")
    
    return link

def main():
    print("=" * 70)
    print("🚀 راه‌اندازی خودکار تونل VLESS + Cloudflare")
    print("=" * 70)
    
    # 1. دانلود ابزارها
    download_cloudflared()
    
    # 2. اجرای Xray در پس‌زمینه
    xray_thread = threading.Thread(target=run_xray, daemon=True)
    xray_thread.start()
    
    # 3. منتظر بمان تا Xray کاملاً شروع شود
    print("⏳ منتظر آماده‌سازی Xray...")
    time.sleep(5)
    
    # 4. اجرای تونل و گرفتن آدرس
    tunnel_process, output_thread, get_url_func = get_tunnel_url()
    
    print("\n" + "=" * 70)
    print("✅ همه چیز در حال اجراست!")
    print("⚠️  برای متوقف کردن: Ctrl+C بزنید")
    print("=" * 70)
    
    try:
        while True:
            time.sleep(10)
            url = get_url_func()
            if url:
                break
            time.sleep(5)
        
        # منتظر بمان تا تونل فعال بماند
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 در حال متوقف کردن سرویس‌ها...")
        tunnel_process.terminate()
        print("✅ توقف کامل. خداحافظ!")

if __name__ == "__main__":
    main()

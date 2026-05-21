import subprocess
import time
import os
import json
import threading

# ================== تنظیمات ==================
UUID = "4ba5ee7f-f9e3-4226-aa59-a84b569297ab"
WORKER_HOST = "wispy-wind-f455.arvin341az.workers.dev"
VLESS_PORT = 2083          # پورت VLESS inbound در Codespace
SOCKS_PORT = 1080

def download_xray():
    if not os.path.exists("xray"):
        print("📥 Now DAwnloading X2ay")
        os.system("wget -q https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -O xray.zip")
        os.system("unzip -o xray.zip && chmod +x xray && rm xray.zip")
        print("✅ Dawnload X2ray.")

def generate_config():
    config = {
        "inbounds": [
            # VLESS Inbound (برای اتصال مستقیم کلاینت تو)
            {
                "port": VLESS_PORT,
                "listen": "0.0.0.0",
                "protocol": "vless",
                "settings": {
                    "clients": [{"id": UUID, "flow": ""}]
                },
                "streamSettings": {
                    "network": "tcp"
                }
            },
            # SOCKS5 (اختیاری)
            {
                "port": SOCKS_PORT,
                "listen": "0.0.0.0",
                "protocol": "socks",
                "settings": {"udp": True}
            }
        ],
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
    print(f"X2ray Config Generated For Connect To Cloudflare Vless (VLESS Port: {VLESS_PORT})")

def run_xray():
    download_xray()
    generate_config()
    
    print("🚀 Now Starting The X2ray")
    try:
        subprocess.run(["./xray", "run", "-c", "config.json"])
    except KeyboardInterrupt:
        print("🛑 Stoped X2ray")

def generate_vless_link(codespace_url):
    link = f"vless://{UUID}@{codespace_url}:{VLESS_PORT}?security=none&encryption=none&type=tcp#{codespace_url}-Via-CF"
    print("\n" + "="*60)
    print("✅ Ready The Config:")
    print(link)
    print("="*60)
    print("Import The clint")
    return link

if __name__ == "__main__":
    threading.Thread(target=run_xray, daemon=True).start()
    
    time.sleep(6)  # زمان برای آماده شدن Xray
    
    # تشخیص آدرس Codespace
    try:
        codespace_url = os.getenv("CODESPACE_NAME") + ".app.github.dev"
        generate_vless_link(codespace_url)
    except:
        print("\n⚠️  آدرس Codespace را دستی وارد کنید (مثلاً: abc123-2083.app.github.dev)")
        codespace_url = input("آدرس Codespace: ")
        generate_vless_link(codespace_url)
    
    # نگه داشتن برنامه
    try:
        while True:
            time.sleep(300)
    except KeyboardInterrupt:
        print("خداحافظ!")

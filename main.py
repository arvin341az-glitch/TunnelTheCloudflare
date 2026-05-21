import subprocess
import time
import os
import json
import threading
import re
import sys

# ================== SETTINGS ==================
UUID = "4ba5ee7f-f9e3-4226-aa59-a84b569297ab"
WORKER_HOST = "wispy-wind-f455.arvin341az.workers.dev"
VLESS_PORT = 2083

def download_xray():
    if not os.path.exists("xray"):
        print("📥 Downloading Xray...")
        os.system("wget -q https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -O xray.zip")
        os.system("unzip -o xray.zip && chmod +x xray && rm xray.zip")
        print("✅ Xray ready.")

def generate_config():
    config = {
        "log": {"loglevel": "warning"},
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

def run_xray():
    download_xray()
    generate_config()
    
    process = subprocess.Popen(
        ["./xray", "run", "-c", "config.json"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return process

def download_cloudflared():
    if not os.path.exists("./cloudflared"):
        print("📥 Downloading Cloudflared...")
        os.system("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared")
        os.system("chmod +x cloudflared")
        print("✅ Cloudflared ready.")

def run_tunnel():
    """Run tunnel and automatically get URL"""
    process = subprocess.Popen(
        ["./cloudflared", "tunnel", "--url", f"http://localhost:{VLESS_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    tunnel_url = None
    
    for line in process.stdout:
        if "trycloudflare.com" in line and "https://" in line:
            match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
            if match:
                tunnel_url = match.group(1)
                print(f"\n✅ Tunnel created: {tunnel_url}")
                generate_and_save_link(tunnel_url)
                break
    
    return process, tunnel_url

def generate_and_save_link(tunnel_url):
    """Generate link and save automatically"""
    host = tunnel_url.replace("https://", "").replace("http://", "")
    
    link = (
        f"vless://{UUID}@{host}:443"
        f"?type=ws&security=tls&sni={host}&fp=random&allowInsecure=1&path=%2F"
        f"#{host}"
    )
    
    print("\n" + "═" * 85)
    print("🔗 VLESS Link (copy and paste in your client):")
    print(link)
    print("═" * 85)
    
    with open("vless_link.txt", "w") as f:
        f.write(link)
    
    print("📁 Link saved in vless_link.txt file")
    
    # Auto copy to clipboard if possible
    try:
        import pyperclip
        pyperclip.copy(link)
        print("📋 Link copied to clipboard (you can Ctrl+V now).")
    except:
        pass
    
    return link

def main():
    os.system("clear")
    print("=" * 70)
    print("🚀 Automatic VLESS + Cloudflare Tunnel Setup")
    print("⏳ Please wait... (max 30 seconds)")
    print("=" * 70)
    
    # Download tools
    download_cloudflared()
    
    # Run Xray
    xray_process = run_xray()
    time.sleep(3)
    
    # Run tunnel and get URL
    tunnel_process, tunnel_url = run_tunnel()
    
    if not tunnel_url:
        print("❌ Error: Tunnel failed to create!")
        return
    
    print("\n" + "=" * 70)
    print("✅ Service successfully started!")
    print("🟢 Status: Active")
    print("🔗 Enter the link above in your client")
    print("⚠️ To stop: Press Ctrl+C")
    print("=" * 70)
    
    # Keep the program running
    try:
        while True:
            time.sleep(3600)  # Check every hour
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        tunnel_process.terminate()
        xray_process.terminate()
        print("✅ Complete stop.")

if __name__ == "__main__":
    main()

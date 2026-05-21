import subprocess
import time
import os
import json
import re

# ================== SETTINGS ==================
UUID = "4ba5ee7f-f9e3-4226-aa59-a84b569297ab"
VLESS_PORT = 2083

def download_xray():
    if not os.path.exists("xray"):
        print("📥 Downloading Xray...")
        os.system("wget -q https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -O xray.zip")
        os.system("unzip -o xray.zip && chmod +x xray && rm xray.zip")
        print("✅ Xray ready.")

def generate_config():
    """Config with direct internet outbound (no Worker)"""
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
            }
        }],
        "outbounds": [{
            "protocol": "freedom",  # Direct connection to internet
            "settings": {}
        }]
    }
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("✅ Config created (direct internet outbound)")

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
                break
    
    return process, tunnel_url

def main():
    os.system("clear")
    print("=" * 70)
    print("🚀 GitHub Codespace VPN - Direct Internet")
    print("   Your traffic goes through GitHub (not Cloudflare)")
    print("=" * 70)
    
    download_cloudflared()
    xray_process = run_xray()
    time.sleep(3)
    
    tunnel_process, tunnel_url = run_tunnel()
    
    if not tunnel_url:
        print("❌ Error: Tunnel failed!")
        return
    
    host = tunnel_url.replace("https://", "")
    link = f"vless://{UUID}@{host}:443?type=ws&security=tls&sni={host}&fp=random&allowInsecure=1&path=%2F#{host}"
    
    print("\n" + "═" * 85)
    print("🔗 YOUR VLESS LINK (Copy this):")
    print(link)
    print("═" * 85)
    print("\n✅ Traffic flow: You → GitHub Codespace → Internet")
    print("⚠️  Press Ctrl+C to stop")
    
    with open("vless_link.txt", "w") as f:
        f.write(link)
    
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        tunnel_process.terminate()
        xray_process.terminate()
        print("✅ Done")

if __name__ == "__main__":
    main()

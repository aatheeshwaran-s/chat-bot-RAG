"""
Share Public URL for Streamlit Tier-1 Deflection & RAG UI.
Supports both Ngrok (requires free authtoken) and instant zero-config tunneling.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

def share_with_ngrok(authtoken: str = None, port: int = 8501):
    from pyngrok import ngrok, conf

    token = authtoken or os.getenv("NGROK_AUTHTOKEN")
    if token:
        ngrok.set_auth_token(token)
    else:
        print("\n[!] Notice: Ngrok requires a free authtoken from https://dashboard.ngrok.com/get-started/your-authtoken")
        print("    You can run: python share_url.py --ngrok --token <YOUR_TOKEN>")
        print("    Or add NGROK_AUTHTOKEN=<token> to your .env file.\n")

    try:
        tunnel = ngrok.connect(port)
        print("=" * 65)
        print(f"🚀 NGROK PUBLIC URL: {tunnel.public_url}")
        print(f"🔗 Forwarding: {tunnel.public_url} -> http://localhost:{port}")
        print("=" * 65)
        print("\nPress Ctrl+C to close the tunnel.\n")
        # Keep process alive
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing Ngrok tunnel...")
        ngrok.disconnect(tunnel.public_url)
    except Exception as e:
        print(f"\n[NGROK ERROR] {e}")


def share_with_localtunnel(port: int = 8501):
    import subprocess
    print("=" * 65)
    print("🚀 Launching Instant Public Tunnel (No Account Required)...")
    print(f"🔗 Forwarding port {port}")
    print("=" * 65)
    subprocess.run(["npx", "-y", "localtunnel", "--port", str(port)])


def main():
    parser = argparse.ArgumentParser(description="Share public tunnel for Streamlit UI")
    parser.add_argument("--ngrok", action="store_true", help="Use Ngrok tunnel")
    parser.add_argument("--token", type=str, default=None, help="Ngrok Authtoken")
    parser.add_argument("--port", type=int, default=8501, help="Local port (default 8501)")
    args = parser.parse_args()

    if args.ngrok or args.token or os.getenv("NGROK_AUTHTOKEN"):
        share_with_ngrok(authtoken=args.token, port=args.port)
    else:
        share_with_localtunnel(port=args.port)


if __name__ == "__main__":
    main()

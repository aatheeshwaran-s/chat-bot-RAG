"""
Share Public URL for Streamlit Tier-1 Deflection & RAG UI.
Supports both Ngrok (with free authtoken) and instant zero-config tunneling (localtunnel).
"""

import os
import sys
import shutil
import subprocess
import argparse
from dotenv import load_dotenv

load_dotenv()

def _save_token_to_env(token: str):
    """Save NGROK_AUTHTOKEN to .env file for future executions."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        lines = []
        token_found = False
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("NGROK_AUTHTOKEN="):
                        lines.append(f"NGROK_AUTHTOKEN={token}\n")
                        token_found = True
                    else:
                        lines.append(line)
        if not token_found:
            lines.append(f"\nNGROK_AUTHTOKEN={token}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"✅ Saved NGROK_AUTHTOKEN to {env_path}")
    except Exception as e:
        print(f"[Warning] Could not persist token to .env: {e}")


def share_with_localtunnel(port: int = 8501):
    """Launch instant zero-config public tunnel using localtunnel."""
    print("\n" + "=" * 65)
    print("🚀 Launching Instant Public Tunnel (No Account Required)...")
    print(f"🔗 Forwarding: http://localhost:{port}")
    print("=" * 65)

    npx_cmd = shutil.which("npx") or "npx"
    try:
        # On Windows, npx is npx.cmd and requires shell=True
        subprocess.run([npx_cmd, "-y", "localtunnel", "--port", str(port)], shell=(os.name == "nt"))
    except KeyboardInterrupt:
        print("\nTunnel closed.")
    except Exception as e:
        print(f"\n[TUNNEL ERROR] {e}")


def share_with_ngrok(authtoken: str = None, port: int = 8501):
    """Deploy public tunnel via Ngrok (requires free authtoken)."""
    from pyngrok import ngrok

    token = authtoken or os.getenv("NGROK_AUTHTOKEN")
    if not token:
        print("\n" + "=" * 65)
        print("🔑 NGROK AUTHENTICATION REQUIRED")
        print("Ngrok requires a free authtoken from:")
        print("👉 https://dashboard.ngrok.com/get-started/your-authtoken")
        print("=" * 65)
        try:
            user_token = input("\nPaste your Ngrok authtoken here (or press Enter for instant tunnel): ").strip()
            if user_token:
                token = user_token
                _save_token_to_env(token)
            else:
                print("\nFalling back to instant public tunnel (no account needed)...")
                share_with_localtunnel(port=port)
                return
        except (KeyboardInterrupt, EOFError):
            print("\nTunnel setup cancelled.")
            return

    try:
        ngrok.set_auth_token(token)
        tunnel = ngrok.connect(port)
        print("\n" + "=" * 65)
        print(f"🚀 NGROK PUBLIC URL: {tunnel.public_url}")
        print(f"🔗 Forwarding: {tunnel.public_url} -> http://localhost:{port}")
        print("=" * 65)
        print("\nPress Ctrl+C to close the tunnel.\n")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing Ngrok tunnel...")
        try:
            ngrok.disconnect(tunnel.public_url)
            ngrok.kill()
        except Exception:
            pass
    except Exception as e:
        print(f"\n[NGROK ERROR] {e}")
        print("Falling back to instant public tunnel...")
        share_with_localtunnel(port=port)


def main():
    parser = argparse.ArgumentParser(description="Share public tunnel for Streamlit UI")
    parser.add_argument("--ngrok", action="store_true", help="Use Ngrok tunnel")
    parser.add_argument("--token", type=str, default=None, help="Ngrok Authtoken")
    parser.add_argument("--port", type=int, default=8501, help="Local port (default 8501)")
    args = parser.parse_args()

    # If --token or --ngrok or NGROK_AUTHTOKEN provided, use Ngrok
    if args.ngrok or args.token or os.getenv("NGROK_AUTHTOKEN"):
        share_with_ngrok(authtoken=args.token, port=args.port)
    else:
        # Prompt user or default to ngrok handler which prompts/falls back
        share_with_ngrok(authtoken=None, port=args.port)


if __name__ == "__main__":
    main()

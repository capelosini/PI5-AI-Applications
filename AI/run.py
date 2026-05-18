import asyncio
import json
import os
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HOST = "0.0.0.0"
PORT = 8081

# Configuration from .env
BASE_URL = os.getenv("GAME_API_URL")
PLAYER_ID = os.getenv("BOT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")


def setup_directory():
    """Ensure the script runs from the project root and can find the app directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    app_dir = os.path.join(script_dir, "app")
    if not os.path.exists(app_dir):
        print(f"Error: app directory not found at {app_dir}")
        sys.exit(1)


# Global list to keep track of tasks to prevent garbage collection
_tasks = set()

async def stream_output(stream, prefix):
    """Streams output from a subprocess to the console."""
    try:
        while True:
            line = await stream.readline()
            if not line:
                break
            print(f"[{prefix}] {line.decode(errors='replace').strip()}", flush=True)
    except Exception as e:
        print(f"[{prefix}] Error streaming output: {e}", flush=True)


async def start_service(cmd, prefix, cwd=None):
    """Starts a subprocess and pipes its output."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=cwd,
        env=env,
    )
    
    task = asyncio.create_task(stream_output(process.stdout, prefix))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    
    return process


def fetch_ngrok_url():
    """Fetches the public URL from ngrok's local API using standard library."""
    for _ in range(15):
        try:
            with urlopen("http://localhost:4040/api/tunnels", timeout=2) as response:
                data = json.load(response)
                tunnels = data.get("tunnels", [])
                if tunnels:
                    return tunnels[0].get("public_url")
        except (URLError, ConnectionError, json.JSONDecodeError):
            pass
        time.sleep(1)
    return None


def update_external_api(public_url):
    """Updates the external API with the new Ngrok public URL."""
    if not all([BASE_URL, PLAYER_ID, BOT_TOKEN]):
        print(
            "[!] Error: Missing required environment variables (GAME_API_URL, BOT_ID, BOT_TOKEN)."
        )
        return False

    url = f"{BASE_URL.rstrip('/')}/players/{PLAYER_ID}"
    data = json.dumps({"ai_player_move_endpoint": f"{public_url}/move"}).encode("utf-8")

    print(f"[*] Registering endpoint at {url}...")

    req = Request(url, data=data, method="PUT")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {BOT_TOKEN}")

    try:
        with urlopen(req, timeout=10) as response:
            if response.status in (200, 201, 204):
                print("[+] Successfully registered endpoint with external API.")
                return True
            else:
                print(f"[!] External API returned status: {response.status}")
    except URLError as e:
        print(f"[!] Failed to register endpoint: {e}")
    except Exception as e:
        print(f"[!] Unexpected error during registration: {e}")

    return False


async def main():
    setup_directory() # Ensure we are in project root

    print("--- Starting CAPTCHA 2.0 API Services ---")

    # Start Uvicorn using the new package structure
    # We run from root, so the module path is app.api.main:app
    uvicorn_cmd = f"uvicorn app.api.main:app --host {HOST} --port {PORT}"
    uvicorn_proc = await start_service(uvicorn_cmd, "Uvicorn")

    # Start Ngrok
    ngrok_cmd = f"ngrok http {PORT}"
    ngrok_proc = await start_service(ngrok_cmd, "Ngrok")

    print("Waiting for Ngrok to initialize...")
    await asyncio.sleep(2)

    public_url = fetch_ngrok_url()

    if public_url:
        print("\n" + "═" * 50)
        print(f"  API Local:  http://localhost:{PORT}")
        print(f"  API Public: {public_url}")
        print("" + "═" * 50 + "\n")

        # Update external API
        update_external_api(public_url)
    else:
        print("\n[!] Warning: Could not retrieve Ngrok public URL.")
        print(
            "[!] Verify ngrok is authenticated: 'ngrok config add-authtoken <token>'\n"
        )

    # Keep services running
    try:
        await asyncio.gather(uvicorn_proc.wait(), ngrok_proc.wait())
    except (asyncio.CancelledError, KeyboardInterrupt):
        print("\nShutting down services...")
        uvicorn_proc.terminate()
        ngrok_proc.terminate()
        await asyncio.gather(uvicorn_proc.wait(), ngrok_proc.wait())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

#!/usr/bin/env python3
"""
==========================================================================
  SATYA PRIMEVECTOR — LOCAL LIGHTWEIGHT LAUNCHER (Colab Hybrid Mode)
==========================================================================
  Runs the local microservices on your PC (~350 MB RAM), including the
  Dhwani 2 Deepfake Detection Model on port 8002.
  
  The heavy ML processing (Feature Extraction & Speaker Enrollment)
  is hosted on Google Colab and reached via the ngrok tunnel URL.

  ARCHITECTURE:
    Local PC:
      - spoof-detection-service  :8002 (Local Dhwani 2 Deepfake Model)
      - risk-fusion-engine       :8000 (Local Compliance & Fusion Math)
      - policy-threshold-engine  :8004 (Local Policy & Auto-Block)
      - alerting-service         :8005 (Local Alert Dispatch)
      - orchestrator             :8085 (Local Pipeline Coordinator)
      - api-gateway              :8090 (Local REST API & Metering)
      - serve_dashboard          :9000 (Local Web Dashboard)
    
    Google Colab (via Ngrok Tunnel):
      - feature-extraction-service /feat  (3-Channel Spectrograms)
      - enrollment-service       /enroll (Resemblyzer Voiceprints)

  PREREQUISITES:
    1. Run colab_ml_services.py on Google Colab first.
    2. Enter or copy the ngrok URL when prompted or set in .env as:
       COLAB_TUNNEL_URL=https://xxxx.ngrok-free.app
    3. Run: python run_local_lightweight.py
==========================================================================
"""

import os
import sys
import time
import signal
import subprocess
import urllib.request
import webbrowser

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ANSI Colors for clean logging
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_env():
    """Load .env file into environment."""
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def save_env_colab_url(colab_url: str):
    """Save or update COLAB_TUNNEL_URL in .env file."""
    env_file = os.path.join(BASE_DIR, ".env")
    lines = []
    updated = False
    if os.path.isfile(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.strip().startswith("COLAB_TUNNEL_URL="):
                    lines.append(f"COLAB_TUNNEL_URL={colab_url}\n")
                    updated = True
                else:
                    lines.append(line)
    if not updated:
        lines.append(f"\n# Google Colab Ngrok Tunnel URL\nCOLAB_TUNNEL_URL={colab_url}\n")

    with open(env_file, "w") as f:
        f.writelines(lines)
    os.environ["COLAB_TUNNEL_URL"] = colab_url


def get_colab_url():
    """Get the Colab tunnel URL from environment or prompt interactively."""
    url = os.environ.get("COLAB_TUNNEL_URL", "").strip()
    if not url or "ngrok" not in url:
        print(f"\n{YELLOW}{'=' * 70}{RESET}")
        print(f"{YELLOW}  ⚠️  COLAB_TUNNEL_URL not configured or invalid in .env!{RESET}")
        print(f"{YELLOW}{'=' * 70}{RESET}")
        print(f"""
  To connect heavy ML services from Google Colab:
    1. Open Google Colab notebook & paste `colab_ml_services.py`
    2. Copy the active ngrok URL (e.g. https://xxxx-xx-xx.ngrok-free.app)
""")
        try:
            user_input = input(f"{CYAN}  Enter Ngrok Tunnel URL (or press Enter to skip): {RESET}").strip()
            if user_input:
                url = user_input.rstrip("/")
                save_env_colab_url(url)
                print(f"{GREEN}  ✅ Saved COLAB_TUNNEL_URL={url} to .env{RESET}")
            else:
                url = "http://localhost:8001"
        except (KeyboardInterrupt, EOFError):
            url = "http://localhost:8001"

    return url.rstrip("/")


# ─────────────────────────────────────────────────────────────────────────
# LOCAL SERVICES CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────

LOCAL_SERVICES = [
    {
        "name": "risk-fusion-engine",
        "app_dir": os.path.join(BASE_DIR, "services", "risk-fusion-engine", "app"),
        "port": 8000,
        "module": "main:app",
        "env": {},
    },
    {
        "name": "spoof-detection-service (Local Dhwani 2 Model)",
        "app_dir": os.path.join(BASE_DIR, "services", "spoof-detection-service", "app"),
        "port": 8002,
        "module": "main:app",
        "env": {"SPOOF_MODEL_REGISTRY_BACKEND": "deepfake"},
    },
    {
        "name": "policy-threshold-engine",
        "app_dir": os.path.join(BASE_DIR, "services", "policy-threshold-engine", "app"),
        "port": 8004,
        "module": "main:app",
        "env": {},
    },
    {
        "name": "alerting-service",
        "app_dir": os.path.join(BASE_DIR, "services", "alerting-service", "app"),
        "port": 8005,
        "module": "main:app",
        "env": {},
    },
    {
        "name": "api-gateway",
        "app_dir": os.path.join(BASE_DIR, "services", "api-gateway"),
        "port": 8090,
        "module": "main:app",
        "env": {"SPOOF_SERVICE_URL": "http://localhost:8002"},
    },
    {
        "name": "orchestrator",
        "app_dir": os.path.join(BASE_DIR, "services", "orchestrator", "app"),
        "port": 8085,
        "module": "main:app",
        "env": {},
    },
]

_processes = []


def is_port_available(port):
    """Check if a port is free."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(("127.0.0.1", port))
            return True
    except OSError:
        return False


def check_port_in_use(port):
    """Check if a service is already running on the port."""
    try:
        req = urllib.request.Request(
            f"http://localhost:{port}/healthz",
            headers={"User-Agent": "SatyaLauncher/1.0"}
        )
        resp = urllib.request.urlopen(req, timeout=2)
        return resp.status == 200
    except Exception:
        return False


def verify_colab_health(colab_url):
    """Verify Colab ML services are reachable via the ngrok tunnel."""
    if "localhost" in colab_url or "127.0.0.1" in colab_url:
        print(f"  {YELLOW}⚠️  Colab tunnel URL is set to local. Remote feature extraction bypassed.{RESET}")
        return False

    print(f"\n{CYAN}  Verifying Colab ML services via ngrok tunnel...{RESET}")

    try:
        req = urllib.request.Request(
            f"{colab_url}/healthz",
            headers={
                "User-Agent": "SatyaLauncher/1.0",
                "ngrok-skip-browser-warning": "true",
            }
        )
        resp = urllib.request.urlopen(req, timeout=8)
        if resp.status == 200:
            print(f"{GREEN}  ✅ Colab tunnel is LIVE and responding at {colab_url}{RESET}")
            return True
    except Exception as e:
        print(f"{RED}  ❌ Colab tunnel NOT reachable ({e}){RESET}")
        print(f"{YELLOW}  Make sure Colab notebook is active and ngrok URL is valid.{RESET}")
        return False


def start_local_services(colab_url):
    """Start all local microservices."""
    print(f"\n{CYAN}  Starting local microservices...{RESET}\n")

    orchestrator_port = None

    for svc in LOCAL_SERVICES:
        port = svc["port"]
        name = svc["name"]

        # Check if port is occupied
        if not is_port_available(port):
            if "orchestrator" in name:
                for alt in [8085, 8086, 8088, 8090]:
                    if is_port_available(alt):
                        print(f"  {YELLOW}⚠️  Port {port} occupied, using {alt} for orchestrator{RESET}")
                        port = alt
                        break
                else:
                    print(f"  {RED}❌ No available port for orchestrator!{RESET}")
                    continue
            else:
                print(f"  {YELLOW}⚠️  {name:45s} — port {port} occupied, skipping{RESET}")
                continue

        # Build environment
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{svc['app_dir']};{os.path.dirname(svc['app_dir'])}"

        # Environment routes
        if "orchestrator" in name:
            # Route Heavy ML Feature Extraction & Enrollment to Colab
            env["FEATURE_EXTRACTION_URL"] = f"{colab_url}/feat"
            env["ENROLLMENT_URL"] = f"{colab_url}/enroll"
            # Route Deepfake Detection Model LOCALLY
            env["SPOOF_DETECTION_URL"] = "http://localhost:8002"
            # Local microservices
            env["RISK_FUSION_URL"] = "http://localhost:8000"
            env["POLICY_ENGINE_URL"] = "http://localhost:8004"
            env["ALERTING_URL"] = "http://localhost:8005"
            env["OLLAMA_URL"] = "http://localhost:11434"
            env["OLLAMA_MODEL"] = os.environ.get("OLLAMA_MODEL", "qwen3:1.7b")
            orchestrator_port = port

        env.update(svc.get("env", {}))

        cmd = [
            sys.executable, "-m", "uvicorn",
            svc["module"],
            "--host", "0.0.0.0",
            "--port", str(port),
            "--workers", "1",
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=svc["app_dir"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _processes.append((name, proc))
            print(f"  {GREEN}▶ {name:45s} → port {port} (PID {proc.pid}){RESET}")
        except Exception as e:
            print(f"  {RED}❌ {name:45s} FAILED: {e}{RESET}")

    print(f"\n{CYAN}  Waiting for local services to initialize...{RESET}")
    time.sleep(4)

    return orchestrator_port or 8085


def verify_all_health(colab_url, orchestrator_port=8085):
    """Print complete health matrix across Local & Colab services."""
    services = [
        ("Risk Fusion Engine", 8000, "local", "healthz"),
        ("Spoof Detection (Local Dhwani 2 Model)", 8002, "local", "healthz"),
        ("Policy Threshold Engine", 8004, "local", "healthz"),
        ("Alerting Service", 8005, "local", "healthz"),
        ("API Gateway", 8090, "local", "v1/health"),
        ("Orchestrator Engine", orchestrator_port, "local", "healthz"),
        ("Feature Extraction (PyTorch/Librosa)", None, "colab", f"{colab_url}/feat/healthz"),
        ("Speaker Enrollment (Resemblyzer)", None, "colab", f"{colab_url}/enroll/healthz"),
    ]

    print(f"\n{BOLD}{'=' * 75}{RESET}")
    print(f"{BOLD}          HYBRID MICROSERVICES HEALTH MATRIX{RESET}")
    print(f"{BOLD}{'=' * 75}{RESET}")

    for name, port, location, endpoint in services:
        if location == "local":
            url = f"http://localhost:{port}/{endpoint}"
        else:
            url = endpoint

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "SatyaLauncher/1.0",
                    "ngrok-skip-browser-warning": "true",
                }
            )
            resp = urllib.request.urlopen(req, timeout=4)
            if resp.status == 200:
                loc_tag = f"{GREEN}[LOCAL]{RESET}" if location == "local" else f"{CYAN}[COLAB]{RESET}"
                status = f"{GREEN}ONLINE (HTTP 200){RESET}"
            else:
                loc_tag = f"{YELLOW}[????]{RESET}"
                status = f"{YELLOW}HTTP {resp.status}{RESET}"
        except Exception:
            loc_tag = f"{GREEN}[LOCAL]{RESET}" if location == "local" else f"{YELLOW}[COLAB]{RESET}"
            status = f"{YELLOW}STANDBY / PENDING{RESET}"

        port_str = f":{port}" if port else ":ngrok"
        print(f"  {loc_tag} {name:<42s} [Port {port_str:<6s}] → {status}")

    print(f"{BOLD}{'=' * 75}{RESET}\n")


def start_dashboard():
    """Start serve_dashboard.py if not already active."""
    if check_port_in_use(9000):
        print(f"  {GREEN}✅ Web Dashboard already running on http://localhost:9000{RESET}")
        return None

    print(f"  {CYAN}▶ Starting Web Dashboard on http://localhost:9000...{RESET}")
    try:
        proc = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, "serve_dashboard.py")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _processes.append(("dashboard", proc))
        time.sleep(2)
        return proc
    except Exception as e:
        print(f"  {YELLOW}⚠️  Dashboard failed to start: {e}{RESET}")
        return None


def cleanup(signum=None, frame=None):
    """Clean shutdown of all local processes."""
    print(f"\n{YELLOW}  Shutting down local services...{RESET}")
    for name, proc in _processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
            print(f"  ✅ {name} stopped.")
        except Exception:
            try:
                proc.kill()
                print(f"  ⚠️  {name} force-killed.")
            except Exception:
                pass
    sys.exit(0)


def main():
    """Main entry point."""
    print(f"{CYAN}{BOLD}")
    print("  ╔═════════════════════════════════════════════════════════════════════╗")
    print("  ║   🛡️  SATYA PRIMEVECTOR — COLAB HYBRID SYSTEM LAUNCHER  🛡️         ║")
    print("  ║                                                                     ║")
    print("  ║   • Deepfake Detection Model runs LOCALLY on Port 8002              ║")
    print("  ║   • Heavy Feature Extraction & Enrollment offloaded to Colab GPU    ║")
    print("  ║   • Local PC RAM Usage: ~350 MB (Sub-50ms Local Deepfake Model)     ║")
    print("  ╚═════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    load_env()

    colab_url = get_colab_url()
    print(f"  {CYAN}Colab Ngrok Tunnel URL: {colab_url}{RESET}")

    verify_colab_health(colab_url)

    orch_port = start_local_services(colab_url)

    start_dashboard()

    verify_all_health(colab_url, orch_port)

    target_url = "http://localhost:9000"
    print(f"{GREEN}{BOLD}  ✨ Satya PrimeVector Platform is LIVE at: {target_url}{RESET}")
    print(f"{CYAN}  ▶ Opening dashboard in browser...{RESET}\n")

    try:
        webbrowser.open(target_url)
    except Exception:
        pass

    print(f"{DIM}  💡 Deepfake Detection Model (Dhwani 2) is running locally on http://localhost:8002{RESET}")
    print(f"{DIM}  💡 API Gateway & Metering active on http://localhost:8090{RESET}")
    print(f"\n{YELLOW}  Press Ctrl+C to stop all local services.{RESET}\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()

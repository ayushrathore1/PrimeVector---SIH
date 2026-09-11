#!/usr/bin/env python3
"""
==========================================================================
  SATYA PRIMEVECTOR — LOCAL LIGHTWEIGHT LAUNCHER (Colab Hybrid Mode)
==========================================================================
  Runs ONLY the 5 lightweight Python microservices locally (~300 MB RAM).
  The 3 heavy ML services (feature-extraction, enrollment, spoof-detection)
  are hosted on Google Colab and reached via the ngrok tunnel URL.

  PREREQUISITES:
    1. Run colab_ml_services.py on Google Colab first
    2. Copy the ngrok URL into your .env file as COLAB_TUNNEL_URL=...
    3. Then run: python run_local_lightweight.py

  NO DOCKER REQUIRED. Total RAM usage: ~300-400 MB.
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

# ANSI Colors
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


def get_colab_url():
    """Get the Colab tunnel URL from environment."""
    url = os.environ.get("COLAB_TUNNEL_URL", "").strip()
    if not url:
        print(f"\n{RED}{'=' * 70}{RESET}")
        print(f"{RED}  ERROR: COLAB_TUNNEL_URL not found in .env file!{RESET}")
        print(f"{RED}{'=' * 70}{RESET}")
        print(f"""
  To fix this:
    1. Open Google Colab: https://colab.research.google.com
    2. Paste and run the colab_ml_services.py script
    3. Copy the ngrok URL it prints
    4. Add to your .env file:
       COLAB_TUNNEL_URL=https://xxxx-xx-xx-xx-xx.ngrok-free.app
    5. Re-run this script

  Alternatively, run ALL services locally (uses more RAM):
    python start_project.py
""")
        sys.exit(1)
    return url.rstrip("/")


# ─────────────────────────────────────────────────────────────────────────
# Service definitions — only the LIGHTWEIGHT ones run locally
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
        "name": "orchestrator",
        "app_dir": os.path.join(BASE_DIR, "services", "orchestrator", "app"),
        "port": 8085,  # Avoid 8080 which is often occupied by other tools
        "module": "main:app",
        "env": {},  # Will be populated with Colab URLs dynamically
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
    print(f"\n{CYAN}  Verifying Colab ML services via tunnel...{RESET}")

    try:
        req = urllib.request.Request(
            f"{colab_url}/healthz",
            headers={
                "User-Agent": "SatyaLauncher/1.0",
                "ngrok-skip-browser-warning": "true",
            }
        )
        resp = urllib.request.urlopen(req, timeout=10)
        if resp.status == 200:
            print(f"{GREEN}  ✅ Colab tunnel is LIVE and responding at {colab_url}{RESET}")
            return True
    except Exception as e:
        print(f"{RED}  ❌ Colab tunnel NOT reachable: {e}{RESET}")
        print(f"{YELLOW}  Make sure:")
        print(f"    • The Colab notebook is still running")
        print(f"    • The ngrok tunnel URL in .env is correct")
        print(f"    • The Colab tab hasn't been closed/timed out{RESET}")
        return False


def start_local_services(colab_url):
    """Start all local lightweight services."""
    print(f"\n{CYAN}  Starting local lightweight services...{RESET}\n")

    orchestrator_port = None  # Track actual orchestrator port

    for svc in LOCAL_SERVICES:
        port = svc["port"]

        # Check if port is occupied by ANOTHER process
        if not is_port_available(port):
            if svc["name"] == "orchestrator":
                # Try alternative ports
                for alt in [8085, 8086, 8088, 8090]:
                    if is_port_available(alt):
                        print(f"  {YELLOW}⚠️  Port {port} occupied, using {alt} for orchestrator{RESET}")
                        port = alt
                        break
                else:
                    print(f"  {RED}❌ No available port for orchestrator!{RESET}")
                    continue
            else:
                print(f"  {YELLOW}⚠️  {svc['name']:30s} — port {port} occupied, skipping{RESET}")
                continue

        # Build environment
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{svc['app_dir']};{os.path.dirname(svc['app_dir'])}"

        # For the orchestrator: point ML service URLs to Colab tunnel
        if svc["name"] == "orchestrator":
            env["FEATURE_EXTRACTION_URL"] = f"{colab_url}/feat"
            env["SPOOF_DETECTION_URL"] = f"{colab_url}/spoof"
            env["ENROLLMENT_URL"] = f"{colab_url}/enroll"
            # Local services
            env["RISK_FUSION_URL"] = "http://localhost:8000"
            env["POLICY_ENGINE_URL"] = "http://localhost:8004"
            env["ALERTING_URL"] = "http://localhost:8005"
            # Ollama LLM (running locally, not in Docker)
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
            # Log orchestrator stderr to a file for debugging
            if svc["name"] == "orchestrator":
                _orch_log = open(os.path.join(BASE_DIR, "orchestrator_debug.log"), "w")
                proc = subprocess.Popen(
                    cmd,
                    cwd=svc["app_dir"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=_orch_log,
                )
            else:
                proc = subprocess.Popen(
                    cmd,
                    cwd=svc["app_dir"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            _processes.append((svc["name"], proc))
            print(f"  {GREEN}▶ {svc['name']:30s} → port {port} (PID {proc.pid}){RESET}")
        except Exception as e:
            print(f"  {RED}❌ {svc['name']:30s} FAILED: {e}{RESET}")

    # Wait for startup
    print(f"\n{CYAN}  Waiting for services to initialize...{RESET}")
    time.sleep(4)

    return orchestrator_port or 8085


def verify_all_health(colab_url, orchestrator_port=8085):
    """Print health status of all services."""
    services = [
        ("Risk Fusion Engine", 8000, "local"),
        ("Policy Threshold Engine", 8004, "local"),
        ("Alerting Service", 8005, "local"),
        ("Orchestrator", orchestrator_port, "local"),
        ("Feature Extraction", None, "colab"),
        ("Spoof Detection", None, "colab"),
        ("Enrollment Service", None, "colab"),
    ]

    colab_route_map = {
        "Feature Extraction": f"{colab_url}/feat/healthz",
        "Spoof Detection": f"{colab_url}/spoof/healthz",
        "Enrollment Service": f"{colab_url}/enroll/healthz",
    }

    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}          MICROSERVICES HEALTH STATUS MATRIX{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}")

    for name, port, location in services:
        if location == "local":
            url = f"http://localhost:{port}/healthz"
        else:
            url = colab_route_map.get(name, "")

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "SatyaLauncher/1.0",
                    "ngrok-skip-browser-warning": "true",
                }
            )
            resp = urllib.request.urlopen(req, timeout=5)
            if resp.status == 200:
                loc_tag = f"{GREEN}[LOCAL]{RESET}" if location == "local" else f"{CYAN}[COLAB]{RESET}"
                status = f"{GREEN}ONLINE{RESET}"
            else:
                loc_tag = f"{YELLOW}[????]{RESET}"
                status = f"{YELLOW}HTTP {resp.status}{RESET}"
        except Exception:
            loc_tag = f"{RED}[DOWN]{RESET}" if location == "local" else f"{YELLOW}[COLAB]{RESET}"
            status = f"{RED}OFFLINE{RESET}"

        port_str = f":{port}" if port else ":ngrok"
        print(f"  {loc_tag} {name:<26s} [Port {port_str:<6s}] → {status}")

    print(f"{BOLD}{'=' * 70}{RESET}\n")


def start_dashboard():
    """Start the serve_dashboard.py if not already running."""
    if check_port_in_use(9000):
        print(f"  {GREEN}✅ Dashboard already running on http://localhost:9000{RESET}")
        return None

    print(f"  {CYAN}▶ Starting dashboard on http://localhost:9000...{RESET}")
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
            proc.wait(timeout=5)
            print(f"  ✅ {name} stopped.")
        except Exception:
            proc.kill()
            print(f"  ⚠️  {name} force-killed.")
    sys.exit(0)


def main():
    """Main entry point."""
    print(f"{CYAN}{BOLD}")
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║   🛡️  SATYA PRIMEVECTOR — COLAB HYBRID LAUNCHER  🛡️        ║")
    print("  ║                                                              ║")
    print("  ║   Running lightweight services locally (~300 MB RAM)         ║")
    print("  ║   Heavy ML services are on Google Colab via ngrok tunnel     ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    # Register cleanup
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Load environment
    load_env()

    # Get Colab URL
    colab_url = get_colab_url()
    print(f"  {CYAN}Colab tunnel URL: {colab_url}{RESET}")

    # Verify Colab is reachable
    if not verify_colab_health(colab_url):
        print(f"\n{YELLOW}  Proceeding anyway — Colab services may come online later.{RESET}")

    # Start local services
    orch_port = start_local_services(colab_url)

    # Start dashboard
    start_dashboard()

    # Health matrix
    verify_all_health(colab_url, orch_port)

    print(f"{CYAN}  📌 Orchestrator is on port {orch_port} (use /api/{orch_port}/... in dashboard){RESET}")

    # Open browser
    target_url = "http://localhost:9000"
    print(f"{GREEN}{BOLD}  ✨ Satya PrimeVector Platform is LIVE at: {target_url}{RESET}")
    print(f"{CYAN}  ▶ Opening dashboard in browser...{RESET}\n")

    try:
        webbrowser.open(target_url)
    except Exception:
        pass

    # RAM usage estimate
    print(f"{DIM}  💡 Estimated local RAM usage: ~300-400 MB (vs 5+ GB with Docker){RESET}")
    print(f"{DIM}  💡 Heavy ML processing is handled by Google Colab (12 GB RAM){RESET}")
    print(f"\n{YELLOW}  Press Ctrl+C to stop all local services.{RESET}\n")

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()

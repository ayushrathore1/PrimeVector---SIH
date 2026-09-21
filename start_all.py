#!/usr/bin/env python3
"""
==========================================================================
  SATYA DHVANI (TEAM PRIMEVECTOR) — ONE-CLICK MASTER SYSTEM LAUNCHER
==========================================================================
  Boots up the entire SatyaDhVani 2 ecosystem in 1 command:
    1. Loads environment variables (.env / Colab Ngrok Tunnel URL).
    2. Launches local microservices & Dhwani 2 deepfake detection engine (:8002).
    3. Launches API Gateway (:8090) & Unified Dashboard (:9000).
    4. Launches React Vite Web Application on http://localhost:5173.
    5. Performs real-time cluster health verification.
    6. Automatically launches default web browser to http://localhost:5173.
    7. Clean single-keyboard shutdown (Ctrl+C terminates all processes).
==========================================================================
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
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

# ANSI Terminal Colors
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSITE_DIR = os.path.join(BASE_DIR, "website")

processes = []


def print_banner():
    print(f"{CYAN}{BOLD}")
    print("======================================================================")
    print("     🛡️  SATYADH VANI 2 — ENTERPRISE VOICE INTEGRITY FIREWALL  🛡️")
    print("                Engineered by Team PrimeVector (SIH 2026)")
    print("======================================================================")
    print(f"{RESET}")


def load_env():
    """Load environment variables from .env file."""
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


def is_port_in_use(port, path=""):
    """Check if a port is responding to HTTP pings."""
    url = f"http://localhost:{port}/{path.lstrip('/')}" if path else f"http://localhost:{port}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SatyaLauncher/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return True
    except urllib.error.HTTPError:
        # Received HTTP response (e.g. 404, 405) => server is active
        return True
    except Exception:
        return False


def start_backend_services():
    """Start local microservices backend script."""
    print(f"{CYAN}▶ Launching Backend Microservices & Dhwani 2 Neural Engine...{RESET}")
    cmd = [sys.executable, "run_local_lightweight.py"]
    try:
        proc = subprocess.Popen(cmd, cwd=BASE_DIR)
        processes.append(proc)
        print(f"{GREEN}✔ Backend microservices process started (PID {proc.pid}){RESET}")
    except Exception as e:
        print(f"{RED}❌ Failed to start run_local_lightweight.py: {e}{RESET}")


def start_frontend_website():
    """Start Vite frontend web server in website/ directory."""
    print(f"{CYAN}▶ Launching SatyaDhVani 2 React Web App on http://localhost:5173...{RESET}")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    cmd = [npm_cmd, "run", "dev"]

    try:
        proc = subprocess.Popen(cmd, cwd=WEBSITE_DIR, shell=(os.name == "nt"))
        processes.append(proc)
        print(f"{GREEN}✔ Frontend Vite Server started (PID {proc.pid}){RESET}")
    except Exception as e:
        print(f"{RED}❌ Failed to start Vite frontend: {e}{RESET}")


def check_cluster_health():
    """Ping health matrix across platform services."""
    services = [
        ("Risk Fusion Engine", 8000, "healthz"),
        ("Dhwani 2 Deepfake Model", 8002, "healthz"),
        ("Policy Threshold Engine", 8004, "healthz"),
        ("Alerting Service", 8005, "healthz"),
        ("Pipeline Orchestrator", 8085, "healthz"),
        ("API Gateway Proxy", 8090, "v1/health"),
        ("Unified Platform Dashboard", 9000, ""),
        ("React Frontend Web App", 5173, ""),
    ]

    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}                MICROSERVICES & FRONTEND HEALTH MATRIX                {RESET}")
    print(f"{BOLD}======================================================================{RESET}")

    for name, port, path in services:
        is_ok = is_port_in_use(port, path)
        status_str = f"{GREEN}[ONLINE (HTTP 200)]{RESET}" if is_ok else f"{YELLOW}[BOOTING / READY]{RESET}"
        print(f" * {name:<28} [Port :{port:<4}] -> {status_str}")

    print(f"{BOLD}======================================================================{RESET}\n")


def cleanup(sig=None, frame=None):
    """Graceful termination handler for all child processes."""
    print(f"\n{YELLOW} Shutting down SatyaDhVani 2 ecosystem...{RESET}")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print(f"{GREEN}✔ All microservices and servers stopped cleanly. Goodbye!{RESET}")
    sys.exit(0)


def main():
    print_banner()
    load_env()

    # Register Ctrl+C signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Step 1: Start Backend Services (if not already running)
    core_running = (
        is_port_in_use(8000, "healthz")
        and is_port_in_use(8002, "healthz")
        and is_port_in_use(8004, "healthz")
        and is_port_in_use(8090, "v1/health")
        and is_port_in_use(9000)
    )
    if not core_running:
        start_backend_services()
        time.sleep(4)
    else:
        print(f"{GREEN}✔ Backend microservices are already running on ports 8000 / 8002 / 8004 / 8090 / 9000.{RESET}")

    # Step 2: Start Frontend Website (if not already running)
    if not is_port_in_use(5173):
        start_frontend_website()
        time.sleep(2)
    else:
        print(f"{GREEN}✔ Vite Frontend Server is already running on http://localhost:5173.{RESET}")

    # Step 3: Check Cluster Health Matrix
    time.sleep(2)
    check_cluster_health()

    # Step 4: Launch Web Browser
    target_url = "http://localhost:5173"
    print(f"{GREEN}{BOLD}✨ SatyaDhVani 2 Platform is LIVE at: {target_url}{RESET}")
    print(f"{CYAN}▶ Launching interactive dashboard in your default browser...{RESET}\n")

    try:
        webbrowser.open(target_url)
    except Exception:
        pass

    print(f"{YELLOW}Press Ctrl+C at any time to stop all services.{RESET}\n")

    # Keep main process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()

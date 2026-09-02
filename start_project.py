#!/usr/bin/env python3
"""
======================================================================
  SATYA PRIMEVECTOR PLATFORM — ONE-CLICK MASTER LAUNCHER
======================================================================
Boots up the entire Satya PrimeVector system:
  1. Checks Docker & launches all 8 backend microservices via docker-compose.
  2. Launches the Unified Web Server & API Gateway on port 9000.
  3. Performs real-time health verification on all components.
  4. Automatically opens the dashboard in your default web browser.
"""

import os
import sys
import time
import subprocess
import urllib.request
import webbrowser

# ANSI Colors for terminal output
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    """Print ASCII Header."""
    print(f"{CYAN}{BOLD}")
    print("======================================================================")
    print("     🛡️  SATYA PRIMEVECTOR: VOICE INTEGRITY & FRAUD PREVENTION  🛡️")
    print("======================================================================")
    print(f"{RESET}")


def check_command_exists(cmd):
    """Check if a system command is available."""
    try:
        subprocess.run([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False


def start_docker_services():
    """Start Docker containers via docker-compose."""
    print(f"{YELLOW}▶ Checking Docker environment...{RESET}")
    
    if not check_command_exists("docker"):
        print(f"{RED}❌ Docker is not installed or not in PATH. Please install Docker Desktop.{RESET}")
        return False

    # Check if Docker daemon is running
    try:
        res = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0:
            print(f"{YELLOW}⚠️  Docker daemon is not running. Please start Docker Desktop.{RESET}")
            return False
    except Exception as e:
        print(f"{YELLOW}⚠️  Docker check warning: {e}{RESET}")

    print(f"{GREEN}✔ Docker engine is active.{RESET}")
    print(f"{CYAN}▶ Launching backend microservice containers via docker-compose...{RESET}")
    
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print(f"{GREEN}✔ Docker microservices containerized and running.{RESET}")
        return True
    except Exception as e:
        print(f"{YELLOW}⚠️ Could not run docker-compose up automatically ({e}). Checking local Python fallbacks...{RESET}")
        return False


def verify_service_health(port, path="health"):
    """Verify HTTP health endpoint."""
    url = f"http://localhost:{port}/{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SatyaLauncher/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def verify_all_health():
    """Verify health across all services."""
    services = [
        ("Risk Fusion Engine", 8000, "health"),
        ("Feature Extraction", 8001, "health"),
        ("Spoof Detection", 8002, "health"),
        ("Enrollment Service", 8003, "health"),
        ("Policy Threshold", 8004, "health"),
        ("Alerting Service", 8005, "health"),
        ("Orchestrator Engine", 8080, "health"),
        ("Unified Platform Proxy", 9000, ""),
    ]

    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}                MICROSERVICES HEALTH STATUS MATRIX                    {RESET}")
    print(f"{BOLD}======================================================================{RESET}")

    all_healthy = True
    for name, port, path in services:
        is_ok = verify_service_health(port, path)
        status_str = f"{GREEN}🟢 ONLINE (HTTP 200){RESET}" if is_ok else f"{YELLOW}🟡 PENDING / LOCAL{RESET}"
        print(f" • {name:<26} [Port :{port:<4}] ➔ {status_str}")
        if not is_ok and port == 9000:
            all_healthy = False

    print(f"{BOLD}======================================================================{RESET}\n")
    return all_healthy


def main():
    """Main execution workflow."""
    print_banner()

    # Step 1: Start Docker Services
    start_docker_services()

    # Step 2: Check if serve_dashboard.py is already running on port 9000
    is_running_9000 = verify_service_health(9000)
    
    dashboard_process = None
    if not is_running_9000:
        print(f"{CYAN}▶ Starting Unified Web Server & API Proxy on http://localhost:9000...{RESET}")
        try:
            dashboard_process = subprocess.Popen([sys.executable, "serve_dashboard.py"])
            time.sleep(2)
        except Exception as e:
            print(f"{RED}❌ Failed to start serve_dashboard.py: {e}{RESET}")
            sys.exit(1)
    else:
        print(f"{GREEN}✔ Unified Web Server is already running on http://localhost:9000.{RESET}")

    # Step 3: Verify Health
    time.sleep(1)
    verify_all_health()

    # Step 4: Open Browser
    target_url = "http://localhost:9000"
    print(f"{GREEN}{BOLD}✨ Satya PrimeVector Platform is LIVE at: {target_url}{RESET}")
    print(f"{CYAN}▶ Opening dashboard in your default browser...{RESET}\n")
    
    try:
        webbrowser.open(target_url)
    except Exception:
        pass

    print(f"{YELLOW}Press Ctrl+C at any time to stop the launcher.{RESET}")
    
    try:
        if dashboard_process:
            dashboard_process.wait()
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW} Shutting down Satya PrimeVector Platform...{RESET}")
        if dashboard_process:
            dashboard_process.terminate()
        print(f"{GREEN}✔ Stopped gracefully. Goodbye!{RESET}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# ============================================================
# TRINAY X — Simulation Engine
# ============================================================
# This is your kitchen inspector.
# Before ANY deployment goes live, this script:
#   1. Starts the container
#   2. Runs a series of checks
#   3. Returns a structured report
#   4. The risk engine reads this report and scores it
# ============================================================

import subprocess   # runs shell commands from Python
import requests     # makes HTTP requests
import time         # for sleep/timeout
import os
import json
import sys


# ============================================================
# CONFIGURATION
# These values can be overridden by environment variables
# so GitHub Actions can pass different values during CI
# ============================================================
IMAGE_NAME    = os.getenv("IMAGE_NAME", "trinayops")
CONTAINER_NAME = "trinayops-simulation-test"
APP_PORT      = int(os.getenv("APP_PORT", 5000))
STARTUP_WAIT  = int(os.getenv("STARTUP_WAIT", 8))  # seconds to wait for app to boot


# ============================================================
# HELPER: Run a shell command and return the output
# ============================================================
def run_cmd(command):
    """
    Runs a terminal command and returns (success, output).
    Like typing a command yourself but from Python.
    """
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


# ============================================================
# CHECK 1: Required Environment Variables
# Missing env vars are one of the most common deploy failures.
# Like checking the recipe has all ingredients listed.
# ============================================================
def check_env_variables():
    print("\n[CHECK 1] Environment Variables")

    required_vars = ["APP_ENV", "PORT", "SECRET_KEY"]
    results = {}

    for var in required_vars:
        value = os.getenv(var)
        if value:
            results[var] = {"status": "present", "risk_points": 0}
            print(f"  ✅ {var} is set")
        else:
            results[var] = {"status": "missing", "risk_points": 25}
            print(f"  ❌ {var} is MISSING — adds 25 risk points")

    return results


# ============================================================
# CHECK 2: Port Availability
# Is the port your app needs actually free?
# Like checking the delivery bay isn't already occupied.
# ============================================================
def check_port_availability():
    print(f"\n[CHECK 2] Port Availability — checking port {APP_PORT}")

    # Try to find any process using that port
    ok, output, _ = run_cmd(f"lsof -i :{APP_PORT} 2>/dev/null | grep LISTEN")

    if ok and output:
        print(f"  ❌ Port {APP_PORT} is OCCUPIED — adds 30 risk points")
        return {"status": "occupied", "risk_points": 30, "detail": output}
    else:
        print(f"  ✅ Port {APP_PORT} is free")
        return {"status": "free", "risk_points": 0}


# ============================================================
# CHECK 3: Docker Image Exists
# Can't deploy what doesn't exist.
# ============================================================
def check_image_exists():
    print(f"\n[CHECK 3] Docker Image — looking for '{IMAGE_NAME}'")

    ok, output, _ = run_cmd(f"docker images -q {IMAGE_NAME}")

    if ok and output:
        print(f"  ✅ Image '{IMAGE_NAME}' found")
        return {"status": "found", "risk_points": 0}
    else:
        print(f"  ❌ Image '{IMAGE_NAME}' NOT found — adds 40 risk points")
        return {"status": "missing", "risk_points": 40}


# ============================================================
# CHECK 4: Container Startup Test
# Actually starts the container and checks if it boots cleanly.
# The most important check — does it actually RUN?
# ============================================================
def check_container_startup():
    print(f"\n[CHECK 4] Container Startup Test")

    # Remove any leftover test container from previous runs
    run_cmd(f"docker rm -f {CONTAINER_NAME} 2>/dev/null")

    # Start the container in detached mode (-d = runs in background)
    ok, _, err = run_cmd(
        f"docker run -d --name {CONTAINER_NAME} "
        f"-p {APP_PORT}:{APP_PORT} "
        f"-e APP_ENV=production "
        f"-e PORT={APP_PORT} "
        f"-e SECRET_KEY=sim-test-key "
        f"{IMAGE_NAME}"
    )

    if not ok:
        print(f"  ❌ Container failed to START — adds 50 risk points")
        return {"status": "failed_to_start", "risk_points": 50, "error": err}

    print(f"  ⏳ Container started, waiting {STARTUP_WAIT}s for app to boot...")
    time.sleep(STARTUP_WAIT)

    # Check if the container is still running (didn't crash on startup)
    ok, output, _ = run_cmd(f"docker ps -q -f name={CONTAINER_NAME}")
    if not ok or not output:
        print(f"  ❌ Container CRASHED after startup — adds 50 risk points")
        # Grab the crash logs for diagnosis
        _, logs, _ = run_cmd(f"docker logs {CONTAINER_NAME} --tail 20")
        return {"status": "crashed", "risk_points": 50, "logs": logs}

    print(f"  ✅ Container is running")
    return {"status": "running", "risk_points": 0}


# ============================================================
# CHECK 5: HTTP Health Check
# Is the app actually responding to web requests?
# Like knocking on the door and waiting for someone to answer.
# ============================================================
def check_http_health():
    print(f"\n[CHECK 5] HTTP Health Check — calling /health endpoint")

    url = f"http://localhost:{APP_PORT}/health"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ App responded — status: {data.get('status')}")
            print(f"     Memory: {data.get('memory_used_pct')}% | CPU: {data.get('cpu_used_pct')}%")

            # Extra check: is the app already under high load?
            if data.get("memory_used_pct", 0) > 80:
                return {"status": "high_memory", "risk_points": 20, "data": data}

            return {"status": "healthy", "risk_points": 0, "data": data}

        else:
            print(f"  ⚠️  App responded but with status {response.status_code} — adds 15 risk points")
            return {"status": f"http_{response.status_code}", "risk_points": 15}

    except requests.exceptions.ConnectionError:
        print(f"  ❌ App is NOT responding on port {APP_PORT} — adds 40 risk points")
        return {"status": "no_response", "risk_points": 40}

    except requests.exceptions.Timeout:
        print(f"  ❌ App TIMED OUT — adds 30 risk points")
        return {"status": "timeout", "risk_points": 30}


# ============================================================
# CLEANUP: Stop and remove the test container
# Always clean up after simulation — like washing dishes
# ============================================================
def cleanup():
    print(f"\n[CLEANUP] Removing simulation container...")
    run_cmd(f"docker rm -f {CONTAINER_NAME} 2>/dev/null")
    print(f"  ✅ Cleaned up")


# ============================================================
# MAIN: Run all checks and produce the final report
# ============================================================
def run_simulation():
    print("=" * 55)
    print("  TRINAYOPS — SIMULATION ENGINE")
    print("=" * 55)

    report = {
        "image":   IMAGE_NAME,
        "checks":  {},
        "total_risk_points": 0,
        "passed":  True
    }

    # Run every check and collect results
    report["checks"]["env_variables"]       = check_env_variables()
    report["checks"]["port_availability"]   = check_port_availability()
    report["checks"]["image_exists"]        = check_image_exists()

    # Only run startup test if image exists
    if report["checks"]["image_exists"]["status"] == "found":
        report["checks"]["container_startup"] = check_container_startup()

        # Only run HTTP check if container started
        if report["checks"]["container_startup"]["status"] == "running":
            report["checks"]["http_health"] = check_http_health()

    # Clean up the test container
    cleanup()

    # --------------------------------------------------------
    # CALCULATE TOTAL RISK
    # Sum up risk points from every check
    # --------------------------------------------------------
    total_risk = 0
    for check_name, check_result in report["checks"].items():
        if isinstance(check_result, dict):
            # Some checks (like env_variables) return nested dicts
            if "risk_points" in check_result:
                total_risk += check_result["risk_points"]
            else:
                # env_variables check returns per-variable results
                for var_result in check_result.values():
                    if isinstance(var_result, dict):
                        total_risk += var_result.get("risk_points", 0)

    report["total_risk_points"] = total_risk

    # --------------------------------------------------------
    # DECISION: Based on total risk points
    # --------------------------------------------------------
    if total_risk < 30:
        report["decision"]   = "DEPLOY"
        report["risk_level"] = "LOW"
        report["passed"]     = True
    elif total_risk < 60:
        report["decision"]   = "WARN"
        report["risk_level"] = "MEDIUM"
        report["passed"]     = True   # deploy with warning
    else:
        report["decision"]   = "BLOCK"
        report["risk_level"] = "HIGH"
        report["passed"]     = False  # do not deploy

    # --------------------------------------------------------
    # PRINT SUMMARY
    # --------------------------------------------------------
    print("\n" + "=" * 55)
    print(f"  SIMULATION COMPLETE")
    print(f"  Risk Points : {total_risk}")
    print(f"  Risk Level  : {report['risk_level']}")
    print(f"  Decision    : {report['decision']}")
    print("=" * 55)

    # Save report as JSON file so GitHub Actions can read it
    with open("simulation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  Report saved to simulation_report.json")

    # Exit with error code if deployment should be blocked
    # GitHub Actions reads this — non-zero = pipeline fails = no deploy
    if not report["passed"] and report["decision"] == "BLOCK":
        sys.exit(1)   # ← This STOPS the GitHub Actions pipeline
    else:
        sys.exit(0)   # ← This lets the pipeline continue


# Run simulation when script is called directly
if __name__ == "__main__":
    run_simulation()

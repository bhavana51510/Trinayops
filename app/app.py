# ============================================================
# TrinayOps — The Flask App (Your "Restaurant")
# ============================================================
# Flask is a lightweight Python web framework.
# Think of it as the engine that powers your website.
# Every line here is explained so you understand WHY it exists.
# ============================================================

from flask import Flask, jsonify, request
import os
import time
import psutil  # reads CPU and memory info from the computer

# -----------------------------------------------------------
# Create the Flask app
# "app" is just a variable name — it holds your entire website
# -----------------------------------------------------------
app = Flask(__name__)

# -----------------------------------------------------------
# Read the app version from environment variable
# Environment variables = settings passed from OUTSIDE the app
# Like a restaurant's daily specials — they can change without
# rewriting the entire menu
# -----------------------------------------------------------
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV     = os.getenv("APP_ENV", "development")  # development or production
SECRET_KEY  = os.getenv("SECRET_KEY", "")           # must be set in production


# -----------------------------------------------------------
# ROUTE 1: Home page
# A "route" is a URL path. When someone visits "/", this runs.
# -----------------------------------------------------------
@app.route("/")
def home():
    return jsonify({
        "service":  "TrinayOps",
        "version":  APP_VERSION,
        "status":   "running",
        "env":      APP_ENV,
        "message":  "TrinayOps — The eye that sees failures before they happen"
    })


# -----------------------------------------------------------
# ROUTE 2: Health Check
# Every real production app has this.
# Monitoring tools ping /health every 30 seconds to confirm
# the app is alive. Like a heartbeat monitor in a hospital.
# -----------------------------------------------------------
@app.route("/health")
def health():
    # Read current memory usage
    memory = psutil.virtual_memory()
    cpu    = psutil.cpu_percent(interval=0.1)

    # Decide health status based on resource usage
    if memory.percent > 90 or cpu > 95:
        status = "degraded"   # app is alive but struggling
        code   = 503
    else:
        status = "healthy"
        code   = 200

    return jsonify({
        "status":         status,
        "memory_used_pct": round(memory.percent, 2),
        "cpu_used_pct":   round(cpu, 2),
        "uptime_check":   "passed"
    }), code


# -----------------------------------------------------------
# ROUTE 3: Deployment Info
# Returns details about this specific deployment.
# The simulation engine will call this to verify the app
# started correctly and can respond to requests.
# -----------------------------------------------------------
@app.route("/info")
def info():
    return jsonify({
        "version":    APP_VERSION,
        "environment": APP_ENV,
        "secret_set": bool(SECRET_KEY),   # True if SECRET_KEY exists
        "port":       int(os.getenv("PORT", 5000)),
        "timestamp":  time.strftime("%Y-%m-%d %H:%M:%S")
    })


# -----------------------------------------------------------
# ROUTE 4: Simulate a failure (for testing your pipeline)
# This intentionally causes a memory spike so you can test
# whether your anomaly detection catches it.
# Real apps obviously don't have this — this is your test tool.
# -----------------------------------------------------------
@app.route("/simulate-failure")
def simulate_failure():
    failure_type = request.args.get("type", "memory")

    if failure_type == "memory":
        # Eat memory temporarily — triggers anomaly detection
        big_list = [0] * (10 ** 7)  # 10 million zeros in RAM
        time.sleep(2)
        del big_list
        return jsonify({"simulated": "memory_spike", "status": "recovered"})

    elif failure_type == "slow":
        # Simulate a slow response — another anomaly type
        time.sleep(5)
        return jsonify({"simulated": "slow_response", "status": "recovered"})

    return jsonify({"error": "unknown failure type"}), 400


# -----------------------------------------------------------
# Start the app when you run "python app.py"
# host="0.0.0.0" means accept connections from ANY machine
# (needed inside Docker — otherwise Docker can't reach the app)
# debug=False in production — never expose debug mode live
# -----------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=(APP_ENV == "development"))

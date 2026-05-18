# ============================================================
# Dockerfile — Instructions for building your lunchbox
# ============================================================
# Docker reads this file top to bottom and builds a sealed
# container with EVERYTHING your app needs to run anywhere.
# Think of each line as one step in packing the lunchbox.
# ============================================================


# STEP 1: Start from an existing Python base
# "python:3.11-slim" = a minimal Linux computer with Python
# already installed. "slim" = stripped down, smaller size.
# You don't build from scratch — you start from a clean kitchen.
FROM python:3.11-slim


# STEP 2: Set the working directory inside the container
# Like saying "from now on, we work in the /app folder"
# All future commands happen inside this folder.
WORKDIR /app


# STEP 3: Copy the ingredients list first
# WHY first? Docker is smart — if requirements.txt didn't change,
# it skips re-installing everything. Saves minutes on every build.
# Only copy what's needed for this step.
COPY requirements.txt .


# STEP 4: Install all Python packages
# --no-cache-dir = don't save installer cache (keeps image small)
RUN pip install --no-cache-dir -r requirements.txt


# STEP 5: Copy the rest of your app code into the container
COPY . .


# STEP 6: Tell Docker which port this app listens on
# This is documentation — it doesn't actually open the port.
# The actual port mapping happens when you run the container.
EXPOSE 5000


# STEP 7: Set default environment variables
# These are fallback values if nothing is passed at runtime.
ENV APP_ENV=production
ENV PORT=5000


# STEP 8: The command that runs when the container starts
# gunicorn = production-grade web server (not flask's dev server)
# "app:app" = file named app.py, variable named app
# -w 2 = 2 worker processes (handles 2 requests simultaneously)
# -b 0.0.0.0:5000 = listen on all network interfaces, port 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]

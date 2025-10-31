# Local Development vs Docker Containers - Complete Explanation

## The Confusion: Two Different Ways to Run InvenioRDM

---

## Mode 1: Local Development (invenio-cli run)

### What Happens:

```bash
# Step 1: Start backend services in Docker
docker compose up -d

# This starts ONLY:
# - PostgreSQL (Docker container on port 5432)
# - Redis (Docker container on port 6379)
# - OpenSearch (Docker container on port 9200)
# - MinIO (Docker container on port 9000)
# - Cantaloupe (Docker container on port 8182)

# Step 2: Run app on YOUR MACHINE (not Docker!)
invenio-cli run

# This starts:
# - Flask development server (Python process on YOUR machine)
# - Running on port 5000
# - Uses your virtual environment (.venv)
# - Connects to Docker containers via localhost
```

### How to Verify:

```bash
# Check processes on your machine
ps aux | grep invenio
# You'll see Python processes running OUTSIDE Docker!

# Check Docker containers
docker ps
# You'll see: db, redis, search, s3, cantaloupe
# You'll NOT see: web-ui, web-api, worker
```

### Visual:

```
┌─────────────────────────────────────┐
│ YOUR MACHINE (macOS)                │
│                                     │
│  Python Process (PID 12345)         │
│  ├── Flask app on port 5000         │
│  ├── Virtual env: .venv             │
│  └── Connects to ↓                  │
└──────────────┬──────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ DOCKER CONTAINERS                    │
│                                      │
│  postgres:14  (localhost:5432)       │
│  redis:7      (localhost:6379)       │
│  opensearch   (localhost:9200)       │
│  minio        (localhost:9000)       │
└──────────────────────────────────────┘
```

**Where the code lives:**
- Your code: `/Users/alaaalbarazi/Projects/Turath/turath-rdm/site/`
- Runs using: Your machine's Python + virtual env
- No Docker image needed!

---

## Mode 2: Full Docker Stack (docker-compose.full.yml)

### What Happens:

```bash
# Start EVERYTHING in Docker
docker compose -f docker-compose.full.yml up -d

# OR
invenio-cli containers start

# This starts:
# - PostgreSQL (Docker)
# - Redis (Docker)
# - OpenSearch (Docker)
# - MinIO (Docker)
# - Cantaloupe (Docker)
# - web-ui (Docker) ← NEW!
# - web-api (Docker) ← NEW!
# - worker (Docker) ← NEW!
# - scheduler (Docker) ← NEW!
# - frontend (Docker) ← NEW!
```

### How to Verify:

```bash
docker ps
# You'll see ALL containers including:
# - web-ui-1
# - web-api-1
# - worker-1
# - frontend-1
```

### Visual:

```
┌─────────────────────────────────────────┐
│ YOUR MACHINE (macOS)                    │
│  (Nothing running except Docker Desktop)│
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ DOCKER CONTAINERS                        │
│                                          │
│  frontend (Nginx) port 443               │
│      ↓                                   │
│  web-ui (Flask) port 5000                │
│  web-api (Flask) port 5000               │
│  worker (Celery)                         │
│  scheduler (Celery Beat)                 │
│      ↓                                   │
│  postgres:14                             │
│  redis:7                                 │
│  opensearch                              │
│  minio                                   │
└──────────────────────────────────────────┘
```

**Where the code lives:**
- Your code: Copied INTO Docker image
- Runs using: Docker container's Python
- Image: `turath-inveniordm:latest`

---

## Why Two Modes?

| Aspect | Local Dev | Docker Full Stack |
|--------|-----------|-------------------|
| **Speed** | ⚡ Very fast (instant restart) | 🐢 Slower (restart container) |
| **Debugging** | ✅ Easy (attach debugger) | ⚠️ Harder (need Docker debug) |
| **Code Changes** | ✅ Instant (no rebuild) | ❌ Need to rebuild image |
| **Realism** | ⚠️ Different from production | ✅ Similar to production |
| **Use Case** | Daily development | Testing production setup |

---

## How web-ui, web-api Access Your Code

### Mode 1 (Local):
```bash
# App runs on your machine
invenio-cli run

# Code location:
/Users/alaaalbarazi/Projects/Turath/turath-rdm/site/
# Python reads from here directly!
```

### Mode 2 (Docker):
```bash
# App runs in container
docker compose -f docker-compose.full.yml up

# Code location (INSIDE container):
/opt/invenio/var/instance/
# Copied during image build!
```

---

## How Same Image Runs Different Services

The SECRET: **Different commands for same image!**

### In docker-compose.full.yml:

```yaml
# Service 1: Web UI
web-ui:
  image: turath-inveniordm:latest  # ← SAME IMAGE
  command: ["uwsgi /opt/invenio/var/instance/uwsgi_ui.ini"]
  # Runs: Web interface for users

# Service 2: Web API
web-api:
  image: turath-inveniordm:latest  # ← SAME IMAGE
  command: ["uwsgi /opt/invenio/var/instance/uwsgi_rest.ini"]
  # Runs: REST API endpoints

# Service 3: Worker
worker:
  image: turath-inveniordm:latest  # ← SAME IMAGE
  command: ["celery -A invenio_app.celery worker"]
  # Runs: Background job processor

# Service 4: Scheduler
scheduler:
  image: turath-inveniordm:latest  # ← SAME IMAGE
  command: ["celery -A invenio_app.celery beat"]
  # Runs: Job scheduler
```

**Analogy:**
- Same Python installation
- Different programs: `python app.py` vs `python worker.py` vs `python scheduler.py`

---

## The Image Contains EVERYTHING:

```
turath-inveniordm:latest image contains:
├── Python 3.9
├── InvenioRDM packages
├── Your custom code (site/)
├── Configuration files
│   ├── uwsgi_ui.ini (for web-ui)
│   ├── uwsgi_rest.ini (for web-api)
│   └── celery config (for worker)
└── All dependencies
```

**Different containers run different commands with this image:**
- `web-ui`: Starts Flask UI server
- `web-api`: Starts Flask API server  
- `worker`: Starts Celery worker
- `scheduler`: Starts Celery beat

---

## Accessing on Port 5000

### Local Mode:
```
Browser → https://127.0.0.1:5000
    ↓
Python process on YOUR machine
```

### Docker Mode:
```
Browser → https://127.0.0.1 (port 443)
    ↓
frontend container (Nginx)
    ↓
web-ui container (Flask on port 5000 INSIDE Docker)
```

**Both work, but connection path is different!**

---

## Summary Table

| Question | Answer |
|----------|--------|
| **Where does app run in local mode?** | On your machine (not Docker) |
| **How can I access it without Docker?** | Flask dev server runs on your machine's port 5000 |
| **Why same image for web-ui/api/worker?** | Different commands, same codebase |
| **What's in the image?** | All code + configs, different entry points |
| **Which mode for daily dev?** | Local (faster) |
| **Which mode tests production?** | Docker full stack |

---

## Quick Test

### Prove app runs on your machine:

```bash
# Stop all Docker containers
docker compose down

# Start ONLY backend
docker compose up -d

# Check what's running in Docker
docker ps
# You'll see: db, redis, search, s3, cantaloupe
# You'll NOT see: web-ui, web-api

# Now run app on your machine
invenio-cli run

# Check processes on your machine
ps aux | grep uwsgi
# You'll see Python processes with YOUR username!

# Access the site
open https://127.0.0.1:5000
# It works! Because Python is running on YOUR machine!
```

This proves the app runs locally, not in Docker! ✅

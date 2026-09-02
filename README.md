# QRNation – Production-Ready QR & Barcode Generator

QRNation is a Flask-based web app to generate standard and artistic QR codes. It supports multiple data types, inline logo overlays, and an SVG-based artistic renderer with dot/diamond modules and custom finder patterns. This README describes the production-ready structure, workflows, deployment guidance, and operations.


## Features
- Generate QR codes for URL, Text, WiFi, vCard, Social profiles, Files (image, pdf, audio, video), and more
- Artistic SVG renderer:
  - Module shapes: square, circle, diamond, rounded
  - Finder styles: classic, rounded, bullseye
  - Image-based color sampling and optional halftone
- Center logo overlay in standard PNG mode
- Client-side downloads: PNG, PDF (using jsPDF)
- Responsive UI and an enhanced global footer


## Recommended Production Structure

You can progressively migrate to this standardized structure while keeping your current static and template assets:

```
qr-code-generator/
├─ wsgi.py                         # WSGI entry (gunicorn)
├─ requirements.txt                # Pinned dependencies
├─ .env                            # Production environment (not committed)
├─ instance/
│  └─ config.py                    # Instance-specific secrets/overrides (optional)
├─ qrnation/
│  ├─ __init__.py                  # App factory create_app(config)
│  ├─ config.py                    # Base/Dev/Prod config
│  ├─ routes/
│  │  ├─ __init__.py
│  │  ├─ public.py                 # index, generator page
│  │  ├─ generator.py              # /api/generate, /api/render_artistic_svg
│  │  └─ uploads.py                # /uploads/<filename>
│  ├─ services/
│  │  ├─ __init__.py
│  │  └─ qr_service.py             # matrix generation, artistic svg, logo overlay
│  ├─ templates/                   # (option A) move templates here
│  └─ static/                      # (option A) move static here
├─ templates/                      # (option B) keep current templates
├─ static/                         # (option B) keep current static
│  ├─ css/
│  ├─ js/
│  ├─ images/
│  └─ uploads/                     # writable at runtime
├─ scripts/
│  ├─ gunicorn_start.sh            # Launch gunicorn with config
│  └─ collectstatic.sh             # Optional; for asset pipeline/CDN
├─ docker/
│  ├─ Dockerfile
│  └─ gunicorn.conf.py
├─ .gitignore
├─ LICENSE (optional)
└─ README.md
```

Notes:
- Option A: co-locate templates/static under qrnation/ for a fully self-contained package.
- Option B: keep using current templates/ and static/ at project root; configure Flask with template_folder and static_folder accordingly.
- Ensure static/uploads is writable by the runtime user.


## Configuration

Environment variables (set via .env in production):
- SECRET_KEY: strong random string
- FLASK_ENV=production
- MAX_CONTENT_LENGTH=16777216  # 16MB default
- UPLOAD_FOLDER=/app/static/uploads  # path must exist and be writable

Flask Config classes:
- BaseConfig: loads from environment
- DevelopmentConfig: DEBUG=True
- ProductionConfig: DEBUG=False


## Dependencies (Pinned)

```
Flask==3.0.2
qrcode[pil]==7.4.2
Pillow==10.2.0
gunicorn==21.2.0
# Dev optional
python-dotenv==1.0.1
black==24.2.0
isort==5.13.2
flake8==7.0.0
```

Update your requirements.txt accordingly.


## Local Development Workflow

1) Setup
- python3 -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt

2) Run in dev
- export FLASK_APP=wsgi.py
- export FLASK_ENV=development
- flask run --port 8080

App available at http://localhost:8080


## Production (Gunicorn + NGINX)

1) Gunicorn configuration (docker/gunicorn.conf.py example):
```
bind = '0.0.0.0:8080'
workers = 2
threads = 2
timeout = 60
accesslog = '-'
errorlog = '-'
loglevel = 'info'
```

2) Startup script (scripts/gunicorn_start.sh):
```
#!/usr/bin/env bash
set -e
exec gunicorn -c docker/gunicorn.conf.py wsgi:app
```
Make executable: chmod +x scripts/gunicorn_start.sh

3) Reverse proxy (NGINX):
- Terminate TLS
- Proxy / to http://127.0.0.1:8080
- Long cache for /static/
- Disable directory listing for /static/uploads/
- Add security headers (HSTS, X-Content-Type-Options, etc.)


## Production (Docker)

docker/Dockerfile example:
```
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

EXPOSE 8080
CMD ["bash", "scripts/gunicorn_start.sh"]
```

Build and run:
- docker build -t qrnation:latest .
- docker run --rm -p 8080:8080 --env-file .env -v $(pwd)/static/uploads:/app/static/uploads qrnation:latest


## WSGI Entry

wsgi.py:
```
# Minimal WSGI entry using the current app (temporary) or the app factory once you migrate.
try:
    # Prefer app factory if present
    from qrnation import create_app  # type: ignore
    app = create_app('production')
except Exception:
    # Fallback to current monolithic app for compatibility
    from app import app  # noqa: F401
    # 'app' is the Flask instance defined in app.py
```

This allows immediate deployment with gunicorn wsgi:app while you progressively adopt the app factory structure.


## Migration Plan (Incremental)

Phase 1 – Add WSGI and Docker/Gunicorn scaffolding
- Add wsgi.py, docker/Dockerfile, docker/gunicorn.conf.py, scripts/gunicorn_start.sh
- Keep existing app.py, templates/, and static/

Phase 2 – App factory & blueprints
- Create qrnation/__init__.py with create_app
- Add qrnation/config.py
- Split routes into qrnation/routes/{public,generator,uploads}.py
- Move QR generation and SVG rendering logic to qrnation/services/qr_service.py
- Point templates/static via app factory

Phase 3 – Hardening and optimization
- Validate file uploads (content-type, extensions)
- Unique filename generation and optional cleanup policy
- Add error handlers (404/500) and logging formatters
- Add caching headers for assets and fingerprinting (query-string or hashed names)


## Security Checklist
- Set SECRET_KEY via environment
- Enforce HTTPS with HSTS (via NGINX)
- Validate and limit uploads
- Disable directory listing in uploads
- Avoid leaking stack traces in production (DEBUG=False)


## CI/CD (Optional)
- Lint & format (black, isort, flake8)
- Build Docker image on push
- Healthcheck: curl / (200 OK)
- Push to registry and deploy (e.g., to a VM or container platform)


## License
Choose a license (MIT/Apache-2.0/etc.) if the project is public.


## Acknowledgements
- Flask, Pillow, qrcode
- jsPDF for client-side PDF download

---
This README documents a production-ready layout and end-to-end workflow. In the repository, you can now add the files listed (wsgi.py, docker, scripts, qrnation package) and progressively refactor your current app.py into the app factory + blueprints structure without breaking existing functionality.
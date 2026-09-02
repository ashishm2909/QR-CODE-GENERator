# QRNation — QR Code Generator

QRNation is a Flask-based web application for generating standard and artistic QR codes. It supports multiple data types, inline logo overlays, an SVG-based artistic renderer with dot/diamond modules and custom finder patterns, QR scanning, and paid plans via Razorpay.




https://github.com/user-attachments/assets/c0d14f33-add4-441e-b4e1-53c5616d6d02







## Features

- Generate QR codes for URL, Text, WiFi, vCard, Social profiles, and more
- Artistic SVG renderer with configurable module shapes (square, circle, diamond, rounded), finder styles (classic, rounded, bullseye), image-based color sampling, and optional halftone
- Center logo overlay in standard PNG mode
- Client-side downloads: PNG, PDF (via jsPDF)
- QR code scanner (browser-based, using pyzbar)
- User accounts with registration, login, and password reset
- Paid plans via Razorpay payment gateway
- Admin dashboard for user/plan management
- Responsive UI with seasonal themes

## Project Structure

```
qr-code-generator/
├─ backend/
│  ├─ app.py                    # Development entry point
│  ├─ wsgi.py                   # WSGI entry (gunicorn)
│  ├─ config.py                 # Flask config (Base/Dev/Prod)
│  ├─ requirements.txt          # Python dependencies
│  ├─ .env.example             # Environment variable template
│  ├─ .env                     # Local environment (gitignored)
│  ├─ entrypoint.sh            # Container startup (migrations + gunicorn)
│  ├─ src/
│  │  ├─ __init__.py           # App factory create_app()
│  │  ├─ models.py            # SQLAlchemy models (User, Payment, QRCode)
│  │  ├─ services/
│  │  │  └─ qr_service.py     # QR generation, artistic SVG, scanning
│  │  └─ routes/
│  │     ├─ auth_routes.py    # Login, signup, logout
│  │     ├─ admin_routes.py   # Admin dashboard
│  │     ├─ main_routes.py    # Public pages
│  │     ├─ api_routes.py     # API endpoints
│  │     └─ payment_routes.py # Razorpay checkout
│  └─ migrations/             # Alembic database migrations
├─ frontend/
│  ├─ templates/              # Jinja2 templates (18 pages)
│  ├─ static/
│  │  ├─ css/                # Stylesheets
│  │  ├─ js/                 # Client-side JavaScript
│  │  ├─ images/             # Static images
│  │  └─ uploads/            # User-uploaded files (runtime)
│  └─ static/style.css       # Main stylesheet
├─ Dockerfile
├─ docker-compose.yml
├─ Makefile
├─ requirements.txt           # Pinned dependencies (root)
├─ README.md
└─ .gitignore
```

## Requirements

- Python 3.11+
- pip

## Local Development

1. **Clone and setup:**
```bash
git clone <repo-url>
cd qr-code-generator
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

2. **Configure environment:**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env — set SECRET_KEY, APP_URL, and Razorpay credentials
```

3. **Run the development server:**
```bash
cd backend
flask db upgrade
flask run --port 8000
```

App available at http://localhost:8000

## Production (Gunicorn)

```bash
cd backend
flask db upgrade
gunicorn --bind 0.0.0.0:8080 --workers 4 --threads 2 --timeout 60 wsgi:app
```

For production, always set:
- `FLASK_ENV=production`
- `SECRET_KEY` to a strong random value
- `APP_URL` to your domain

## Production (Docker)

```bash
docker build -t qrnation:latest .
docker run --rm -p 8080:8080 --env-file backend/.env qrnation:latest
```

Or with docker-compose:
```bash
docker-compose up -d --build
```

The compose file maps a local volume for `static/uploads` and applies `backend/.env` as environment variables. A health check hits `/health`.

## Configuration

Environment variables (`.env`):

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask secret key (required in production) | — |
| `FLASK_ENV` | `development` or `production` | `development` |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///app.db` |
| `PORT` | Server port | `8080` |
| `APP_URL` | Base URL for redirects | `http://localhost:8080` |
| `RAZORPAY_KEY_ID` | Razorpay API key | — |
| `RAZORPAY_KEY_SECRET` | Razorpay API secret | — |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/generate` | Generate standard QR code (PNG) |
| POST | `/render_artistic_svg` | Generate artistic SVG QR code |
| POST | `/api/scan-qr` | Scan/upload QR image and decode |
| POST | `/api/plan` | Process plan purchase (Razorpay) |
| DELETE | `/api/delete_qr/<id>` | Delete a saved QR code |
| GET | `/api/qr-svg/<id>` | Retrieve a saved QR as SVG |
| GET | `/health` | Health check |

## Security

- CSRF protection via Flask-WTF on all forms
- Content Security Policy and security headers via Flask-Talisman (production only)
- Static file serving via WhiteNoise (production)
- Session cookies secured in production (`Secure`, `HttpOnly`, `SameSite=Lax`)
- Upload size limited to 16 MB
- Never commit `.env` — it contains secrets

## License

Choose a license (MIT/Apache-2.0/etc.) for public distribution.

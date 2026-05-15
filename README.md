# StudentHome Marrakech

A web platform connecting UCA students with housing near their faculties in Marrakech. Built with Flask, deployed on Render.

**Live:** https://studenthome-marrakech.onrender.com

---

## Features

### For Students
- Register with Massar code (validated format) and secure password
- Browse listings without an account — login required only to interact
- Search by faculty, neighbourhood, price, and availability
- Request reservations and track status in real time
- Simulated secure payment via QR Code
- Leave reviews after a confirmed or completed stay
- Messaging with landlords
- Favourites list
- Colocation matching — find compatible roommates
- Document vault (coffre-fort) for storing personal files
- Budget calculator for shared housing

### For Landlords (Propriétaires)
- Publish, edit, and delete listings
- Upload up to 10 photos per listing (stored on Cloudinary)
- Manage reservation requests (accept / reject)
- Generate rental contracts
- Inventory management per listing
- Messaging with tenants

### For Admins
- Full dashboard — users, listings, reservations overview
- Moderate content and manage accounts

### Platform
- Multilingual interface (French, English, Arabic)
- Interactive map per faculty (Leaflet.js)
- Responsive design

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3 / Flask |
| Database | SQLite (local) · PostgreSQL (production) |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login + Werkzeug password hashing |
| Media storage | Cloudinary |
| Server | Waitress (dev) · Gunicorn (prod) |
| Deployment | Render |

---

## Project Structure

```
StudentHome/
├── app.py                  # All routes, models, and business logic
├── config.py               # App configuration (DB, Cloudinary, secret key)
├── requirements.txt        # Python dependencies
├── Procfile                # Render/Heroku start command
├── render.yaml             # Render deployment config
├── .env.example            # Environment variable template
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/
└── templates/
    ├── base.html
    ├── index.html
    ├── logements.html
    ├── detail_logement.html
    ├── dashboard_etudiant.html
    ├── dashboard_proprietaire.html
    ├── dashboard_admin.html
    └── ...
```

---

## Local Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd StudentHome

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in environment variables
cp .env.example .env

# 4. Run the app
python app.py
```

Open: http://127.0.0.1:5000

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///instance/studenthome.db   # or PostgreSQL URL
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

---

## Test Accounts

| Role | Login | Password |
|---|---|---|
| Student | `G123456789` | `Etudiant@123` |
| Landlord | `youssef@mail.com` | `test123` |
| Admin | `redakouchtam@icloud.com` | `Admin@12345` |

---

## Deployment (Render)

The repo includes a `render.yaml` for one-click deployment.

Manual setup:
1. Push this repo to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Set the start command: `waitress-serve --host=0.0.0.0 --port=$PORT app:app`
4. Add the environment variables from `.env.example`

---

## UCA Faculties Supported

FSSM · FSJES · FLSH · FMPM · FST · ENCG · ENSA · ENS

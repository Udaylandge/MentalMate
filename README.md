# MentalMate 

**A Comprehensive Mental Health & Wellness Tracking Platform**

> **Academic Context**: This repository serves as the final submission for the Master of Computer Applications (MCA) program. It demonstrates professional software engineering practices, clean monolithic architecture, and a strong separation of concerns.

MentalMate is a full-stack Django web application designed to help users track their daily moods, maintain a personal journal, and receive tailored wellness recommendations. By aggregating daily logs, MentalMate provides actionable analytics, visualizations, and automated weekly/monthly reports to help users identify patterns in their mental wellbeing.

---

## ? Features

- **Auth & Onboarding**: Secure user registration, password strength validation, and email verification.
- **Mood Tracking**: Log daily mood scores (1-10), energy levels, stress factors, sleep hours, and qualitative notes.
- **Journaling**: A private space for self-reflection with full CRUD capabilities.
- **Analytics Dashboard**: Visual charts, streak tracking, and weekly/monthly mood averages.
- **Wellness Library**: A curated repository of mindfulness, breathing, and exercise resources dynamically recommended based on the user's current mood and stress levels.
- **Automated Reports**: Generate comprehensive weekly and monthly insights, with CSV export functionality.
- **RESTful API**: Exposes core functionalities via Django Rest Framework (`/api/v1/`) for future mobile client integrations.

---

## dY" Tech Stack

- **Backend Framework**: Python 3.11, Django 5.x
- **API Layer**: Django REST Framework (DRF)
- **Database**: SQLite (Configured for future MongoDB migration)
- **Architecture**: Service-Oriented Monolith (Domain logic extracted into `services.py`, `analytics.py`, `recommendation.py`)
- **Frontend**: Django Templates, Vanilla HTML/CSS

---

## dY" Project Structure

The application transitioned from a 12-app micro-architecture to a unified `core` monolith to reduce bloat and improve maintainability:

```text
MentalMate/
├── config/                 # Django settings, WSGI/ASGI, global routing
├── core/                   # Unified application logic
│   ├── models.py           # Database schemas
│   ├── views.py            # Web and API request handlers
│   ├── services.py         # Business logic (Auth, Mood, Journal)
│   ├── analytics.py        # Chart calculations & data aggregation
│   ├── recommendation.py   # Recommendation engine logic
│   ├── reports.py          # CSV export and report generation
│   ├── serializers.py      # DRF API serializers
│   ├── forms.py            # Django forms
│   ├── urls.py             # Internal app routing
│   └── templates/          # HTML views
├── docs/                   # Architectural & System Documentation
├── db.sqlite3              # Local Database
├── manage.py               # Django execution script
└── requirements.txt        # Python dependencies
```

---

## dY" Installation & Setup

Follow these steps to run MentalMate locally:

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/MentalMate.git
cd MentalMate
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Copy the example environment file and configure your keys:
```bash
cp .env.example .env
```
Ensure `DJANGO_SECRET_KEY` is set and `DJANGO_DEBUG=True` for local development.

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Start the Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your web browser.

---

## dY"o API Documentation
MentalMate includes a RESTful API for mobile integration.
- **Base Route**: `/api/v1/`
- **Endpoints**: `/mood/`, `/journal/`, `/resources/`

*Detailed API documentation can be found in `docs/API_DOCUMENTATION.md`.*

---

## dY"C License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

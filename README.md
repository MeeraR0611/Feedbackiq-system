# 🚀 FeedbackIQ — How to Run

## Prerequisites
- Python 3.8+ installed
- pip installed
- Terminal / Command Prompt

---

## Step 1 — Download / Copy the project

Put the `feedback_app/` folder anywhere on your computer, e.g.:
```
C:\Users\YourName\feedback_app\       (Windows)
/home/yourname/feedback_app/          (Mac/Linux)
```

---

## Step 2 — Open Terminal in that folder

```bash
cd feedback_app
```

---

## Step 3 — Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

---

## Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask
- Flask-SQLAlchemy
- vaderSentiment
- Werkzeug

---

## Step 5 — Run the app

```bash
python app.py
```

You should see:
```
✅ Admin seeded: admin@feedback.com / admin123
 * Running on http://127.0.0.1:5000
```

---

## Step 6 — Open in browser

```
http://localhost:5000          ← Main feedback page
http://localhost:5000/dashboard ← Charts & analytics
http://localhost:5000/admin    ← Admin panel (login first)
```

---

## 🔑 Default Credentials

| Role  | Email                  | Password   |
|-------|------------------------|------------|
| Admin | admin@feedback.com     | admin123   |

To create a regular user: click **Register** on the home page.

---

## Project Structure

```
feedback_app/
├── app.py                  ← Flask backend (all API routes)
├── requirements.txt        ← Python dependencies
├── instance/
│   └── feedback.db        ← SQLite database (auto-created)
└── templates/
    ├── index.html          ← Feedback submission page
    ├── dashboard.html      ← Charts & analytics
    └── admin.html          ← Admin panel
```

---

## API Endpoints (test with Postman)

| Method | Endpoint                    | Description              | Auth     |
|--------|-----------------------------|--------------------------|----------|
| POST   | /api/register               | Register new user        | None     |
| POST   | /api/login                  | Login                    | None     |
| POST   | /api/logout                 | Logout                   | None     |
| GET    | /api/me                     | Get session info         | None     |
| POST   | /api/feedback               | Submit feedback          | Optional |
| GET    | /api/summary                | Sentiment summary        | None     |
| GET    | /api/my-feedback            | User's feedback history  | User     |
| GET    | /api/admin/all-feedback     | All feedback (admin)     | Admin    |
| DELETE | /api/admin/delete/:id       | Delete feedback (admin)  | Admin    |

---

## Postman Quick Test

### Submit feedback (no login needed):
```
POST http://localhost:5000/api/feedback
Content-Type: application/json

{
  "message": "The service was absolutely amazing!"
}
```

### Expected response:
```json
{
  "sentiment": "Positive",
  "score": 0.8442,
  "id": 1
}
```

---

## Stopping the server
Press `Ctrl + C` in the terminal.

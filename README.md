# GlucoFoot Sentinel

GlucoFoot Sentinel is a full-stack screening application for diabetic patients to assess possible risk of diabetic foot ulcer or cellulitis using a placeholder AI module.

## Features
- Landing page and healthcare-themed UI
- Register/login/logout flow
- Patient dashboard for vitals, symptoms, and image uploads
- Placeholder AI prediction engine
- Risk result page with medical guidance and disclaimer
- Downloadable PDF report
- Admin dashboard for patient review and deletion

## Structure
- frontend/: Vite React frontend
- backend/: Flask API and SQLAlchemy models
- database/: SQLite database
- uploads/: uploaded images
- reports/: generated PDF reports

## Local Setup
### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
pip install -r requirements.txt
python app.py
```

## Default Admin Account
- Email: admin@glucofoot.com
- Password: admin123

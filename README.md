# DocuPilot AI

Phase 0 Step 1: Windows 11 development foundation.

## Prerequisites
Python 3.12, Node.js 22 LTS or newer, npm. PostgreSQL is introduced during the persistence step.

## Backend (PowerShell from repository root)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
cd backend
python manage.py check
python manage.py test
python manage.py runserver
```
Visit http://127.0.0.1:8000/api/health/

## Frontend (second PowerShell terminal)
```powershell
cd frontend
npm install
npm run build
npm run dev
```
Visit http://localhost:5173. Frontend calls backend via Vite proxy.

## Scope
Foundation only: no upload, document processing, invoice extraction or AI yet. SQLite is a temporary local bootstrap; PostgreSQL will be configured in a subsequent step. Never use the example secret in production.

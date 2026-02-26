# Notes Backend (FastAPI)

REST API for the Personal Notes Organizer.

## Environment variables

Copy `.env.example` to your actual environment (the orchestrator will manage `.env`):

- `HOST` (default `0.0.0.0`)
- `PORT` (default `3001`)
- `CORS_ORIGINS` (comma-separated; e.g. `http://localhost:3000`)
- `SQLITE_DB_PATH` (path to `notes.db` created by `notes_database/init_db.py`)

## Run

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001
```

## API overview

- `GET /healthz`
- `GET /notes?q=&tag=&limit=&offset=`
- `POST /notes`
- `GET /notes/{id}`
- `PUT /notes/{id}`
- `DELETE /notes/{id}`
- `GET /tags`
"""

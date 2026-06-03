# Sonexa

## Local setup

Backend:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

## Vercel

Set `VITE_API_URL` in the Vercel project environment variables to the deployed backend URL.

Do not commit `.env` files. Use `.env.example` as the template.

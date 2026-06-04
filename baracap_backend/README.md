# BARACAP Backend

FastAPI backend for the public financial literacy assessment page.

## Railway

Deploy from the repository root, not from this subfolder. Railway reads `railway.json` and starts the app with:

```bash
python main.py
```

Health check:

```text
/api/health
```

## Run

From the project root:

```bash
python main.py
```

Open the printed URL, usually `http://127.0.0.1:8000`.

## Environment

Copy `.env.example` to `.env` and fill Telegram/PDF values when ready:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ADMIN_STATS_TOKEN=
```

Telegram variables are optional. `TELEGRAM_CHAT_ID` is for the admin chat only. Public users stay on the web page, receive the PDF gift through the backend download endpoint, and can open the public channel at `https://t.me/BeTraderuzb`.
Admin Telegram notifications include the latest submitted result and aggregate statistics. `ADMIN_STATS_TOKEN` protects the optional `/api/literacy-assessment/statistics?token=...` endpoint.

## Active Endpoints

- `GET /api/health`
- `GET /api/config`
- `GET /api/literacy-assessment/questions`
- `POST /api/literacy-assessment`
- `GET /api/literacy-assessment/statistics?token=...`
- `GET /api/literacy-assessment/guide/{simple|professional}`

The frontend is served from `/`.

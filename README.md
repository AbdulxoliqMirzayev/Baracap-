# BARACAP Financial Literacy Test

Public financial literacy test page. A user enters name, phone, current status, answers 6 weighted questions, receives a 100-point score and a PDF gift tier.

## Railway Deploy

This repository is ready for Railway through GitHub.

1. Push the project to GitHub.
2. In Railway, create a new project from that GitHub repository.
3. Railway will use `railway.json` and run:

```bash
python main.py
```

4. Add these environment variables in Railway only if Telegram notifications are needed:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ADMIN_STATS_TOKEN=
```

`TELEGRAM_CHAT_ID` should be the admin chat or private admin group. Users do not access the bot; they only use the web page. After finishing the quiz, users see a Telegram channel button that opens `https://t.me/BeTraderuzb`.
Each admin Telegram notification includes the latest user result plus total users, 50+ score count, low-score count, average score, and recent results.
`ADMIN_STATS_TOKEN` protects the optional JSON statistics endpoint:

```text
/api/literacy-assessment/statistics?token=your-secret
```

Railway provides `PORT` automatically. Do not set `APP_HOST=127.0.0.1` in Railway; the app defaults to `0.0.0.0` for deployment.

## Run

Windowsda eng oson yo'l:

```bat
start_baracap.bat
```

Brauzerda oching:

```text
http://127.0.0.1:8000
```

Agar `python` va `pip` PATH ichida ishlamasa, explicit Python 3.12 yo'lidan foydalaning:

```bash
"%LocalAppData%\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
"%LocalAppData%\Programs\Python\Python312\python.exe" main.py
```

Open the URL printed in the terminal, usually `http://127.0.0.1:8000`.

## Environment

Copy `.env.example` to `.env` and fill:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ADMIN_STATS_TOKEN`

Telegram variables are optional. PDF gifts are generated and downloaded from the browser after the quiz result.

## Health Check

Railway health check path:

```text
/api/health
```

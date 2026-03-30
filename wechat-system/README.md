# WeChat QA and Score System

A FastAPI-based backend for a WeChat Official Account with two core features:

- Document-grounded intelligent Q&A
- Student score query page (`student_id + name`)

## Features

- WeChat server verification and message callback endpoint
- Keyword trigger for score query (`查成绩`)
- Strict doc-based answers with fallback reply: `暂无法解答`
- Simple retrieval + AI API call pipeline (DeepSeek/OpenAI-compatible endpoint)
- Score query API with input validation and rate limiting
- Static score query page

## Project Structure

```text
wechat-system/
  app/
    main.py
    config.py
    database.py
    qa/
    score/
    wechat/
  docs/faq.txt
  scripts/init_db.py
  static/score.html
  requirements.txt
  .env
```

## Requirements

- Python 3.10+
- pip

## Install

```bash
cd wechat-system
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If your network has proxy issues, clear proxy env vars before install:

```powershell
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""
pip install -r requirements.txt -i https://pypi.org/simple --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

## Environment Variables

Edit `.env`:

- `WECHAT_TOKEN`: token used in WeChat server config
- `SCORE_PAGE_URL`: public URL for `score.html`
- `AI_API_KEY`: your model provider key
- `AI_API_BASE`: API base URL (for example DeepSeek OpenAI-compatible endpoint)
- `AI_CHAT_MODEL`: model name
- `DATABASE_URL`: default is sqlite file

## Initialize Database

```bash
python scripts/init_db.py
```

This creates tables and inserts sample score data if empty.

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```text
GET http://127.0.0.1:8000/healthz
```

## Local Testing

### Score Query Page

Open:

```text
http://127.0.0.1:8000/static/score.html
```

Sample data:

- `2026001 + 张三`
- `2026002 + 李四`

API:

```text
POST /api/score/query
```

### WeChat Endpoint

- Verification: `GET /wechat`
- Message callback: `POST /wechat` (XML)

Behavior:

- Contains `查成绩` -> returns score page URL
- Other text -> Q&A pipeline
- No related doc evidence -> returns `暂无法解答`

## WeChat Official Account Configuration

In WeChat backend (developer settings):

- URL: `https://your-domain/wechat`
- Token: same as `.env` `WECHAT_TOKEN`
- Encoding mode: plaintext mode for current implementation

Use a public HTTPS domain (or tunnel) for real callback tests.

## Notes

- This project does not train a model.
- It calls external model APIs directly.
- Keep API keys in `.env` only, never commit secrets.

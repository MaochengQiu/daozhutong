# WeChat QA and Score System

A FastAPI-based backend for a WeChat Official Account with two core features:

- Document-grounded intelligent Q&A
- Student score query page (`student_id + name + ID card suffix`)

## Features

- WeChat server verification and message callback endpoint
- Keyword trigger for score query (`查成绩`)
- Strict doc-based answers with fallback reply: `暂无法回答，请直接询问老师`
- Simple retrieval + AI API call pipeline (DeepSeek/OpenAI-compatible chat endpoint + Tencent Cloud Hunyuan embeddings)
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
- `TENCENT_SECRET_ID`: Tencent Cloud SecretId for Hunyuan embeddings; leave empty in code and fill it in your local `.env`
- `TENCENT_SECRET_KEY`: Tencent Cloud SecretKey for Hunyuan embeddings; leave empty in code and fill it in your local `.env`
- `TENCENT_REGION`: Tencent Cloud region, default `ap-guangzhou`
- `TENCENT_EMBEDDING_ENDPOINT`: Tencent Cloud Hunyuan endpoint, default `hunyuan.tencentcloudapi.com`
- `DATABASE_URL`: default is sqlite file

Document Q&A supports `.txt`, `.docx`, and text-based `.pdf` files. Set `DOCS_PATH` to either a single supported file or a directory containing supported files.

After switching embedding providers, recreate the Qdrant collection because Tencent Cloud Hunyuan embeddings use a different vector space and dimension from OpenAI embeddings.

## Initialize Database

```bash
python scripts/init_db.py
```

This creates tables and inserts sample score data if empty.

## Import Score XLSX

Score query supports importing `.xlsx` score files into the database.

Required columns can use either English or Chinese headers:

```text
student_id / 学号
name / 姓名
id_card_suffix / 身份证后6位
course / 课程 / 科目
score / 成绩 / 分数
```

Example:

```bash
python scripts/import_scores.py data/scores.xlsx --replace
```

Use `--replace` when the Excel file should become the full score table. Without `--replace`, matching records with the same `student_id + name + id_card_suffix + course` are updated and other records are kept.

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

- `2026001 + 张三 + 000001`
- `2026002 + 李四 + 000002`

API:

```text
POST /api/score/query
```

Request body:

```json
{
  "student_id": "2026001",
  "name": "张三",
  "id_card_suffix": "000001"
}
```

### QA Chat Page

Open:

```text
http://127.0.0.1:8000/static/chat.html
```

API:

```text
POST /api/qa/ask
```

### Home Page

Open:

```text
http://127.0.0.1:8000/
```

### WeChat Endpoint

- Verification: `GET /wechat`
- Message callback: `POST /wechat` (XML)

Behavior:

- Contains `查成绩` -> returns score page URL
- Other text -> Q&A pipeline
- No related doc evidence -> returns `暂无法回答，请直接询问老师`

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

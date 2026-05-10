# 微信问答助手 (WeChat QA & Score System)

基于 **FastAPI** 的微信公众号后端，提供**知识库智能问答**与**学生成绩查询**两大功能，支持 Vercel 部署。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | FastAPI + Uvicorn |
| 数据库 | SQLAlchemy + SQLite / PostgreSQL |
| 向量检索 | Qdrant（余弦相似度） |
| Embedding | 腾讯云混元 Hunyuan |
| LLM | DeepSeek / OpenAI 兼容 API |
| 文档解析 | python-docx (.docx)、pypdf (.pdf) |
| 数据导入 | openpyxl (.xlsx) |
| 部署 | Vercel Serverless |
| 前端 | 纯 HTML + CSS + JS（响应式） |

---

## 架构流程

### 智能问答 (RAG Pipeline)

```
用户提问
  │
  ├─► 腾讯混元 Embedding 向量化
  │     │
  │     ▼
  │   Qdrant 向量库检索 top-5 相关片段
  │     │
  │     ▼
  │   拼接上下文 → 调用 DeepSeek/OpenAI API
  │     │
  │     ▼
  │   返回回答（无匹配时 fallback: "暂无法回答，请直接询问老师"）
  │
  └─► 降级策略：向量检索失败则使用全文作为上下文
```

### 微信公众号消息路由

```
微信用户发消息
  │
  ▼
GET/POST /wechat（SHA1 签名验证）
  │
  ▼
XML 解析 → 关键字判断
  │
  ├─► 包含"查成绩" → 返回成绩查询页面链接
  │
  └─► 其他文本 → 进入 RAG 问答管道
```

---

## 功能特性

- **微信公众号对接** — 服务器验证、消息回调、XML 回复
- **RAG 智能问答** — 文档切片 → 向量化 → 语义检索 → LLM 生成，支持 `.txt` / `.docx` / `.pdf`
- **成绩查询** — 学号 + 姓名 + 身份证后 6 位精确匹配，IP 限流保护
- **Excel 成绩导入** — 支持中英文表头别名，全量替换或增量更新
- **前端三页面** — 首页入口、成绩查询、智能问答，响应式设计
- **统一 UI 主题** — teal 绿色调 + 书籍装饰元素

---

## 项目结构

```
wechat-system/
├── app/
│   ├── main.py              # FastAPI 应用工厂（路由、CORS、静态文件、启动初始化）
│   ├── config.py            # Pydantic Settings 配置管理
│   ├── database.py          # SQLAlchemy 引擎与会话
│   │
│   ├── qa/                  # 知识库问答模块
│   │   ├── ai_client.py     # LLM API 调用 + 腾讯混元 Embedding
│   │   ├── doc_processor.py # 文档解析（txt / docx / pdf）
│   │   ├── retriever.py     # Qdrant 向量检索 + QA 主流程
│   │   └── router.py        # POST /api/qa/ask
│   │
│   ├── score/               # 成绩查询模块
│   │   ├── models.py        # ScoreRecord ORM
│   │   ├── service.py       # 查询逻辑
│   │   ├── router.py        # POST /api/score/query（限流）
│   │   └── importer.py      # .xlsx 导入（表头别名映射）
│   │
│   └── wechat/              # 微信公众号对接
│       ├── handler.py       # GET/POST /wechat（签名验证 + 消息路由）
│       └── reply.py         # XML 回复构造
│
├── static/                  # 前端页面
│   ├── home.html            # 首页
│   ├── score.html           # 成绩查询
│   ├── chat.html            # 智能问答
│   └── ui.css               # 全局主题样式
│
├── docs/
│   ├── faq.txt              # 知识库文档
│   └── CHANGELOG.md
│
├── scripts/
│   ├── init_db.py           # 数据库初始化
│   └── import_scores.py     # 成绩 Excel 导入
│
├── requirements.txt
└── .env                     # 环境变量（不入库）
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Qdrant 向量数据库（本地或远程）

### 安装

```bash
cd wechat-system
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\activate
pip install -r requirements.txt
```

网络代理问题时可清理代理后安装：

```powershell
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""
pip install -r requirements.txt -i https://pypi.org/simple --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### 配置环境变量

在 `wechat-system/.env` 中配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WECHAT_TOKEN` | 微信服务器配置 Token | `replace_with_wechat_token` |
| `AI_API_KEY` | LLM API 密钥 | — |
| `AI_API_BASE` | API 地址 | `https://api.deepseek.com` |
| `AI_CHAT_MODEL` | 模型名称 | `deepseek-chat` |
| `TENCENT_SECRET_ID` | 腾讯云 SecretId（混元 Embedding） | — |
| `TENCENT_SECRET_KEY` | 腾讯云 SecretKey | — |
| `TENCENT_REGION` | 地域 | `ap-guangzhou` |
| `DATABASE_URL` | 数据库连接 | `sqlite:///data/app.db` |
| `SCORE_PAGE_URL` | 成绩页面公网 URL | `http://localhost:8000/static/score.html` |
| `DOCS_PATH` | 知识库文档路径（文件或目录） | `docs/faq.txt` |
| `QDRANT_URL` | Qdrant 地址 | `http://localhost:6333` |

> 切换 Embedding 提供方后需重建 Qdrant collection，因向量维度不同。

### 初始化数据库

```bash
python scripts/init_db.py
```

自动创建表结构，若为空则插入两条示例数据。

### 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：`GET http://localhost:8000/healthz`

---

## API 文档

### 智能问答

```
POST /api/qa/ask
```

Request:
```json
{
  "question": "如何查询成绩？"
}
```

Response:
```json
{
  "ok": true,
  "answer": "在公众号内发送\"查成绩\"，系统会返回成绩查询页面链接..."
}
```

### 成绩查询

```
POST /api/score/query
```

Request:
```json
{
  "student_id": "2026001",
  "name": "张三",
  "id_card_suffix": "000001"
}
```

Response:
```json
{
  "ok": true,
  "data": [
    { "course": "数学", "score": 92 },
    { "course": "英语", "score": 88 }
  ]
}
```

限流：同一 IP 每分钟最多 20 次请求。

### 微信接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/wechat` | 服务器验证（echostr 返回） |
| `POST` | `/wechat` | 消息回调（XML 格式） |

---

## Excel 成绩导入

支持 `.xlsx` 文件导入，表头支持中英文别名：

| 标准字段 | 支持的表头别名 |
|----------|---------------|
| `student_id` | 学号, studentid, 考号 |
| `name` | 姓名, 学生姓名 |
| `id_card_suffix` | 身份证后6位, 身份证号, 证件号 |
| `course` | 课程, 科目, 考试科目 |
| `score` | 成绩, 分数, 得分 |

```bash
# 全量替换（清空后导入）
python scripts/import_scores.py data/scores.xlsx --replace

# 增量更新（匹配 student_id + name + id_card_suffix + course 则更新）
python scripts/import_scores.py data/scores.xlsx
```

---

## 本地测试

### 成绩查询

访问 `http://localhost:8000/static/score.html`

示例账号：
- `2026001` + `张三` + `000001`
- `2026002` + `李四` + `000002`

### 智能问答

访问 `http://localhost:8000/static/chat.html`

### 首页

访问 `http://localhost:8000/` 或 `http://localhost:8000/static/home.html`

---

## 微信公众号配置

在公众号后台「开发 > 基本配置」中设置：

- **URL**: `https://your-domain/wechat`
- **Token**: 与 `WECHAT_TOKEN` 一致
- **消息加解密方式**: 明文模式

本地开发可用内网穿透工具（如 ngrok）暴露公网 HTTPS 地址进行测试。

---

## Vercel 部署

根目录 `vercel.json` 将所有路由代理至 `api/index.py`：

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/api/index" }
  ]
}
```

`api/index.py` 将 `wechat-system` 加入 Python 路径后导入 FastAPI app。

---

## 开发说明

- 本项目不训练模型，所有 AI 能力通过调用外部 API 实现
- API 密钥仅存在于 `.env` 中，禁止提交至版本控制
- 前端页面支持 `<meta name="viewport">` 响应式适配，移动端自动单列布局
- 问答系统中的 composition 事件处理保证中文输入法体验

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import inspect, text

from app.config import BASE_DIR, get_settings
from app.database import Base, SessionLocal, engine
from app.qa.router import router as qa_router
from app.score.router import router as score_router
from app.score.models import ScoreRecord
from app.wechat.handler import router as wechat_router


def _ensure_score_schema():
    inspector = inspect(engine)
    if not inspector.has_table(ScoreRecord.__tablename__):
        return

    columns = {column["name"] for column in inspector.get_columns(ScoreRecord.__tablename__)}
    if "id_card_suffix" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE score_records ADD COLUMN id_card_suffix VARCHAR(4)"))


def _seed_score_records(session):
    existing = session.query(ScoreRecord).count()
    if existing == 0:
        session.add_all(
            [
                ScoreRecord(student_id="2026001", name="张三", id_card_suffix="0001", course="数学", score=92),
                ScoreRecord(student_id="2026001", name="张三", id_card_suffix="0001", course="英语", score=88),
                ScoreRecord(student_id="2026002", name="李四", id_card_suffix="0002", course="数学", score=79),
                ScoreRecord(student_id="2026002", name="李四", id_card_suffix="0002", course="英语", score=85),
            ]
        )
        session.commit()
        return

    session.query(ScoreRecord).filter(
        ScoreRecord.name == "张三",
        ScoreRecord.id_card_suffix.is_(None),
    ).update({"id_card_suffix": "0001"}, synchronize_session=False)
    session.query(ScoreRecord).filter(
        ScoreRecord.name == "李四",
        ScoreRecord.id_card_suffix.is_(None),
    ).update({"id_card_suffix": "0002"}, synchronize_session=False)
    session.commit()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.middleware("http")
    async def no_cache_static_pages(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(wechat_router, tags=["wechat"])
    app.include_router(qa_router, tags=["qa"])
    app.include_router(score_router, tags=["score"])
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.on_event("startup")
    def startup():
        _ensure_score_schema()
        Base.metadata.create_all(bind=engine)
        session = SessionLocal()
        try:
            _seed_score_records(session)
        finally:
            session.close()

    @app.get("/healthz")
    def health_check():
        return {"status": "ok"}

    @app.get("/")
    def home():
        return RedirectResponse(url="/static/home.html")

    @app.head("/")
    def home_head():
        return RedirectResponse(url="/static/home.html")

    return app


app = create_app()

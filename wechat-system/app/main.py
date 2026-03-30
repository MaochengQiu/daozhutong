from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, get_settings
from app.database import Base, engine
from app.score.router import router as score_router
from app.wechat.handler import router as wechat_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(wechat_router, tags=["wechat"])
    app.include_router(score_router, tags=["score"])
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.on_event("startup")
    def startup():
        Base.metadata.create_all(bind=engine)

    @app.get("/healthz")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()

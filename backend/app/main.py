from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from containers import AppContainer
from .api import chat_v3, university

origins = ["http://localhost:5173"]


def create_app() -> FastAPI:
    container = AppContainer()

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.container = container # type: ignore
    app.include_router(chat_v3.router)
    app.include_router(university.router)

    return app


app = create_app()

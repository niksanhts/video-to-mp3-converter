import uvicorn
from fastapi import FastAPI
from app.endpoints import router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/files", tags=["files"])
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000)

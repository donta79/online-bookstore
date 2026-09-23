from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.books import router as books_router

app = FastAPI(title="Online Bookstore")
app.include_router(books_router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def read_index() -> FileResponse:
    return FileResponse(static_dir / "index.html")

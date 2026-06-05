from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.analytics import analyze_dataset, load_sample_dataset, load_uploaded_dataset


app = FastAPI(
    title="API Analitica de Supermercado",
    description="Backend FastAPI para analisis descriptivo, clustering y recomendaciones.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse("frontend/index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/sample")
def sample_analysis() -> dict:
    try:
        return analyze_dataset(load_sample_dataset())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/upload")
async def upload_analysis(file: UploadFile = File(...)) -> dict:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos CSV.")
    content = await file.read()
    try:
        return analyze_dataset(load_uploaded_dataset(file.filename, content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

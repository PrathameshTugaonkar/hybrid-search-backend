# app/main.py
import os
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .search import hybrid_search
from .models import SearchResponse, FormulationInput

from .regulatory_agent import check_formulation
from .report_generator import generate_pdf_report

from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="Hybrid Search API", version="1.0.0")

frontend_origin = os.environ.get("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin] if frontend_origin != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/search", response_model=SearchResponse)
async def search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(20, ge=1, le=100),
    vector_top_k: int = Query(10, ge=1, le=100),
    text_top_k: int = Query(10, ge=1, le=100),
):
    results = hybrid_search(
        query_text=query,
        top_k=top_k,
        vector_top_k=vector_top_k,
        text_top_k=text_top_k,
    )
    return {"results": results}

@app.post("/validate")
async def validate_formulation(data: FormulationInput):
    report = await check_formulation(data.name, data.ingredients)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = data.name.replace(" ", "_")
    pdf_name = f"Compliance_{safe_name}_{timestamp}.pdf"
    pdf_path = f"/tmp/{pdf_name}"

    generate_pdf_report(data.name, data.ingredients, report, pdf_path)

    return {
        "formulation": data.name,
        "results": report["raw_results"],
        "summary": report["markdown_report"],
        "pdf_url": f"/download/{pdf_name}"
    }

@app.get("/download/{file_name}")
async def download_pdf(file_name: str):
    file_path = f"/tmp/{file_name}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=file_name)
    return {"error": "File not found"}
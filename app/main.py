# app/main.py
import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .search import hybrid_search
from .models import SearchResponse

from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="Hybrid Search API", version="1.0.0")

# CORS (restrict in prod)
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

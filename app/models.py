# app/models.py
from pydantic import BaseModel
from typing import List, Optional

class SearchResult(BaseModel):
    id: str
    source_id: str
    incinamefull: Optional[str] = None
    functions: Optional[List[str]] = None
    textScore: Optional[float] = None
    vectorScore: Optional[float] = None
    combinedScore: Optional[float] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]

class FormulationInput(BaseModel):
    name: str
    ingredients: dict
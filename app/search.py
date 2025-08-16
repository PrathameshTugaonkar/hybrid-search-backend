# app/search.py
import os
from typing import Any, Dict, List
from pymongo import MongoClient
import voyageai

from dotenv import load_dotenv
load_dotenv()

# ---- Env ----
MONGO_URI    = os.environ["MONGO_URI"]          
VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]   
VECTOR_INDEX = os.environ["VECTOR_INDEX"]       
TEXT_INDEX   = os.environ["TEXT_INDEX"]         

DB_NAME      = os.environ.get("DB_NAME", "search")
COLL_NAME    = os.environ.get("COLL_NAME", "voyageai3.5VectorEmbeddings")

# ---- Clients ----
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLL_NAME]
vo = voyageai.Client(api_key=VOYAGE_API_KEY)

def _vector_pipeline(query_vector: List[float], limit: int) -> List[Dict[str, Any]]:
    """Exact match to your CLI script vector search"""
    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 400,
                "limit": limit
            }
        },
        {
            "$set": {
                "vectorScore": {"$meta": "vectorSearchScore"},
                "textScore": None  # Explicitly set to None like in CLI
            }
        },
        {
            "$project": {
                "_id": 1,
                "source_id": 1,
                "incinamefull": 1,
                "functions": 1,
                "textScore": 1,
                "vectorScore": 1
            }
        }
    ]
    return list(collection.aggregate(pipeline))

def _text_pipeline(query_text: str, limit: int) -> List[Dict[str, Any]]:
    """Exact match to your CLI script text search"""
    pipeline = [
        {
            "$search": {
                "index": TEXT_INDEX,
                "text": {
                    "query": query_text,
                    "path": ["incinamefull", "functions"],
                    "fuzzy": {
                        "maxEdits": 2,
                        "prefixLength": 1,
                        "maxExpansions": 50
                    }
                }
            }
        },
        {"$limit": limit},
        {
            "$set": {
                "textScore": {"$meta": "searchScore"},
                "vectorScore": 0  # Set to 0 like in CLI, not None
            }
        },
        {
            "$project": {
                "_id": 1,
                "source_id": 1,
                "incinamefull": 1,
                "functions": 1,
                "textScore": 1,
                "vectorScore": 1
            }
        }
    ]
    return list(collection.aggregate(pipeline))

def rerank(text_hits: List[Dict[str, Any]], 
           vector_hits: List[Dict[str, Any]], 
           query: str, 
           k: int = 20) -> List[Dict[str, Any]]:
    """Exact replication of your CLI script rerank logic"""
    merged = {}

    # Index by _id - exact same logic as CLI
    for doc in text_hits + vector_hits:
        _id = str(doc["_id"])
        if _id not in merged:
            merged[_id] = doc
        else:
            # Preserve existing scores when merging
            merged[_id]["textScore"] = doc.get("textScore") or merged[_id].get("textScore")
            merged[_id]["vectorScore"] = doc.get("vectorScore") or merged[_id].get("vectorScore")

    results = list(merged.values())
    q = query.lower()

    def bucket_boost(name: str) -> float:
        """Exact same bucket boost logic as CLI"""
        name_lower = name.lower()
        if name_lower == q:
            return 2.0
        elif name_lower.startswith(q):
            return 1.5
        elif q in name_lower:
            return 1.2
        return 1.0

    reranked = []
    for doc in results:
        text_score = doc.get("textScore") or 0
        vec_score = doc.get("vectorScore") or 0
        boost = bucket_boost(doc.get("incinamefull", ""))

        # Exact same scoring logic as CLI
        if text_score > 0 and vec_score > 0:
            combined = (0.6 * text_score + 0.4 * vec_score) * boost
        elif text_score > 0:
            combined = text_score * boost
        elif vec_score > 0:
            combined = vec_score * boost
        else:
            combined = 0

        doc["combinedScore"] = combined
        reranked.append(doc)

    reranked.sort(key=lambda d: d["combinedScore"], reverse=True)
    return reranked[:k]

def hybrid_search(query_text: str,
                  top_k: int = 20,
                  vector_top_k: int = 10,
                  text_top_k: int = 10) -> List[Dict[str, Any]]:
    """Main hybrid search function matching CLI logic exactly"""
    if not query_text or not query_text.strip():
        return []

    # 1) Embed - same as CLI
    embed_response = vo.embed(texts=[query_text], model="voyage-3.5")
    query_vector = embed_response.embeddings[0]

    # 2) Vector search (top 10) - same as CLI
    vector_results = _vector_pipeline(query_vector, limit=vector_top_k)

    # 3) Text search (top 10) - same as CLI  
    text_results = _text_pipeline(query_text, limit=text_top_k)

    # 4) Merge + bucketed rerank - exact same function as CLI
    final_results = rerank(text_results, vector_results, query_text, k=top_k)

    # Return with same structure as CLI but clean for API
    cleaned = []
    for doc in final_results:
        cleaned.append({
            "id": str(doc.get("_id")),
            "source_id": str(doc.get("source_id", "")),  # Convert ObjectId to string
            "incinamefull": doc.get("incinamefull"),
            "functions": doc.get("functions"),
            "textScore": doc.get("textScore"),
            "vectorScore": doc.get("vectorScore"),
            "combinedScore": round(doc.get("combinedScore", 0), 4)  # Round like CLI output
        })
    return cleaned
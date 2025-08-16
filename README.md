# hybrid-search-backend


# 1) create .env (or export vars)

export MONGO_URI="mongodb+srv://..."
export VOYAGE_API_KEY="..."
export VECTOR_INDEX="voyageai_vector_index"
export TEXT_INDEX="voyageai_text_index"
export DB_NAME="search"
export COLL_NAME="voyageai3.5VectorEmbeddings"
export FRONTEND_ORIGIN="http://localhost:3000"

# 2) install

pip install -r requirements.txt

# 3) run (local dev)

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4) test

curl "http://localhost:8000/search?query=water"

# api/index.py
# Vercel detects this file as a Serverless Function and serves the ASGI app.
from app.main import app as app

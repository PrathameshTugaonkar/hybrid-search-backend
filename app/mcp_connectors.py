import requests
import os


from dotenv import load_dotenv
load_dotenv()

HYBRID_SEARCH_URL = os.getenv(
    "HYBRID_SEARCH_URL"
)

def query_regulatory_db(ingredient: str):
    """
    Use Smart INCI Hybrid Search API to fetch ingredient info.
    """
    try:
        res = requests.get(HYBRID_SEARCH_URL, params={"query": ingredient})
        if res.status_code == 200:
            return res.json().get("results", [])
        return [{"error": f"No data for {ingredient}"}]
    except Exception as e:
        return [{"error": str(e)}]

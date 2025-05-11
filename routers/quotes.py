from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.quote_scraper import scrape_quotes_from_urls, save_quotes_to_postgres
import psycopg2
import os
router = APIRouter()

class ScrapeRequest(BaseModel):
    urls: List[str]
    max_pages: int = 3

@router.post("/scrape-and-save")
def scrape_and_save(request: ScrapeRequest):
    quotes = scrape_quotes_from_urls(request.urls, request.max_pages)
    save_quotes_to_postgres(quotes)
    return {
        "status": "success",
        "message": f"{len(quotes)} quotes scraped and saved to database.",
        "quotes": quotes  # ✅ Include scraped quotes in the response
    }

@router.get("/count")
def get_quote_count():
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            database=os.getenv("PG_DATABASE"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            port=os.getenv("PG_PORT")
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM scraped_quotes;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()

        return {
            "status": "success",
            "quote_count": count
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
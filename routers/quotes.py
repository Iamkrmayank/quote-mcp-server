# routers/quotes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.quote_scraper import scrape_quotes_from_urls

class QuoteRequest(BaseModel):
    urls: List[str]
    max_pages: int = 10

router = APIRouter()

@router.post("/scrape")
def scrape_quotes(request: QuoteRequest):
    try:
        data = scrape_quotes_from_urls(request.urls, request.max_pages)
        return {"status": "success", "count": len(data), "quotes": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

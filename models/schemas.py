# models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class QuoteRequest(BaseModel):
    urls: List[str]
    max_pages: Optional[int] = 10

class MetadataRequest(BaseModel):
    csv_base64: str  # Base64-encoded CSV content

class ImageRequest(BaseModel):
    keywords: List[str]
    count: int = 5

class BatchTrackingRequest(BaseModel):
    tracking_json: str  # Base64 JSON string

class MergeRequest(BaseModel):
    csv_base64: str
    jsonl_base64: str

# routers/metadata.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import base64
import pandas as pd
from services.azure_batch import generate_metadata_batch

class MetadataRequest(BaseModel):
    csv_base64: str  # Base64-encoded CSV content

router = APIRouter()

@router.post("/generate")
def generate_metadata(request: MetadataRequest):
    try:
        decoded = base64.b64decode(request.csv_base64).decode("utf-8")
        df = pd.read_csv(pd.io.common.StringIO(decoded))
        result = generate_metadata_batch(df)
        return {"status": "success", "batch_summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

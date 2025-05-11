# routers/images.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.s3_uploader import process_and_upload_images

class ImageRequest(BaseModel):
    keywords: List[str]
    count: int = 5

router = APIRouter()

@router.post("/download-upload-transform")
def handle_images(request: ImageRequest):
    try:
        result_df = process_and_upload_images(request.keywords, request.count)
        return {
            "status": "success",
            "count": len(result_df),
            "data": result_df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

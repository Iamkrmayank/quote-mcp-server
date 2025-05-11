# routers/structure.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd

router = APIRouter()
class QuoteItem(BaseModel):
    serial: int
    quote: str
    link: Optional[str] = ""
    author: str

class QuoteStructureRequest(BaseModel):
    quotes: List[QuoteItem]

@router.post("/structure")
def structure_quotes(request: QuoteStructureRequest):
    try:
        df = pd.DataFrame([q.dict() for q in request.quotes])

        # Filter: max 180 characters per quote
        df = df[df["quote"].apply(lambda x: isinstance(x, str) and len(x.strip()) <= 180)]

        groups = []
        for author, group in df.groupby("author"):
            quotes = group["quote"].dropna().tolist()[:8]
            quotes += ['NA'] * (8 - len(quotes))
            groups.append(quotes + [author])

        columns = [f"s{i}paragraph1" for i in range(2, 10)] + ["Author"]
        final_df = pd.DataFrame(groups, columns=columns)

        return {
            "status": "success",
            "rows": len(final_df),
            "data": final_df.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
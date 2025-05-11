# routers/merge.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import base64
import pandas as pd
import json
import re
from io import StringIO

router = APIRouter()

class MergeRequest(BaseModel):
    csv_base64: str  # base64 encoded CSV file with custom_id
    jsonl_base64: str  # base64 encoded JSONL results from Azure

@router.post("/merge")
def merge_metadata(request: MergeRequest):
    try:
        def norm(cid):
            cid = str(cid).strip().lower()
            m = re.match(r"(\d+)-(.+)", cid)
            return f"{int(m.group(1))}-{m.group(2)}" if m else cid

        df = pd.read_csv(StringIO(base64.b64decode(request.csv_base64).decode("utf-8")))
        df["custom_id_normalized"] = df["custom_id"].apply(norm)

        meta_map = {}
        for line in base64.b64decode(request.jsonl_base64).decode("utf-8").splitlines():
            try:
                obj = json.loads(line)
                rid = norm(obj.get("custom_id", ""))
                raw = obj["response"]["body"]["choices"][0]["message"]["content"]
                clean = re.sub(r"^```json\\s*|\\s*```$", "", raw.strip())
                meta = json.loads(clean)
                meta_map[rid] = meta
            except Exception:
                continue

        df["storytitle"] = df["custom_id_normalized"].map(lambda x: meta_map.get(x, {}).get("storytitle", ""))
        df["metadescription"] = df["custom_id_normalized"].map(lambda x: meta_map.get(x, {}).get("metadescription", ""))
        df["metakeywords"] = df["custom_id_normalized"].map(lambda x: meta_map.get(x, {}).get("metakeywords", ""))
        df.drop(columns=["custom_id_normalized"], inplace=True)

        return {
            "status": "merged",
            "records": len(df),
            "csv": df.to_csv(index=False)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

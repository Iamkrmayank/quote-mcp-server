# routers/structure.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

router = APIRouter()
load_dotenv()

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
        df = df[df["quote"].apply(lambda x: isinstance(x, str) and len(x.strip()) <= 180)]

        used_quotes = set()
        groups = []

        for author, group in df.groupby("author"):
            quotes_list = group["quote"].dropna().tolist()
            for i in range(0, len(quotes_list), 8):
                chunk = quotes_list[i:i + 8]
                used_quotes.update(chunk)
                chunk += ['NA'] * (8 - len(chunk))
                groups.append(chunk + [author])

        columns = [f"s{i}paragraph1" for i in range(2, 10)] + ["Author"]
        final_df = pd.DataFrame(groups, columns=columns)

        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            database=os.getenv("PG_DATABASE"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            port=os.getenv("PG_PORT")
        )
        cur = conn.cursor()

        # 1. Insert structured data into structured_quotes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS structured_quotes (
                id SERIAL PRIMARY KEY,
                s2paragraph1 TEXT,
                s3paragraph1 TEXT,
                s4paragraph1 TEXT,
                s5paragraph1 TEXT,
                s6paragraph1 TEXT,
                s7paragraph1 TEXT,
                s8paragraph1 TEXT,
                s9paragraph1 TEXT,
                Author TEXT
            );
        """)

        for _, row in final_df.iterrows():
            cur.execute("""
                INSERT INTO structured_quotes (
                    s2paragraph1, s3paragraph1, s4paragraph1, s5paragraph1,
                    s6paragraph1, s7paragraph1, s8paragraph1, s9paragraph1, Author
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(row[col] for col in columns))

        # 2. Mark used quotes as Completed
        for quote in used_quotes:
            cur.execute("""
                UPDATE scraped_quotes SET status = 'Completed'
                WHERE quote = %s;
            """, (quote,))

        # 3. Delete rows from scraped_quotes that still have status 'Pending'
        cur.execute("""
            DELETE FROM scraped_quotes WHERE status = 'Pending';
        """)

        conn.commit()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "rows": len(final_df),
            "data": final_df.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# services/azure_batch.py
import os
import re
import json
import time
import pandas as pd
import requests

AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = "2025-03-01-preview"
HEADERS = {
    "api-key": AZURE_API_KEY,
    "Content-Type": "application/json"
}

def normalize_author(author):
    return author.replace(" ", "_").lower()

def generate_metadata_batch(df: pd.DataFrame):
    ts = str(int(time.time()))
    df.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
    df.replace("NA", pd.NA, inplace=True)
    df.dropna(inplace=True)

    author_map, counter = {}, {}
    ids, gcount = [], 1
    for _, row in df.iterrows():
        a = row['Author'].strip()
        k = normalize_author(a)
        if a not in author_map:
            author_map[a], counter[a] = gcount, 1
            gcount += 1
        else:
            counter[a] += 1
        ids.append(f"{author_map[a]}-{k}-{counter[a]}")
    df["custom_id"] = ids

    deployment_model = "gpt-4o-global-batch"
    payloads = []
    for _, row in df.iterrows():
        quotes = [row.get(f"s{i}paragraph1", '') for i in range(2, 10)]
        block = "\n".join(f"- {q}" for q in quotes if q and q != "NA")
        author = row['Author']
        prompt = f"You're given a series of quotes by {author}.\nUse them to generate metadata for a web story.\nQuotes:\n{block}\n\nPlease respond ONLY in this exact JSON format:\n{{\n  \"storytitle\": \"...\",\n  \"metadescription\": \"...\",\n  \"metakeywords\": \"...\"\n}}"

        payloads.append({
            "custom_id": row["custom_id"],
            "method": "POST",
            "url": "/chat/completions",
            "body": {
                "model": deployment_model,
                "messages": [
                    {"role": "system", "content": "You are a creative and SEO-savvy content writer."},
                    {"role": "user", "content": prompt}
                ]
            }
        })

    # Save to JSONL file
    jsonl_str = "\n".join(json.dumps(p) for p in payloads)
    jsonl_filename = f"batch_{ts}.jsonl"
    with open(jsonl_filename, "w") as f:
        f.write(jsonl_str)

    # Upload file to Azure
    with open(jsonl_filename, "rb") as f:
        file_upload_url = f"{AZURE_ENDPOINT}/openai/files?api-version={API_VERSION}"
        files = {
            "file": (jsonl_filename, f, "application/jsonl"),
            "purpose": (None, "batch"),
            "expires_after": (None, json.dumps({"seconds": 1209600, "anchor": "created_at"}))
        }
        upload_resp = requests.post(file_upload_url, headers={"api-key": AZURE_API_KEY}, files=files)
        upload_resp.raise_for_status()
        file_id = upload_resp.json()["id"]

    # Create batch job
    batch_payload = {
        "input_file_id": file_id,
        "endpoint": "/chat/completions",
        "completion_window": "24h",
        "output_expires_after": {"seconds": 1209600, "anchor": "created_at"}
    }
    batch_url = f"{AZURE_ENDPOINT}/openai/batches?api-version={API_VERSION}"
    batch_resp = requests.post(batch_url, headers=HEADERS, json=batch_payload)
    batch_resp.raise_for_status()
    batch_id = batch_resp.json()["id"]

    return {
        "ts": ts,
        "file_id": file_id,
        "batch_id": batch_id,
        "jsonl_file": jsonl_filename
    }
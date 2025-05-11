# routers/azure.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import base64
import os
import datetime
import requests
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings

router = APIRouter()

class BatchTrackingRequest(BaseModel):
    tracking_json: str  # base64 encoded tracking JSON file

@router.post("/fetch-result")
def fetch_azure_batch_result(request: BatchTrackingRequest):
    try:
        tracking_info = json.loads(base64.b64decode(request.tracking_json))
        batch_id = tracking_info.get("batch_id")
        ts = tracking_info.get("ts")
        output_filename = f"batch_results_{ts}.jsonl"

        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = "2025-03-01-preview"
        headers = {"api-key": api_key}

        # Step 1: Retrieve batch status
        batch_url = f"{endpoint}/openai/batches/{batch_id}?api-version={api_version}"
        batch_resp = requests.get(batch_url, headers=headers)
        batch_resp.raise_for_status()
        batch_job = batch_resp.json()

        if batch_job.get("status") != "completed":
            return {"status": batch_job.get("status"), "message": "Batch not completed yet."}

        output_file_id = batch_job.get("output_file_id") or batch_job.get("error_file_id")
        if not output_file_id:
            raise ValueError("No output or error file available for this batch.")

        # Step 2: Download result
        file_url = f"{endpoint}/openai/files/{output_file_id}/content?api-version={api_version}"
        file_resp = requests.get(file_url, headers=headers)
        file_resp.raise_for_status()
        raw_lines = file_resp.text.strip().split('\n')

        with open(output_filename, "w") as f:
            for line in raw_lines:
                f.write(line + "\n")

        # Step 3: Upload to Azure Blob
        connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
        container_name = os.getenv("AZURE_BLOB_CONTAINER")
        account_name = os.getenv("AZURE_BLOB_ACCOUNT_NAME")
        account_key = os.getenv("AZURE_BLOB_ACCOUNT_KEY")

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=output_filename)

        with open(output_filename, "rb") as data:
            blob_client.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type="application/json"))

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=output_filename,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.utcnow() + datetime.timedelta(days=1)
        )

        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{output_filename}?{sas_token}"

        return {
            "status": "completed",
            "azure_blob_url": blob_url,
            "lines": len(raw_lines)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

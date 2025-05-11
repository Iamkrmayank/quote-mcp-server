# services/s3_uploader.py
import os
import json
import base64
import shutil
import boto3
import pandas as pd
from simple_image_download import simple_image_download as simp

# Replace these with your actual keys or environment variables
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
REGION_NAME = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("AWS_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX")
CDN_BASE =  os.getenv("CDN_BASE")


def process_and_upload_images(keywords, count):
    if os.path.exists("simple_images"):
        shutil.rmtree("simple_images")

    response = simp.simple_image_download()
    for kw in keywords:
        response.download(kw, count)

    s3 = boto3.client("s3",
                      aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY,
                      region_name=REGION_NAME)

    results = []
    for folder, _, files in os.walk("simple_images"):
        for f in files:
            path = os.path.join(folder, f)
            kf = os.path.basename(folder).replace(" ", "-")
            fname = f.replace(" ", "-")
            key = f"{S3_PREFIX}{kf}/{fname}"
            try:
                s3.upload_file(path, BUCKET_NAME, key)
                cdn_url = f"{CDN_BASE}{key}"
                transformed_url = transform_to_cdn_url(key)
                results.append({"Keyword": kf, "Filename": fname, "CDN_URL": cdn_url, "standardurl": transformed_url})
            except Exception as e:
                results.append({"Keyword": kf, "Filename": fname, "error": str(e)})

    return pd.DataFrame(results)


def transform_to_cdn_url(key_value):
    template = {
        "bucket": BUCKET_NAME,
        "key": key_value,
        "edits": {
            "resize": {
                "width": 720,
                "height": 1280,
                "fit": "cover"
            }
        }
    }
    encoded = base64.urlsafe_b64encode(json.dumps(template).encode()).decode()
    return f"https://media.suvichaar.org/{encoded}"

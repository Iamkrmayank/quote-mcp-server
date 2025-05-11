# 📦 Quote MCP Server

A Model Control Protocol (MCP) server built with **FastAPI** that manages the full lifecycle of quote processing:
- 🕸️ Scraping quotes from QuoteFancy
- 📊 Structuring quotes by author
- 🧠 Generating metadata using Azure OpenAI
- ☁️ Uploading results to Azure Blob Storage
- 🖼️ Downloading images and uploading to AWS S3 + CDN transformation
- 📅 Merging metadata back into the dataset

---

## 🚀 How to Run

```bash
# Step 1: Clone the repo
$ git clone https://github.com/Iamkrmayank/quote-mcp-server
$ cd quote-mcp-server

# Step 2: Create virtual environment and install dependencies
$ python -m venv env
$ source env/bin/activate  # On Windows: env\Scripts\activate
$ pip install -r requirements.txt

# Step 3: Run the server
$ uvicorn main:app --reload
```

Server will start at `http://127.0.0.1:8000`

---

## 📘 API Endpoints

### 🕸️ `/quotes/scrape`
**Method**: POST  
**Description**: Scrape quotes from QuoteFancy.
```json
{
  "urls": ["https://quotefancy.com/author-name"],
  "max_pages": 5
}
```

### 🧠 `/metadata/generate`
**Method**: POST  
**Description**: Generate metadata using Azure OpenAI.  
**Payload**: Base64-encoded CSV containing quote blocks.
```json
{
  "csv_base64": "..."
}
```

### 📦 `/azure/fetch-result`
**Method**: POST  
**Description**: Retrieve Azure batch result and upload to Blob Storage.
```json
{
  "tracking_json": "..."  # base64 encoded
}
```

### 🖼️ `/images/download-upload-transform`
**Method**: POST  
**Description**: Download images, upload to S3, and generate transformed CDN URLs.
```json
{
  "keywords": ["cat", "dog"],
  "count": 5
}
```

### 📅 `/merge/merge`
**Method**: POST  
**Description**: Merge structured CSV and metadata from JSONL.
```json
{
  "csv_base64": "...",
  "jsonl_base64": "..."
}
```

---

## 🔐 Secrets & Credentials
Store the following securely in environment variables or a secrets manager:
- `AZURE_OPENAI_API_KEY`
- `AZURE_BLOB_CONNECTION_STRING`
- `AZURE_BLOB_ACCOUNT_KEY`
- `AWS_ACCESS_KEY`
- `AWS_SECRET_KEY`

You can load these with `.env` or through your CI/CD secrets.

---

## 📂 Project Structure
```
mcp_server/
├── main.py
├── routers/
│   ├── quotes.py
│   ├── metadata.py
│   ├── azure.py
│   ├── images.py
│   └── merge.py
├── services/
│   ├── quote_scraper.py
│   ├── azure_batch.py
│   ├── s3_uploader.py
│   └── utils.py
├── models/
│   └── schemas.py
├── requirements.txt
└── README.md
```

---

## 🧪 Testing
Use Swagger UI for testing endpoints:
```
http://127.0.0.1:8000/docs
```

---

## 🛠️ Future Improvements
- Add job queuing with Celery
- Add authentication
- Add Redis caching for batch status
- Add logging middleware

---

## 👨‍💻 Author
Built by **Kumar Mayank** ✨

---

## 📄 License
MIT License

# main.py
from fastapi import FastAPI
from routers import quotes, metadata, azure, images, merge, structure
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

app = FastAPI(title="Quote MCP Server", version="1.0")

app.include_router(quotes.router, prefix="/quotes")
app.include_router(metadata.router, prefix="/metadata")
app.include_router(azure.router, prefix="/azure")
app.include_router(images.router, prefix="/images")
app.include_router(merge.router, prefix="/merge")
app.include_router(structure.router, prefix="/quotes")

@app.get("/")
def root():
    return {"message": "Welcome to the Quote MCP Server"}
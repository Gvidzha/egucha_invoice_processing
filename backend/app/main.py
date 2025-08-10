"""
FastAPI aplikācijas galvenais fails
Satur aplikācijas konfigurāciju, middleware un galvenos maršrutus
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Importēt API maršrutus
from app.api import upload, process, preview, history
# Atkomentējam corrections un products API endpoints
from app.api import corrections, products

# Importēt datubāzes konfigurāciju
from app.database import engine, create_tables

app = FastAPI(
    title="Invoice Processing API",
    description="Pavadzīmju apstrādes sistēma ar OCR",
    version="1.0.0"
)

# CORS konfigurācija priekš frontend savienojuma
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://165.232.112.180",
        "http://localhost",
        "http://localhost:8080"
    ],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static failu servēšana (uploads directory)
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Pievienot API maršrutus
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(process.router, prefix="/api/v1", tags=["process"])
app.include_router(preview.router, prefix="/api/v1", tags=["preview"])
app.include_router(history.router, prefix="/api/v1", tags=["history"])
# Atkomentējam corrections un products API endpoints
app.include_router(corrections.router, prefix="/api/v1", tags=["corrections"])
app.include_router(products.router, prefix="/api/v1", tags=["products"])

@app.get("/")
async def root():
    """Saknes endpoint - API status pārbaude"""
    return {
        "message": "Invoice Processing API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Datubāzes inicializācija pie aplikācijas startēšanas
@app.on_event("startup")
async def startup_event():
    create_tables()

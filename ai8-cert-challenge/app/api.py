"""
FastAPI backend for Scout - School Events Assistant
Minimal API wrapper around existing agent functionality
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from pathlib import Path
import sys
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PDF_DIR
from app.agent import ask
from app.tools import ensure_prepared
from app.rag import index_health_check, build_rag_index_from_folder

app = FastAPI(title="Scout API", version="1.0.0")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://*.vercel.app",   # Vercel deployments
        "*"  # Allow all (remove this in production for security)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    openai_api_key: str
    cohere_api_key: str = ""
    use_reranking: bool = False

class ChatResponse(BaseModel):
    response: str
    error: str = ""

class HealthCheckResponse(BaseModel):
    status: str
    details: dict = {}

class PrepareDataResponse(BaseModel):
    status: str
    message: str

class BuildIndexResponse(BaseModel):
    status: str
    message: str
    details: dict = {}

class UploadResponse(BaseModel):
    status: str
    filename: str
    message: str

class ListFilesResponse(BaseModel):
    files: list
    count: int

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Scout API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        # Set API keys
        if not request.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        
        os.environ["OPENAI_API_KEY"] = request.openai_api_key
        
        if request.cohere_api_key:
            os.environ["COHERE_API_KEY"] = request.cohere_api_key
        
        # Get response from agent
        response = ask(request.message, PDF_DIR, use_reranking=request.use_reranking)
        
        return ChatResponse(response=response)
    
    except Exception as e:
        return ChatResponse(response="", error=str(e))

@app.post("/api/prepare", response_model=PrepareDataResponse)
async def prepare_data(openai_api_key: str):
    """Prepare data (extract events and build index)"""
    try:
        if not openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        ensure_prepared(PDF_DIR)
        
        return PrepareDataResponse(
            status="success",
            message="Data prepared successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/build-index", response_model=BuildIndexResponse)
async def build_index(openai_api_key: str):
    """Build RAG index"""
    try:
        if not openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        result = build_rag_index_from_folder(PDF_DIR)
        
        return BuildIndexResponse(
            status="success",
            message="RAG index built successfully",
            details=result
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Check RAG index health"""
    try:
        health_status = index_health_check()
        # Ensure health_status is a dict
        if health_status is None:
            health_status = {"message": "Index not yet built"}
        return HealthCheckResponse(
            status="ok",
            details=health_status if isinstance(health_status, dict) else {"message": str(health_status)}
        )
    
    except Exception as e:
        return HealthCheckResponse(
            status="error",
            details={"error": str(e)}
        )

@app.post("/api/upload", response_model=UploadResponse)
async def upload_newsletter(file: UploadFile = File(...)):
    """Upload a newsletter PDF"""
    try:
        print(f"📤 Received upload request for: {file.filename}")
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Create newsletters directory if it doesn't exist
        newsletters_dir = Path(PDF_DIR)
        newsletters_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Saving to directory: {newsletters_dir}")
        
        # Save the file
        file_path = newsletters_dir / file.filename
        print(f"💾 Writing file to: {file_path}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = file_path.stat().st_size / 1024 / 1024
        print(f"✅ Upload complete! File size: {file_size:.2f} MB")
        
        return UploadResponse(
            status="success",
            filename=file.filename,
            message=f"File '{file.filename}' uploaded successfully. Click 'Prepare Data' to process it."
        )
    
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files", response_model=ListFilesResponse)
async def list_files():
    """List all uploaded newsletter files"""
    try:
        newsletters_dir = Path(PDF_DIR)
        if not newsletters_dir.exists():
            return ListFilesResponse(files=[], count=0)
        
        files = [f.name for f in newsletters_dir.glob("*.pdf")]
        return ListFilesResponse(files=sorted(files), count=len(files))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """Delete a newsletter file"""
    try:
        file_path = Path(PDF_DIR) / filename
        
        # Security: prevent path traversal
        if not file_path.is_relative_to(Path(PDF_DIR)):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path.unlink()
        
        return {
            "status": "success",
            "message": f"File '{filename}' deleted successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


"""
DataContractIQ FastAPI Application
Main entry point for the backend API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DataContractIQ API",
    description="AI-powered data contract generation and drift detection using IBM Bob",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DataContractIQ API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DataContractIQ",
        "version": "1.0.0"
    }

# Include API routers
from app.api import schema, contracts

app.include_router(schema.router, prefix="/api/schema", tags=["schema"])
app.include_router(contracts.router, prefix="/api", tags=["contracts"])

# TODO: Include additional routers when implemented
# from app.api import drift
# app.include_router(drift.router, prefix="/api/drift", tags=["drift"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import psycopg2
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    port: int = 8080
    database_url: Optional[str] = None
    data_path: str = "/app/data"
    
    class Config:
        env_file = ".env"

class HealthResponse(BaseModel):
    status: str
    service: str
    port: int
    database: Optional[str] = None
    data_directory: Optional[str] = None
    database_error: Optional[str] = None
    data_directory_error: Optional[str] = None

class ConfigResponse(BaseModel):
    port: int
    database_url: str
    data_path: str
    message: str

class AnalysisRequest(BaseModel):
    demo_id: str
    analysis_type: str = "basic"

class AnalysisResponse(BaseModel):
    demo_id: str
    analysis_type: str
    status: str
    results: Dict[str, Any]
    message: str

class AnalysisService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_connection = None
        
        # Initialize data directory
        self._ensure_data_directory()
        
        # Initialize database connections
        self._init_connections()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        try:
            Path(self.settings.data_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Data directory ready: {self.settings.data_path}")
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")
            raise
    
    def _init_connections(self):
        """Initialize database connections"""
        # PostgreSQL connection
        if self.settings.database_url:
            try:
                self.db_connection = psycopg2.connect(self.settings.database_url)
                logger.info("Successfully connected to PostgreSQL")
            except Exception as e:
                logger.warning(f"Could not connect to PostgreSQL: {e}")
    
    def check_health(self) -> HealthResponse:
        """Check service health"""
        response = HealthResponse(
            status="healthy",
            service="analysis-service",
            port=self.settings.port
        )
        
        # Check PostgreSQL connection
        if self.db_connection:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                response.database = "healthy"
            except Exception as e:
                response.database = "unhealthy"
                response.database_error = str(e)
                response.status = "unhealthy"
        else:
            response.database = "not_configured"
        
        # Check data directory
        try:
            if not Path(self.settings.data_path).exists():
                raise FileNotFoundError(f"Data directory does not exist: {self.settings.data_path}")
            response.data_directory = "healthy"
        except Exception as e:
            response.data_directory = "unhealthy"
            response.data_directory_error = str(e)
            response.status = "unhealthy"
        
        return response
    
    def get_config(self) -> ConfigResponse:
        """Get service configuration"""
        return ConfigResponse(
            port=self.settings.port,
            database_url="configured (masked for security)" if self.settings.database_url else "not configured",
            data_path=self.settings.data_path,
            message="Analysis service is running and reading configuration from environment variables"
        )
    
    def run_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """Run analysis on demo data"""
        logger.info(f"Running {request.analysis_type} analysis for demo {request.demo_id}")
        
        # Placeholder implementation
        # In a real implementation, this would:
        # 1. Load parquet files from data_path using pandas
        # 2. Use pandas for data manipulation and analysis
        # 3. Return structured results
        
        try:
            # Simulate analysis using pandas
            demo_file_pattern = f"{self.settings.data_path}/{request.demo_id}*.parquet"
            
            # Placeholder results
            results = {
                "demo_id": request.demo_id,
                "total_rounds": 30,
                "total_kills": 145,
                "average_round_time": 95.5,
                "map_name": "de_dust2",
                "winner": "terrorist",
                "score": {"terrorist": 16, "counter_terrorist": 14},
                "top_players": [
                    {"name": "Player1", "kills": 25, "deaths": 18, "assists": 5},
                    {"name": "Player2", "kills": 22, "deaths": 20, "assists": 8},
                    {"name": "Player3", "kills": 20, "deaths": 19, "assists": 6}
                ]
            }
            
            return AnalysisResponse(
                demo_id=request.demo_id,
                analysis_type=request.analysis_type,
                status="completed",
                results=results,
                message=f"Successfully completed {request.analysis_type} analysis"
            )
            
        except Exception as e:
            logger.error(f"Analysis failed for demo {request.demo_id}: {e}")
            return AnalysisResponse(
                demo_id=request.demo_id,
                analysis_type=request.analysis_type,
                status="failed",
                results={},
                message=f"Analysis failed: {str(e)}"
            )
    
    def list_available_demos(self) -> Dict[str, Any]:
        """List available demo files for analysis"""
        try:
            data_path = Path(self.settings.data_path)
            parquet_files = list(data_path.glob("*.parquet"))
            
            demos = []
            for file in parquet_files:
                stat = file.stat()
                demos.append({
                    "name": file.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "path": str(file)
                })
            
            return {
                "demos": demos,
                "count": len(demos),
                "data_path": str(data_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to list demos: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list demos: {str(e)}")

# Global settings and service instance
settings = Settings()
analysis_service = AnalysisService(settings)

# FastAPI app
app = FastAPI(
    title="StratagemForge Analysis Service",
    description="Counterstrike 2 demo analysis service using FastAPI and pandas",
    version="1.0.0"
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    health = analysis_service.check_health()
    status_code = 200 if health.status == "healthy" else 503
    return JSONResponse(content=health.dict(), status_code=status_code)

@app.get("/ready")
async def ready_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "analysis-service"}

@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get service configuration"""
    return analysis_service.get_config()

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_demo(request: AnalysisRequest):
    """Run analysis on a demo"""
    return analysis_service.run_analysis(request)

@app.get("/demos")
async def list_demos():
    """List available demos for analysis"""
    return analysis_service.list_available_demos()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "analysis-service",
        "status": "running",
        "message": "StratagemForge Analysis Service - Counterstrike 2 demo analysis using FastAPI and pandas",
        "endpoints": {
            "health": "/health",
            "ready": "/ready", 
            "config": "/config",
            "analyze": "/analyze",
            "demos": "/demos",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Analysis Service...")
    logger.info(f"Configuration: Port={settings.port}, DataPath={settings.data_path}")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=settings.port, 
        log_level="info"
    )
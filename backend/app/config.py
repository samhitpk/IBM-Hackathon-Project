"""
Configuration management for DataContractIQ
"""
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "DataContractIQ"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://sree@localhost:5432/pagila"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173"]
    
    # File Paths - Use absolute paths
    contracts_dir: str = str(Path(__file__).parent.parent.parent / "data" / "contracts")
    snapshots_dir: str = str(Path(__file__).parent.parent.parent / "data" / "snapshots")
    sql_file_path: str = str(Path(__file__).parent.parent.parent / "GreenCycleBikes" / "pagila-master" / "pagila-insert-data.sql")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Made with Bob

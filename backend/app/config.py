"""
Configuration management for DataContractIQ
"""
from pydantic_settings import BaseSettings
from typing import List


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
    
    # File Paths
    contracts_dir: str = "../data/contracts"
    snapshots_dir: str = "../data/snapshots"
    sql_file_path: str = "../GreenCycleBikes/pagila-master/pagila-insert-data.sql"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Made with Bob

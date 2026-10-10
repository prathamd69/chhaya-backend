from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Chhaya Backend"
    API_PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = False
    
    # AWS & S3 Settings
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET: str = "chhaya-delhi"
    S3_CELLS_KEY: str = "features/cells.geojson"
    REFRESH_SECONDS: int = 30

    # Comma-separated list of allowed frontend origins, or "*" for all
    CORS_ORIGINS: str = "*"
    
    # PostgreSQL Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "chhaya"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "chhaya_db"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
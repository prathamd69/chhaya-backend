from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Chhaya Backend"
    API_PORT: int = 8000
    
    # AWS & S3 Settings
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET: str = "your-bucket-name-here"
    S3_CELLS_KEY: str = "features/cells.geojson"
    
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
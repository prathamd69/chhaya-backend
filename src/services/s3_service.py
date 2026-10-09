import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pathlib import Path
from src.core.config import settings

logger = logging.getLogger(__name__)

# Global variable to hold our loaded data in memory
cell_data = None

def load_data():
    """
    Attempts to load cells.geojson from S3 on startup.
    Falls back to local mock_cells.geojson if S3 fails or is not configured.
    """
    global cell_data
    
    mock_path = Path("contract/mock_cells.geojson")
    
    # Try S3 first if a bucket is configured
    if settings.S3_BUCKET and settings.S3_BUCKET != "your-bucket-name-here":
        try:
            logger.info(f"Attempting to load {settings.S3_CELLS_KEY} from S3 bucket {settings.S3_BUCKET}...")
            
            # Since the EC2 box uses an IAM role, boto3 automatically picks up the credentials[cite: 2]
            s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
            response = s3_client.get_object(Bucket=settings.S3_BUCKET, Key=settings.S3_CELLS_KEY)
            file_content = response['Body'].read().decode('utf-8')
            
            cell_data = json.loads(file_content)
            logger.info("Successfully loaded cells data from S3.")
            return
            
        except (BotoCoreError, ClientError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load from S3: {e}. Falling back to mock data.")

    # Fallback to local mock data
    logger.info("Loading fallback mock data from local contract folder...")
    if mock_path.exists():
        with open(mock_path, "r") as f:
            cell_data = json.load(f)
    else:
        logger.error("Mock data file not found! API will serve empty data.")
        cell_data = {"type": "FeatureCollection", "features": []}

def get_cell_data():
    """Accessor for the loaded data."""
    if cell_data is None:
        load_data()
    return cell_data
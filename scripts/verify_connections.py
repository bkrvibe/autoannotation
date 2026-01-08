import sys
import os
import logging
from pprint import pprint

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.airflow import AirflowService
from app.services.gcs import GCSService
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_airflow():
    print("\n--- Checking Airflow Connection ---")
    print(f"URL: {settings.AIRFLOW_BASE_URL}")
    try:
        service = AirflowService()
        dags = service.list_dags()
        print(f"✅ Success! Found {len(dags)} DAGs.")
        for dag in dags[:3]: # Show first 3
            print(f"  - {dag.get('dag_id')} ({dag.get('is_paused') and 'Paused' or 'Active'})")
    except Exception as e:
        print(f"❌ Airflow Failed: {e}")

def check_gcs():
    print("\n--- Checking GCS Connection ---")
    print(f"Bucket: {settings.GCS_BUCKET}")
    try:
        service = GCSService()
        # List blobs in the root or a known prefix
        # We'll just try to list the first few blobs to ensure read access
        blobs = list(service.client.list_blobs(settings.GCS_BUCKET, max_results=5))
        print(f"✅ Success! Bucket accessible.")
        print("First 5 files:")
        for blob in blobs:
            print(f"  - {blob.name}")
            
        # Optional: Check write access?
        # print("Checking write access...")
        # service.upload_file("README.md", "connection_check.txt")
        # print("✅ Write success.")
        
    except Exception as e:
        print(f"❌ GCS Failed: {e}")

if __name__ == "__main__":
    check_airflow()
    check_gcs()

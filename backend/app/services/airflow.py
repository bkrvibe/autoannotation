import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import requests
from app.core.config import settings

class DAGRunState(Enum):
    """Possible states of a DAG run."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"

class AirflowService:
    """Service for interacting with Airflow REST API."""
    
    def __init__(self):
        """Initialize the Airflow service."""
        self.base_url = settings.AIRFLOW_BASE_URL.rstrip("/")
        self.token = settings.AIRFLOW_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request to Airflow API."""
        url = f"{self.base_url}{endpoint}"
        # Set default timeout to 30 seconds if not provided
        kwargs.setdefault("timeout", 30)
        response = requests.request(method, url, headers=self.headers, **kwargs)
        return response
    
    def list_dags(self) -> list:
        """List all DAGs."""
        # Increase limit to capture all DAGs (default is often 100 or less)
        response = self._make_request("GET", "/api/v2/dags?limit=200")
        if response.status_code != 200:
            print(f"Error listing DAGs: {response.status_code} {response.text}")
            return []
        return response.json().get("dags", [])

    def trigger_dag(
        self,
        dag_id: str,
        gcs_path: str,
        additional_conf: Optional[Dict[str, Any]] = None,
        use_gcp_path: bool = False
    ) -> Dict[str, Any]:
        """
        Trigger a DAG run.
        """
        # Generate run ID
        now = datetime.utcnow()
        run_id = f"run_{now.strftime('%Y%m%dT%H%M%S')}"
        logical_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Build configuration
        path_key = "gcp_path" if use_gcp_path else "gcs_path"
        conf = {
            path_key: gcs_path,
        }
        
        if additional_conf:
            conf.update(additional_conf)
        
        # Payload
        payload = {
            "dag_run_id": run_id,
            "logical_date": logical_date,
            "conf": conf
        }
        
        endpoint = f"/api/v2/dags/{dag_id}/dagRuns"
        response = self._make_request("POST", endpoint, json=payload)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to trigger DAG ({response.status_code}): {response.text}")
        
        data = response.json()
        return {
            "dag_id": dag_id,
            "dag_run_id": run_id,
            "state": data.get("state", "queued"),
            "logical_date": logical_date
        }

    def get_dag_run_status(self, dag_id: str, dag_run_id: str) -> Dict[str, Any]:
        """Get status of a specific DAG run."""
        endpoint = f"/api/v2/dags/{dag_id}/dagRuns/{dag_run_id}"
        response = self._make_request("GET", endpoint)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get status: {response.text}")
            
        data = response.json()
        return {
            "dag_id": dag_id,
            "dag_run_id": dag_run_id,
            "state": data.get("state", "unknown"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date")
        }

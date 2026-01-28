import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from enum import Enum
import requests
from app.core.config import settings

if TYPE_CHECKING:
    from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


class DAGRunState(Enum):
    """Possible states of a DAG run."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"


def get_secret_from_manager(secret_id: str) -> Optional[str]:
    """
    Retrieve a secret from GCP Secret Manager.
    """
    try:
        from google.cloud import secretmanager

        project_id = settings.GCP_PROJECT_ID
        if not project_id:
            logger.warning("GCP_PROJECT_ID not configured")
            return None

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    except ImportError:
        logger.warning("google-cloud-secret-manager not installed")
        return None
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_id}: {e}")
        return None


def get_default_airflow_token() -> Optional[str]:
    """
    Get the default Airflow token, preferring Secret Manager over env variable.
    """
    # First try Secret Manager
    if settings.AIRFLOW_TOKEN_SECRET_ID:
        token = get_secret_from_manager(settings.AIRFLOW_TOKEN_SECRET_ID)
        if token:
            return token

    # Fall back to env variable (deprecated)
    return settings.AIRFLOW_TOKEN


def get_tenant_airflow_token(tenant: "Tenant") -> Optional[str]:
    """
    Retrieve Airflow token for a tenant from GCP Secret Manager.
    Falls back to default token if not available.
    """
    if not tenant.airflow_token_secret_id:
        return None

    return get_secret_from_manager(tenant.airflow_token_secret_id)


def get_airflow_service_for_tenant(tenant: "Tenant") -> "AirflowService":
    """
    Get an AirflowService configured for a specific tenant.
    Uses tenant's dedicated token if available, otherwise falls back to default.
    """
    token = get_tenant_airflow_token(tenant)
    
    if token:
        return AirflowService(token=token)
    else:
        # Fall back to default token
        return AirflowService()


class AirflowService:
    """Service for interacting with Airflow REST API."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Airflow service.

        Args:
            token: Optional Airflow API token. If not provided, fetches from Secret Manager.
        """
        self.base_url = settings.AIRFLOW_BASE_URL.rstrip("/")
        self.token = token or get_default_airflow_token()
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

    def get_xcom_value(
        self,
        dag_id: str,
        dag_run_id: str,
        task_id: str,
        xcom_key: str = "return_value"
    ) -> Any:
        """
        Get XCom value from a task.
        
        Args:
            dag_id: The DAG ID
            dag_run_id: The DAG run ID
            task_id: The task ID
            xcom_key: The XCom key (default: return_value)
            
        Returns:
            The XCom value
        """
        endpoint = f"/api/v2/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/xcomEntries/{xcom_key}"
        response = self._make_request("GET", endpoint)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        return data.get("value")

    def get_task_instances(self, dag_id: str, dag_run_id: str) -> list:
        """
        Get all task instances for a DAG run.
        
        Args:
            dag_id: The DAG ID
            dag_run_id: The DAG run ID
            
        Returns:
            List of task instance dictionaries
        """
        endpoint = f"/api/v2/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
        response = self._make_request("GET", endpoint)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data.get("task_instances", [])

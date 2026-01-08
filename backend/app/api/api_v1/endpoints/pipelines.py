from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.schemas.pipeline import Pipeline, PipelineDetail
from app.schemas.user import User
from app.services.airflow import AirflowService

router = APIRouter()

def _get_generic_conf_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "generic_param": {
                "type": "string",
                "default": "default_value",
                "title": "Generic Parameter"
            }
        }
    }

def _get_generic_conf_defaults() -> Dict[str, Any]:
    return {"generic_param": "default_value"}

@router.get("/", response_model=List[PipelineDetail])
def read_pipelines(
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve available active pipelines from Airflow.
    """
    try:
        service = AirflowService()
        dags = service.list_dags()
    except Exception as e:
        # Fallback or error handling
        print(f"Error fetching DAGs: {e}")
        return []

    pipelines = []
    
    # Filter for active DAGs only
    active_dags = [d for d in dags if not d.get("is_paused")]

    for dag in active_dags:
        # Extract tags if available; Airflow tags are usually a list of dicts [{'name': 'tag1'}]
        tags_raw = dag.get("tags", [])
        tags = [t.get("name") for t in tags_raw] if tags_raw else []

        pipeline = {
            "id": dag.get("dag_id"),
            "airflow_dag_id": dag.get("dag_id"),
            "display_name": dag.get("dag_id"), # Or dag_display_name if available
            "description": dag.get("description") or "Imported from Airflow",
            "tags": tags,
            "input_type": "mixed", # Default unknown
            "version": "1.0.0",
            "enabled": True,
            "conf_schema": _get_generic_conf_schema(),
            "conf_defaults": _get_generic_conf_defaults()
        }
        pipelines.append(pipeline)

    return pipelines[skip : skip + limit]

@router.get("/{pipeline_id}", response_model=PipelineDetail)
def read_pipeline(
    pipeline_id: str,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get pipeline details by ID (fetches fresh from Airflow to ensure it exists/is active).
    """
    # Simply reuse the list logic for MVP, or call specific DAG endpoint.
    # calling list is safer against partial implementation in service
    pipelines = read_pipelines(current_user=current_user, skip=0, limit=1000)
    for p in pipelines:
        if p["id"] == pipeline_id:
            return p
            
    raise HTTPException(status_code=404, detail="Pipeline not found or not active")

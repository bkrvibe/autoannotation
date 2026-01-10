from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.schemas.pipeline import Pipeline, PipelineDetail
from app.schemas.user import User
from app.services.airflow import AirflowService
import yaml
import os
from pathlib import Path

router = APIRouter()

# Map DAG IDs to config directories and display info
PIPELINE_CONFIG_MAP = {
    'image_auto_annotation_2d': {
        'config_dir': '2d_detection',
        'config_file': 'config_multi_class_detection.yaml',
        'display_name': '2D Object Detection',
        'description': 'Multi-class object detection using GroundingDINO with CLIP classification',
        'category': '2D'
    },
    'image_auto_annotation_2d_segmentation': {
        'config_dir': '2d_segmentation',
        'config_file': 'config_segmentation.yaml',
        'display_name': '2D Instance Segmentation',
        'description': 'Instance segmentation using SAM2 with bounding box prompts',
        'category': '2D'
    },
    'image_auto_annotation_2d_semantic_segmentation': {
        'config_dir': '2d_semantic_segmentation',
        'config_file': 'config_semantic_segmentation.yaml',
        'display_name': '2D Semantic Segmentation',
        'description': 'Semantic segmentation using Mask2Former/OneFormer on Cityscapes classes',
        'category': '2D'
    },
    'image_auto_annotation_2d_tracking': {
        'config_dir': '2d_tracking',
        'config_file': 'config_tracking.yaml',
        'display_name': '2D Object Tracking',
        'description': 'Multi-object tracking with appearance features and Kalman filtering',
        'category': '2D'
    },
    'auto_annotation_pipeline_dynamic': {
        'config_dir': None,  # No config file for 3D pipeline
        'config_file': None,
        'display_name': '3D Object Detection & Tracking',
        'description': 'Automated 3D object detection and tracking for LiDAR point cloud data',
        'category': '3D'
    }
}

# Get the autoann_confs directory (relative to workspace root)
CONF_BASE_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "autoann_confs"


def _load_yaml_config(dag_id: str) -> Dict[str, Any]:
    """Load YAML config for a DAG and extract threshold fields."""
    config_info = PIPELINE_CONFIG_MAP.get(dag_id)
    if not config_info or not config_info.get('config_dir'):
        return {}
    
    config_path = CONF_BASE_DIR / config_info['config_dir'] / config_info['config_file']
    
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            full_config = yaml.safe_load(f)
        return full_config or {}
    except Exception as e:
        print(f"Error loading config {config_path}: {e}")
        return {}


def _extract_threshold_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract fields that contain 'threshold' in their name from the config."""
    thresholds = {}
    
    def find_thresholds(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if 'threshold' in key.lower() or 'confidence' in key.lower():
                    thresholds[full_key] = value
                elif isinstance(value, dict):
                    find_thresholds(value, full_key)
    
    find_thresholds(config)
    return thresholds


def _get_pipeline_info(dag_id: str) -> Dict[str, Any]:
    """Get display info and config for a pipeline."""
    config_info = PIPELINE_CONFIG_MAP.get(dag_id, {})
    full_config = _load_yaml_config(dag_id)
    threshold_fields = _extract_threshold_fields(full_config)
    
    return {
        'display_name': config_info.get('display_name', dag_id),
        'description': config_info.get('description', 'Imported from Airflow'),
        'category': config_info.get('category', '2D'),
        'full_config': full_config,
        'threshold_fields': threshold_fields
    }

@router.get("/", response_model=List[PipelineDetail])
def read_pipelines(
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve available active pipelines from Airflow with their configs.
    """
    try:
        service = AirflowService()
        dags = service.list_dags()
    except Exception as e:
        print(f"Error fetching DAGs: {e}")
        return []

    pipelines = []
    
    # Filter for active DAGs only
    active_dags = [d for d in dags if not d.get("is_paused")]

    for dag in active_dags:
        dag_id = dag.get("dag_id")
        
        # Get pipeline info including config
        pipeline_info = _get_pipeline_info(dag_id)
        
        # Extract tags
        tags_raw = dag.get("tags", [])
        tags = [t.get("name") for t in tags_raw] if tags_raw else []
        
        # Add category tag if not already present
        category = pipeline_info.get('category', '2D')
        if category not in tags:
            tags = [category] + tags

        pipeline = {
            "id": dag_id,
            "airflow_dag_id": dag_id,
            "display_name": pipeline_info.get('display_name', dag_id),
            "description": pipeline_info.get('description', dag.get("description") or "Imported from Airflow"),
            "tags": tags,
            "input_type": "lidar" if category == "3D" else "image",
            "version": "1.0.0",
            "enabled": True,
            "conf_schema": {"threshold_fields": pipeline_info.get('threshold_fields', {})},
            "conf_defaults": pipeline_info.get('full_config', {})
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

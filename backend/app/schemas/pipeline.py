from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class PipelineBase(BaseModel):
    id: str
    airflow_dag_id: str
    display_name: str
    description: Optional[str] = None
    tags: List[str] = []
    input_type: str  # images | zip | pointcloud | mixed
    version: str = "1.0.0"
    enabled: bool = True

class Pipeline(PipelineBase):
    # For the list view, we might not need the full schema/defaults
    pass

class PipelineDetail(PipelineBase):
    # Full details including config schema for the UI form
    conf_schema: Dict[str, Any] = {}
    conf_defaults: Dict[str, Any] = {}

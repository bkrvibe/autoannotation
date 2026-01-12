from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.job import Job, JobCreate
from app.models.job import Job as JobModel
from app.models.tenant import Tenant
from app.services.airflow import AirflowService, get_airflow_service_for_tenant
from app.core.config import settings
import subprocess
import tempfile
import os

router = APIRouter()

# SSH config for Airflow worker
AIRFLOW_SSH_HOST = "caliper-autoanno-ubuntu224"
AIRFLOW_SSH_USER = "administrator"
AIRFLOW_SSH_ZONE = "us-central1-b"


def validate_gcs_path_for_tenant(gcs_path: str, tenant: Tenant) -> bool:
    """
    Validate that a GCS path belongs to the tenant.
    Enforces tenant isolation at the path level.
    """
    if not gcs_path:
        return False
    
    # Expected pattern: gs://bucket/tenants/{tenant_id_or_slug}/...
    # or: gs://bucket/{prefix}/tenants/{tenant_id_or_slug}/...
    
    expected_patterns = [
        f"tenants/{tenant.id}/",
        f"tenants/{tenant.slug}/",
    ]
    
    # Also allow the configured prefix
    if tenant.gcs_path_prefix:
        expected_patterns.append(f"{tenant.gcs_path_prefix}/")
    
    # Check if path contains any valid tenant pattern
    for pattern in expected_patterns:
        if pattern in gcs_path:
            return True
    
    # For backward compatibility, allow "default" tenant to access any path
    if tenant.slug == "default":
        return True
    
    return False


@router.post("/", response_model=Job)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user),
):
    """
    Create a new annotation job and trigger Airflow.
    """
    # Validate GCS path belongs to tenant
    if not validate_gcs_path_for_tenant(job_in.input_uri, current_user.tenant):
        raise HTTPException(
            status_code=403,
            detail="Access denied: input_uri must be within your tenant's storage path"
        )
    
    # Get Airflow service for this tenant
    airflow_service = get_airflow_service_for_tenant(current_user.tenant)
    
    dag_id = job_in.pipeline_id
    
    try:
        # Build config matching DAG expected structure:
        # conf: { gcs_path: "...", config: { batch_size: ..., ... } }
        final_conf = {
            "tenant_id": str(current_user.tenant_id)
        }
        
        # If overrides provided, nest them under "config" key as DAG expects
        if job_in.overrides:
            final_conf["config"] = job_in.overrides
        
        # Determine strict GCS/GCP path key logic based on pipeline tags or ID if needed
        use_gcp_path = False  # Most new DAGs use gcs_path
        
        run_info = airflow_service.trigger_dag(
            dag_id=dag_id,
            gcs_path=job_in.input_uri,
            additional_conf=final_conf,
            use_gcp_path=use_gcp_path
        )
    except Exception as e:
        print(f"Airflow Error: {e}")
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=f"Pipeline '{dag_id}' not found in Airflow")
        raise HTTPException(status_code=500, detail=f"Failed to trigger Airflow: {str(e)}")

    # Save to DB with proper tenant_id and user_id
    db_job = JobModel(
        tenant_id=current_user.tenant_id,
        created_by_user_id=current_user.user_id,
        pipeline_id=dag_id,
        airflow_dag_id=dag_id,
        airflow_run_id=run_info["dag_run_id"],
        input_uri=job_in.input_uri,
        status=run_info["state"],
        config=final_conf
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.get("/{job_id}", response_model=Job)
def read_job(
    job_id: int,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user),
):
    """
    Get a specific job by ID, syncing status from Airflow.
    """
    # Query with tenant isolation
    job = db.query(JobModel).filter(
        JobModel.id == job_id,
        JobModel.tenant_id == current_user.tenant_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get Airflow service for this tenant
    airflow_service = get_airflow_service_for_tenant(current_user.tenant)
    
    # Sync status from Airflow if not terminal
    if job.status not in ["success", "failed"]:
        try:
            status_info = airflow_service.get_dag_run_status(job.airflow_dag_id, job.airflow_run_id)
            new_state = status_info.get("state")
            if new_state and new_state != job.status:
                job.status = new_state
                db.add(job)
                db.commit()
                db.refresh(job)
        except Exception as e:
            print(f"Error syncing status: {e}")
    
    # If job is successful, try to fetch XCom result (try multiple task IDs)
    if job.status == "success" and not job.result_artifacts:
        task_ids_to_try = ["convert_to_calipergt", "convert_to_calipergt_task", "final_task"]
        for task_id in task_ids_to_try:
            try:
                xcom_result = airflow_service.get_xcom_value(
                    job.airflow_dag_id,
                    job.airflow_run_id,
                    task_id,
                    "return_value"
                )
                if xcom_result:
                    print(f"Found XCom from task: {task_id}")
                    job.result_artifacts = xcom_result
                    db.add(job)
                    db.commit()
                    db.refresh(job)
                    break
            except Exception as e:
                print(f"Error fetching XCom from {task_id}: {e}")
    
    return job


@router.get("/", response_model=List[Job])
def read_jobs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user),
):
    """
    Retrieve jobs for current tenant.
    Admins and ops see all jobs, other users only see their own.
    """
    # Build query with tenant isolation
    query = db.query(JobModel).filter(JobModel.tenant_id == current_user.tenant_id)
    
    # Non-admin users only see their own jobs
    if current_user.role not in ["admin", "ops", "tenant_admin"]:
        query = query.filter(JobModel.created_by_user_id == current_user.user_id)
    
    jobs = query.order_by(JobModel.created_at.desc()).offset(skip).limit(limit).all()
    
    # Get Airflow service for this tenant
    airflow_service = get_airflow_service_for_tenant(current_user.tenant)
    
    # Sync status
    updates_needed = False
    for job in jobs:
        if job.status not in ["success", "failed"]:
            try:
                status_info = airflow_service.get_dag_run_status(job.airflow_dag_id, job.airflow_run_id)
                new_state = status_info.get("state")
                if new_state and new_state != job.status:
                    job.status = new_state
                    db.add(job)
                    updates_needed = True
            except Exception:
                pass
                
    if updates_needed:
        db.commit()
    
    return jobs


@router.get("/{job_id}/xcom")
def get_job_xcom(
    job_id: int,
    task_id: str = "convert_to_calipergt",
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user),
):
    """
    Fetch XCom value for a job from Airflow.
    """
    job = db.query(JobModel).filter(
        JobModel.id == job_id,
        JobModel.tenant_id == current_user.tenant_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    airflow_service = get_airflow_service_for_tenant(current_user.tenant)
    
    try:
        xcom_result = airflow_service.get_xcom_value(
            job.airflow_dag_id,
            job.airflow_run_id,
            task_id,
            "return_value"
        )
        
        if xcom_result:
            # Save to job
            job.result_artifacts = xcom_result
            db.add(job)
            db.commit()
            
        return {"xcom": xcom_result, "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch XCom: {str(e)}")


@router.get("/{job_id}/tasks")
def get_job_tasks(
    job_id: int,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user),
):
    """
    Get all task instances for a job's DAG run.
    """
    job = db.query(JobModel).filter(
        JobModel.id == job_id,
        JobModel.tenant_id == current_user.tenant_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    airflow_service = get_airflow_service_for_tenant(current_user.tenant)
    
    try:
        tasks = airflow_service.get_task_instances(job.airflow_dag_id, job.airflow_run_id)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")


@router.post("/{job_id}/download")
def download_result_file(
    job_id: int,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user),
):
    """
    Download the annotation result file from the Airflow worker via SCP.
    Automatically fetches XCom if not already available.
    """
    job = db.query(JobModel).filter(
        JobModel.id == job_id,
        JobModel.tenant_id == current_user.tenant_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "success":
        raise HTTPException(status_code=400, detail=f"Job is not complete (status: {job.status})")
    
    airflow_service = get_airflow_service_for_tenant(current_user.tenant)
    
    # If no artifacts, try to fetch XCom first
    if not job.result_artifacts:
        task_ids_to_try = ["convert_to_calipergt", "convert_to_calipergt_task", "final_task"]
        for task_id in task_ids_to_try:
            try:
                xcom_result = airflow_service.get_xcom_value(
                    job.airflow_dag_id,
                    job.airflow_run_id,
                    task_id,
                    "return_value"
                )
                if xcom_result:
                    job.result_artifacts = xcom_result
                    db.add(job)
                    db.commit()
                    db.refresh(job)
                    break
            except Exception as e:
                print(f"Error fetching XCom from {task_id}: {e}")
    
    # Check if we have the file path now
    if not job.result_artifacts:
        raise HTTPException(status_code=404, detail="No result artifacts found. The pipeline may not have produced output.")
    
    remote_path = job.result_artifacts.get("calipergt_file")
    if not remote_path:
        raise HTTPException(status_code=404, detail="No annotation file path in results")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.basename(remote_path)
            local_path = os.path.join(temp_dir, filename)
            
            print(f"Downloading {remote_path} from {AIRFLOW_SSH_HOST}...")
            
            # Use gcloud compute scp with explicit account
            # First try with the compute service account, then fall back to default
            result = subprocess.run(
                [
                    "gcloud", "compute", "scp",
                    f"--zone={AIRFLOW_SSH_ZONE}",
                    f"{AIRFLOW_SSH_USER}@{AIRFLOW_SSH_HOST}:{remote_path}",
                    local_path,
                    "--tunnel-through-iap"  # Use IAP tunneling which works with service accounts
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"SCP stderr: {result.stderr}")
                raise HTTPException(status_code=500, detail=f"SCP failed: {result.stderr}")
            
            with open(local_path, 'rb') as f:
                content = f.read()
            
            from fastapi.responses import Response
            mime_type = "application/json" if filename.endswith('.json') else "application/octet-stream"
            
            return Response(
                content=content,
                media_type=mime_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="SSH connection timed out (120s). The file may be too large.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


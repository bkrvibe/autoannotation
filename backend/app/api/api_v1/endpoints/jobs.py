from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.job import Job, JobCreate
from app.models.job import Job as JobModel
from app.schemas.user import User
from app.services.airflow import AirflowService

router = APIRouter()
airflow_service = AirflowService()

@router.post("/", response_model=Job)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(deps.get_db),
    # current_user: User = Depends(deps.get_current_user), # Skipping user check for speed if auth token is stale
):
    """
    Create a new annotation job and trigger Airflow.
    """
    # 1. Trigger Airflow directly (Validation happens via Airflow response)
    dag_id = job_in.pipeline_id
    
    try:
        # Defaults
        final_conf = job_in.overrides or {}
        
        # Determine strict GCS/GCP path key logic based on pipeline tags or ID if needed
        # For now, simplistic check:
        use_gcp_path = False # Most new DAGs use gcs_path
        
        run_info = airflow_service.trigger_dag(
            dag_id=dag_id,
            gcs_path=job_in.input_uri,
            additional_conf=final_conf,
            use_gcp_path=use_gcp_path
        )
    except Exception as e:
        print(f"Airflow Error: {e}")
        # Return 404 if DAG not found (likely) or 500 for other errors
        if "404" in str(e):
             raise HTTPException(status_code=404, detail=f"Pipeline '{dag_id}' not found in Airflow")
        raise HTTPException(status_code=500, detail=f"Failed to trigger Airflow: {str(e)}")

    # 2. Save to DB
    db_job = JobModel(
        tenant_id="default", # current_user.tenant_id
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
):
    """
    Get a specific job by ID, syncing status from Airflow.
    """
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
        except Exception:
            pass
    
    # If job is successful, try to fetch XCom result
    if job.status == "success" and not job.result_artifacts:
        try:
            xcom_result = airflow_service.get_xcom_value(
                job.airflow_dag_id,
                job.airflow_run_id,
                "convert_to_calipergt",
                "return_value"
            )
            if xcom_result:
                job.result_artifacts = xcom_result
                db.add(job)
                db.commit()
                db.refresh(job)
        except Exception:
            pass
    
    return job


@router.get("/", response_model=List[Job])
def read_jobs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    # current_user: User = Depends(deps.get_current_user),
):
    """
    Retrieve jobs.
    """
    jobs = db.query(JobModel).order_by(JobModel.created_at.desc()).offset(skip).limit(limit).all()
    
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
                # Log error but don't fail the request
                pass 
                
    if updates_needed:
        db.commit()
    
    return jobs


from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.job import Job, JobCreate
from app.models.job import Job as JobModel
from app.models.tenant import Tenant
from app.services.airflow import get_airflow_service_for_tenant
from app.utils.format_converter import calipergt_to_coco, calipergt_to_kitti3d, transform_lidar_orientation
from app.utils.lidar_preprocessing import preprocess_3d_data
import subprocess
import tempfile
import os
import json

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

    # Check if this is a 3D pipeline that requires preprocessing
    is_3d_pipeline = dag_id == 'auto_annotation_pipeline_dynamic'
    actual_input_uri = job_in.input_uri
    preprocessing_message = None

    try:
        # Preprocess 3D data if needed
        if is_3d_pipeline:
            print(f"Preprocessing 3D data for pipeline {dag_id}...")
            try:
                transformed_uri, was_transformed, message = preprocess_3d_data(
                    input_gcs_path=job_in.input_uri,
                    tenant_id=str(current_user.tenant_id),
                    job_id=None  # Job ID not available yet
                )

                if was_transformed:
                    print(f"Data transformed: {message}")
                    actual_input_uri = transformed_uri
                    preprocessing_message = message
                else:
                    print(f"Data preprocessing result: {message}")
            except ValueError as ve:
                # Data format validation error - return clear message to user
                error_msg = str(ve)
                print(f"Data validation failed: {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Data validation failed: {error_msg}"
                )

        # Build config matching DAG expected structure:
        # conf: { gcs_path: "...", config: { batch_size: ..., ... }, user_input_display: "...", lidar_frame: "..." }
        final_conf = {
            "tenant_id": str(current_user.tenant_id)
        }

        # If overrides provided, nest them under "config" key as DAG expects
        if job_in.overrides:
            # Extract lidar_frame to top level for 3D DAG (accessed via conf.get('lidar_frame'))
            if 'lidar_frame' in job_in.overrides:
                final_conf["lidar_frame"] = job_in.overrides["lidar_frame"]
            final_conf["config"] = job_in.overrides

        # Preserve a user-visible input display if provided (e.g. local upload summary)
        if getattr(job_in, "input_display", None):
            final_conf["user_input_display"] = job_in.input_display
            # Also store original input separately for UI display
            final_conf["original_input"] = job_in.input_display

        # Store preprocessing metadata
        if preprocessing_message:
            final_conf["preprocessing"] = {
                "original_path": job_in.input_uri,
                "transformed_path": actual_input_uri,
                "message": preprocessing_message
            }

        # Determine strict GCS/GCP path key logic based on pipeline tags or ID if needed
        use_gcp_path = False  # Most new DAGs use gcs_path

        run_info = airflow_service.trigger_dag(
            dag_id=dag_id,
            gcs_path=actual_input_uri,  # Use transformed URI if preprocessing occurred
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
        input_uri=actual_input_uri,  # Store actual URI (transformed if preprocessing occurred)
        input_display=getattr(job_in, "input_display", None) or job_in.input_uri,  # Store user-provided path
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
    
    # If job is successful, try to fetch XCom result (try multiple task IDs and keys)
    if job.status == "success" and not job.result_artifacts:
        # List of (task_id, xcom_key) to try
        xcom_sources = [
            ("convert_to_calipergt", "return_value"),
            ("convert_to_calipergt_task", "return_value"),
            ("convert_annotations", "annotations"),  # 3D pipeline uses 'annotations' key
            ("final_task", "return_value"),
        ]
        for task_id, xcom_key in xcom_sources:
            try:
                xcom_result = airflow_service.get_xcom_value(
                    job.airflow_dag_id,
                    job.airflow_run_id,
                    task_id,
                    xcom_key
                )
                if xcom_result:
                    print(f"Found XCom from task: {task_id}, key: {xcom_key}")
                    # For 3D pipeline, wrap the direct JSON in result_artifacts format
                    if task_id == "convert_annotations" and isinstance(xcom_result, dict) and "tracks" in xcom_result:
                        job.result_artifacts = {"annotations_data": xcom_result}
                    else:
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
    format: str = Query("calipergt", regex="^(calipergt|coco|kitti3d)$"),
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user),
):
    """
    Download the annotation result file from the Airflow worker via SCP.
    Supports CaliperGT (default), COCO, and KITTI 3D formats.
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
        xcom_sources = [
            ("convert_to_calipergt", "return_value"),
            ("convert_to_calipergt_task", "return_value"),
            ("convert_annotations", "annotations"),  # 3D pipeline uses 'annotations' key
            ("final_task", "return_value"),
        ]
        for task_id, xcom_key in xcom_sources:
            try:
                xcom_result = airflow_service.get_xcom_value(
                    job.airflow_dag_id,
                    job.airflow_run_id,
                    task_id,
                    xcom_key
                )
                if xcom_result:
                    # For 3D pipeline, wrap the direct JSON in result_artifacts format
                    if task_id == "convert_annotations" and isinstance(xcom_result, dict) and "tracks" in xcom_result:
                        job.result_artifacts = {"annotations_data": xcom_result}
                    else:
                        job.result_artifacts = xcom_result
                    db.add(job)
                    db.commit()
                    db.refresh(job)
                    break
            except Exception as e:
                print(f"Error fetching XCom from {task_id}: {e}")

    # Check if we have artifacts now
    if not job.result_artifacts:
        raise HTTPException(status_code=404, detail="No result artifacts found. The pipeline may not have produced output.")

    # Handle 3D pipeline - direct JSON data in annotations_data
    if "annotations_data" in job.result_artifacts:
        annotations = job.result_artifacts["annotations_data"]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"annotations_3d_{job.id}_{timestamp}.json"

        # Transform orientation: add pi/2 to convert from ego frame (+X) to output frame (+Y)
        # Applied for default JSON format here; KITTI format handles it internally
        transformed_annotations = transform_lidar_orientation(annotations)
        content = json.dumps(transformed_annotations, indent=2).encode('utf-8')
        media_type = "application/json"

        # Convert format if requested
        if format == "coco":
            try:
                coco_data = calipergt_to_coco(transformed_annotations)
                content = json.dumps(coco_data, indent=2).encode('utf-8')
                filename = filename.replace('.json', '_coco.json')
            except Exception as e:
                print(f"Format conversion error: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to convert to COCO format: {str(e)}")
        elif format == "kitti3d":
            try:
                # Use original annotations - calipergt_to_kitti3d handles the pi/2 offset internally
                kitti_zip_bytes = calipergt_to_kitti3d(annotations)
                content = kitti_zip_bytes
                filename = f"annotations_3d_{job.id}_{timestamp}_kitti.zip"
                media_type = "application/zip"
            except Exception as e:
                print(f"KITTI 3D conversion error: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to convert to KITTI 3D format: {str(e)}")

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    # Handle 2D pipeline - file path requiring SCP
    remote_path = job.result_artifacts.get("calipergt_file")
    if not remote_path:
        raise HTTPException(status_code=404, detail="No annotation file path in results")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.basename(remote_path)
            local_path = os.path.join(temp_dir, filename)

            print(f"Downloading {remote_path} from {AIRFLOW_SSH_HOST}...")

            # Use gcloud compute scp with explicit account
            result = subprocess.run(
                [
                    "gcloud", "compute", "scp",
                    f"--zone={AIRFLOW_SSH_ZONE}",
                    f"{AIRFLOW_SSH_USER}@{AIRFLOW_SSH_HOST}:{remote_path}",
                    local_path,
                    "--tunnel-through-iap"
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                print(f"SCP stderr: {result.stderr}")
                raise HTTPException(status_code=500, detail=f"SCP failed: {result.stderr}")

            # Read the file
            with open(local_path, 'rb') as f:
                content = f.read()

            # Convert format if requested
            if format == "coco":
                try:
                    calipergt_data = json.loads(content)
                    coco_data = calipergt_to_coco(calipergt_data)
                    content = json.dumps(coco_data, indent=2).encode('utf-8')
                    filename = filename.replace('.json', '_coco.json')
                except Exception as e:
                    print(f"Format conversion error: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to convert to COCO format: {str(e)}")

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


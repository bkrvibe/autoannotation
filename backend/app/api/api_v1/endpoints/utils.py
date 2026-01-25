from typing import List, Optional
from datetime import datetime
import logging
import tempfile
import zipfile
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from app.services.gcs import GCSService
from app.core.config import settings
from app.utils.data_validator import (
    detect_and_validate_data,
    validate_zip_structure,
    get_structure_help_message,
    DataValidationResult,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_POINTCLOUD_EXTENSIONS
)

router = APIRouter()
gcs = GCSService()
logger = logging.getLogger(__name__)


class MissingFileResponse(BaseModel):
    """Info about a missing file that user needs to provide."""
    file_type: str
    expected_names: List[str]
    description: str
    required: bool = True


class DataValidationResponse(BaseModel):
    """Response model for data validation."""
    is_valid: bool
    format_detected: str
    pipeline_type: str
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    file_counts: dict
    structure_help: Optional[dict] = None
    missing_files: List[MissingFileResponse] = []
    found_candidates: dict = {}
    needs_user_input: bool = False

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a single file to GCS and return the GS path.
    """
    try:
        logger.info(f"Uploading single file: {file.filename}")
        content = await file.read()
        gcs_path = gcs.upload_bytes(
            content=content,
            filename=file.filename,
            content_type=file.content_type
        )
        logger.info(f"Upload complete: {gcs_path}")
        return {"gcs_path": gcs_path}
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple files to GCS and return the base GS path.
    All files are uploaded to a common timestamped folder.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    logger.info(f"Starting upload of {len(files)} files")
    
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_path = f"test_data/{timestamp}"
        uploaded_files = []
        
        for i, file in enumerate(files):
            try:
                content = await file.read()
                
                # Preserve relative path structure if provided (for folder uploads)
                # Browser sends paths like "folder/subfolder/file.jpg"
                filename = file.filename or "unknown"
                
                blob_name = f"{base_path}/{filename}"
                blob = gcs.bucket.blob(blob_name)
                
                content_type = file.content_type or "application/octet-stream"
                blob.upload_from_string(content, content_type=content_type)
                
                uploaded_files.append({
                    "filename": filename,
                    "gcs_path": f"gs://{settings.GCS_BUCKET}/{blob_name}"
                })
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Uploaded {i + 1}/{len(files)} files")
            except Exception as file_err:
                logger.warning(f"Failed to upload {file.filename}: {str(file_err)}")
                # Continue with other files instead of failing completely
                continue
        
        logger.info(f"Upload complete: {len(uploaded_files)} files uploaded to {base_path}")
        
        # Return the base folder path for the job
        gcs_folder_path = f"gs://{settings.GCS_BUCKET}/{base_path}/"
        
        # Analyze uploaded structure for validation hints
        validation_hints = analyze_uploaded_structure(uploaded_files)

        return {
            "gcs_path": gcs_folder_path,
            "file_count": len(uploaded_files),
            "files": uploaded_files[:10],  # Return first 10 for display
            "validation": validation_hints
        }
    except Exception as e:
        logger.error(f"Multi-upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def analyze_uploaded_structure(uploaded_files: List[dict]) -> dict:
    """Analyze uploaded file structure for validation hints."""
    result = {
        "detected_type": "unknown",
        "is_valid_structure": False,
        "warnings": [],
        "suggestions": [],
        "missing_files": [],
        "found_candidates": {},
        "needs_user_input": False
    }

    filenames = [f["filename"] for f in uploaded_files]

    # Count file types
    image_count = sum(1 for f in filenames if any(f.lower().endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS))
    pcd_count = sum(1 for f in filenames if f.lower().endswith('.pcd'))
    bin_count = sum(1 for f in filenames if f.lower().endswith('.bin'))
    json_files = [f for f in filenames if f.lower().endswith('.json')]
    json_count = len(json_files)

    # Detect structure
    has_pointcloud_dir = any('pointcloud/' in f for f in filenames)
    has_related_images_dir = any('related_images/' in f for f in filenames)
    has_lidar_dir = any('lidar/' in f for f in filenames)

    # More flexible calibration detection
    calibration_patterns = ['calibration.json', 'calib.json', 'sensor_calibration.json']
    calibration_candidates = [f for f in json_files if any(p in f.lower() for p in ['calib', 'sensor'])]
    has_calibration = any(any(p in f.lower() for p in calibration_patterns) for f in filenames)

    # More flexible poses detection
    poses_patterns = ['poses.json', 'ego_poses.json', 'trajectory.json']
    poses_candidates = [f for f in json_files if any(p in f.lower() for p in ['pose', 'ego', 'trajectory'])]
    has_poses = any(any(p in f.lower() for p in poses_patterns) for f in filenames)

    if has_pointcloud_dir and has_related_images_dir:
        result["detected_type"] = "3d_expected"
        result["is_valid_structure"] = True
    elif has_lidar_dir and has_calibration and has_poses:
        result["detected_type"] = "3d_custom"
        result["is_valid_structure"] = True
    elif pcd_count > 0 or bin_count > 0 or has_lidar_dir:
        # 3D data detected but incomplete
        result["detected_type"] = "3d_incomplete"
        result["is_valid_structure"] = False

        if not has_lidar_dir and not has_pointcloud_dir:
            result["warnings"].append("Point cloud files found but not in expected directory structure")
            result["suggestions"].append("Place .pcd files in 'lidar/' or 'pointcloud/' directory")

        if not has_calibration:
            if calibration_candidates:
                result["found_candidates"]["calibration"] = calibration_candidates
                result["suggestions"].append(
                    f"Found potential calibration file(s): {', '.join(calibration_candidates[:3])}. "
                    "Please confirm which one contains sensor calibration data."
                )
                result["needs_user_input"] = True
            else:
                result["missing_files"].append({
                    "file_type": "calibration",
                    "expected_names": calibration_patterns,
                    "description": "Sensor calibration with ego_to_lidar and camera transforms",
                    "required": True
                })
                result["suggestions"].append(
                    "Missing calibration file. Please upload calibration.json with sensor calibration data."
                )

        if not has_poses:
            if poses_candidates:
                result["found_candidates"]["poses"] = poses_candidates
                result["suggestions"].append(
                    f"Found potential pose file(s): {', '.join(poses_candidates[:3])}. "
                    "Please confirm which one contains ego poses."
                )
                result["needs_user_input"] = True
            else:
                result["missing_files"].append({
                    "file_type": "poses",
                    "expected_names": ["ego_poses/poses.json", "poses.json"],
                    "description": "Vehicle ego poses with position/rotation for each frame",
                    "required": True
                })
                result["suggestions"].append(
                    "Missing poses file. Please upload ego_poses/poses.json with vehicle pose data."
                )

    elif image_count > 0:
        result["detected_type"] = "2d"
        result["is_valid_structure"] = True
    else:
        result["warnings"].append("No recognized data files found")
        result["suggestions"].append("Upload images (.jpg, .png) or point clouds (.pcd)")

    result["file_counts"] = {
        "images": image_count,
        "pointcloud_files": pcd_count + bin_count,
        "json_files": json_count,
        "total": len(filenames)
    }

    return result


@router.post("/validate-upload")
async def validate_uploaded_data(
    file: UploadFile = File(...),
    pipeline_type: Optional[str] = Query(None, description="Pipeline type: 2d or 3d")
) -> DataValidationResponse:
    """
    Validate uploaded data structure (zip file or directory).
    Returns detailed validation results with suggestions.
    """
    try:
        content = await file.read()
        filename = file.filename or "upload"

        # Check if it's a zip file
        if filename.lower().endswith('.zip'):
            # Save temporarily and validate
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                result = validate_zip_structure(tmp_path, pipeline_type)
            finally:
                os.unlink(tmp_path)
        else:
            # Single file - provide feedback
            result = DataValidationResult()
            ext = Path(filename).suffix.lower()

            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                result.is_valid = True
                result.format_detected = "2d"
                result.pipeline_type = "2d"
                result.file_counts["images"] = 1
            elif ext in SUPPORTED_POINTCLOUD_EXTENSIONS:
                result.is_valid = False
                result.format_detected = "3d_incomplete"
                result.pipeline_type = "3d"
                result.warnings.append("Single point cloud file - need full dataset")
                result.suggestions.append("Upload a complete dataset with calibration and poses")
            else:
                result.errors.append(f"Unsupported file type: {ext}")

        # Add structure help based on pipeline type
        structure_help = get_structure_help_message(pipeline_type or result.pipeline_type)

        return DataValidationResponse(
            is_valid=result.is_valid,
            format_detected=result.format_detected,
            pipeline_type=result.pipeline_type,
            errors=result.errors,
            warnings=result.warnings,
            suggestions=result.suggestions,
            file_counts=result.file_counts,
            structure_help=structure_help
        )

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.get("/data-structure-guide")
async def get_data_structure_guide(
    pipeline_type: str = Query("2d", description="Pipeline type: 2d, 3d, or specific pipeline ID")
) -> dict:
    """
    Get the expected data structure guide for a pipeline type.
    """
    return get_structure_help_message(pipeline_type)


@router.post("/upload-additional")
async def upload_additional_file(
    file: UploadFile = File(...),
    base_gcs_path: str = Query(..., description="Base GCS path to upload to"),
    target_path: str = Query(..., description="Target path within the dataset (e.g., 'ego_poses/poses.json')")
):
    """
    Upload an additional file to an existing dataset.
    Used when user needs to add missing files like poses.json or calibration.json.
    """
    try:
        content = await file.read()

        # Parse base path
        if not base_gcs_path.startswith('gs://'):
            raise HTTPException(status_code=400, detail="Invalid GCS path")

        path_parts = base_gcs_path[5:].split('/', 1)
        bucket_name = path_parts[0]
        base_prefix = path_parts[1].rstrip('/') if len(path_parts) > 1 else ''

        # Construct full blob path
        blob_name = f"{base_prefix}/{target_path}" if base_prefix else target_path

        # Upload to GCS
        blob = gcs.bucket.blob(blob_name)
        content_type = file.content_type or "application/octet-stream"
        blob.upload_from_string(content, content_type=content_type)

        logger.info(f"Uploaded additional file to {blob_name}")

        return {
            "success": True,
            "gcs_path": f"gs://{bucket_name}/{blob_name}",
            "message": f"Successfully uploaded {target_path}"
        }
    except Exception as e:
        logger.error(f"Failed to upload additional file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-gcs-data")
async def validate_gcs_data(
    gcs_path: str = Query(..., description="GCS path to validate"),
    pipeline_type: str = Query("3d", description="Pipeline type")
):
    """
    Validate data structure at a GCS path and return detailed info about what's found/missing.
    """
    import tempfile
    import shutil
    from app.utils.lidar_preprocessing import download_from_gcs
    from app.utils.data_validator import detect_and_validate_data

    temp_dir = None
    try:
        # Download to temp directory for validation
        temp_dir = tempfile.mkdtemp(prefix='validate_')

        if not download_from_gcs(gcs_path, temp_dir):
            return {
                "is_valid": False,
                "errors": ["Failed to download data from GCS"],
                "suggestions": ["Check that the GCS path is correct and accessible"]
            }

        # Validate the structure
        result = detect_and_validate_data(temp_dir, pipeline_type)

        return result.to_dict()

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return {
            "is_valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "suggestions": []
        }
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

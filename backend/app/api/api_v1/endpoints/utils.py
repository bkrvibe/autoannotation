from typing import List
from datetime import datetime
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.gcs import GCSService
from app.core.config import settings

router = APIRouter()
gcs = GCSService()
logger = logging.getLogger(__name__)

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
        
        return {
            "gcs_path": gcs_folder_path,
            "file_count": len(uploaded_files),
            "files": uploaded_files[:10]  # Return first 10 for display
        }
    except Exception as e:
        logger.error(f"Multi-upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

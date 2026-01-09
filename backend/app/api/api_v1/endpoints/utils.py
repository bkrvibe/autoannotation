from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.gcs import GCSService

router = APIRouter()
gcs = GCSService()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to GCS and return the GS path.
    """
    try:
        content = await file.read()
        gcs_path = gcs.upload_bytes(
            content=content,
            filename=file.filename,
            content_type=file.content_type
        )
        return {"gcs_path": gcs_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pathlib import Path
from fastapi import HTTPException, status

def validate_file_upload(filename: str, content_type: str | None = None) -> str:
    """
    Validates the uploaded file extension and returns the normalized file_type:
    'kml' or 'shapefile_zip'.
    Raises HTTP 400 for unsupported formats.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or invalid."
        )
    
    suffix = Path(filename).suffix.lower()
    if suffix == ".kml":
        return "kml"
    elif suffix == ".zip":
        return "shapefile_zip"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Only .kml and .zip (Shapefile) files are supported."
        )
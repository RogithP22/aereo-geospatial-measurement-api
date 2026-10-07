import os
import uuid
import zipfile
import re
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

class FileService:
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizes the original filename to prevent unsafe characters."""
        basename = os.path.basename(filename)
        return re.sub(r'[^a-zA-Z0-9_\.-]', '_', basename)

    @staticmethod
    def validate_and_extract_file(file: UploadFile) -> tuple[str, str, str, str | None]:
        """
        Validates size, extension, empty files, ZIP integrity, prevents path traversal,
        extracts ZIPs safely, and locates the .shp file.
        Returns: (file_path, original_filename, file_type, extracted_shp_path)
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a filename."
            )

        original_filename = file.filename
        sanitized_name = FileService.sanitize_filename(original_filename)
        file_extension = os.path.splitext(sanitized_name)[1].lower()

        # 1. Validate file extension
        if file_extension == ".kml":
            file_type = "kml"
        elif file_extension == ".zip":
            file_type = "shapefile_zip"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{file_extension}'. Only '.kml' and '.zip' files are accepted."
            )

        # 2. Store using UUID-based paths rather than trusting user filenames
        file_uuid = uuid.uuid4()
        saved_filename = f"{file_uuid}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

        # 3. Stream upload in chunks to validate size and prevent memory spikes
        total_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        try:
            with open(file_path, "wb") as buffer:
                while True:
                    chunk = file.file.read(chunk_size)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                        )
                    buffer.write(chunk)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file."
            )

        # 4. Validate empty files
        if total_size == 0:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty."
            )

        extracted_shp_path = None

        # 5. Handle Shapefile ZIP validation, path traversal defense, and extraction
        if file_type == "shapefile_zip":
            if not zipfile.is_zipfile(file_path):
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The uploaded file is not a valid or intact ZIP archive."
                )

            extract_dir = os.path.join(settings.UPLOAD_DIR, str(file_uuid))
            os.makedirs(extract_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Guard against ZIP Slip / Path Traversal attacks
                    for member in zip_ref.namelist():
                        member_path = os.path.abspath(os.path.join(extract_dir, member))
                        if not member_path.startswith(os.path.abspath(extract_dir)):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Malicious ZIP archive detected: Path traversal attempt."
                            )
                    zip_ref.extractall(extract_dir)

                # Locate the required .shp component inside extracted files
                shp_files = []
                for root, _, files in os.walk(extract_dir):
                    for f in files:
                        if f.lower().endswith('.shp'):
                            shp_files.append(os.path.join(root, f))

                if not shp_files:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No valid '.shp' file found inside the uploaded ZIP archive."
                    )
                extracted_shp_path = shp_files[0]

            except HTTPException as he:
                if os.path.exists(extract_dir):
                    import shutil
                    shutil.rmtree(extract_dir)
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise he
            except Exception as e:
                if os.path.exists(extract_dir):
                    import shutil
                    shutil.rmtree(extract_dir)
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to process ZIP archive: {str(e)}"
                )

        return file_path, original_filename, file_type, extracted_shp_path
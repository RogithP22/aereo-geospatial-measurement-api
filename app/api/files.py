import os
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import FileModel, FeatureModel, ProcessingStatus
from app.services.file_service import FileService
from app.services.geospatial_service import GeospatialService
from app.services.measurement_service import MeasurementService
from app.utils.file_utils import validate_file_upload

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def upload_and_process_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Validate file extension and headers
    file_type = validate_file_upload(file.filename, file.content_type)
    
    # 2. Generate UUID object and save uploaded file to secure temporary storage
    file_id_obj = uuid.uuid4()
    file_id_str = str(file_id_obj)
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_extension = Path(file.filename).suffix
    saved_file_path = upload_dir / f"{file_id_str}{file_extension}"
    
    try:
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # 3. Create initial database record with PENDING status using uuid.UUID object
    file_record = FileModel(
        id=file_id_obj,
        filename=file.filename,
        file_type=file_type,
        status=ProcessingStatus.PENDING.value
    )
    db.add(file_record)
    db.commit()

    try:
        # 4. Load geospatial file into GeoDataFrame
        shp_path_arg = str(saved_file_path) if file_type == "shapefile_zip" else None
        gdf = GeospatialService.load_geospatial_file(file_type, str(saved_file_path), shp_path_arg)

        # 5. Transform CRS to local UTM for accurate metric measurement if geographic
        if gdf.crs and gdf.crs.is_geographic:
            centroid_lon = gdf.geometry.unary_union.centroid.x
            utm_zone = int((centroid_lon + 180) / 6) + 1
            utm_crs = f"EPSG:{32600 + utm_zone if centroid_lon >= 0 else 32700 + utm_zone}"
            gdf = gdf.to_crs(utm_crs)
        elif gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)

        # 6. Calculate measurements using measurement service
        measurements = MeasurementService.process_features(gdf)

        # 7. Update file record fields cleanly
        file_record.crs = str(gdf.crs)
        file_record.feature_count = len(gdf)
        file_record.status = ProcessingStatus.COMPLETED.value
        file_record.error_message = None

        # 8. Persist measurement records using correct `properties` field
        for m in measurements:
            meas_record = FeatureModel(
                file_id=file_id_obj,
                feature_index=m["feature_index"],
                geometry_type=m["geometry_type"],
                properties=m["properties"],
                measurement_type=m["measurement_type"],
                measurement_value=m["measurement_value"],
                measurement_unit=m["measurement_unit"]
            )
            db.add(meas_record)

        db.commit()
        db.refresh(file_record)

        return {
            "id": str(file_record.id),
            "filename": file_record.filename,
            "file_type": file_record.file_type,
            "crs": file_record.crs,
            "feature_count": file_record.feature_count,
            "status": file_record.status,
            "error_message": file_record.error_message,
            "created_at": file_record.created_at.isoformat() if file_record.created_at else None
        }

    except Exception as e:
        db.rollback()
        file_record.status = ProcessingStatus.FAILED.value
        file_record.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Processing failed: {str(e)}"
        )

@router.get("/{file_id}")
def get_file_details(file_id: uuid.UUID, db: Session = Depends(get_db)):
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "id": str(file_record.id),
        "filename": file_record.filename,
        "file_type": file_record.file_type,
        "crs": file_record.crs,
        "feature_count": file_record.feature_count,
        "status": file_record.status,
        "error_message": file_record.error_message,
        "created_at": file_record.created_at.isoformat() if file_record.created_at else None
    }

@router.get("/{file_id}/measurements/")
def get_file_measurements(file_id: uuid.UUID, db: Session = Depends(get_db)):
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_record.status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="File processing is not completed or failed.")

    meas_records = db.query(FeatureModel).filter(FeatureModel.file_id == file_id).all()
    
    measurements_list = []
    for m in meas_records:
        measurements_list.append({
            "feature_index": m.feature_index,
            "geometry_type": m.geometry_type,
            "properties": m.properties,
            "measurement_type": m.measurement_type,
            "measurement_value": m.measurement_value,
            "measurement_unit": m.measurement_unit
        })

    return {
        "file_id": str(file_record.id),
        "filename": file_record.filename,
        "total_features": file_record.feature_count,
        "measurements": measurements_list
    }
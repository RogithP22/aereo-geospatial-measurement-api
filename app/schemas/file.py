from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class FileResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    crs: Optional[str] = None
    feature_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MeasurementItem(BaseModel):
    feature_index: int
    geometry_type: str
    properties: Optional[Dict[str, Any]] = None
    measurement_type: Optional[str] = None  # area, length, null
    measurement_value: Optional[float] = None
    measurement_unit: Optional[str] = None  # square_meters, meters, null

    model_config = ConfigDict(from_attributes=True)

class FileMeasurementsResponse(BaseModel):
    file_id: UUID
    filename: str
    total_features: int
    measurements: List[MeasurementItem]
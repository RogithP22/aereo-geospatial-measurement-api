import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base

class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"

class FileModel(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # kml or shapefile_zip
    crs = Column(String(100), nullable=True)
    feature_count = Column(Integer, default=0)
    status = Column(String(50), default=ProcessingStatus.PENDING)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    features = relationship("FeatureModel", back_populates="file", cascade="all, delete-orphan")

class FeatureModel(Base):
    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    feature_index = Column(Integer, nullable=False)
    geometry_type = Column(String(100), nullable=False)
    properties = Column(JSON, nullable=True)  # Store attributes/properties as JSON
    measurement_type = Column(String(50), nullable=True)  # area, length, null
    measurement_value = Column(Float, nullable=True)
    measurement_unit = Column(String(50), nullable=True)  # square_meters, meters, null

    file = relationship("FileModel", back_populates="features")
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class DataResponse(BaseModel):
    """Response model for data endpoints"""
    status: str = Field(..., description="Response status")
    data: Dict[str, Any] = Field(..., description="Response data")
    timestamp: str = Field(..., description="Response timestamp")

class IQARequest(BaseModel):
    """Request model for IQA calculation"""
    data: Dict[str, float] = Field(..., description="Air quality measurements")

class AlertRequest(BaseModel):
    """Request model for sending alerts"""
    alert_type: str = Field(..., description="Type of alert (pollution_high, pollution_moderate, co2_high, etc.)")
    recipients: List[Dict[str, Any]] = Field(..., description="List of recipients with contact info")
    data: Dict[str, Any] = Field(..., description="Air quality data for the alert")

class SensibilisationResponse(BaseModel):
    """Response model for sensibilisation content"""
    status: str = Field(..., description="Response status")
    data: Dict[str, Any] = Field(..., description="Sensibilisation content")
    timestamp: str = Field(..., description="Response timestamp")

class DeviceData(BaseModel):
    """Model for device air quality data"""
    device_id: str
    pm25: Optional[float] = None
    co2: Optional[float] = None
    temp: Optional[float] = None
    humidity: Optional[float] = None
    pm10: Optional[float] = None
    pm1: Optional[float] = None
    pm03: Optional[int] = None
    tvoc: Optional[float] = None
    nox: Optional[float] = None
    last_update: Optional[str] = None

class IQAData(BaseModel):
    """Model for IQA calculation results"""
    iqa: float
    status: str
    category: str
    pm25: Optional[float] = None
    co2: Optional[float] = None
    temp: Optional[float] = None
    humidity: Optional[float] = None

class AlertResult(BaseModel):
    """Model for alert sending results"""
    total_sent: int
    total_attempted: int
    results: List[Dict[str, Any]]

class LocationInfo(BaseModel):
    """Model for location/school information"""
    id: str
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

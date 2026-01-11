from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DeviceType(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"

class SessionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    BANNED = "banned"
    PENDING = "pending"

class UnofficialDeviceCreate(BaseModel):
    user_id: str
    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: DeviceType
    device_os: Optional[str] = Field(None, max_length=50)
    browser_info: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    max_daily_messages: int = Field(default=1000, gt=0, le=10000)

class UnofficialDeviceUpdate(BaseModel):
    device_name: Optional[str] = Field(None, min_length=1, max_length=100)
    session_status: Optional[SessionStatus] = None
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    max_daily_messages: Optional[int] = Field(None, gt=0, le=10000)
    is_active: Optional[bool] = None

class UnofficialDeviceResponse(BaseModel):
    device_id: str
    user_id: str
    device_name: str
    device_type: DeviceType
    device_os: Optional[str] = None
    browser_info: Optional[str] = None
    session_status: SessionStatus
    qr_code_data: Optional[str] = None
    qr_last_generated: Optional[datetime] = None
    qr_expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    connection_string: Optional[str] = None
    last_active: datetime
    last_message_sent: Optional[datetime] = None
    last_message_received: Optional[datetime] = None
    messages_sent: int
    messages_received: int
    total_activity_time: int
    is_active: bool
    max_daily_messages: int
    daily_message_count: int
    last_reset_date: datetime
    last_error: Optional[str] = None
    error_count: int
    reconnect_attempts: int
    max_reconnect_attempts: int
    created_at: datetime
    updated_at: datetime
    last_connected_at: Optional[datetime] = None
    last_disconnected_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class QRCodeRequest(BaseModel):
    device_id: str
    regenerate: bool = False

class QRCodeResponse(BaseModel):
    device_id: str
    qr_code_data: str  # Base64 encoded QR code
    qr_last_generated: datetime
    qr_expires_at: datetime
    session_status: SessionStatus

class DeviceConnectRequest(BaseModel):
    device_id: str
    qr_code_scanned: bool = True
    connection_string: Optional[str] = None

class DeviceConnectResponse(BaseModel):
    device_id: str
    session_status: SessionStatus
    connected_at: datetime
    connection_successful: bool
    message: str

class DeviceDisconnectRequest(BaseModel):
    device_id: str
    reason: Optional[str] = None

class DeviceDisconnectResponse(BaseModel):
    device_id: str
    session_status: SessionStatus
    disconnected_at: datetime
    message: str

class DeviceStatusUpdate(BaseModel):
    device_id: str
    session_status: SessionStatus
    last_error: Optional[str] = None
    ip_address: Optional[str] = None

class DeviceStats(BaseModel):
    device_id: str
    device_name: str
    session_status: SessionStatus
    messages_sent: int
    messages_received: int
    daily_message_count: int
    max_daily_messages: int
    total_activity_time: int
    last_active: datetime
    uptime_percentage: Optional[float] = None

class UserDeviceStats(BaseModel):
    user_id: str
    total_devices: int
    active_devices: int
    connected_devices: int
    total_messages_sent: int
    total_messages_received: int
    devices: List[DeviceStats]

class DeviceActivityLog(BaseModel):
    device_id: str
    activity_type: str  # connect, disconnect, message_sent, message_received, error
    timestamp: datetime
    details: Optional[dict] = None

class BulkDeviceOperation(BaseModel):
    device_ids: List[str] = Field(..., min_items=1, max_items=50)
    operation: str  # disconnect, reconnect, reset_daily_count, activate, deactivate

class DeviceHealthCheck(BaseModel):
    device_id: str
    is_responsive: bool
    response_time_ms: Optional[int] = None
    last_check: datetime
    issues: List[str] = []

class DeviceMaintenanceRequest(BaseModel):
    device_id: str
    maintenance_type: str  # cleanup, reconnect, reset, update_settings
    parameters: Optional[dict] = None

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SessionType(str, Enum):
    UNOFFICIAL = "unofficial"
    OFFICIAL = "official"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPROMISED = "compromised"
    LOCKED = "locked"

class DeviceSessionCreate(BaseModel):
    device_id: str
    session_type: SessionType = SessionType.UNOFFICIAL
    user_agent: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    expires_in_hours: int = Field(default=24, gt=0, le=168)  # Max 7 days
    max_login_attempts: int = Field(default=5, gt=0, le=10)

class DeviceSessionUpdate(BaseModel):
    is_valid: Optional[bool] = None
    is_active: Optional[bool] = None
    user_agent: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    requires_reauth: Optional[bool] = None

class DeviceSessionResponse(BaseModel):
    session_id: str
    device_id: str
    session_type: SessionType
    is_valid: bool
    is_active: bool
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    last_ip_address: Optional[str] = None
    login_attempts: int
    max_login_attempts: int
    last_login_attempt: Optional[datetime] = None
    last_successful_login: Optional[datetime] = None
    last_activity: datetime
    total_requests: int
    messages_sent_via_session: int
    created_at: datetime
    expires_at: datetime
    last_extended_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    is_compromised: bool
    compromise_reason: Optional[str] = None
    requires_reauth: bool
    
    class Config:
        from_attributes = True

class SessionCreateRequest(BaseModel):
    device_id: str
    session_data: str = Field(..., min_length=1, max_length=10000)  # Raw session data to encrypt
    user_agent: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    expires_in_hours: int = Field(default=24, gt=0, le=168)

class SessionCreateResponse(BaseModel):
    session_id: str
    device_id: str
    session_token: str  # Encrypted session data
    expires_at: datetime
    created_at: datetime
    is_valid: bool

class SessionValidateRequest(BaseModel):
    session_id: str
    session_token: str  # For additional validation if needed

class SessionValidateResponse(BaseModel):
    session_id: str
    is_valid: bool
    is_active: bool
    is_expired: bool
    is_compromised: bool
    requires_reauth: bool
    expires_at: datetime
    last_activity: datetime
    message: str

class SessionExtendRequest(BaseModel):
    session_id: str
    extend_hours: int = Field(default=24, gt=0, le=168)
    reason: Optional[str] = Field(None, max_length=500)

class SessionExtendResponse(BaseModel):
    session_id: str
    old_expires_at: datetime
    new_expires_at: datetime
    extended_at: datetime
    message: str

class SessionRevokeRequest(BaseModel):
    session_id: str
    reason: Optional[str] = Field(None, max_length=500)

class SessionRevokeResponse(BaseModel):
    session_id: str
    revoked_at: datetime
    reason: Optional[str] = None
    message: str

class SessionLoginRequest(BaseModel):
    session_id: str
    password: Optional[str] = None  # For session re-authentication
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')

class SessionLoginResponse(BaseModel):
    session_id: str
    login_successful: bool
    login_attempts_remaining: int
    last_login_attempt: datetime
    requires_reauth: bool
    message: str

class SessionActivityUpdate(BaseModel):
    session_id: str
    activity_type: str = Field(..., max_length=50)  # message_sent, status_check, etc.
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    metadata: Optional[dict] = None

class SessionStats(BaseModel):
    session_id: str
    device_id: str
    session_type: SessionType
    status: SessionStatus
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    total_requests: int
    messages_sent_via_session: int
    uptime_hours: Optional[float] = None
    requests_per_hour: Optional[float] = None

class DeviceSessionStats(BaseModel):
    device_id: str
    total_sessions: int
    active_sessions: int
    expired_sessions: int
    revoked_sessions: int
    compromised_sessions: int
    total_requests: int
    total_messages_sent: int
    average_session_duration: Optional[float] = None
    sessions: List[SessionStats]

class UserSessionStats(BaseModel):
    user_id: str
    total_devices: int
    total_sessions: int
    active_sessions: int
    expired_sessions: int
    revoked_sessions: int
    compromised_sessions: int
    total_requests: int
    total_messages_sent: int
    devices: List[DeviceSessionStats]

class SessionSecurityCheck(BaseModel):
    session_id: str
    security_issues: List[str]
    risk_level: str  # low, medium, high, critical
    recommendations: List[str]
    last_check: datetime

class BulkSessionOperation(BaseModel):
    session_ids: List[str] = Field(..., min_items=1, max_items=100)
    operation: str  # revoke, extend, deactivate, reactivate
    parameters: Optional[dict] = None

class SessionCleanupRequest(BaseModel):
    cleanup_type: str = Field(..., max_length=50)  # expired, inactive, compromised
    dry_run: bool = Field(default=True)  # If true, only report what would be cleaned

class SessionCleanupResponse(BaseModel):
    cleanup_type: str
    sessions_cleaned: int
    sessions_affected: List[str]
    cleanup_time: datetime
    dry_run: bool
    message: str

class SessionAuditLog(BaseModel):
    session_id: str
    action: str  # create, login, extend, revoke, compromise
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None

class SessionHealthCheck(BaseModel):
    session_id: str
    is_healthy: bool
    health_score: float  # 0.0 to 1.0
    issues: List[str]
    recommendations: List[str]
    last_check: datetime

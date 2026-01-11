from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class UsageType(str, Enum):
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    MEDIA_UPLOAD = "media_upload"
    TEMPLATE_SEND = "template_send"
    API_CALL = "api_call"
    WEBHOOK = "webhook"
    SESSION_CREATE = "session_create"
    DEVICE_CONNECTION = "device_connection"

class UsageStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"
    DISPUTED = "disputed"

class MessageUsageLogCreate(BaseModel):
    user_id: str
    message_id: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    usage_type: UsageType = UsageType.MESSAGE_SEND
    credits_deducted: int = Field(..., ge=0)
    balance_before: int = Field(..., ge=0)
    balance_after: int = Field(..., ge=0)
    cost_per_credit: float = Field(default=0.01, gt=0)
    message_type: Optional[str] = Field(None, max_length=50)
    message_size: Optional[int] = Field(None, ge=0)
    recipient_count: int = Field(default=1, ge=1)
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    user_agent: Optional[str] = Field(None, max_length=500)
    api_endpoint: Optional[str] = Field(None, max_length=200)
    request_id: Optional[str] = Field(None, max_length=100)

class MessageUsageLogUpdate(BaseModel):
    status: Optional[UsageStatus] = None
    error_code: Optional[str] = Field(None, max_length=50)
    error_message: Optional[str] = Field(None, max_length=500)
    delivery_status: Optional[str] = Field(None, max_length=50)
    processed_at: Optional[datetime] = None

class MessageUsageLogResponse(BaseModel):
    usage_id: str
    user_id: str
    message_id: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    usage_type: UsageType
    credits_deducted: int
    credits_refunded: int
    net_credits: int
    balance_before: int
    balance_after: int
    cost_per_credit: float
    total_cost: float
    currency: str
    message_type: Optional[str] = None
    message_size: Optional[int] = None
    recipient_count: int
    delivery_status: Optional[str] = None
    status: UsageStatus
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_endpoint: Optional[str] = None
    request_id: Optional[str] = None
    refund_reason: Optional[str] = None
    refund_timestamp: Optional[datetime] = None
    refund_processed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UsageLogCreateRequest(BaseModel):
    user_id: str
    message_id: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    usage_type: UsageType = UsageType.MESSAGE_SEND
    credits_deducted: int = Field(..., ge=0)
    balance_before: int = Field(..., ge=0)
    message_type: Optional[str] = Field(None, max_length=50)
    message_size: Optional[int] = Field(None, ge=0)
    recipient_count: int = Field(default=1, ge=1)
    ip_address: Optional[str] = Field(None, pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    user_agent: Optional[str] = Field(None, max_length=500)
    api_endpoint: Optional[str] = Field(None, max_length=200)
    request_id: Optional[str] = Field(None, max_length=100)

class UsageLogCreateResponse(BaseModel):
    usage_id: str
    user_id: str
    credits_deducted: int
    balance_before: int
    balance_after: int
    total_cost: float
    currency: str
    status: UsageStatus
    created_at: datetime

class UsageLogRefundRequest(BaseModel):
    usage_id: str
    refund_amount: int = Field(..., gt=0)
    refund_reason: str = Field(..., min_length=1, max_length=500)
    processed_by: Optional[str] = None

class UsageLogRefundResponse(BaseModel):
    usage_id: str
    credits_refunded: int
    net_credits: int
    refund_reason: str
    refund_timestamp: datetime
    message: str

class UsageLogUpdateRequest(BaseModel):
    usage_id: str
    status: Optional[UsageStatus] = None
    error_code: Optional[str] = Field(None, max_length=50)
    error_message: Optional[str] = Field(None, max_length=500)
    delivery_status: Optional[str] = Field(None, max_length=50)

class UsageLogUpdateResponse(BaseModel):
    usage_id: str
    status: UsageStatus
    updated_at: datetime
    message: str

class UsageStats(BaseModel):
    total_usage: int
    total_credits_deducted: int
    total_credits_refunded: int
    net_credits_used: int
    total_cost: float
    successful_usage: int
    failed_usage: int
    refunded_usage: int
    average_cost_per_usage: float
    usage_by_type: dict
    usage_by_status: dict

class UserUsageStats(BaseModel):
    user_id: str
    total_usage: int
    total_credits_deducted: int
    total_credits_refunded: int
    net_credits_used: int
    total_cost: float
    current_balance: int
    usage_by_type: dict
    usage_by_status: dict
    daily_usage: List[dict]
    hourly_usage: List[dict]

class DeviceUsageStats(BaseModel):
    device_id: str
    device_name: Optional[str] = None
    total_usage: int
    total_credits_deducted: int
    total_credits_refunded: int
    net_credits_used: int
    total_cost: float
    usage_by_type: dict
    usage_by_status: dict
    daily_usage: List[dict]

class SessionUsageStats(BaseModel):
    session_id: str
    total_usage: int
    total_credits_deducted: int
    total_credits_refunded: int
    net_credits_used: int
    total_cost: float
    usage_by_type: dict
    usage_by_status: dict
    session_duration_minutes: Optional[float] = None

class UsageAnalytics(BaseModel):
    period_start: datetime
    period_end: datetime
    total_users: int
    total_usage: int
    total_credits_deducted: int
    total_credits_refunded: int
    net_credits_used: int
    total_revenue: float
    average_usage_per_user: float
    top_users_by_usage: List[dict]
    top_devices_by_usage: List[dict]
    usage_trends: List[dict]
    cost_analysis: dict

class UsageFilter(BaseModel):
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    message_id: Optional[str] = None
    usage_type: Optional[UsageType] = None
    status: Optional[UsageStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_credits: Optional[int] = Field(None, ge=0)
    max_credits: Optional[int] = Field(None, ge=0)

class BulkUsageOperation(BaseModel):
    operation: str = Field(..., pattern=r'^(refund|update|delete)$')
    usage_ids: List[str] = Field(..., min_items=1, max_items=100)
    refund_amount: Optional[int] = Field(None, gt=0)
    refund_reason: Optional[str] = Field(None, min_length=1, max_length=500)
    new_status: Optional[UsageStatus] = None
    processed_by: Optional[str] = None

class BulkUsageResponse(BaseModel):
    operation: str
    total_processed: int
    successful: int
    failed: int
    errors: List[dict]
    message: str

class UsageAuditLog(BaseModel):
    audit_id: str
    usage_id: str
    action: str
    old_values: dict
    new_values: dict
    changed_by: str
    changed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UsageHealthCheck(BaseModel):
    usage_id: str
    is_healthy: bool
    health_score: float
    issues: List[str]
    recommendations: List[str]
    last_checked: datetime

class UsageCleanupRequest(BaseModel):
    older_than_days: int = Field(default=30, gt=0)
    status_filter: Optional[List[UsageStatus]] = None
    dry_run: bool = Field(default=True)

class UsageCleanupResponse(BaseModel):
    total_records_found: int
    records_to_delete: int
    records_deleted: int
    dry_run: bool
    message: str

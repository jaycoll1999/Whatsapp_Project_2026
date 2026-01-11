from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    OTP = "otp"
    TEXT = "text"
    TEMPLATE = "template"
    MEDIA = "media"
    DOCUMENT = "document"

class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"

class Mode(str, Enum):
    OFFICIAL = "official"
    UNOFFICIAL = "unofficial"

class MessageCreate(BaseModel):
    user_id: str
    channel: Channel = Channel.WHATSAPP
    mode: Mode
    sender_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    receiver_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    message_type: MessageType
    template_name: Optional[str] = None
    message_body: str = Field(..., min_length=1, max_length=4096)
    credits_used: int = Field(default=1, gt=0)
    
    @field_validator('template_name')
    @classmethod
    def validate_template_name(cls, v, info):
        if info.data.get('message_type') == MessageType.TEMPLATE and not v:
            raise ValueError('template_name is required when message_type is template')
        return v

class MessageUpdate(BaseModel):
    status: Optional[MessageStatus] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    external_message_id: Optional[str] = None
    webhook_response: Optional[str] = None

class MessageResponse(BaseModel):
    message_id: str
    user_id: str
    channel: Channel
    mode: Mode
    sender_number: str
    receiver_number: str
    message_type: MessageType
    template_name: Optional[str] = None
    message_body: str
    status: MessageStatus
    credits_used: int
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    external_message_id: Optional[str] = None
    retry_count: int
    max_retries: int
    
    class Config:
        from_attributes = True

class MessageSendRequest(BaseModel):
    receiver_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    message_type: MessageType
    template_name: Optional[str] = None
    message_body: str = Field(..., min_length=1, max_length=4096)
    mode: Mode = Mode.UNOFFICIAL

class BulkMessageRequest(BaseModel):
    receiver_numbers: List[str] = Field(..., min_items=1, max_items=1000)
    message_type: MessageType
    template_name: Optional[str] = None
    message_body: str = Field(..., min_length=1, max_length=4096)
    mode: Mode = Mode.UNOFFICIAL

class MessageStats(BaseModel):
    total_messages: int
    messages_sent: int
    messages_delivered: int
    messages_failed: int
    messages_read: int
    total_credits_used: int
    average_delivery_time: Optional[float] = None

class UserMessageStats(BaseModel):
    user_id: str
    stats: MessageStats

class MessageTemplate(BaseModel):
    template_name: str
    template_body: str
    message_type: MessageType
    credits_required: int = 1
    is_active: bool = True

class WebhookPayload(BaseModel):
    message_id: str
    status: MessageStatus
    external_message_id: Optional[str] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None

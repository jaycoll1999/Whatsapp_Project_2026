from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean, Numeric, Enum
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime
import uuid
import enum

class UsageType(str, enum.Enum):
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    MEDIA_UPLOAD = "media_upload"
    TEMPLATE_SEND = "template_send"
    API_CALL = "api_call"
    WEBHOOK = "webhook"
    SESSION_CREATE = "session_create"
    DEVICE_CONNECTION = "device_connection"

class UsageStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"
    DISPUTED = "disputed"

class MessageUsageLog(Base):
    __tablename__ = "message_usage_logs"
    
    usage_id = Column(String, primary_key=True, default=lambda: f"usage-{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    message_id = Column(String, ForeignKey("messages.message_id"), nullable=True, index=True)
    device_id = Column(String, ForeignKey("unofficial_linked_devices.device_id"), nullable=True, index=True)
    session_id = Column(String, ForeignKey("device_sessions.session_id"), nullable=True, index=True)
    
    # Usage details
    usage_type = Column(Enum(UsageType), default=UsageType.MESSAGE_SEND, nullable=False)
    credits_deducted = Column(Integer, nullable=False, default=0)
    credits_refunded = Column(Integer, nullable=False, default=0)
    net_credits = Column(Integer, nullable=False, default=0)
    
    # Balance tracking
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    
    # Cost details
    cost_per_credit = Column(Numeric(10, 4), default=0.01)  # Cost in currency
    total_cost = Column(Numeric(10, 4), default=0.00)  # Total cost in currency
    currency = Column(String, default="USD")
    
    # Message details
    message_type = Column(String, nullable=True)  # text, image, video, document, etc.
    message_size = Column(Integer, nullable=True)  # Size in bytes
    recipient_count = Column(Integer, default=1)  # Number of recipients
    delivery_status = Column(String, nullable=True)  # sent, delivered, read, failed
    
    # Status and tracking
    status = Column(Enum(UsageStatus), default=UsageStatus.SUCCESS, nullable=False)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    api_endpoint = Column(String, nullable=True)
    request_id = Column(String, nullable=True)  # For tracking API requests
    
    # Refund details
    refund_reason = Column(Text, nullable=True)
    refund_timestamp = Column(DateTime, nullable=True)
    refund_processed_by = Column(String, nullable=True)  # User ID who processed refund
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)  # When the usage was processed
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    message = relationship("Message", back_populates="usage_logs")
    device = relationship("UnofficialLinkedDevice", back_populates="usage_logs")
    session = relationship("DeviceSession", back_populates="usage_logs")
    
    def __repr__(self):
        return f"<MessageUsageLog(id={self.usage_id}, user_id={self.user_id}, credits={self.credits_deducted})>"
    
    def is_successful(self):
        """Check if usage was successful"""
        return self.status == UsageStatus.SUCCESS
    
    def is_refunded(self):
        """Check if credits were refunded"""
        return self.credits_refunded > 0
    
    def get_net_credit_usage(self):
        """Get net credit usage (deducted - refunded)"""
        return self.credits_deducted - self.credits_refunded
    
    def get_total_cost(self):
        """Calculate total cost in currency"""
        return float(self.total_cost)
    
    def can_be_refunded(self):
        """Check if this usage can be refunded"""
        return (
            self.status == UsageStatus.SUCCESS and
            self.credits_deducted > 0 and
            self.credits_refunded == 0 and
            not self.is_refunded()
        )
    
    def refund_credits(self, refund_amount: int, reason: str, processed_by: str = None):
        """Refund credits for this usage"""
        if not self.can_be_refunded():
            raise ValueError("Cannot refund credits for this usage")
        
        if refund_amount > self.credits_deducted:
            raise ValueError("Refund amount cannot exceed deducted credits")
        
        self.credits_refunded = refund_amount
        self.net_credits = self.credits_deducted - refund_amount
        self.refund_reason = reason
        self.refund_timestamp = datetime.utcnow()
        self.refund_processed_by = processed_by
        self.status = UsageStatus.REFUNDED
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_code: str = None, error_message: str = None):
        """Mark usage as failed"""
        self.status = UsageStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def get_usage_summary(self) -> dict:
        """Get usage summary as dictionary"""
        return {
            "usage_id": self.usage_id,
            "user_id": self.user_id,
            "message_id": self.message_id,
            "usage_type": self.usage_type.value,
            "credits_deducted": self.credits_deducted,
            "credits_refunded": self.credits_refunded,
            "net_credits": self.get_net_credit_usage(),
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "total_cost": float(self.total_cost),
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at,
            "is_successful": self.is_successful(),
            "is_refunded": self.is_refunded()
        }
    
    @staticmethod
    def create_usage_log(
        user_id: str,
        message_id: str = None,
        device_id: str = None,
        session_id: str = None,
        usage_type: UsageType = UsageType.MESSAGE_SEND,
        credits_deducted: int = 0,
        balance_before: int = 0,
        balance_after: int = 0,
        cost_per_credit: float = 0.01,
        message_type: str = None,
        message_size: int = None,
        recipient_count: int = 1,
        ip_address: str = None,
        user_agent: str = None,
        api_endpoint: str = None,
        request_id: str = None
    ):
        """Create a new usage log entry"""
        total_cost = credits_deducted * cost_per_credit
        
        return MessageUsageLog(
            user_id=user_id,
            message_id=message_id,
            device_id=device_id,
            session_id=session_id,
            usage_type=usage_type,
            credits_deducted=credits_deducted,
            net_credits=credits_deducted,
            balance_before=balance_before,
            balance_after=balance_after,
            cost_per_credit=cost_per_credit,
            total_cost=total_cost,
            message_type=message_type,
            message_size=message_size,
            recipient_count=recipient_count,
            ip_address=ip_address,
            user_agent=user_agent,
            api_endpoint=api_endpoint,
            request_id=request_id,
            processed_at=datetime.utcnow()
        )

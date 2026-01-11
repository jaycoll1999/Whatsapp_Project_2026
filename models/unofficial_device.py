from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime
import uuid

class UnofficialLinkedDevice(Base):
    __tablename__ = "unofficial_linked_devices"
    
    device_id = Column(String, primary_key=True, default=lambda: f"device-{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Device information
    device_name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)  # web, mobile, desktop
    device_os = Column(String, nullable=True)  # Windows, macOS, Linux, Android, iOS
    browser_info = Column(Text, nullable=True)  # Browser details for web devices
    
    # Session management
    session_status = Column(String, default="disconnected")  # connected, disconnected, expired, banned
    qr_code_data = Column(Text, nullable=True)  # Base64 encoded QR code
    qr_last_generated = Column(DateTime, nullable=True)
    qr_expires_at = Column(DateTime, nullable=True)
    
    # Connection details
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    connection_string = Column(Text, nullable=True)  # WhatsApp connection string
    
    # Activity tracking
    last_active = Column(DateTime, default=datetime.utcnow)
    last_message_sent = Column(DateTime, nullable=True)
    last_message_received = Column(DateTime, nullable=True)
    
    # Usage statistics
    messages_sent = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    total_activity_time = Column(Integer, default=0)  # in minutes
    
    # Security and limits
    is_active = Column(Boolean, default=True)
    max_daily_messages = Column(Integer, default=1000)
    daily_message_count = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    
    # Error handling
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    reconnect_attempts = Column(Integer, default=0)
    max_reconnect_attempts = Column(Integer, default=5)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_connected_at = Column(DateTime, nullable=True)
    last_disconnected_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="linked_devices")
    sessions = relationship("DeviceSession", back_populates="device")
    usage_logs = relationship("MessageUsageLog", back_populates="device")
    
    def __repr__(self):
        return f"<UnofficialLinkedDevice(id={self.device_id}, user_id={self.user_id}, status={self.session_status})>"
    
    def is_connected(self):
        return self.session_status == "connected"
    
    def is_expired(self):
        if self.qr_expires_at:
            return datetime.utcnow() > self.qr_expires_at
        return False
    
    def can_send_message(self):
        if not self.is_connected():
            return False
        if self.daily_message_count >= self.max_daily_messages:
            return False
        return True
    
    def increment_message_sent(self):
        self.messages_sent += 1
        self.last_message_sent = datetime.utcnow()
        self.last_active = datetime.utcnow()
        
        # Reset daily count if needed
        if self.last_reset_date.date() != datetime.utcnow().date():
            self.daily_message_count = 0
            self.last_reset_date = datetime.utcnow()
        
        self.daily_message_count += 1
    
    def increment_message_received(self):
        self.messages_received += 1
        self.last_message_received = datetime.utcnow()
        self.last_active = datetime.utcnow()

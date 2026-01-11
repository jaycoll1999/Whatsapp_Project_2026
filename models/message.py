from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime
import uuid

class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(String, primary_key=True, default=lambda: f"msg-{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Channel and mode
    channel = Column(String, default="whatsapp")  # whatsapp, sms, email
    mode = Column(String, nullable=False)  # official, unofficial
    
    # Phone numbers
    sender_number = Column(String, nullable=False)
    receiver_number = Column(String, nullable=False)
    
    # Message content
    message_type = Column(String, nullable=False)  # otp, text, template, media, document
    template_name = Column(String, nullable=True)
    message_body = Column(Text, nullable=False)
    
    # Status and tracking
    status = Column(String, default="pending")  # pending, sent, delivered, failed, read
    credits_used = Column(Integer, default=1)
    
    # Timestamps
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # External IDs
    external_message_id = Column(String, nullable=True)  # WhatsApp API message ID
    webhook_response = Column(Text, nullable=True)  # Webhook response data
    
    # Relationships
    user = relationship("User", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.message_id}, user_id={self.user_id}, status={self.status})>"

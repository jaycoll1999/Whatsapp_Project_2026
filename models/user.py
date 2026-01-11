from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=lambda: f"uuid-{uuid.uuid4().hex[:12]}")
    role = Column(String, nullable=False, default="platform_user")  # reseller, admin, platform_user, business_owner
    status = Column(String, nullable=False, default="active")  # active, inactive, suspended
    parent_reseller_id = Column(String, nullable=True)  # Foreign key to reseller
    whatsapp_mode = Column(String, default="official")  # official, unofficial
    
    # Profile fields
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Business fields
    business_name = Column(String)
    business_description = Column(Text)
    erp_system = Column(String)
    gstin = Column(String)
    
    # Address fields
    full_address = Column(String)
    pincode = Column(String)
    country = Column(String, default="India")
    
    # Bank fields
    bank_name = Column(String)
    
    # Wallet fields
    total_credits = Column(Integer, default=0)
    available_credits = Column(Integer, default=0)
    used_credits = Column(Integer, default=0)
    
    # Business owner specific wallet fields
    credits_allocated = Column(Integer, default=0)
    credits_used = Column(Integer, default=0)
    credits_remaining = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    credit_distributions_sent = relationship("CreditDistribution", foreign_keys="CreditDistribution.from_reseller_id", back_populates="from_reseller")
    credit_distributions_received = relationship("CreditDistribution", foreign_keys="CreditDistribution.to_business_user_id", back_populates="to_business_user")
    messages = relationship("Message", back_populates="user")
    linked_devices = relationship("UnofficialLinkedDevice", back_populates="user")

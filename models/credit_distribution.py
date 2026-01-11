from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime
import uuid

class CreditDistribution(Base):
    __tablename__ = "credit_distributions"
    
    distribution_id = Column(String, primary_key=True, default=lambda: f"dist-{uuid.uuid4().hex[:8]}")
    from_reseller_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    to_business_user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    
    credits_shared = Column(Integer, nullable=False)
    shared_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    from_reseller = relationship("User", foreign_keys=[from_reseller_id], back_populates="credit_distributions_sent")
    to_business_user = relationship("User", foreign_keys=[to_business_user_id], back_populates="credit_distributions_received")

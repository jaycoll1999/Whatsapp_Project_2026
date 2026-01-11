from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean, Numeric, Enum
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime
import uuid
import enum

class AnalyticsPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class ResellerAnalytics(Base):
    __tablename__ = "reseller_analytics"
    
    analytics_id = Column(String, primary_key=True, default=lambda: f"analytics-{uuid.uuid4().hex[:8]}")
    reseller_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Credit analytics
    total_credits_purchased = Column(Integer, default=0)
    total_credits_distributed = Column(Integer, default=0)
    total_credits_used = Column(Integer, default=0)
    remaining_credits = Column(Integer, default=0)
    
    # Revenue analytics
    total_revenue = Column(Numeric(10, 2), default=0.00)
    revenue_from_credits = Column(Numeric(10, 2), default=0.00)
    revenue_from_subscriptions = Column(Numeric(10, 2), default=0.00)
    
    # Business user analytics
    total_business_users = Column(Integer, default=0)
    active_business_users = Column(Integer, default=0)
    inactive_business_users = Column(Integer, default=0)
    
    # Message analytics
    total_messages_sent = Column(Integer, default=0)
    total_messages_delivered = Column(Integer, default=0)
    total_messages_failed = Column(Integer, default=0)
    
    # Period and timestamps
    analytics_period = Column(Enum(AnalyticsPeriod), default=AnalyticsPeriod.MONTHLY)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reseller = relationship("User", back_populates="analytics")
    business_user_stats = relationship("BusinessUserAnalytics", back_populates="reseller_analytics")
    
    def __repr__(self):
        return f"<ResellerAnalytics(id={self.analytics_id}, reseller_id={self.reseller_id}, period={self.analytics_period})>"
    
    def to_dict(self):
        """Convert analytics to dictionary format"""
        return {
            "reseller_id": self.reseller_id,
            "analytics": {
                "total_credits_purchased": self.total_credits_purchased,
                "total_credits_distributed": self.total_credits_distributed,
                "total_credits_used": self.total_credits_used,
                "remaining_credits": self.remaining_credits,
                "total_revenue": float(self.total_revenue),
                "revenue_from_credits": float(self.revenue_from_credits),
                "revenue_from_subscriptions": float(self.revenue_from_subscriptions),
                "total_business_users": self.total_business_users,
                "active_business_users": self.active_business_users,
                "inactive_business_users": self.inactive_business_users,
                "total_messages_sent": self.total_messages_sent,
                "total_messages_delivered": self.total_messages_delivered,
                "total_messages_failed": self.total_messages_failed,
                "analytics_period": self.analytics_period,
                "period_start": self.period_start.isoformat() if self.period_start else None,
                "period_end": self.period_end.isoformat() if self.period_end else None
            },
            "business_user_stats": [
                stat.to_dict() for stat in self.business_user_stats
            ]
        }
    
    def calculate_credit_utilization(self):
        """Calculate credit utilization percentage"""
        if self.total_credits_distributed == 0:
            return 0.0
        return (self.total_credits_used / self.total_credits_distributed) * 100
    
    def calculate_delivery_rate(self):
        """Calculate message delivery rate percentage"""
        if self.total_messages_sent == 0:
            return 0.0
        return (self.total_messages_delivered / self.total_messages_sent) * 100
    
    def update_analytics(self, **kwargs):
        """Update analytics with new data"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

class BusinessUserAnalytics(Base):
    __tablename__ = "business_user_analytics"
    
    stat_id = Column(String, primary_key=True, default=lambda: f"stat-{uuid.uuid4().hex[:8]}")
    reseller_analytics_id = Column(String, ForeignKey("reseller_analytics.analytics_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Credit stats for business user
    credits_allocated = Column(Integer, default=0)
    credits_used = Column(Integer, default=0)
    credits_remaining = Column(Integer, default=0)
    
    # Message stats
    messages_sent = Column(Integer, default=0)
    messages_delivered = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    
    # Device stats
    active_devices = Column(Integer, default=0)
    total_devices = Column(Integer, default=0)
    
    # Session stats
    active_sessions = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    
    # Revenue contribution
    revenue_generated = Column(Numeric(10, 2), default=0.00)
    
    # Period and timestamps
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reseller_analytics = relationship("ResellerAnalytics", back_populates="business_user_stats")
    user = relationship("User", back_populates="business_analytics")
    
    def __repr__(self):
        return f"<BusinessUserAnalytics(id={self.stat_id}, user_id={self.user_id}, credits_used={self.credits_used})>"
    
    def to_dict(self):
        """Convert business user stats to dictionary format"""
        # Get user info if available
        business_name = None
        if self.user:
            business_name = self.user.business_name
        
        return {
            "user_id": self.user_id,
            "business_name": business_name,
            "credits_allocated": self.credits_allocated,
            "credits_used": self.credits_used,
            "credits_remaining": self.credits_remaining,
            "messages_sent": self.messages_sent,
            "messages_delivered": self.messages_delivered,
            "messages_failed": self.messages_failed,
            "active_devices": self.active_devices,
            "total_devices": self.total_devices,
            "active_sessions": self.active_sessions,
            "total_sessions": self.total_sessions,
            "revenue_generated": float(self.revenue_generated),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None
        }
    
    def calculate_credit_utilization(self):
        """Calculate credit utilization percentage"""
        if self.credits_allocated == 0:
            return 0.0
        return (self.credits_used / self.credits_allocated) * 100
    
    def calculate_delivery_rate(self):
        """Calculate message delivery rate percentage"""
        if self.messages_sent == 0:
            return 0.0
        return (self.messages_delivered / self.messages_sent) * 100
    
    def update_stats(self, **kwargs):
        """Update stats with new data"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

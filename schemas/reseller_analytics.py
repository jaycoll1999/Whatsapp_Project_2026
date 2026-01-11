from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AnalyticsPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

# Business User Stats Schema
class BusinessUserStats(BaseModel):
    user_id: str
    business_name: Optional[str] = None
    credits_allocated: int = 0
    credits_used: int = 0
    credits_remaining: int = 0
    messages_sent: int = 0
    messages_delivered: int = 0
    messages_failed: int = 0
    active_devices: int = 0
    total_devices: int = 0
    active_sessions: int = 0
    total_sessions: int = 0
    revenue_generated: float = 0.0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Analytics Data Schema
class AnalyticsData(BaseModel):
    total_credits_purchased: int = 0
    total_credits_distributed: int = 0
    total_credits_used: int = 0
    remaining_credits: int = 0
    total_revenue: float = 0.0
    revenue_from_credits: float = 0.0
    revenue_from_subscriptions: float = 0.0
    total_business_users: int = 0
    active_business_users: int = 0
    inactive_business_users: int = 0
    total_messages_sent: int = 0
    total_messages_delivered: int = 0
    total_messages_failed: int = 0
    analytics_period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Main Reseller Analytics Response Schema
class ResellerAnalyticsResponse(BaseModel):
    reseller_id: str
    analytics: AnalyticsData
    business_user_stats: List[BusinessUserStats] = []
    
    class Config:
        from_attributes = True

# Create Analytics Request Schema
class CreateAnalyticsRequest(BaseModel):
    reseller_id: str
    analytics_period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    period_start: datetime
    period_end: datetime
    total_credits_purchased: int = 0
    total_credits_distributed: int = 0
    total_credits_used: int = 0
    remaining_credits: int = 0
    total_revenue: float = 0.0
    revenue_from_credits: float = 0.0
    revenue_from_subscriptions: float = 0.0
    total_business_users: int = 0
    active_business_users: int = 0
    inactive_business_users: int = 0
    total_messages_sent: int = 0
    total_messages_delivered: int = 0
    total_messages_failed: int = 0

# Update Analytics Request Schema
class UpdateAnalyticsRequest(BaseModel):
    total_credits_purchased: Optional[int] = None
    total_credits_distributed: Optional[int] = None
    total_credits_used: Optional[int] = None
    remaining_credits: Optional[int] = None
    total_revenue: Optional[float] = None
    revenue_from_credits: Optional[float] = None
    revenue_from_subscriptions: Optional[float] = None
    total_business_users: Optional[int] = None
    active_business_users: Optional[int] = None
    inactive_business_users: Optional[int] = None
    total_messages_sent: Optional[int] = None
    total_messages_delivered: Optional[int] = None
    total_messages_failed: Optional[int] = None

# Business User Stats Create Request
class CreateBusinessUserStatsRequest(BaseModel):
    reseller_analytics_id: str
    user_id: str
    credits_allocated: int = 0
    credits_used: int = 0
    credits_remaining: int = 0
    messages_sent: int = 0
    messages_delivered: int = 0
    messages_failed: int = 0
    active_devices: int = 0
    total_devices: int = 0
    active_sessions: int = 0
    total_sessions: int = 0
    revenue_generated: float = 0.0
    period_start: datetime
    period_end: datetime

# Business User Stats Update Request
class UpdateBusinessUserStatsRequest(BaseModel):
    credits_allocated: Optional[int] = None
    credits_used: Optional[int] = None
    credits_remaining: Optional[int] = None
    messages_sent: Optional[int] = None
    messages_delivered: Optional[int] = None
    messages_failed: Optional[int] = None
    active_devices: Optional[int] = None
    total_devices: Optional[int] = None
    active_sessions: Optional[int] = None
    total_sessions: Optional[int] = None
    revenue_generated: Optional[float] = None

# Analytics Filter Schema
class AnalyticsFilter(BaseModel):
    reseller_id: Optional[str] = None
    analytics_period: Optional[AnalyticsPeriod] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_business_stats: bool = True

# Analytics Summary Schema
class AnalyticsSummary(BaseModel):
    total_resellers: int
    total_credits_purchased: int
    total_credits_distributed: int
    total_credits_used: int
    total_remaining_credits: int
    total_revenue: float
    total_business_users: int
    total_messages_sent: int
    average_credit_utilization: float
    average_delivery_rate: float

# Reseller Performance Metrics
class ResellerPerformanceMetrics(BaseModel):
    reseller_id: str
    reseller_name: Optional[str] = None
    total_credits_purchased: int
    total_credits_distributed: int
    total_credits_used: int
    remaining_credits: int
    total_revenue: float
    total_business_users: int
    active_business_users: int
    total_messages_sent: int
    credit_utilization_rate: float
    delivery_rate: float
    revenue_per_business_user: float
    growth_rate: float = 0.0
    rank: Optional[int] = None

# Top Performers Schema
class TopPerformersResponse(BaseModel):
    top_resellers_by_revenue: List[ResellerPerformanceMetrics]
    top_resellers_by_credits: List[ResellerPerformanceMetrics]
    top_resellers_by_users: List[ResellerPerformanceMetrics]

# Analytics Trends Schema
class AnalyticsTrends(BaseModel):
    reseller_id: str
    period: AnalyticsPeriod
    trend_data: List[Dict[str, Any]]
    
    # Trend metrics
    credits_purchased_trend: List[Dict[str, Any]]
    credits_distributed_trend: List[Dict[str, Any]]
    credits_used_trend: List[Dict[str, Any]]
    revenue_trend: List[Dict[str, Any]]
    business_users_trend: List[Dict[str, Any]]
    messages_sent_trend: List[Dict[str, Any]]

# Analytics Comparison Schema
class AnalyticsComparison(BaseModel):
    current_period: AnalyticsData
    previous_period: AnalyticsData
    comparison_metrics: Dict[str, float]  # Percentage changes
    
    # Growth metrics
    credits_purchased_growth: float
    credits_distributed_growth: float
    credits_used_growth: float
    revenue_growth: float
    business_users_growth: float
    messages_sent_growth: float

# Analytics Export Schema
class AnalyticsExportRequest(BaseModel):
    reseller_id: Optional[str] = None
    analytics_period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    start_date: datetime
    end_date: datetime
    export_format: str = "json"  # json, csv, excel
    include_business_stats: bool = True
    include_trends: bool = False

# Analytics Export Response
class AnalyticsExportResponse(BaseModel):
    export_id: str
    file_url: Optional[str] = None
    export_status: str  # pending, processing, completed, failed
    total_records: int
    file_size: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# Analytics Health Check
class AnalyticsHealthCheck(BaseModel):
    status: str  # healthy, warning, error
    total_analytics_records: int
    last_updated: Optional[datetime] = None
    data_freshness: str  # fresh, stale, outdated
    issues: List[str] = []
    recommendations: List[str] = []

# Analytics Cleanup Request
class AnalyticsCleanupRequest(BaseModel):
    older_than_days: int = 365
    analytics_period: Optional[AnalyticsPeriod] = None
    dry_run: bool = True

# Analytics Cleanup Response
class AnalyticsCleanupResponse(BaseModel):
    total_records_found: int
    records_to_delete: int
    records_deleted: int
    dry_run: bool
    message: str

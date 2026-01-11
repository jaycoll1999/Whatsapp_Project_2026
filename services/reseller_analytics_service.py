from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from models.reseller_analytics import ResellerAnalytics, BusinessUserAnalytics, AnalyticsPeriod
from models.user import User
from models.credit_distribution import CreditDistribution
from models.message_usage_log import MessageUsageLog
from schemas.reseller_analytics import (
    ResellerAnalyticsResponse, AnalyticsData, BusinessUserStats,
    CreateAnalyticsRequest, UpdateAnalyticsRequest,
    CreateBusinessUserStatsRequest, UpdateBusinessUserStatsRequest,
    AnalyticsFilter, AnalyticsSummary, ResellerPerformanceMetrics,
    TopPerformersResponse, AnalyticsTrends, AnalyticsComparison,
    AnalyticsExportRequest, AnalyticsExportResponse,
    AnalyticsHealthCheck, AnalyticsCleanupRequest, AnalyticsCleanupResponse
)
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class ResellerAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_analytics(self, request: CreateAnalyticsRequest) -> ResellerAnalyticsResponse:
        """Create new analytics record for reseller"""
        # Validate reseller exists
        reseller = self.db.query(User).filter(
            and_(User.user_id == request.reseller_id, User.role == "reseller")
        ).first()
        if not reseller:
            raise ValueError("Reseller not found")
        
        # Create analytics record
        analytics = ResellerAnalytics(
            reseller_id=request.reseller_id,
            analytics_period=request.analytics_period,
            period_start=request.period_start,
            period_end=request.period_end,
            total_credits_purchased=request.total_credits_purchased,
            total_credits_distributed=request.total_credits_distributed,
            total_credits_used=request.total_credits_used,
            remaining_credits=request.remaining_credits,
            total_revenue=request.total_revenue,
            revenue_from_credits=request.revenue_from_credits,
            revenue_from_subscriptions=request.revenue_from_subscriptions,
            total_business_users=request.total_business_users,
            active_business_users=request.active_business_users,
            inactive_business_users=request.inactive_business_users,
            total_messages_sent=request.total_messages_sent,
            total_messages_delivered=request.total_messages_delivered,
            total_messages_failed=request.total_messages_failed
        )
        
        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)
        
        return self._convert_to_response(analytics)
    
    def get_analytics_by_id(self, analytics_id: str) -> Optional[ResellerAnalytics]:
        """Get analytics record by ID"""
        return self.db.query(ResellerAnalytics).filter(
            ResellerAnalytics.analytics_id == analytics_id
        ).first()
    
    def get_reseller_analytics(
        self, 
        reseller_id: str, 
        analytics_period: Optional[AnalyticsPeriod] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_business_stats: bool = True
    ) -> List[ResellerAnalyticsResponse]:
        """Get analytics for a specific reseller"""
        query = self.db.query(ResellerAnalytics).filter(
            ResellerAnalytics.reseller_id == reseller_id
        )
        
        if analytics_period:
            query = query.filter(ResellerAnalytics.analytics_period == analytics_period)
        
        if start_date:
            query = query.filter(ResellerAnalytics.period_start >= start_date)
        
        if end_date:
            query = query.filter(ResellerAnalytics.period_end <= end_date)
        
        query = query.order_by(desc(ResellerAnalytics.period_start))
        
        analytics_records = query.all()
        
        return [
            self._convert_to_response(analytics, include_business_stats)
            for analytics in analytics_records
        ]
    
    def get_latest_analytics(self, reseller_id: str) -> Optional[ResellerAnalyticsResponse]:
        """Get latest analytics for reseller"""
        analytics = self.db.query(ResellerAnalytics).filter(
            ResellerAnalytics.reseller_id == reseller_id
        ).order_by(desc(ResellerAnalytics.period_start)).first()
        
        if analytics:
            return self._convert_to_response(analytics)
        
        return None
    
    def update_analytics(self, analytics_id: str, update_data: UpdateAnalyticsRequest) -> Optional[ResellerAnalytics]:
        """Update analytics record"""
        analytics = self.get_analytics_by_id(analytics_id)
        if not analytics:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(analytics, field):
                setattr(analytics, field, value)
        
        analytics.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(analytics)
        
        return analytics
    
    def create_business_user_stats(self, request: CreateBusinessUserStatsRequest) -> BusinessUserAnalytics:
        """Create business user statistics"""
        # Validate analytics record exists
        analytics = self.db.query(ResellerAnalytics).filter(
            ResellerAnalytics.analytics_id == request.reseller_analytics_id
        ).first()
        if not analytics:
            raise ValueError("Analytics record not found")
        
        # Validate user exists
        user = self.db.query(User).filter(User.user_id == request.user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Create business user stats
        stats = BusinessUserAnalytics(
            reseller_analytics_id=request.reseller_analytics_id,
            user_id=request.user_id,
            credits_allocated=request.credits_allocated,
            credits_used=request.credits_used,
            credits_remaining=request.credits_remaining,
            messages_sent=request.messages_sent,
            messages_delivered=request.messages_delivered,
            messages_failed=request.messages_failed,
            active_devices=request.active_devices,
            total_devices=request.total_devices,
            active_sessions=request.active_sessions,
            total_sessions=request.total_sessions,
            revenue_generated=request.revenue_generated,
            period_start=request.period_start,
            period_end=request.period_end
        )
        
        self.db.add(stats)
        self.db.commit()
        self.db.refresh(stats)
        
        return stats
    
    def update_business_user_stats(self, stat_id: str, update_data: UpdateBusinessUserStatsRequest) -> Optional[BusinessUserAnalytics]:
        """Update business user statistics"""
        stats = self.db.query(BusinessUserAnalytics).filter(
            BusinessUserAnalytics.stat_id == stat_id
        ).first()
        
        if not stats:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(stats, field):
                setattr(stats, field, value)
        
        stats.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(stats)
        
        return stats
    
    def get_analytics_summary(self) -> AnalyticsSummary:
        """Get overall analytics summary"""
        # Get all reseller analytics
        analytics_query = self.db.query(ResellerAnalytics)
        
        # Calculate totals
        total_resellers = self.db.query(User).filter(User.role == "reseller").count()
        total_credits_purchased = analytics_query.with_entities(
            func.sum(ResellerAnalytics.total_credits_purchased)
        ).scalar() or 0
        
        total_credits_distributed = analytics_query.with_entities(
            func.sum(ResellerAnalytics.total_credits_distributed)
        ).scalar() or 0
        
        total_credits_used = analytics_query.with_entities(
            func.sum(ResellerAnalytics.total_credits_used)
        ).scalar() or 0
        
        total_remaining_credits = analytics_query.with_entities(
            func.sum(ResellerAnalytics.remaining_credits)
        ).scalar() or 0
        
        total_revenue = analytics_query.with_entities(
            func.sum(ResellerAnalytics.total_revenue)
        ).scalar() or Decimal('0.00')
        
        total_business_users = analytics_query.with_entities(
            func.sum(ResellerAnalytics.total_business_users)
        ).scalar() or 0
        
        total_messages_sent = analytics_query.with_entities(
            func.sum(ResellerAnalytics.total_messages_sent)
        ).scalar() or 0
        
        # Calculate averages
        avg_credit_utilization = 0.0
        if total_credits_distributed > 0:
            avg_credit_utilization = (total_credits_used / total_credits_distributed) * 100
        
        avg_delivery_rate = 0.0
        if total_messages_sent > 0:
            total_delivered = analytics_query.with_entities(
                func.sum(ResellerAnalytics.total_messages_delivered)
            ).scalar() or 0
            avg_delivery_rate = (total_delivered / total_messages_sent) * 100
        
        return AnalyticsSummary(
            total_resellers=total_resellers,
            total_credits_purchased=total_credits_purchased,
            total_credits_distributed=total_credits_distributed,
            total_credits_used=total_credits_used,
            total_remaining_credits=total_remaining_credits,
            total_revenue=float(total_revenue),
            total_business_users=total_business_users,
            total_messages_sent=total_messages_sent,
            average_credit_utilization=avg_credit_utilization,
            average_delivery_rate=avg_delivery_rate
        )
    
    def get_top_performers(self, limit: int = 10) -> TopPerformersResponse:
        """Get top performing resellers"""
        # Get latest analytics for each reseller
        subquery = self.db.query(
            ResellerAnalytics.reseller_id,
            func.max(ResellerAnalytics.period_start).label('latest_period')
        ).group_by(ResellerAnalytics.reseller_id).subquery()
        
        latest_analytics = self.db.query(ResellerAnalytics).join(
            subquery,
            and_(
                ResellerAnalytics.reseller_id == subquery.c.reseller_id,
                ResellerAnalytics.period_start == subquery.c.latest_period
            )
        ).all()
        
        # Convert to performance metrics
        performers = []
        for analytics in latest_analytics:
            reseller = self.db.query(User).filter(
                User.user_id == analytics.reseller_id
            ).first()
            
            metrics = ResellerPerformanceMetrics(
                reseller_id=analytics.reseller_id,
                reseller_name=reseller.name if reseller else None,
                total_credits_purchased=analytics.total_credits_purchased,
                total_credits_distributed=analytics.total_credits_distributed,
                total_credits_used=analytics.total_credits_used,
                remaining_credits=analytics.remaining_credits,
                total_revenue=float(analytics.total_revenue),
                total_business_users=analytics.total_business_users,
                active_business_users=analytics.active_business_users,
                total_messages_sent=analytics.total_messages_sent,
                credit_utilization_rate=analytics.calculate_credit_utilization(),
                delivery_rate=analytics.calculate_delivery_rate(),
                revenue_per_business_user=(
                    float(analytics.total_revenue) / analytics.total_business_users
                    if analytics.total_business_users > 0 else 0.0
                )
            )
            performers.append(metrics)
        
        # Sort by different criteria
        top_by_revenue = sorted(performers, key=lambda x: x.total_revenue, reverse=True)[:limit]
        top_by_credits = sorted(performers, key=lambda x: x.total_credits_distributed, reverse=True)[:limit]
        top_by_users = sorted(performers, key=lambda x: x.total_business_users, reverse=True)[:limit]
        
        # Add ranks
        for i, metric in enumerate(top_by_revenue, 1):
            metric.rank = i
        
        return TopPerformersResponse(
            top_resellers_by_revenue=top_by_revenue,
            top_resellers_by_credits=top_by_credits,
            top_resellers_by_users=top_by_users
        )
    
    def get_analytics_trends(
        self, 
        reseller_id: str, 
        period: AnalyticsPeriod,
        months: int = 12
    ) -> AnalyticsTrends:
        """Get analytics trends for a reseller"""
        # Get analytics for the specified period
        start_date = datetime.utcnow() - timedelta(days=months * 30)
        
        analytics_records = self.db.query(ResellerAnalytics).filter(
            and_(
                ResellerAnalytics.reseller_id == reseller_id,
                ResellerAnalytics.analytics_period == period,
                ResellerAnalytics.period_start >= start_date
            )
        ).order_by(asc(ResellerAnalytics.period_start)).all()
        
        # Prepare trend data
        trend_data = []
        credits_purchased_trend = []
        credits_distributed_trend = []
        credits_used_trend = []
        revenue_trend = []
        business_users_trend = []
        messages_sent_trend = []
        
        for analytics in analytics_records:
            period_data = {
                "period_start": analytics.period_start.isoformat(),
                "period_end": analytics.period_end.isoformat(),
                "total_credits_purchased": analytics.total_credits_purchased,
                "total_credits_distributed": analytics.total_credits_distributed,
                "total_credits_used": analytics.total_credits_used,
                "total_revenue": float(analytics.total_revenue),
                "total_business_users": analytics.total_business_users,
                "total_messages_sent": analytics.total_messages_sent,
                "credit_utilization": analytics.calculate_credit_utilization(),
                "delivery_rate": analytics.calculate_delivery_rate()
            }
            trend_data.append(period_data)
            
            credits_purchased_trend.append({
                "period": analytics.period_start.isoformat(),
                "value": analytics.total_credits_purchased
            })
            
            credits_distributed_trend.append({
                "period": analytics.period_start.isoformat(),
                "value": analytics.total_credits_distributed
            })
            
            credits_used_trend.append({
                "period": analytics.period_start.isoformat(),
                "value": analytics.total_credits_used
            })
            
            revenue_trend.append({
                "period": analytics.period_start.isoformat(),
                "value": float(analytics.total_revenue)
            })
            
            business_users_trend.append({
                "period": analytics.period_start.isoformat(),
                "value": analytics.total_business_users
            })
            
            messages_sent_trend.append({
                "period": analytics.period_start.isoformat(),
                "value": analytics.total_messages_sent
            })
        
        return AnalyticsTrends(
            reseller_id=reseller_id,
            period=period,
            trend_data=trend_data,
            credits_purchased_trend=credits_purchased_trend,
            credits_distributed_trend=credits_distributed_trend,
            credits_used_trend=credits_used_trend,
            revenue_trend=revenue_trend,
            business_users_trend=business_users_trend,
            messages_sent_trend=messages_sent_trend
        )
    
    def compare_periods(
        self, 
        reseller_id: str,
        current_period_start: datetime,
        current_period_end: datetime,
        previous_period_start: datetime,
        previous_period_end: datetime
    ) -> AnalyticsComparison:
        """Compare analytics between two periods"""
        # Get current period analytics
        current_analytics = self.db.query(ResellerAnalytics).filter(
            and_(
                ResellerAnalytics.reseller_id == reseller_id,
                ResellerAnalytics.period_start >= current_period_start,
                ResellerAnalytics.period_end <= current_period_end
            )
        ).first()
        
        # Get previous period analytics
        previous_analytics = self.db.query(ResellerAnalytics).filter(
            and_(
                ResellerAnalytics.reseller_id == reseller_id,
                ResellerAnalytics.period_start >= previous_period_start,
                ResellerAnalytics.period_end <= previous_period_end
            )
        ).first()
        
        # Convert to analytics data
        current_data = self._convert_to_analytics_data(current_analytics)
        previous_data = self._convert_to_analytics_data(previous_analytics)
        
        # Calculate comparison metrics
        comparison_metrics = {}
        credits_purchased_growth = 0.0
        credits_distributed_growth = 0.0
        credits_used_growth = 0.0
        revenue_growth = 0.0
        business_users_growth = 0.0
        messages_sent_growth = 0.0
        
        if previous_analytics:
            if previous_analytics.total_credits_purchased > 0:
                credits_purchased_growth = (
                    (current_analytics.total_credits_purchased - previous_analytics.total_credits_purchased)
                    / previous_analytics.total_credits_purchased * 100
                )
            
            if previous_analytics.total_credits_distributed > 0:
                credits_distributed_growth = (
                    (current_analytics.total_credits_distributed - previous_analytics.total_credits_distributed)
                    / previous_analytics.total_credits_distributed * 100
                )
            
            if previous_analytics.total_credits_used > 0:
                credits_used_growth = (
                    (current_analytics.total_credits_used - previous_analytics.total_credits_used)
                    / previous_analytics.total_credits_used * 100
                )
            
            if previous_analytics.total_revenue > 0:
                revenue_growth = (
                    (float(current_analytics.total_revenue) - float(previous_analytics.total_revenue))
                    / float(previous_analytics.total_revenue) * 100
                )
            
            if previous_analytics.total_business_users > 0:
                business_users_growth = (
                    (current_analytics.total_business_users - previous_analytics.total_business_users)
                    / previous_analytics.total_business_users * 100
                )
            
            if previous_analytics.total_messages_sent > 0:
                messages_sent_growth = (
                    (current_analytics.total_messages_sent - previous_analytics.total_messages_sent)
                    / previous_analytics.total_messages_sent * 100
                )
        
        comparison_metrics = {
            "credits_purchased_growth": credits_purchased_growth,
            "credits_distributed_growth": credits_distributed_growth,
            "credits_used_growth": credits_used_growth,
            "revenue_growth": revenue_growth,
            "business_users_growth": business_users_growth,
            "messages_sent_growth": messages_sent_growth
        }
        
        return AnalyticsComparison(
            current_period=current_data,
            previous_period=previous_data,
            comparison_metrics=comparison_metrics,
            credits_purchased_growth=credits_purchased_growth,
            credits_distributed_growth=credits_distributed_growth,
            credits_used_growth=credits_used_growth,
            revenue_growth=revenue_growth,
            business_users_growth=business_users_growth,
            messages_sent_growth=messages_sent_growth
        )
    
    def get_health_check(self) -> AnalyticsHealthCheck:
        """Get analytics system health check"""
        total_records = self.db.query(ResellerAnalytics).count()
        
        # Get last updated time
        last_analytics = self.db.query(ResellerAnalytics).order_by(
            desc(ResellerAnalytics.updated_at)
        ).first()
        
        last_updated = last_analytics.updated_at if last_analytics else None
        
        # Determine data freshness
        data_freshness = "fresh"
        issues = []
        recommendations = []
        
        if not last_updated:
            data_freshness = "outdated"
            issues.append("No analytics data found")
            recommendations.append("Generate initial analytics data")
        else:
            days_since_update = (datetime.utcnow() - last_updated).days
            if days_since_update > 7:
                data_freshness = "stale"
                issues.append(f"Analytics data is {days_since_update} days old")
                recommendations.append("Update analytics data regularly")
            elif days_since_update > 1:
                data_freshness = "stale"
                recommendations.append("Consider updating analytics data")
        
        # Determine overall status
        status = "healthy"
        if issues:
            status = "warning" if len(issues) <= 2 else "error"
        
        return AnalyticsHealthCheck(
            status=status,
            total_analytics_records=total_records,
            last_updated=last_updated,
            data_freshness=data_freshness,
            issues=issues,
            recommendations=recommendations
        )
    
    def cleanup_old_analytics(self, cleanup_request: AnalyticsCleanupRequest) -> AnalyticsCleanupResponse:
        """Clean up old analytics records"""
        cutoff_date = datetime.utcnow() - timedelta(days=cleanup_request.older_than_days)
        
        query = self.db.query(ResellerAnalytics).filter(
            ResellerAnalytics.period_end < cutoff_date
        )
        
        if cleanup_request.analytics_period:
            query = query.filter(
                ResellerAnalytics.analytics_period == cleanup_request.analytics_period
            )
        
        total_records_found = query.count()
        
        if cleanup_request.dry_run:
            return AnalyticsCleanupResponse(
                total_records_found=total_records_found,
                records_to_delete=total_records_found,
                records_deleted=0,
                dry_run=True,
                message=f"Found {total_records_found} records to delete (dry run)"
            )
        
        # Actually delete the records
        deleted_count = query.delete()
        self.db.commit()
        
        return AnalyticsCleanupResponse(
            total_records_found=total_records_found,
            records_to_delete=total_records_found,
            records_deleted=deleted_count,
            dry_run=False,
            message=f"Deleted {deleted_count} old analytics records"
        )
    
    def _convert_to_response(self, analytics: ResellerAnalytics, include_business_stats: bool = True) -> ResellerAnalyticsResponse:
        """Convert analytics model to response schema"""
        # Get business user stats if requested
        business_stats = []
        if include_business_stats:
            business_stats = [
                BusinessUserStats(
                    user_id=stat.user_id,
                    business_name=stat.user.business_name if stat.user else None,
                    credits_allocated=stat.credits_allocated,
                    credits_used=stat.credits_used,
                    credits_remaining=stat.credits_remaining,
                    messages_sent=stat.messages_sent,
                    messages_delivered=stat.messages_delivered,
                    messages_failed=stat.messages_failed,
                    active_devices=stat.active_devices,
                    total_devices=stat.total_devices,
                    active_sessions=stat.active_sessions,
                    total_sessions=stat.total_sessions,
                    revenue_generated=float(stat.revenue_generated),
                    period_start=stat.period_start,
                    period_end=stat.period_end
                ) for stat in analytics.business_user_stats
            ]
        
        # Convert analytics data
        analytics_data = AnalyticsData(
            total_credits_purchased=analytics.total_credits_purchased,
            total_credits_distributed=analytics.total_credits_distributed,
            total_credits_used=analytics.total_credits_used,
            remaining_credits=analytics.remaining_credits,
            total_revenue=float(analytics.total_revenue),
            revenue_from_credits=float(analytics.revenue_from_credits),
            revenue_from_subscriptions=float(analytics.revenue_from_subscriptions),
            total_business_users=analytics.total_business_users,
            active_business_users=analytics.active_business_users,
            inactive_business_users=analytics.inactive_business_users,
            total_messages_sent=analytics.total_messages_sent,
            total_messages_delivered=analytics.total_messages_delivered,
            total_messages_failed=analytics.total_messages_failed,
            analytics_period=analytics.analytics_period,
            period_start=analytics.period_start,
            period_end=analytics.period_end
        )
        
        return ResellerAnalyticsResponse(
            reseller_id=analytics.reseller_id,
            analytics=analytics_data,
            business_user_stats=business_stats
        )
    
    def _convert_to_analytics_data(self, analytics: Optional[ResellerAnalytics]) -> AnalyticsData:
        """Convert analytics model to analytics data schema"""
        if not analytics:
            return AnalyticsData()
        
        return AnalyticsData(
            total_credits_purchased=analytics.total_credits_purchased,
            total_credits_distributed=analytics.total_credits_distributed,
            total_credits_used=analytics.total_credits_used,
            remaining_credits=analytics.remaining_credits,
            total_revenue=float(analytics.total_revenue),
            revenue_from_credits=float(analytics.revenue_from_credits),
            revenue_from_subscriptions=float(analytics.revenue_from_subscriptions),
            total_business_users=analytics.total_business_users,
            active_business_users=analytics.active_business_users,
            inactive_business_users=analytics.inactive_business_users,
            total_messages_sent=analytics.total_messages_sent,
            total_messages_delivered=analytics.total_messages_delivered,
            total_messages_failed=analytics.total_messages_failed,
            analytics_period=analytics.analytics_period,
            period_start=analytics.period_start,
            period_end=analytics.period_end
        )

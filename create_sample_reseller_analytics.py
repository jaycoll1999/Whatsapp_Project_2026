from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from models.reseller_analytics import ResellerAnalytics, BusinessUserAnalytics, AnalyticsPeriod
from models.user import User
from services.reseller_analytics_service import ResellerAnalyticsService
from schemas.reseller_analytics import CreateAnalyticsRequest, CreateBusinessUserStatsRequest
from datetime import datetime, timedelta
import uuid

def create_sample_reseller_analytics():
    db = SessionLocal()
    analytics_service = ResellerAnalyticsService(db)
    
    # Check if analytics already exists
    existing_analytics = db.query(ResellerAnalytics).filter(
        ResellerAnalytics.reseller_id == "uuid-reseller-001"
    ).first()
    if existing_analytics:
        print("Sample reseller analytics already exists!")
        return
    
    # Check if reseller exists
    reseller = db.query(User).filter(
        and_(User.user_id == "uuid-reseller-001", User.role == "reseller")
    ).first()
    if not reseller:
        print("Reseller not found! Please create sample reseller first.")
        return
    
    # Create sample analytics record
    analytics_request = CreateAnalyticsRequest(
        reseller_id="uuid-reseller-001",
        analytics_period=AnalyticsPeriod.MONTHLY,
        period_start=datetime(2026, 1, 1),
        period_end=datetime(2026, 1, 31),
        total_credits_purchased=100000,
        total_credits_distributed=25000,
        total_credits_used=18000,
        remaining_credits=75000,
        total_revenue=5000.0,
        revenue_from_credits=2500.0,
        revenue_from_subscriptions=2500.0,
        total_business_users=5,
        active_business_users=4,
        inactive_business_users=1,
        total_messages_sent=18000,
        total_messages_delivered=17500,
        total_messages_failed=500
    )
    
    try:
        analytics_response = analytics_service.create_analytics(analytics_request)
        
        # Update analytics record with sample data
        analytics = analytics_service.get_analytics_by_id(analytics_response.analytics_id)
        analytics.analytics_id = "analytics-111"
        analytics.created_at = datetime(2026, 1, 31, 23, 59, 59)
        analytics.updated_at = datetime(2026, 1, 31, 23, 59, 59)
        
        db.commit()
        db.refresh(analytics)
        
        print(f"Sample reseller analytics created:")
        print(f"Analytics ID: {analytics.analytics_id}")
        print(f"Reseller ID: {analytics.reseller_id}")
        print(f"Period: {analytics.analytics_period}")
        print(f"Period Start: {analytics.period_start}")
        print(f"Period End: {analytics.period_end}")
        print(f"Total Credits Purchased: {analytics.total_credits_purchased}")
        print(f"Total Credits Distributed: {analytics.total_credits_distributed}")
        print(f"Total Credits Used: {analytics.total_credits_used}")
        print(f"Remaining Credits: {analytics.remaining_credits}")
        print(f"Total Revenue: ${analytics.total_revenue}")
        print(f"Total Business Users: {analytics.total_business_users}")
        print(f"Active Business Users: {analytics.active_business_users}")
        print(f"Total Messages Sent: {analytics.total_messages_sent}")
        print(f"Total Messages Delivered: {analytics.total_messages_delivered}")
        print(f"Total Messages Failed: {analytics.total_messages_failed}")
        print(f"Credit Utilization: {analytics.calculate_credit_utilization():.2f}%")
        print(f"Delivery Rate: {analytics.calculate_delivery_rate():.2f}%")
        
        # Create sample business user stats
        business_user_stats_request = CreateBusinessUserStatsRequest(
            reseller_analytics_id=analytics.analytics_id,
            user_id="uuid-business-101",
            credits_allocated=5000,
            credits_used=3200,
            credits_remaining=1800,
            messages_sent=3200,
            messages_delivered=3100,
            messages_failed=100,
            active_devices=2,
            total_devices=3,
            active_sessions=1,
            total_sessions=5,
            revenue_generated=800.0,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 1, 31)
        )
        
        business_stats = analytics_service.create_business_user_stats(business_user_stats_request)
        business_stats.stat_id = "stat-222"
        business_stats.created_at = datetime(2026, 1, 31, 23, 59, 59)
        business_stats.updated_at = datetime(2026, 1, 31, 23, 59, 59)
        
        db.commit()
        db.refresh(business_stats)
        
        print(f"\nSample business user stats created:")
        print(f"Stat ID: {business_stats.stat_id}")
        print(f"User ID: {business_stats.user_id}")
        print(f"Business Name: {business_stats.user.business_name if business_stats.user else 'N/A'}")
        print(f"Credits Allocated: {business_stats.credits_allocated}")
        print(f"Credits Used: {business_stats.credits_used}")
        print(f"Credits Remaining: {business_stats.credits_remaining}")
        print(f"Messages Sent: {business_stats.messages_sent}")
        print(f"Messages Delivered: {business_stats.messages_delivered}")
        print(f"Messages Failed: {business_stats.messages_failed}")
        print(f"Active Devices: {business_stats.active_devices}")
        print(f"Total Devices: {business_stats.total_devices}")
        print(f"Active Sessions: {business_stats.active_sessions}")
        print(f"Total Sessions: {business_stats.total_sessions}")
        print(f"Revenue Generated: ${business_stats.revenue_generated}")
        print(f"Credit Utilization: {business_stats.calculate_credit_utilization():.2f}%")
        print(f"Delivery Rate: {business_stats.calculate_delivery_rate():.2f}%")
        
        # Show analytics summary
        summary = analytics_service.get_analytics_summary()
        print(f"\nOverall Analytics Summary:")
        print(f"  Total Resellers: {summary.total_resellers}")
        print(f"  Total Credits Purchased: {summary.total_credits_purchased}")
        print(f"  Total Credits Distributed: {summary.total_credits_distributed}")
        print(f"  Total Credits Used: {summary.total_credits_used}")
        print(f"  Total Remaining Credits: {summary.total_remaining_credits}")
        print(f"  Total Revenue: ${summary.total_revenue}")
        print(f"  Total Business Users: {summary.total_business_users}")
        print(f"  Total Messages Sent: {summary.total_messages_sent}")
        print(f"  Average Credit Utilization: {summary.average_credit_utilization:.2f}%")
        print(f"  Average Delivery Rate: {summary.average_delivery_rate:.2f}%")
        
        # Show top performers
        top_performers = analytics_service.get_top_performers(limit=5)
        print(f"\nTop 5 Performers by Revenue:")
        for i, performer in enumerate(top_performers.top_resellers_by_revenue, 1):
            print(f"  {i}. {performer.reseller_name or performer.reseller_id}: ${performer.total_revenue} (Rank: {performer.rank})")
        
        print(f"\nTop 5 Performers by Credits Distributed:")
        for i, performer in enumerate(top_performers.top_resellers_by_credits, 1):
            print(f"  {i}. {performer.reseller_name or performer.reseller_id}: {performer.total_credits_distributed} credits")
        
        print(f"\nTop 5 Performers by Business Users:")
        for i, performer in enumerate(top_performers.top_resellers_by_users, 1):
            print(f"  {i}. {performer.reseller_name or performer.reseller_id}: {performer.total_business_users} users")
        
        # Show analytics trends
        trends = analytics_service.get_analytics_trends("uuid-reseller-001", AnalyticsPeriod.MONTHLY, 6)
        print(f"\nAnalytics Trends (Last 6 Months):")
        print(f"  Period: {trends.period}")
        print(f"  Trend Data Points: {len(trends.trend_data)}")
        if trends.trend_data:
            latest = trends.trend_data[-1]
            print(f"  Latest Period:")
            print(f"    Period Start: {latest['period_start']}")
            print(f"    Total Credits Purchased: {latest['total_credits_purchased']}")
            print(f"    Total Credits Distributed: {latest['total_credits_distributed']}")
            print(f"    Total Credits Used: {latest['total_credits_used']}")
            print(f"    Total Revenue: ${latest['total_revenue']}")
            print(f"    Total Business Users: {latest['total_business_users']}")
            print(f"    Total Messages Sent: {latest['total_messages_sent']}")
            print(f"    Credit Utilization: {latest['credit_utilization']:.2f}%")
            print(f"    Delivery Rate: {latest['delivery_rate']:.2f}%")
        
        # Show health check
        health_check = analytics_service.get_health_check()
        print(f"\nAnalytics Health Check:")
        print(f"  Status: {health_check.status}")
        print(f"  Total Analytics Records: {health_check.total_analytics_records}")
        print(f"  Last Updated: {health_check.last_updated}")
        print(f"  Data Freshness: {health_check.data_freshness}")
        if health_check.issues:
            print(f"  Issues: {', '.join(health_check.issues)}")
        if health_check.recommendations:
            print(f"  Recommendations: {', '.join(health_check.recommendations)}")
        
    except ValueError as e:
        print(f"Error creating analytics: {e}")
    
    db.close()

if __name__ == "__main__":
    # Create tables
    from db.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample reseller analytics
    create_sample_reseller_analytics()

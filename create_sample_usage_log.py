from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from models.message_usage_log import MessageUsageLog, UsageType, UsageStatus
from models.user import User
from models.message import Message
from services.message_usage_log_service import MessageUsageLogService
from schemas.message_usage_log import UsageLogCreateRequest
from datetime import datetime

def create_sample_usage_log():
    db = SessionLocal()
    usage_service = MessageUsageLogService(db)
    
    # Check if usage log already exists
    existing_usage = db.query(MessageUsageLog).filter(MessageUsageLog.usage_id == "usage-333").first()
    if existing_usage:
        print("Sample usage log already exists!")
        return
    
    # Check if user exists
    user = db.query(User).filter(User.user_id == "uuid-business-101").first()
    if not user:
        print("User not found! Please create the sample business owner first.")
        return
    
    # Check if message exists
    message = db.query(Message).filter(Message.message_id == "msg-9001").first()
    if not message:
        print("Message not found! Please create the sample message first.")
        return
    
    # Create sample usage log
    usage_request = UsageLogCreateRequest(
        user_id="uuid-business-101",
        message_id="msg-9001",
        usage_type=UsageType.MESSAGE_SEND,
        credits_deducted=1,
        balance_before=1800,
        message_type="text",
        message_size=150,
        recipient_count=1,
        ip_address="192.168.1.10",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        api_endpoint="/api/messages/send",
        request_id="req-12345"
    )
    
    try:
        usage_response = usage_service.create_usage_log(usage_request)
        
        # Update usage log with sample data
        usage = usage_service.get_usage_log_by_id(usage_response.usage_id)
        usage.usage_id = "usage-333"
        usage.created_at = datetime(2026, 1, 6, 12, 15, 1)
        usage.timestamp = datetime(2026, 1, 6, 12, 15, 1)
        usage.balance_after = 1799
        usage.status = UsageStatus.SUCCESS
        usage.delivery_status = "sent"
        usage.processed_at = datetime(2026, 1, 6, 12, 15, 2)
        
        db.commit()
        db.refresh(usage)
        
        print(f"Sample usage log created:")
        print(f"Usage ID: {usage.usage_id}")
        print(f"User ID: {usage.user_id}")
        print(f"Message ID: {usage.message_id}")
        print(f"Usage Type: {usage.usage_type}")
        print(f"Credits Deducted: {usage.credits_deducted}")
        print(f"Balance Before: {usage.balance_before}")
        print(f"Balance After: {usage.balance_after}")
        print(f"Total Cost: ${usage.total_cost}")
        print(f"Status: {usage.status}")
        print(f"Delivery Status: {usage.delivery_status}")
        print(f"Created At: {usage.created_at}")
        print(f"Timestamp: {usage.timestamp}")
        print(f"Processed At: {usage.processed_at}")
        print(f"IP Address: {usage.ip_address}")
        print(f"API Endpoint: {usage.api_endpoint}")
        print(f"Request ID: {usage.request_id}")
        
        # Show usage validation
        print(f"\nUsage Validation:")
        print(f"  Is Successful: {usage.is_successful()}")
        print(f"  Is Refunded: {usage.is_refunded()}")
        print(f"  Net Credit Usage: {usage.get_net_credit_usage()}")
        print(f"  Can Be Refunded: {usage.can_be_refunded()}")
        
        # Show usage summary
        summary = usage.get_usage_summary()
        print(f"\nUsage Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Show user usage stats
        user_stats = usage_service.get_user_usage_stats("uuid-business-101", days=30)
        print(f"\nUser Usage Stats:")
        print(f"  Total Usage: {user_stats.total_usage}")
        print(f"  Total Credits Deducted: {user_stats.total_credits_deducted}")
        print(f"  Total Credits Refunded: {user_stats.total_credits_refunded}")
        print(f"  Net Credits Used: {user_stats.net_credits_used}")
        print(f"  Total Cost: ${user_stats.total_cost}")
        print(f"  Current Balance: {user_stats.current_balance}")
        print(f"  Usage By Type: {user_stats.usage_by_type}")
        print(f"  Usage By Status: {user_stats.usage_by_status}")
        
        # Show overall usage stats
        from schemas.message_usage_log import UsageFilter
        overall_stats = usage_service.get_usage_stats(UsageFilter())
        print(f"\nOverall Usage Stats:")
        print(f"  Total Usage: {overall_stats.total_usage}")
        print(f"  Total Credits Deducted: {overall_stats.total_credits_deducted}")
        print(f"  Total Credits Refunded: {overall_stats.total_credits_refunded}")
        print(f"  Net Credits Used: {overall_stats.net_credits_used}")
        print(f"  Total Cost: ${overall_stats.total_cost}")
        print(f"  Successful Usage: {overall_stats.successful_usage}")
        print(f"  Failed Usage: {overall_stats.failed_usage}")
        print(f"  Refunded Usage: {overall_stats.refunded_usage}")
        print(f"  Average Cost Per Usage: ${overall_stats.average_cost_per_usage:.4f}")
        print(f"  Usage By Type: {overall_stats.usage_by_type}")
        print(f"  Usage By Status: {overall_stats.usage_by_status}")
        
    except ValueError as e:
        print(f"Error creating usage log: {e}")
    
    db.close()

if __name__ == "__main__":
    # Create tables
    from db.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample usage log
    create_sample_usage_log()

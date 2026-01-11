from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from models.message import Message
from models.user import User
from services.message_service import MessageService
from schemas.message import MessageCreate
from datetime import datetime

def create_sample_message():
    db = SessionLocal()
    message_service = MessageService(db)
    
    # Check if message already exists
    existing_message = db.query(Message).filter(Message.message_id == "msg-9001").first()
    if existing_message:
        print("Sample message already exists!")
        return
    
    # Check if business owner exists
    business_owner = db.query(User).filter(User.user_id == "uuid-business-101").first()
    if not business_owner:
        print("Business owner not found! Please create the sample business owner first.")
        return
    
    # Create sample message
    message_data = MessageCreate(
        user_id="uuid-business-101",
        channel="whatsapp",
        mode="unofficial",
        sender_number="+918888888888",
        receiver_number="+917777777777",
        message_type="otp",
        template_name=None,
        message_body="Your OTP is 458912",
        credits_used=1
    )
    
    try:
        message = message_service.create_message(message_data)
        
        print(f"Sample message created:")
        print(f"Message ID: {message.message_id}")
        print(f"User ID: {message.user_id}")
        print(f"Channel: {message.channel}")
        print(f"Mode: {message.mode}")
        print(f"Sender: {message.sender_number}")
        print(f"Receiver: {message.receiver_number}")
        print(f"Message Type: {message.message_type}")
        print(f"Message Body: {message.message_body}")
        print(f"Status: {message.status}")
        print(f"Credits Used: {message.credits_used}")
        print(f"Sent At: {message.sent_at}")
        
        # Show updated business owner stats
        updated_business_owner = db.query(User).filter(User.user_id == "uuid-business-101").first()
        print(f"\nUpdated Business Owner Credits:")
        print(f"  Credits Used: {updated_business_owner.credits_used}")
        print(f"  Credits Remaining: {updated_business_owner.credits_remaining}")
        
        # Show message stats
        stats = message_service.get_message_stats("uuid-business-101")
        print(f"\nMessage Statistics:")
        print(f"  Total Messages: {stats.total_messages}")
        print(f"  Messages Sent: {stats.messages_sent}")
        print(f"  Total Credits Used: {stats.total_credits_used}")
        
    except ValueError as e:
        print(f"Error creating message: {e}")
    
    db.close()

if __name__ == "__main__":
    # Create tables
    from db.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample message
    create_sample_message()

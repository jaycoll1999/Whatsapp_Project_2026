from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from models.unofficial_device import UnofficialLinkedDevice
from models.user import User
from services.unofficial_device_service import UnofficialDeviceService
from schemas.unofficial_device import UnofficialDeviceCreate
from datetime import datetime

def create_sample_device():
    db = SessionLocal()
    device_service = UnofficialDeviceService(db)
    
    # Check if device already exists
    existing_device = db.query(UnofficialLinkedDevice).filter(UnofficialLinkedDevice.device_id == "device-001").first()
    if existing_device:
        print("Sample device already exists!")
        return
    
    # Check if business owner exists
    business_owner = db.query(User).filter(User.user_id == "uuid-business-101").first()
    if not business_owner:
        print("Business owner not found! Please create the sample business owner first.")
        return
    
    # Create sample device
    device_data = UnofficialDeviceCreate(
        user_id="uuid-business-101",
        device_name="Chrome on Windows",
        device_type="web",
        device_os="Windows",
        browser_info="Chrome 120.0.0.0",
        ip_address="192.168.1.10",
        max_daily_messages=1000
    )
    
    try:
        device = device_service.create_device(device_data)
        
        # Update device with sample data
        device.session_status = "connected"
        device.qr_last_generated = datetime(2026, 1, 6, 11, 0, 0)
        device.last_active = datetime(2026, 1, 6, 12, 20, 0)
        device.last_connected_at = datetime(2026, 1, 6, 11, 30, 0)
        device.messages_sent = 45
        device.messages_received = 38
        device.total_activity_time = 120  # 2 hours in minutes
        device.daily_message_count = 15
        device.connection_string = "wa-session-abc123def456"
        
        db.commit()
        db.refresh(device)
        
        print(f"Sample unofficial linked device created:")
        print(f"Device ID: {device.device_id}")
        print(f"User ID: {device.user_id}")
        print(f"Device Name: {device.device_name}")
        print(f"Device Type: {device.device_type}")
        print(f"Device OS: {device.device_os}")
        print(f"Browser Info: {device.browser_info}")
        print(f"Session Status: {device.session_status}")
        print(f"IP Address: {device.ip_address}")
        print(f"QR Last Generated: {device.qr_last_generated}")
        print(f"Last Active: {device.last_active}")
        print(f"Messages Sent: {device.messages_sent}")
        print(f"Messages Received: {device.messages_received}")
        print(f"Daily Message Count: {device.daily_message_count}")
        print(f"Max Daily Messages: {device.max_daily_messages}")
        print(f"Total Activity Time: {device.total_activity_time} minutes")
        print(f"Is Active: {device.is_active}")
        
        # Show device stats
        stats = device_service.get_device_stats(device.device_id)
        print(f"\nDevice Statistics:")
        print(f"  Session Status: {stats.session_status}")
        print(f"  Messages Sent: {stats.messages_sent}")
        print(f"  Messages Received: {stats.messages_received}")
        print(f"  Daily Usage: {stats.daily_message_count}/{stats.max_daily_messages}")
        print(f"  Uptime Percentage: {stats.uptime_percentage:.2f}%")
        
        # Show user device stats
        user_stats = device_service.get_user_device_stats("uuid-business-101")
        print(f"\nUser Device Statistics:")
        print(f"  Total Devices: {user_stats.total_devices}")
        print(f"  Active Devices: {user_stats.active_devices}")
        print(f"  Connected Devices: {user_stats.connected_devices}")
        print(f"  Total Messages Sent: {user_stats.total_messages_sent}")
        print(f"  Total Messages Received: {user_stats.total_messages_received}")
        
    except ValueError as e:
        print(f"Error creating device: {e}")
    
    db.close()

if __name__ == "__main__":
    # Create tables
    from db.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample device
    create_sample_device()

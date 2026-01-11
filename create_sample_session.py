from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from models.device_session import DeviceSession
from models.unofficial_device import UnofficialLinkedDevice
from services.device_session_service import DeviceSessionService
from schemas.device_session import SessionCreateRequest
from datetime import datetime

def create_sample_session():
    db = SessionLocal()
    session_service = DeviceSessionService(db)
    
    # Check if session already exists
    existing_session = db.query(DeviceSession).filter(DeviceSession.session_id == "session-777").first()
    if existing_session:
        print("Sample device session already exists!")
        return
    
    # Check if device exists
    device = db.query(UnofficialLinkedDevice).filter(UnofficialLinkedDevice.device_id == "device-001").first()
    if not device:
        print("Device not found! Please create the sample device first.")
        return
    
    # Create sample session
    session_request = SessionCreateRequest(
        device_id="device-001",
        session_data="sample_encrypted_session_data_for_whatsapp_web",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ip_address="192.168.1.10",
        expires_in_hours=24
    )
    
    try:
        session_response = session_service.create_session(session_request)
        
        # Update session with sample data
        session = session_service.get_session_by_id(session_response.session_id)
        session.session_id = "session-777"
        session.created_at = datetime(2026, 1, 6, 11, 5, 0)
        session.expires_at = datetime(2026, 1, 7, 11, 5, 0)
        session.last_activity = datetime(2026, 1, 6, 12, 20, 0)
        session.last_successful_login = datetime(2026, 1, 6, 11, 30, 0)
        session.total_requests = 156
        session.messages_sent_via_session = 23
        session.is_valid = True
        session.is_active = True
        
        db.commit()
        db.refresh(session)
        
        print(f"Sample device session created:")
        print(f"Session ID: {session.session_id}")
        print(f"Device ID: {session.device_id}")
        print(f"Session Type: {session.session_type}")
        print(f"Is Valid: {session.is_valid}")
        print(f"Is Active: {session.is_active}")
        print(f"User Agent: {session.user_agent}")
        print(f"IP Address: {session.ip_address}")
        print(f"Created At: {session.created_at}")
        print(f"Expires At: {session.expires_at}")
        print(f"Last Activity: {session.last_activity}")
        print(f"Total Requests: {session.total_requests}")
        print(f"Messages Sent Via Session: {session.messages_sent_via_session}")
        print(f"Login Attempts: {session.login_attempts}")
        print(f"Max Login Attempts: {session.max_login_attempts}")
        print(f"Is Compromised: {session.is_compromised}")
        print(f"Requires Reauth: {session.requires_reauth}")
        
        # Show session validation
        validation = session_service.validate_session(session.session_id)
        print(f"\nSession Validation:")
        print(f"  Is Valid: {validation.is_valid}")
        print(f"  Is Active: {validation.is_active}")
        print(f"  Is Expired: {validation.is_expired}")
        print(f"  Is Compromised: {validation.is_compromised}")
        print(f"  Message: {validation.message}")
        
        # Show session stats
        stats = session_service.get_session_stats(session.session_id)
        print(f"\nSession Statistics:")
        print(f"  Status: {stats.status}")
        print(f"  Uptime Hours: {stats.uptime_hours:.2f}")
        print(f"  Requests Per Hour: {stats.requests_per_hour:.2f}")
        print(f"  Total Requests: {stats.total_requests}")
        print(f"  Messages Sent: {stats.messages_sent_via_session}")
        
        # Show device session stats
        device_stats = session_service.get_device_session_stats("device-001")
        print(f"\nDevice Session Statistics:")
        print(f"  Total Sessions: {device_stats.total_sessions}")
        print(f"  Active Sessions: {device_stats.active_sessions}")
        print(f"  Expired Sessions: {device_stats.expired_sessions}")
        print(f"  Revoked Sessions: {device_stats.revoked_sessions}")
        print(f"  Compromised Sessions: {device_stats.compromised_sessions}")
        print(f"  Average Session Duration: {device_stats.average_session_duration:.2f} hours")
        
        # Show security check
        security = session_service.security_check(session.session_id)
        print(f"\nSecurity Check:")
        print(f"  Risk Level: {security.risk_level}")
        print(f"  Security Issues: {security.security_issues}")
        print(f"  Recommendations: {security.recommendations}")
        
        # Show health check
        health = session_service.health_check(session.session_id)
        print(f"\nHealth Check:")
        print(f"  Is Healthy: {health.is_healthy}")
        print(f"  Health Score: {health.health_score:.2f}")
        print(f"  Issues: {health.issues}")
        print(f"  Recommendations: {health.recommendations}")
        
    except ValueError as e:
        print(f"Error creating session: {e}")
    
    db.close()

if __name__ == "__main__":
    # Create tables
    from db.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample session
    create_sample_session()
